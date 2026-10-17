"""
Module 2 — yêu cầu 2.8 (Tuning): giải; nếu infeasible thì nới ràng buộc hoặc đổi trọng số.
Kèm đối chứng bằng PuLP trên instance nhỏ: hai solver (PuLP và CP-SAT) cho cùng đáp số.

Người làm: 2551920 Nguyễn Quang Phúc
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import random
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pulp

from m2_ilp.model import (
    SCALE, _as_int_coef, _kiem_nghiem, build_params, soft_weights_from_seed, solve_week,
)
from m2_ilp.preprocess import generate_location_preferences

CBC = pulp.PULP_CBC_CMD(msg=False, threads=1)
MAX_LOAD_MAC_DINH = 2


def _ca_khong_co_so(params):
    return [j for j in params["J"] if not params["campus"].get(j)]


def _cung(m, x, params, slack=None):
    I, J = params["I"], params["J"]
    cap, campus = params["capacity"], params["campus"]
    busy, eligible = params["busy"], params["eligible"]
    khong_co_so = set(_ca_khong_co_so(params))

    for j in khong_co_so:
        for i in I:
            m += x[i, j] == 0
    for i in I:
        for j in J:
            if busy.get(f"{i}|{j}", False):
                m += x[i, j] == 0
            if eligible is not None and (i, j) not in eligible:
                m += x[i, j] == 0
    for j, k in params["overlap"]:
        if j in cap and k in cap:
            for i in I:
                m += x[i, j] + x[i, k] <= 1
    for j in J:
        if j in khong_co_so:
            continue
        tong = pulp.lpSum(x[i, j] for i in I)
        m += (tong + slack[j] if slack else tong) == int(cap[j])


def _bien(params, tag):
    x = {(i, j): pulp.LpVariable(f"x_{tag}_{a}_{b}", cat="Binary")
         for a, i in enumerate(params["I"]) for b, j in enumerate(params["J"])}
    return x


def _tai(x, params, i):
    return pulp.lpSum(x[i, j] for j in params["J"])


def _q(params):
    tong_cap = sum(int(v) for v in params["capacity"].values())
    return tong_cap // max(len(params["I"]), 1)


def solve_pulp(params, seed_int, *, relax=False, time_limit=60):
    I, J = params["I"], params["J"]
    campus, prefs = params["campus"], params["preferences"]
    w_loc, w_load, w_fair = soft_weights_from_seed(seed_int)
    c_fair, c_loc, c_load = _as_int_coef(w_fair), _as_int_coef(w_loc), _as_int_coef(w_load)
    q = _q(params)
    khong_co_so = set(_ca_khong_co_so(params))
    cbc = pulp.PULP_CBC_CMD(msg=False, threads=1, timeLimit=time_limit)
    t0 = time.perf_counter()
    out = {"relax": relax}

    def slack_vars(tag):
        return {j: pulp.LpVariable(f"s_{tag}_{b}", lowBound=0, upBound=int(params["capacity"][j]),
                                   cat="Integer")
                for b, j in enumerate(J) if j not in khong_co_so}

    s_star = None
    if relax:
        m0 = pulp.LpProblem("pha0", pulp.LpMinimize)
        x0, s0 = _bien(params, "p0"), slack_vars("p0")
        m0 += pulp.lpSum(s0.values())
        _cung(m0, x0, params, s0)
        m0.solve(cbc)
        if pulp.LpStatus[m0.status] != "Optimal":
            return {**out, "status": pulp.LpStatus[m0.status], "feasible": False}
        s_star = round(pulp.value(m0.objective))
        out["tong_thieu"] = s_star

    def them_nhom_thieu(m, s):
        if relax:
            m += pulp.lpSum(s.values()) <= s_star

    m1 = pulp.LpProblem("pha1", pulp.LpMinimize)
    x1, s1 = _bien(params, "p1"), (slack_vars("p1") if relax else None)
    t = pulp.LpVariable("t", lowBound=0, upBound=len(J), cat="Integer")
    m1 += t
    _cung(m1, x1, params, s1)
    them_nhom_thieu(m1, s1)
    for i in I:
        m1 += t >= _tai(x1, params, i)
    m1.solve(cbc)
    if pulp.LpStatus[m1.status] != "Optimal":
        return {**out, "status": pulp.LpStatus[m1.status], "feasible": False}
    t_star = round(pulp.value(t))

    m2 = pulp.LpProblem("pha2", pulp.LpMinimize)
    x2, s2 = _bien(params, "p2"), (slack_vars("p2") if relax else None)
    _cung(m2, x2, params, s2)
    them_nhom_thieu(m2, s2)
    dev, vuot, hang = {}, {}, []
    for b, i in enumerate(I):
        tai = _tai(x2, params, i)
        m2 += tai <= t_star
        dev[i] = pulp.LpVariable(f"dev_{b}", lowBound=0, cat="Integer")
        m2 += dev[i] >= tai - q
        m2 += dev[i] >= q - tai
        nguong = int(params["max_load"].get(i, MAX_LOAD_MAC_DINH))
        vuot[i] = pulp.LpVariable(f"vuot_{b}", lowBound=0, cat="Integer")
        m2 += vuot[i] >= tai - nguong
        hang.append(c_load * vuot[i])
        pc = prefs.get(i, {}).get("prefer_campus")
        if pc:
            hang += [c_loc * x2[i, j] for j in J if campus.get(j) and campus[j] != pc]
    m2 += c_fair * pulp.lpSum(dev.values()) + pulp.lpSum(hang)
    m2.solve(cbc)
    status = pulp.LpStatus[m2.status]
    out.update(status=status, feasible=status == "Optimal", t_star=t_star,
               runtime_s=round(time.perf_counter() - t0, 3))
    if status == "Optimal":
        out["objective_scaled"] = round(pulp.value(m2.objective))
        out["assignment"] = sorted([i, j] for (i, j), v in x2.items() if v.value() > 0.5)
        if relax:
            out["thieu"] = {j: round(v.value()) for j, v in s2.items() if round(v.value()) > 0}
    return out


def tinh_lai(params, seed_int, assignment):
    w_loc, w_load, w_fair = soft_weights_from_seed(seed_int)
    q = _q(params)
    tai = {i: 0 for i in params["I"]}
    for i, _ in assignment:
        tai[i] += 1
    t = max(tai.values()) if tai else 0
    dev = sum(abs(tai[i] - q) for i in params["I"])
    loc = 0
    for i, j in assignment:
        pc = params["preferences"].get(i, {}).get("prefer_campus")
        if pc and params["campus"].get(j) and params["campus"][j] != pc:
            loc += 1
    vuot = sum(max(0, tai[i] - int(params["max_load"].get(i, MAX_LOAD_MAC_DINH)))
               for i in params["I"])
    return t, _as_int_coef(w_fair) * dev + _as_int_coef(w_loc) * loc + _as_int_coef(w_load) * vuot


def doi_chung(params, seed_int):
    kq = solve_week(params, seed_int=seed_int, verbose=False)
    pp = solve_pulp(params, seed_int)
    ok_c, ok_p = bool(kq.get("feasible")), bool(pp.get("feasible"))
    if not ok_c and not ok_p:
        return {"dong_y": True, "kha_thi": False, "cpsat": kq, "pulp": pp}
    if ok_c != ok_p:
        return {"dong_y": False, "kha_thi": True, "cpsat": kq, "pulp": pp,
                "ly_do": "trạng thái khả thi KHÁC nhau"}
    obj_cp = round(kq["objective"] * SCALE)
    cat_cut = kq["objective_scaled"] != obj_cp
    for ten, asg, t_s, obj_s in (("CP-SAT", kq["assignment"], kq["t_star"], obj_cp),
                                  ("PuLP", pp["assignment"], pp["t_star"], pp["objective_scaled"])):
        kiem = _kiem_nghiem(params, asg)
        assert kiem["tat_ca_dat"], f"{ten}: lịch vi phạm ràng buộc cứng: {kiem}"
        assert tinh_lai(params, seed_int, asg) == (t_s, obj_s), \
            f"{ten}: mục tiêu tính lại {tinh_lai(params, seed_int, asg)} != solver {(t_s, obj_s)}"
    cung = (kq["t_star"], obj_cp) == (pp["t_star"], pp["objective_scaled"])
    return {"dong_y": cung, "kha_thi": True, "cpsat": kq, "pulp": pp,
            "cung_lich": kq["assignment"] == pp["assignment"], "cat_cut": cat_cut}


def instance_ngau_nhien(rng):
    n_i, n_j = rng.randint(5, 9), rng.randint(3, 6)
    I = [f"CB{k:02d}" for k in range(n_i)]
    J = [f"S{k}" for k in range(n_j)]
    cap = {j: rng.randint(1, 3) for j in J}
    coso = ["Cơ sở 1", "Cơ sở 2"]
    return {
        "meta": {}, "invigilators": I, "shifts": J, "capacity": cap, "campuses": coso,
        "campus_of": {j: (None if rng.random() < 0.1 else rng.choice(coso)) for j in J},
        "overlap": [[a, b] for k, a in enumerate(J) for b in J[k + 1:] if rng.random() < 0.35],
        "busy": [[i, j] for i in I for j in J if rng.random() < 0.1],
        "eligible": [[i, j] for i in I for j in J if rng.random() < 0.92],
        "max_load": {i: rng.randint(1, 3) for i in I},
    }


def params_tu_instance(instance, seed_int):
    p = build_params(instance)
    p["preferences"] = generate_location_preferences(
        p["I"], instance["campuses"], random.Random(seed_int))
    return p


def diagnose_infeasible(params, chi_ca_don=False):
    I, J = params["I"], params["J"]
    cap = params["capacity"]
    khong_co_so = set(_ca_khong_co_so(params))
    kha_dung = {j: {i for i in I
                    if not params["busy"].get(f"{i}|{j}", False)
                    and (params["eligible"] is None or (i, j) in params["eligible"])}
                for j in J if j not in khong_co_so}
    msgs = []
    for j, ds in kha_dung.items():
        if len(ds) < int(cap[j]):
            msgs.append(f"Ca {j}: cần {cap[j]} người nhưng chỉ {len(ds)} giám thị khả dụng "
                        f"(sau khi loại lịch bận và không đủ điều kiện)")
    if not chi_ca_don:
        for a, b in params["overlap"]:
            if a in kha_dung and b in kha_dung:
                can, co = int(cap[a]) + int(cap[b]), len(kha_dung[a] | kha_dung[b])
                if can > co:
                    msgs.append(f"Cặp ca chồng giờ {a},{b}: cần {can} người KHÁC nhau "
                                f"(mỗi người chỉ 1 ca) nhưng chỉ {co} giám thị khả dụng")
    return msgs


def giai_co_tuning(params, seed_int):
    chat = solve_pulp(params, seed_int)
    if chat["feasible"]:
        return {"giai_doan": "chặt", "ket_qua": chat, "thieu": {}, "chan_doan": []}
    nl = solve_pulp(params, seed_int, relax=True)
    return {"giai_doan": "nới H5", "ket_qua": nl, "thieu": nl.get("thieu", {}),
            "chan_doan": diagnose_infeasible(params)}


def _doc_seed(duong_dan):
    return int(Path(duong_dan).read_text(encoding="utf-8-sig").strip())


def _tim(*cach):
    goc = Path(__file__).resolve().parent.parent
    for c in cach:
        if (goc / c).exists():
            return goc / c
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Đối chứng PuLP vs CP-SAT + tuning infeasible (M2)")
    ap.add_argument("--instance", default=None)
    ap.add_argument("--seed-file", default=None)
    ap.add_argument("--trials", type=int, default=60, help="số instance ngẫu nhiên")
    a = ap.parse_args(argv)

    seed_f = Path(a.seed_file) if a.seed_file else _tim("data/seed.txt")
    inst_f = Path(a.instance) if a.instance else _tim("data/instance_slice.json")
    seed_int = _doc_seed(seed_f) if seed_f else 0
    w = soft_weights_from_seed(seed_int)
    print(f"seed={seed_int}  trọng số (w_loc, w_load, w_fair) = {w}\n")

    print("[A] Đối chứng trên lát dữ liệu thật")
    if inst_f is None:
        print("    không thấy data/instance_slice.json — bỏ qua (chạy m1_logic/slice_builder.py trước)")
    else:
        instance = json.loads(inst_f.read_text(encoding="utf-8-sig"))
        from m2_ilp.preprocess import run as run_preprocess
        with contextlib.redirect_stdout(io.StringIO()):
            m2_data = run_preprocess(instance, seed_int=seed_int, out_dir=str(inst_f.parent / "processed"))
        params = build_params(instance, m2_data)
        r = doi_chung(params, seed_int)
        kq, pp = r["cpsat"], r["pulp"]
        if not r["kha_thi"]:
            print("    cả hai solver cùng báo infeasible")
        else:
            print(f"    {'solver':8s} {'t*':>3s} {'objective(thang %d)' % SCALE:>20s} {'time(s)':>8s}")
            print(f"    {'CP-SAT':8s} {kq['t_star']:3d} {kq['objective_scaled']:20d} {kq['runtime_s']:8.3f}")
            print(f"    {'PuLP':8s} {pp['t_star']:3d} {pp['objective_scaled']:20d} {pp['runtime_s']:8.3f}")
            print(f"    -> {'CÙNG đáp số' if r['dong_y'] else 'KHÁC đáp số'}; "
                  f"lịch giống hệt nhau: {r.get('cung_lich')}")
        assert r["dong_y"], "PuLP và CP-SAT KHÔNG cùng đáp số trên dữ liệu thật!"

    print(f"\n[B] {a.trials} instance ngẫu nhiên (seed lấy từ seed nhóm; trọng số đổi theo từng seed)")
    rng = random.Random(seed_int)
    dong_y = kha_thi = cung_lich = cat_cut = 0
    for k in range(a.trials):
        s = rng.randint(1, 10**8)
        p = params_tu_instance(instance_ngau_nhien(rng), s)
        r = doi_chung(p, s)
        assert r["dong_y"], f"trial {k} (seed {s}): KHÁC đáp số: {r}"
        dong_y += 1
        if r["kha_thi"]:
            kha_thi += 1
            cung_lich += bool(r.get("cung_lich"))
            cat_cut += bool(r.get("cat_cut"))
    print(f"    {dong_y}/{a.trials} cùng đáp số ({kha_thi} khả thi, {a.trials - kha_thi} "
          f"infeasible cả hai); {cung_lich}/{kha_thi} có lịch giống hệt "
          f"(nghiệm tối ưu không duy nhất là bình thường)")
    if cat_cut:
        print(f"    CẢNH BÁO model.py: objective_scaled bị cắt cụt (int thay vì round) ở "
              f"{cat_cut}/{kha_thi} instance, lệch 1 đơn vị.\n"
              f"      Sửa: model.py dòng \"objective_scaled\": int(s2.ObjectiveValue()) -> "
              f"round(s2.ObjectiveValue())")

    print("\n[C] Tuning khi infeasible (req 2.8)")
    base = {
        "meta": {}, "invigilators": [f"CB{k}" for k in range(1, 5)], "shifts": ["S1", "S2"],
        "capacity": {"S1": 2, "S2": 2}, "campuses": ["Cơ sở 1", "Cơ sở 2"],
        "campus_of": {"S1": "Cơ sở 1", "S2": "Cơ sở 2"}, "overlap": [["S1", "S2"]],
        "busy": [["CB1", "S1"], ["CB1", "S2"]], "eligible": [[i, j] for i in
                 [f"CB{k}" for k in range(1, 5)] for j in ("S1", "S2")],
        "max_load": {f"CB{k}": 2 for k in range(1, 5)},
    }
    p = params_tu_instance(base, seed_int)
    print("    Instance cố ý gây infeasible: 2 ca chồng giờ, mỗi ca cần 2 người, "
          "4 giám thị nhưng CB1 bận cả hai ca")
    print("    Chẩn đoán:", *diagnose_infeasible(p), sep="\n      - ")
    g = giai_co_tuning(p, seed_int)
    print(f"    Giai đoạn giải: {g['giai_doan']}; nới capacity tối thiểu, thiếu: {g['thieu']}")
    assert g["giai_doan"] == "nới H5" and sum(g["thieu"].values()) == 1
    asg = g["ket_qua"]["assignment"]
    for j, cap in p["capacity"].items():
        phuc_vu = sum(1 for _, jj in asg if jj == j)
        assert phuc_vu + g["thieu"].get(j, 0) == cap
    kiem = _kiem_nghiem(p, asg)
    assert kiem["H1_khong_trung_ca"] and kiem["H2_lich_ban"] and kiem["H3_du_dieu_kien"] \
        and kiem["H4_toan_ven_du_lieu"], kiem
    print(f"    Lịch sau khi nới: {asg}")
    print("    OK — H1–H4 vẫn thỏa; lượt gán + thiếu hụt = capacity ở mọi ca.")

    print("\nOK — đối chứng và tuning đều qua.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
