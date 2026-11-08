#!/usr/bin/env python3
"""
m3_automata/regular_to_ilp.py — Module 3, yêu cầu 3.3
=====================================================================
Đưa ràng buộc CHÍNH QUY vào mô hình tối ưu nguyên: mỗi giám thị có một chuỗi
lịch nhiều ngày, và chuỗi đó phải được DFA tối thiểu của giao 4 luật chấp nhận.
Dùng `AddAutomaton` của OR-Tools CP-SAT, đúng quyết định nhóm chốt ngày 03/09.

Bài toán:
  · Chân trời: các ngày thật trong `data/processed/m3_real_strings.json`
    (Phúc dựng từ dataset, task 11), 73 giám thị.
  · Biến: x[i,d,s] ∈ {0,1} — giám thị i ngày d mang ký hiệu s ∈ {M,A,N,-};
    đúng một ký hiệu mỗi ngày. y[i,d] = chỉ số ký hiệu (M=0, A=1, N=2, -=3).
  · NHU CẦU: ngày d cần đúng bằng số ca M, A, N mà lịch THẬT đã xếp ngày đó.
    Tức mô hình phải gánh cùng một khối lượng việc như trường đã gánh, chỉ
    được đổi AI làm.
  · CHÍNH QUY: AddAutomaton(y[i,0..D−1], DFA tối thiểu 155 trạng thái của
    R1 ∧ R2 ∧ R3 ∧ R4). Bỏ mọi chuyển vào bẫy: CP-SAT coi chuyển không có
    trong danh sách là bị cấm, nên bẫy không cần tồn tại trong mô hình.
  · MỤC TIÊU — từ điển, đúng như M2: pha 1 tối thiểu tải lớn nhất t; pha 2
    cố định t ≤ t* rồi tối thiểu Σ|Load(i) − q|, q = ⌊tổng ngày-công / n⌋ —
    giải qua đồng nhất thức tổng-thiếu-hụt (xem chú thích ở pha 2).

Đơn giản hóa đã nêu rõ: coi mọi giám thị đều làm được mọi ca. Dataset có
cho biết ai đủ điều kiện ca nào theo từng ngày, nhưng mục tiêu của 3.3 là
chứng minh ràng buộc chính quy đổ được vào ILP; thêm điều kiện đủ chuẩn chỉ
làm nhỏ miền nghiệm, không đổi cách mã hóa.

Kiểm chứng KHÔNG tin solver:
  · mỗi chuỗi lịch đầu ra được chạy lại qua DFA tối thiểu VÀ qua từng
    dfa_r1..r4.json gốc — phải được chấp nhận hết;
  · nhu cầu từng ngày, từng ca phải khớp đúng;
  · đem so với lịch thật: bao nhiêu giám thị thật vi phạm từng luật.

Cách dùng:
    python m3_automata/regular_to_ilp.py
    python m3_automata/regular_to_ilp.py --time-limit 120 --workers 8
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

from ortools.sat.python import cp_model

SIGMA = ["M", "A", "N", "-"]
CHI_SO = {s: k for k, s in enumerate(SIGMA)}


def doc(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def chay(d: dict, w: str) -> bool:
    q = d["start"]
    for ch in w:
        q = d["transitions"][q][ch]
    return q in d["accepting"]


def nhu_cau(chuoi: dict, D: int) -> list[dict]:
    return [dict(collections.Counter(w[d] for w in chuoi.values())) for d in range(D)]


def bo_ba_chuyen(dfa: dict) -> tuple[dict, list, list]:
    """Trạng thái -> số nguyên; danh sách (từ, nhãn, tới) KHÔNG đi vào bẫy."""
    bay = set(dfa["states"]) - set(dfa["accepting"])
    so = {q: k for k, q in enumerate(q for q in dfa["states"] if q not in bay)}
    triples = [(so[q], CHI_SO[s], so[q2])
               for q, hang in dfa["transitions"].items() if q in so
               for s, q2 in hang.items() if q2 in so]
    return so, triples, [so[q] for q in dfa["accepting"]]


def dung_mo_hinh(nguoi: list, D: int, can: list, dfa: dict):
    so, triples, finals = bo_ba_chuyen(dfa)
    m = cp_model.CpModel()
    x = {(i, d, s): m.NewBoolVar(f"x[{i},{d},{s}]") for i in nguoi for d in range(D) for s in SIGMA}
    y = {}
    for i in nguoi:
        for d in range(D):
            m.AddExactlyOne(x[i, d, s] for s in SIGMA)
            y[i, d] = m.NewIntVar(0, len(SIGMA) - 1, f"y[{i},{d}]")
            m.Add(y[i, d] == sum(CHI_SO[s] * x[i, d, s] for s in SIGMA))
        # ---- ràng buộc chính quy: chuỗi y[i,0..D-1] phải được DFA chấp nhận ----
        m.AddAutomaton([y[i, d] for d in range(D)], so[dfa["start"]], finals, triples)
    # ---- nhu cầu: đúng bằng lịch thật ----
    for d in range(D):
        for s in ("M", "A", "N"):
            m.Add(sum(x[i, d, s] for i in nguoi) == int(can[d].get(s, 0)))
    tai = {}
    for i in nguoi:
        tai[i] = m.NewIntVar(0, D, f"tai[{i}]")
        m.Add(tai[i] == sum(1 - x[i, d, "-"] for d in range(D)))
    t = m.NewIntVar(0, D, "t")
    for i in nguoi:
        m.Add(t >= tai[i])
    return m, x, tai, t, len(so), len(triples)


def giai(m, workers, time_limit, seed):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    s.parameters.random_seed = seed % (2 ** 31 - 1)
    st = s.Solve(m)
    return s, st


def chi_so_lich(lich: dict, q: int) -> dict:
    tai = {i: sum(ch != "-" for ch in w) for i, w in lich.items()}
    v = list(tai.values())
    return {"tai_lon_nhat": max(v), "tai_nho_nhat": min(v), "khoang_tai": max(v) - min(v),
            "lech_L1_quanh_q": sum(abs(a - q) for a in v), "q": q}


def vi_pham_tung_luat(lich: dict, dfas: dict) -> dict:
    return {t: sorted(i for i, w in lich.items() if not chay(d, w)) for t, d in dfas.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ràng buộc chính quy vào ILP bằng AddAutomaton (req 3.3)")
    ap.add_argument("--time-limit", type=float, default=60.0, help="giây cho MỖI pha")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed-file", default="data/seed.txt")
    a = ap.parse_args(argv)

    goc = Path(__file__).resolve().parent.parent
    th = goc / "m3_automata"
    seed = int((goc / a.seed_file).read_text(encoding="utf-8-sig").strip())
    rs = doc(goc / "data" / "processed" / "m3_real_strings.json")
    chuoi, D = rs["strings"], int(rs["meta"]["days"])
    nguoi = sorted(chuoi)
    can = nhu_cau(chuoi, D)
    dfa = doc(th / "dfa_product_min.json")
    goc4 = {f"R{k}": doc(th / f"dfa_r{k}.json") for k in (1, 2, 3, 4)}
    tong = sum(sum(v for s, v in c.items() if s != "-") for c in can)
    q = tong // len(nguoi)

    print(f"[regular_to_ilp] {len(nguoi)} giám thị × {D} ngày từ {rs['meta']['start']} · "
          f"{tong} ngày-công cần phủ (giống hệt lịch thật)")
    t0 = time.perf_counter()

    # ---- pha 1 ----
    m, x, tai, t, n_q, n_tr = dung_mo_hinh(nguoi, D, can, dfa)
    print(f"  automaton: {n_q} trạng thái sống, {n_tr} chuyển (đã bỏ bẫy) · "
          f"{len(x):,} biến nhị phân")
    m.Minimize(t)
    s1, st1 = giai(m, a.workers, a.time_limit, seed)
    if st1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if st1 == cp_model.INFEASIBLE:
            ly_do = ("CHỨNG MINH được không có lịch nào vừa phủ đúng nhu cầu thật vừa thỏa "
                     "cả 4 luật")
        else:
            ly_do = (f"hết {a.time_limit:.0f}s mà chưa tìm được nghiệm — CHƯA kết luận được gì "
                     f"về tính khả thi; tăng --time-limit hoặc --workers")
        print(f"  Pha 1: {s1.StatusName(st1)} — {ly_do}.", file=sys.stderr)
        return 1
    t_sao = int(s1.Value(t))
    print(f"  Pha 1 (min-max) : t* = {t_sao} ngày làm/người  ({s1.StatusName(st1)}, "
          f"{s1.WallTime():.1f}s)")

    # ---- pha 2 ----
    goi_y = {k: s1.Value(v) for k, v in x.items()}
    m, x, tai, t, _, _ = dung_mo_hinh(nguoi, D, can, dfa)
    m.Add(t <= t_sao)
    # Mồi bằng nghiệm pha 1: nó hợp lệ cho pha 2 (cùng ràng buộc, t ≤ t*), nên
    # solver có ngay một nghiệm khả thi thay vì phải tự mò lại từ đầu.
    for k, v in goi_y.items():
        m.AddHint(x[k], v)
    # Pha 2 không tối thiểu Σ|tải − q| trực tiếp (chạy thử: 90s vẫn chỉ FEASIBLE,
    # 36 so với cận 34). Thay vào đó dùng một đồng nhất thức. Với tổng ngày-công T
    # cố định, n người, q = ⌊T/n⌋, r = T − n·q:
    #
    #     Σᵢ |tảiᵢ − q|  =  r  +  2 · Σᵢ max(0, q − tảiᵢ)
    #
    # (Σ(tảiᵢ − q) = r, nên phần trên q đóng góp r cộng đúng phần dưới q; phần dưới
    # q bị đếm hai lần.) Vậy tối thiểu L1 ⇔ tối thiểu TỔNG THIẾU HỤT dưới q — một
    # mục tiêu tuyến tính có cận dưới 0 hiển nhiên. Chạm 0 là solver chứng minh
    # tối ưu ngay, không phải đóng khoảng cách cận nào.
    r = tong - len(nguoi) * q
    thieu = []
    for i in nguoi:
        h = m.NewIntVar(0, q, f"thieu[{i}]")
        m.Add(h >= q - tai[i])            # h ≥ 0 sẵn từ miền; tối thiểu hóa đẩy h = max(0, q − tải)
        thieu.append(h)
    m.Minimize(sum(thieu))
    s2, st2 = giai(m, a.workers, a.time_limit, seed)
    if st2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"  Pha 2: {s2.StatusName(st2)} — lạ, vì nghiệm pha 1 đã được mồi vào và hợp lệ "
              f"cho pha 2", file=sys.stderr)
        return 1
    thieu_sao = int(s2.ObjectiveValue())
    l1_sao = r + 2 * thieu_sao
    print(f"  Pha 2 (lệch L1) : tổng thiếu hụt dưới q={q} = {thieu_sao} "
          f"⇒ Σ|tải − {q}| = {r} + 2·{thieu_sao} = {l1_sao}  "
          f"({s2.StatusName(st2)}, {s2.WallTime():.1f}s)")
    if st2 == cp_model.OPTIMAL and thieu_sao == 0:
        print(f"                    chạm cận dưới r = {r}: TỐI ƯU, đã chứng minh")

    lich_moi = {i: "".join(next(s for s in SIGMA if s2.Value(x[i, d, s])) for d in range(D))
                for i in nguoi}
    thoi_gian = round(time.perf_counter() - t0, 2)

    # ---- kiểm chứng, không tin solver ----
    loi = []
    for i, w in lich_moi.items():
        if not chay(dfa, w):
            loi.append(f"{i}: DFA tối thiểu từ chối lịch mới")
        for ten, d in goc4.items():
            if not chay(d, w):
                loi.append(f"{i}: {ten} từ chối lịch mới")
    can_moi = nhu_cau(lich_moi, D)
    for d in range(D):
        for s in ("M", "A", "N"):
            if can_moi[d].get(s, 0) != can[d].get(s, 0):
                loi.append(f"ngày {d}, ca {s}: phủ {can_moi[d].get(s, 0)} ≠ cần {can[d].get(s, 0)}")

    vp_that = vi_pham_tung_luat(chuoi, goc4)
    vp_moi = vi_pham_tung_luat(lich_moi, goc4)
    cs_that, cs_moi = chi_so_lich(chuoi, q), chi_so_lich(lich_moi, q)
    thoa_ca4_that = sum(all(chay(d, w) for d in goc4.values()) for w in chuoi.values())

    print(f"\n  {'':<32}{'lịch thật':>12}{'ILP + DFA':>12}")
    print(f"  {'-'*56}")
    for ten in goc4:
        print(f"  {'giám thị vi phạm ' + ten:<32}{len(vp_that[ten]):>12}{len(vp_moi[ten]):>12}")
    print(f"  {'giám thị thỏa CẢ 4 luật':<32}{thoa_ca4_that:>12}{len(nguoi) - len({i for v in vp_moi.values() for i in v}):>12}")
    print(f"  {'tải lớn nhất (ngày làm)':<32}{cs_that['tai_lon_nhat']:>12}{cs_moi['tai_lon_nhat']:>12}")
    print(f"  {'khoảng tải':<32}{cs_that['khoang_tai']:>12}{cs_moi['khoang_tai']:>12}")
    print(f"  {'lệch L1 quanh q=' + str(q):<32}{cs_that['lech_L1_quanh_q']:>12}{cs_moi['lech_L1_quanh_q']:>12}")
    print(f"  {'tổng ngày-công phủ':<32}{tong:>12}{sum(sum(v for s, v in c.items() if s != '-') for c in can_moi):>12}")
    print(f"\n  Thời gian cả hai pha: {thoi_gian}s")

    out = th / "out"
    out.mkdir(exist_ok=True)
    (out / "regular_ilp.json").write_text(json.dumps({
        "chan_troi": {"ngay_bat_dau": rs["meta"]["start"], "so_ngay": D, "so_giam_thi": len(nguoi),
                      "tong_ngay_cong": tong},
        "automaton": {"trang_thai_song": n_q, "so_chuyen": n_tr},
        "pha1": {"status": s1.StatusName(st1), "t_sao": t_sao},
        "pha2": {"status": s2.StatusName(st2), "tong_thieu_hut": thieu_sao, "lech_L1": l1_sao,
                 "can_duoi_L1": r + 2 * int(s2.BestObjectiveBound()), "du_r": r,
                 "toi_uu_da_chung_minh": st2 == cp_model.OPTIMAL},
        "lich_that": {"chi_so": cs_that, "vi_pham": {k: len(v) for k, v in vp_that.items()},
                      "thoa_ca_4": thoa_ca4_that},
        "lich_ilp": {"chi_so": cs_moi, "vi_pham": {k: len(v) for k, v in vp_moi.items()}},
        "thoi_gian_s": thoi_gian, "workers": a.workers,
        "lich_ilp_chi_tiet": lich_moi,
        "loi": loi,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  Đã ghi m3_automata/out/regular_ilp.json")

    if loi:
        print("  HỎNG:")
        for l in loi[:10]:
            print("   -", l)
        return 1
    print(f"  OK — {len(nguoi)}/{len(nguoi)} lịch đầu ra được cả DFA tối thiểu lẫn 4 DFA gốc "
          f"chấp nhận; nhu cầu thật phủ đúng từng ngày, từng ca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
