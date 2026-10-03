#!/usr/bin/env python3
"""
m2_ilp/model.py — Module 2, yêu cầu 2.2–2.4 + 2.7
=====================================================================
Mô hình CP-SAT lõi cho bài toán phân công giám thị.

Biến quyết định (2.2)
    x[i, j] ∈ {0, 1}   — giám thị i được gán vào ca j hay không.

Năm ràng buộc CỨNG (2.3) — dịch 1-1 từ `m1_logic/spec.md`, không thêm không bớt:
    H1  không trùng ca      Overlap(j,k) → x[i,j] + x[i,k] ≤ 1
    H2  tôn trọng lịch bận  Busy(i,j)    → x[i,j] = 0
    H3  đủ điều kiện        ¬Eligible(i,j) → x[i,j] = 0
    H4  toàn vẹn dữ liệu    ca không có cơ sở → x[i,j] = 0 với mọi i
    H5  đúng sĩ số          Σᵢ x[i,j] = Cap(j)

Hai ràng buộc MỀM (2.5) nằm ở `m2_ilp/soft.py`, không lặp lại ở đây:
    S1  ưu tiên cơ sở       w_loc  · Σ Viol_loc(i,j)
    S2  giới hạn mệt mỏi    w_load · Σ Viol_load(i)
`spec.md` ghi rõ MaxLoad là ràng buộc MỀM, nên ở đây KHÔNG có ràng buộc cứng
nào chặn tải — vượt tải bị phạt, không bị cấm.

Hàm mục tiêu (2.7) — TỪ ĐIỂN (lexicographic), hai pha:
    Pha 1   tối thiểu t, với t ≥ Load(i) ∀i          → t*  (min-max, công bằng
            theo nghĩa không ai phải gánh nhiều hơn mức cần thiết)
    Pha 2   thêm ràng buộc t ≤ t*, rồi tối thiểu
                w_fair · Σᵢ |Load(i) − q|            (độ lệch L1)
              + w_loc  · Σ Viol_loc
              + w_load · Σ Viol_load
            với q = ⌊ΣCap / |I|⌋ là tải lý tưởng nguyên.

Vì sao hai pha chứ không gộp một hàm có trọng số: gộp lại thì một nghiệm
"rất công bằng theo L1 nhưng có một người gánh 4 ca" có thể thắng một nghiệm
min-max tốt hơn, tùy trọng số. Từ điển bảo đảm min-max không bao giờ bị đánh đổi.

TRỌNG SỐ: ba trọng số mềm lấy từ `tools/make_seed.py` (hàm `soft_weights`), tức
sinh từ Team ID của nhóm và người chấm tính lại ra đúng ba số đó. KHÔNG tự rút
số ngẫu nhiên mới ở bất cứ đâu trong file này.
    nhóm CO2011-261-A01-2551905 → seed 43003334 → [0.71, 1.62, 1.33]
    w_loc = 0.71   w_load = 1.62   w_fair = 1.33

Cách dùng từ run_all.py:
    from m2_ilp.model import build_params, solve_week
    params = build_params(instance, m2_data)
    kq = solve_week(params, lambdas=None)

Chạy độc lập để test:
    python m2_ilp/model.py --instance data/instance_slice.json --seed-file data/seed.txt
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

from ortools.sat.python import cp_model

# Trọng số mềm có đúng 2 chữ số thập phân (make_seed.py làm tròn 2), nên nhân
# 100 là đủ để đưa về số nguyên cho CP-SAT mà KHÔNG mất mát làm tròn nào.
SCALE = 100


# ---------------------------------------------------------------------------
# 0. Trọng số mềm — phải trùng tools/make_seed.py từng số
# ---------------------------------------------------------------------------
def soft_weights_from_seed(seed_int: int) -> list[float]:
    """Ba trọng số mềm trong [0.5, 2.0], rút THEO THỨ TỰ từ random.Random(seed),
    làm tròn 2 chữ số — y hệt `tools/make_seed.py: soft_weights()`.

    Phần `round(..., 2)` là bắt buộc: người chấm tính lại bằng make_seed.py nên
    bỏ round sẽ ra 0.7054693790735072 thay vì 0.71, và mọi con số trong báo cáo
    lệch theo.
    """
    rng = random.Random(seed_int)
    return [round(rng.uniform(0.5, 2.0), 2) for _ in range(3)]


def _as_int_coef(w: float) -> int:
    """Đưa trọng số float về hệ số nguyên cho CP-SAT."""
    return int(round(w * SCALE))


# ---------------------------------------------------------------------------
# 1. Gộp tham số: m2_data (của preprocess.py) + instance (của slice_builder.py)
# ---------------------------------------------------------------------------
def build_params(instance: dict, m2_data: dict | None = None) -> dict:
    """Trả về một dict tham số duy nhất mà `solve_week` cần.

    `m2_ilp/preprocess.py` (task 6) hiện trả I, J, capacity, busy, campus,
    preferences — nhưng KHÔNG trả `overlap` (cần cho H1) và `max_load` (cần cho
    S2). Hai thứ đó nằm trong `instance` do slice_builder sinh. Hàm này gộp lại
    thay vì sửa đầu ra của preprocess.py, để hợp đồng dữ liệu của task 6 không
    bị đổi sau lưng người viết nó.
    """
    p: dict[str, Any] = {}
    if m2_data:
        p.update({k: m2_data[k] for k in
                  ("I", "J", "capacity", "busy", "campus", "preferences")
                  if k in m2_data})
    p.setdefault("I", sorted(instance["invigilators"]))
    p.setdefault("J", sorted(instance["shifts"]))
    p.setdefault("capacity", dict(instance["capacity"]))
    p.setdefault("campus", dict(instance["campus_of"]))
    p.setdefault("preferences", {})
    if "busy" not in p:
        p["busy"] = {f"{i}|{j}": True for i, j in instance.get("busy", [])}

    # overlap: danh sách cặp ca chồng giờ, chuẩn hóa về tập cặp có thứ tự
    p["overlap"] = [tuple(pair) for pair in instance.get("overlap", [])]
    # eligible: tập (i, j) hợp lệ. Thiếu field -> coi như mọi cặp đều hợp lệ.
    el = instance.get("eligible")
    p["eligible"] = {(i, j) for i, j in el} if el else None
    # max_load: ngưỡng MỀM của S2, theo từng người
    p["max_load"] = dict(instance.get("max_load", {}))
    p["meta"] = instance.get("meta", {})
    return p


# ---------------------------------------------------------------------------
# 2. Dựng mô hình
# ---------------------------------------------------------------------------
def _build(params: dict) -> tuple[cp_model.CpModel, dict, dict, Any]:
    """Dựng model với 5 ràng buộc cứng. Trả (model, x, load, t)."""
    I, J = params["I"], params["J"]
    cap, campus = params["capacity"], params["campus"]
    busy, eligible = params["busy"], params["eligible"]

    model = cp_model.CpModel()
    x = {(i, j): model.NewBoolVar(f"x[{i},{j}]") for i in I for j in J}

    # H4 — toàn vẹn dữ liệu: ca không có cơ sở xác định thì không ai được gán.
    ca_khong_co_so = [j for j in J if not campus.get(j)]
    for j in ca_khong_co_so:
        for i in I:
            model.Add(x[i, j] == 0)

    # H2 — lịch bận  |  H3 — đủ điều kiện
    for i in I:
        for j in J:
            if busy.get(f"{i}|{j}", False):
                model.Add(x[i, j] == 0)
            if eligible is not None and (i, j) not in eligible:
                model.Add(x[i, j] == 0)

    # H1 — không trùng ca
    for j, k in params["overlap"]:
        if j in cap and k in cap:
            for i in I:
                model.Add(x[i, j] + x[i, k] <= 1)

    # H5 — đúng sĩ số (bỏ qua ca đã bị H4 cấm, nếu không sẽ vô nghiệm hiển nhiên)
    for j in J:
        if j in ca_khong_co_so:
            continue
        model.Add(sum(x[i, j] for i in I) == int(cap[j]))

    # Biến dẫn xuất: tải của từng người, và trần min-max t
    load = {}
    for i in I:
        v = model.NewIntVar(0, len(J), f"load[{i}]")
        model.Add(v == sum(x[i, j] for j in J))
        load[i] = v
    t = model.NewIntVar(0, len(J), "t_minmax")
    for i in I:
        model.Add(t >= load[i])

    return model, x, load, t


def _l1_deviation(model: cp_model.CpModel, load: dict, q: int, J: list) -> tuple[list, int]:
    """Σᵢ |Load(i) − q| với q là tải lý tưởng nguyên. Trả (danh sách dev, q)."""
    devs = []
    for i, li in load.items():
        d = model.NewIntVar(0, len(J), f"dev[{i}]")
        model.AddAbsEquality(d, li - q)
        devs.append(d)
    return devs, q


# ---------------------------------------------------------------------------
# 3. Giải — hai pha từ điển
# ---------------------------------------------------------------------------
def solve_week(
    params: dict,
    lambdas: dict[str, float] | None = None,
    *,
    seed_int: int | None = None,
    time_limit_s: float = 60.0,
    workers: int = 1,
    verbose: bool = True,
) -> dict:
    """Giải một tuần phân công. Đây là hàm M4 (rolling-horizon) gọi lại.

    params      — đầu ra của build_params()
    lambdas     — trọng số phạt mệt mỏi cộng thêm cho từng người, do M4 bơm vào:
                  cộng + Σᵢ lambdas[i] · Load(i) vào hàm mục tiêu pha 2.
                  None nghĩa là M2 thuần, không có vòng phản hồi.
    seed_int    — để lấy 3 trọng số mềm. Mặc định đọc params["meta"]["seed"].
    workers     — MẶC ĐỊNH 1, có lý do: CP-SAT chạy nhiều luồng thì khi bài toán
                  có nhiều nghiệm tối ưu bằng điểm, luồng nào về trước quyết định
                  nghiệm trả ra, nên bảng phân công có thể đổi giữa hai lần chạy
                  trên hai máy khác số nhân. Giá trị objective vẫn như nhau, nhưng
                  "một lệnh tái tạo MỌI con số" (DoD của đề) gồm cả bảng phân công.
                  Mô hình hiện tại 108 biến, giải trong 0,02s nên 1 luồng không đắt.
                  Khi mô hình lớn lên thì tăng lên, và ghi rõ trong báo cáo rằng
                  chỉ objective là tái lập được.

    Trả về dict đã mô tả ở cuối hàm; `status` là tên trạng thái của CP-SAT.
    """
    from m2_ilp.soft import build_soft_penalty_terms

    I, J = params["I"], params["J"]
    if seed_int is None:
        seed_int = int(params.get("meta", {}).get("seed", 0))
    w_loc, w_load, w_fair = soft_weights_from_seed(seed_int)

    tong_cap = sum(int(v) for v in params["capacity"].values())
    q = tong_cap // max(len(I), 1)

    t0 = time.perf_counter()

    # ---- Pha 1: min-max ----
    model, x, load, t = _build(params)
    model.Minimize(t)
    s1 = cp_model.CpSolver()
    s1.parameters.max_time_in_seconds = time_limit_s
    s1.parameters.num_workers = workers
    s1.parameters.random_seed = seed_int % (2**31 - 1)
    st1 = s1.Solve(model)
    if st1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": s1.StatusName(st1),
            "feasible": False,
            "phase": 1,
            "message": ("Pha 1 không tìm được nghiệm khả thi — 5 ràng buộc cứng "
                        "mâu thuẫn. Đối chiếu m1_logic/out/unsat_core.json để biết "
                        "họ ràng buộc nào là nguyên nhân (yêu cầu 2.8)."),
            "runtime_s": round(time.perf_counter() - t0, 3),
            "weights": {"w_loc": w_loc, "w_load": w_load, "w_fair": w_fair},
        }
    t_star = int(s1.Value(t))
    if verbose:
        print(f"[m2_model] Pha 1 (min-max): t* = {t_star} ca/người  "
              f"({s1.StatusName(st1)}, {s1.WallTime():.2f}s)")

    # ---- Pha 2: cố định t ≤ t*, tối thiểu L1 + phạt mềm ----
    model, x, load, t = _build(params)
    model.Add(t <= t_star)

    devs, q = _l1_deviation(model, load, q, J)
    pen_terms = build_soft_penalty_terms(model, x, params, seed_int)

    muc_tieu = _as_int_coef(w_fair) * sum(devs) + sum(pen_terms)
    if lambdas:
        muc_tieu += sum(_as_int_coef(float(lambdas.get(i, 0.0))) * load[i] for i in I)
    model.Minimize(muc_tieu)

    s2 = cp_model.CpSolver()
    s2.parameters.max_time_in_seconds = time_limit_s
    s2.parameters.num_workers = workers
    s2.parameters.random_seed = seed_int % (2**31 - 1)
    st2 = s2.Solve(model)
    if st2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": s2.StatusName(st2), "feasible": False, "phase": 2,
            "t_star": t_star,
            "message": "Pha 2 thất bại dù pha 1 khả thi — gần như chắc là hết thời gian.",
            "runtime_s": round(time.perf_counter() - t0, 3),
            "weights": {"w_loc": w_loc, "w_load": w_load, "w_fair": w_fair},
        }

    # ---- Trích nghiệm & tính lại MỌI chỉ số từ nghiệm, không tin objective ----
    assignment = sorted([i, j] for i in I for j in J if s2.Value(x[i, j]) == 1)
    tai = {i: int(s2.Value(load[i])) for i in I}

    vi_pham_loc = 0
    for i, j in assignment:
        pc = params["preferences"].get(i, {}).get("prefer_campus")
        if pc and params["campus"].get(j) != pc:
            vi_pham_loc += 1
    vi_pham_load = {i: max(0, tai[i] - int(params["max_load"].get(i, 10**9)))
                    for i in I}
    tong_vi_pham_load = sum(vi_pham_load.values())

    trung_binh = tong_cap / max(len(I), 1)
    lech_l1_q = sum(abs(tai[i] - q) for i in I)
    lech_l1_tb = sum(abs(tai[i] - trung_binh) for i in I)

    kq = {
        "status": s2.StatusName(st2),
        "feasible": True,
        "t_star": t_star,
        "q_ideal": q,
        "assignment": assignment,
        "load": tai,
        "weights": {"w_loc": w_loc, "w_load": w_load, "w_fair": w_fair,
                    "nguon": "tools/make_seed.py soft_weights(TEAM_ID)",
                    "seed_int": seed_int},
        "fairness": {
            "tai_lon_nhat": max(tai.values()) if tai else 0,
            "tai_nho_nhat": min(tai.values()) if tai else 0,
            "khoang_tai": (max(tai.values()) - min(tai.values())) if tai else 0,
            "lech_L1_quanh_q": lech_l1_q,
            "lech_L1_quanh_trung_binh": round(lech_l1_tb, 4),
            "tai_trung_binh": round(trung_binh, 4),
        },
        "soft": {
            "vi_pham_S1_loc": vi_pham_loc,
            "vi_pham_S2_load": tong_vi_pham_load,
            "phat_S1": round(w_loc * vi_pham_loc, 4),
            "phat_S2": round(w_load * tong_vi_pham_load, 4),
            "phat_cong_bang": round(w_fair * lech_l1_q, 4),
        },
        "objective_scaled": int(s2.ObjectiveValue()),
        "objective": round(s2.ObjectiveValue() / SCALE, 4),
        "runtime_s": round(time.perf_counter() - t0, 3),
        "lambdas_da_dung": bool(lambdas),
    }

    # ---- Tự kiểm 5 ràng buộc cứng TRÊN NGHIỆM, không tin solver ----
    kq["kiem_rang_buoc_cung"] = _kiem_nghiem(params, assignment)
    if verbose:
        _in_ket_qua(kq)
    return kq


def _kiem_nghiem(params: dict, assignment: list) -> dict:
    """Kiểm lại từng ràng buộc cứng trên nghiệm trả về. Mọi giá trị phải là True
    — nếu có False thì mô hình sai, không phải dữ liệu sai."""
    gan = {(i, j) for i, j in assignment}
    cap, campus = params["capacity"], params["campus"]
    tai: dict[str, int] = {}
    for i, _ in assignment:
        tai[i] = tai.get(i, 0) + 1

    h1 = all(not ((i, j) in gan and (i, k) in gan)
             for j, k in params["overlap"] for i in params["I"])
    h2 = all(not params["busy"].get(f"{i}|{j}", False) for i, j in gan)
    h3 = (params["eligible"] is None
          or all((i, j) in params["eligible"] for i, j in gan))
    h4 = all(campus.get(j) for _, j in gan)
    h5 = all(sum(1 for i, jj in gan if jj == j) == int(cap[j])
             for j in params["J"] if campus.get(j))
    return {"H1_khong_trung_ca": h1, "H2_lich_ban": h2, "H3_du_dieu_kien": h3,
            "H4_toan_ven_du_lieu": h4, "H5_dung_si_so": h5,
            "tat_ca_dat": all([h1, h2, h3, h4, h5])}


def _in_ket_qua(kq: dict) -> None:
    f, s = kq["fairness"], kq["soft"]
    print(f"[m2_model] Pha 2 ({kq['status']}): objective = {kq['objective']} "
          f"(thang {SCALE}: {kq['objective_scaled']})")
    print(f"[m2_model]   {len(kq['assignment'])} lượt gán · tải "
          f"{f['tai_nho_nhat']}–{f['tai_lon_nhat']} (khoảng {f['khoang_tai']}) · "
          f"lệch L1 quanh q={kq['q_ideal']}: {f['lech_L1_quanh_q']}")
    print(f"[m2_model]   S1 vi phạm cơ sở: {s['vi_pham_S1_loc']} "
          f"(phạt {s['phat_S1']}) · S2 vượt tải: {s['vi_pham_S2_load']} "
          f"(phạt {s['phat_S2']})")
    kiem = kq["kiem_rang_buoc_cung"]
    xau = [k for k, v in kiem.items() if k != "tat_ca_dat" and not v]
    print(f"[m2_model]   tự kiểm ràng buộc cứng: "
          f"{'5/5 ĐẠT' if kiem['tat_ca_dat'] else 'HỎNG ở ' + ', '.join(xau)}")
    print(f"[m2_model]   thời gian: {kq['runtime_s']}s")


# ---------------------------------------------------------------------------
# 4. CLI — chỉ để test độc lập
# ---------------------------------------------------------------------------
def _doc_seed(duong_dan: str) -> int:
    raw = Path(duong_dan).read_text(encoding="utf-8-sig").strip()
    if not raw.isdigit():
        raise ValueError(f"{duong_dan} phải chỉ chứa chữ số")
    return int(raw)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chạy độc lập mô hình CP-SAT M2 (2.2–2.4, 2.7)")
    ap.add_argument("--instance", default="data/instance_slice.json")
    ap.add_argument("--seed-file", default="data/seed.txt")
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=1,
                    help="1 de bao dam tai lap duoc nghiem (xem docstring solve_week)")
    ap.add_argument("--out", default="m2_ilp/out/solution.json")
    a = ap.parse_args(argv)

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        seed_int = _doc_seed(a.seed_file)
        instance = json.loads(Path(a.instance).read_text(encoding="utf-8-sig"))
        from m2_ilp.preprocess import run as run_preprocess
        m2_data = run_preprocess(instance, seed_int=seed_int)
        params = build_params(instance, m2_data)
        kq = solve_week(params, seed_int=seed_int, time_limit_s=a.time_limit,
                        workers=a.workers)
    except (FileNotFoundError, KeyError, ValueError, TypeError) as e:
        print(f"[m2_model] LỖI: {e}", file=sys.stderr)
        return 1

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kq, ensure_ascii=False, indent=2, sort_keys=True),
                   encoding="utf-8")
    print(f"[m2_model] Đã ghi {out}")
    return 0 if kq.get("feasible") and kq["kiem_rang_buoc_cung"]["tat_ca_dat"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
