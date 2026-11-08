#!/usr/bin/env python3
"""
m3_automata/product_minimize.py — Module 3, yêu cầu 3.2
=====================================================================
Giao bốn DFA bằng DFA tích, tối thiểu hóa, báo cáo số trạng thái — và CHỨNG
MINH (không lấy mẫu) rằng DFA tối thiểu đúng là DFA của giao bốn luật.

Các bước:
  1. Tích đồng bộ, chỉ dựng trạng thái ĐẠT TỚI được từ (s₁, s₂, s₃, s₄).
     Chấp nhận ⇔ cả bốn thành phần đều chấp nhận.
  2. Tối thiểu hóa bằng thuật toán Hopcroft (tinh chỉnh phân hoạch), O(n·|Σ|·log n).
  3. Kiểm chứng, theo thứ tự từ mạnh tới yếu:
       a. TƯƠNG ĐƯƠNG CHÍNH XÁC: BFS trên tích (DFA tích × DFA tối thiểu) — mọi
          cặp trạng thái đạt tới phải cùng chấp nhận/không chấp nhận. Đây là một
          chứng minh, không phải thử ngẫu nhiên.
       b. TỐI THIỂU: chạy lại Hopcroft trên DFA tối thiểu không gộp thêm được
          gì (điểm bất động) ⇔ mọi cặp trạng thái phân biệt được (Myhill–Nerode).
       c. Đối chiếu với bốn DFA gốc trên toàn bộ chuỗi dài ≤ 8 và chuỗi thật.
  4. LUẬT THỪA: với từng luật Rᵢ, kiểm xem giao ba luật còn lại đã kéo theo Rᵢ
     chưa (L(¬Rᵢ ∩ giao ba luật kia) = ∅). Nếu có thì Rᵢ không thêm ràng buộc
     nào. Phép kiểm này đã có thì bản R3 viết tay đầu tiên (thực chất là
     "không hai ca N liền nhau", bị R2 bao trùm) sẽ bị bắt ngay.

Đầu ra:
  m3_automata/dfa_product_min.json   — DFA tối thiểu, ĐÚNG schema 5 khóa của dfa_r*.json
  m3_automata/out/product_report.json — số trạng thái từng bước, kết quả kiểm chứng
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import deque
from pathlib import Path

SIGMA = ["M", "A", "N", "-"]


def doc_dfa(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def chay(d: dict, w: str) -> bool:
    q = d["start"]
    for ch in w:
        q = d["transitions"][q][ch]
    return q in d["accepting"]


# ---------------------------------------------------------------------------
# 1. Tích đồng bộ, chỉ trạng thái đạt tới
# ---------------------------------------------------------------------------
def tich(dfas: list[dict]) -> dict:
    """Trả DFA với trạng thái là tuple. Chấp nhận ⇔ mọi thành phần chấp nhận."""
    dau = tuple(d["start"] for d in dfas)
    F = [set(d["accepting"]) for d in dfas]
    Q, T, hang = {dau}, {}, deque([dau])
    while hang:
        q = hang.popleft()
        T[q] = {}
        for s in SIGMA:
            q2 = tuple(d["transitions"][qi][s] for d, qi in zip(dfas, q))
            T[q][s] = q2
            if q2 not in Q:
                Q.add(q2)
                hang.append(q2)
    acc = {q for q in Q if all(qi in Fi for qi, Fi in zip(q, F))}
    return {"Q": Q, "start": dau, "F": acc, "T": T}


# ---------------------------------------------------------------------------
# 2. Hopcroft
# ---------------------------------------------------------------------------
def hopcroft(Q: set, F: set, T: dict) -> list[frozenset]:
    """Phân hoạch thô nhất của Q ổn định theo δ, tách F khỏi Q∖F."""
    F, NF = frozenset(F), frozenset(Q - F)
    P = [b for b in (F, NF) if b]
    W = [min(P, key=len)] if len(P) == 2 else list(P)
    # nghịch ảnh: nguoc[s][q2] = {q : δ(q, s) = q2}
    nguoc = {s: {} for s in SIGMA}
    for q in Q:
        for s in SIGMA:
            nguoc[s].setdefault(T[q][s], set()).add(q)
    while W:
        A = W.pop()
        for s in SIGMA:
            X = set()
            for q2 in A:
                X |= nguoc[s].get(q2, set())
            if not X:
                continue
            P_moi = []
            for Y in P:
                giao, hieu = Y & X, Y - X
                if giao and hieu:
                    giao, hieu = frozenset(giao), frozenset(hieu)
                    P_moi += [giao, hieu]
                    if Y in W:
                        W.remove(Y)
                        W += [giao, hieu]
                    else:
                        W.append(min(giao, hieu, key=len))
                else:
                    P_moi.append(Y)
            P = P_moi
    return P


def thu_gon(D: dict) -> tuple[dict, dict]:
    """DFA tối thiểu dạng schema 5 khóa + ánh xạ khối -> các trạng thái tích."""
    P = hopcroft(D["Q"], D["F"], D["T"])
    khoi_cua = {q: i for i, B in enumerate(P) for q in B}
    # đánh số lại theo thứ tự BFS từ trạng thái đầu cho ổn định, bẫy cuối cùng
    thu_tu, seen, hang = [], set(), deque([khoi_cua[D["start"]]])
    while hang:
        b = hang.popleft()
        if b in seen:
            continue
        seen.add(b)
        thu_tu.append(b)
        dai_dien = next(iter(P[b]))
        for s in SIGMA:
            hang.append(khoi_cua[D["T"][dai_dien][s]])
    bay = [b for b in thu_tu if not (P[b] & D["F"])]
    con = [b for b in thu_tu if b not in bay]
    ten = {b: f"s{i}" for i, b in enumerate(con)}
    for j, b in enumerate(bay):
        ten[b] = "trap" if len(bay) == 1 else f"trap{j}"
    states = [ten[b] for b in con + bay]
    T = {}
    for b in con + bay:
        dd = next(iter(P[b]))
        T[ten[b]] = {s: ten[khoi_cua[D["T"][dd][s]]] for s in SIGMA}
    dfa = {"states": states, "alphabet": list(SIGMA), "start": ten[khoi_cua[D["start"]]],
           "accepting": [ten[b] for b in con], "transitions": T}
    return dfa, {ten[b]: sorted(map(list, P[b])) for b in con + bay}


# ---------------------------------------------------------------------------
# 3. Kiểm chứng
# ---------------------------------------------------------------------------
def tuong_duong(D: dict, M: dict) -> tuple[bool, str | None]:
    """BFS trên tích D × M. Trả (True, None) hoặc (False, chuỗi phản ví dụ)."""
    dau = (D["start"], M["start"])
    seen, hang = {dau: ""}, deque([dau])
    FM = set(M["accepting"])
    while hang:
        p, q = hang.popleft()
        if (p in D["F"]) != (q in FM):
            return False, seen[(p, q)]
        for s in SIGMA:
            nx = (D["T"][p][s], M["transitions"][q][s])
            if nx not in seen:
                seen[nx] = seen[(p, q)] + s
                hang.append(nx)
    return True, None


def la_toi_thieu(M: dict) -> bool:
    Q = set(M["states"])
    P = hopcroft(Q, set(M["accepting"]), M["transitions"])
    # và mọi trạng thái đều đạt tới được
    seen, hang = {M["start"]}, deque([M["start"]])
    while hang:
        q = hang.popleft()
        for s in SIGMA:
            if M["transitions"][q][s] not in seen:
                seen.add(M["transitions"][q][s])
                hang.append(M["transitions"][q][s])
    return len(P) == len(Q) and seen == Q


def ngon_ngu_rong(D: dict) -> tuple[bool, str | None]:
    """L(D) = ∅ ? Nếu không, trả chuỗi ngắn nhất thuộc L(D)."""
    seen, hang = {D["start"]: ""}, deque([D["start"]])
    while hang:
        q = hang.popleft()
        if q in D["F"]:
            return False, seen[q]
        for s in SIGMA:
            q2 = D["T"][q][s]
            if q2 not in seen:
                seen[q2] = seen[q] + s
                hang.append(q2)
    return True, None


def phan_bu(d: dict) -> dict:
    """DFA của Σ* ∖ L(d) — chỉ đổi tập chấp nhận vì d đầy đủ."""
    return {**d, "accepting": [q for q in d["states"] if q not in set(d["accepting"])]}


def luat_thua(dfas: dict) -> dict:
    """Rᵢ thừa ⇔ (giao các luật còn lại) ∩ ¬Rᵢ = ∅."""
    kq = {}
    for ten in dfas:
        khac = [d for t, d in dfas.items() if t != ten]
        D = tich(khac + [phan_bu(dfas[ten])])
        rong, vi_du = ngon_ngu_rong(D)
        kq[ten] = {"thua": rong,
                   "chuoi_chi_luat_nay_cam": vi_du}   # ngắn nhất: 3 luật kia cho qua, luật này chặn
    return kq


# ---------------------------------------------------------------------------
def main() -> int:
    goc = Path(__file__).resolve().parent.parent
    th = goc / "m3_automata"
    ten = ["r1", "r2", "r3", "r4"]
    dfas = {t: doc_dfa(th / f"dfa_{t}.json") for t in ten}
    chuoi_that_f = goc / "data" / "processed" / "m3_real_strings.json"
    chuoi_that = (json.loads(chuoi_that_f.read_text(encoding="utf-8"))["strings"]
                  if chuoi_that_f.exists() else {})

    ly_thuyet = 1
    for t in ten:
        ly_thuyet *= len(dfas[t]["states"])

    D = tich([dfas[t] for t in ten])
    M, khoi = thu_gon(D)

    print("[product_minimize] Giao 4 DFA (req 3.2)")
    print(f"  kích thước từng DFA      : " +
          " × ".join(f"{t.upper()}={len(dfas[t]['states'])}" for t in ten) + f" = {ly_thuyet:,}")
    print(f"  tích, trạng thái đạt tới : {len(D['Q']):,}  "
          f"({len(D['F']):,} chấp nhận, {len(D['Q']) - len(D['F']):,} chứa bẫy)")
    print(f"  sau tối thiểu (Hopcroft) : {len(M['states'])}  "
          f"({len(M['accepting'])} chấp nhận + {len(M['states']) - len(M['accepting'])} bẫy)")

    # ---- kiểm chứng ----
    loi = []
    td, pv = tuong_duong(D, M)
    if not td:
        loi.append(f"DFA tối thiểu KHÁC ngôn ngữ DFA tích, phản ví dụ {pv!r}")
    if not la_toi_thieu(M):
        loi.append("DFA tối thiểu vẫn còn cặp trạng thái tương đương hoặc trạng thái không đạt tới")
    dem = 0
    for L in range(9):
        for tt in itertools.product(SIGMA, repeat=L):
            w = "".join(tt)
            dem += 1
            if chay(M, w) != all(chay(dfas[t], w) for t in ten):
                loi.append(f"lệch AND của 4 DFA gốc tại {w!r}")
                break
    nhan = 0
    for gt, w in chuoi_that.items():
        a, b = chay(M, w), all(chay(dfas[t], w) for t in ten)
        nhan += a
        if a != b:
            loi.append(f"lệch AND của 4 DFA gốc trên chuỗi thật của {gt}")

    print(f"\n  tương đương chính xác    : {'ĐẠT' if td else 'HỎNG'} — BFS trên tích (tích × tối thiểu)")
    print(f"  tối thiểu (Myhill–Nerode): {'ĐẠT' if la_toi_thieu(M) else 'HỎNG'} — Hopcroft lần 2 không gộp thêm")
    print(f"  khớp AND 4 DFA gốc       : {'ĐẠT' if not any('lệch' in l for l in loi) else 'HỎNG'} — "
          f"{dem:,} chuỗi dài ≤ 8 + {len(chuoi_that)} chuỗi thật")
    if chuoi_that:
        print(f"  giám thị thật thỏa CẢ 4  : {nhan}/{len(chuoi_that)} = {nhan/len(chuoi_that):.0%}")

    # ---- luật thừa ----
    lt = luat_thua(dfas)
    print("\n  Luật nào thừa (bị 3 luật kia kéo theo)?")
    for t in ten:
        r = lt[t]
        if r["thua"]:
            print(f"    {t.upper()}: THỪA — không thêm ràng buộc nào")
            loi.append(f"{t.upper()} thừa: giao 3 luật kia đã kéo theo nó")
        else:
            print(f"    {t.upper()}: cần thiết — chuỗi ngắn nhất chỉ mình nó chặn: "
                  f"{r['chuoi_chi_luat_nay_cam']!r}")

    # ---- ghi ----
    (th / "dfa_product_min.json").write_text(json.dumps(M, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    out = th / "out"
    out.mkdir(exist_ok=True)
    (out / "product_report.json").write_text(json.dumps({
        "so_trang_thai": {"tung_dfa": {t: len(dfas[t]["states"]) for t in ten},
                          "tich_ly_thuyet": ly_thuyet, "tich_dat_toi": len(D["Q"]),
                          "tich_chap_nhan": len(D["F"]), "toi_thieu": len(M["states"]),
                          "toi_thieu_chap_nhan": len(M["accepting"])},
        "kiem_chung": {"tuong_duong_chinh_xac": td, "toi_thieu": la_toi_thieu(M),
                       "so_chuoi_vet_can": dem, "so_chuoi_that": len(chuoi_that),
                       "giam_thi_that_thoa_ca_4": nhan},
        "luat_thua": lt,
        "loi": loi,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n  Đã ghi m3_automata/dfa_product_min.json và m3_automata/out/product_report.json")

    if loi:
        print("  HỎNG:")
        for l in loi:
            print("   -", l)
        return 1
    print("  OK — tích + tối thiểu hóa đã được chứng minh đúng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
