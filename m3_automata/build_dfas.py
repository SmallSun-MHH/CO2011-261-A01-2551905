#!/usr/bin/env python3
"""
m3_automata/build_dfas.py — Module 3, yêu cầu 3.1 + 3.4a
=====================================================================
SINH bốn DFA từ tham số, thay vì viết tay từng bảng chuyển.

Bốn luật nhóm đã chốt ngày 03/09/2026:
    R1  không quá 2 ngày làm liên tiếp
    R2  sau ca đêm (N) phải nghỉ ngay ngày hôm sau
    R3  tối đa k ca trong mọi cửa sổ trượt 7 ngày
    R4  |#M − #A| ≤ c tại MỌI tiền tố của lịch

Bảng chữ cái Σ = {M, A, N, -}: mỗi ngày một ký hiệu (sáng / chiều / đêm / nghỉ).

Tham số k và c LẤY TỪ dữ liệu thật — `m3_automata/strings_from_data.py` (task
11, Phúc) hiệu chỉnh chúng sao cho ≥ 90% giám thị thật thỏa, ghi vào
`data/processed/m3_calibration.json`. Ngưỡng 2 của R1 là quyết định chính sách
của nhóm, KHÔNG hiệu chỉnh: lịch thật chỉ có 62% giám thị thỏa — đó là phát
hiện để báo cáo, không phải lý do để nới luật.

Vì sao sinh bằng code: bản viết tay đầu tiên (commit 4fe71a8, 02/11) có hai lỗi
mà mắt thường khó thấy, phép kiểm ở dưới bắt được ngay:
  · dfa_r3 mã hóa "không hai ca N liền nhau" thay vì cửa sổ trượt 7 ngày. Hơn
    nữa L(R2) ⊆ L(R3 cũ) — kiểm trên toàn bộ 87.381 chuỗi dài ≤ 8 — nên R3 cũ
    không thêm ràng buộc nào: tích 4 DFA thực chất chỉ còn 3 luật.
  · dfa_r4 dùng c = 1 tự đặt, chỉ chấp nhận 7/73 = 10% giám thị thật, trong
    khi hiệu chỉnh từ dữ liệu cho c = 5 (71/73).
R1 và R2 bản cũ ĐÚNG nên GIỮ NGUYÊN file, script chỉ kiểm chúng. Hàm dfa_r1/dfa_r2
ở dưới vẫn có để đối chiếu và tái tạo nếu cần.

Schema giữ nguyên đúng 5 khóa như bản cũ, theo đúng thứ tự:
    {"states", "alphabet", "start", "accepting", "transitions"}
vì test ẩn của đề sinh từ chính file này — thêm khóa lạ có thể làm hỏng nó.

Cách dùng:
    python m3_automata/build_dfas.py          # sinh + tự kiểm, ghi đè 4 file
    python m3_automata/build_dfas.py --check  # chỉ kiểm, không ghi
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

SIGMA = ["M", "A", "N", "-"]
LAM = {"M", "A", "N"}          # ký hiệu tính là một ngày làm
R1_MAX_LIEN_TIEP = 2           # quyết định chính sách 03/09, KHÔNG hiệu chỉnh
CUA_SO = 7
TRAP = "trap"


# ---------------------------------------------------------------------------
# Bốn bộ sinh DFA — mỗi cái là một DFA an toàn: mọi trạng thái trừ trap đều
# chấp nhận, trap là bẫy hút. Ngôn ngữ đóng theo tiền tố, đúng bản chất "lịch
# hợp lệ cho tới hôm nay".
# ---------------------------------------------------------------------------
def dfa_r1(m: int = R1_MAX_LIEN_TIEP) -> dict:
    """Đếm số ngày làm liên tiếp tính tới hôm nay; quá m thì vào bẫy."""
    Q = [f"q{i}" for i in range(m + 1)] + [TRAP]
    T = {TRAP: {s: TRAP for s in SIGMA}}
    for i in range(m + 1):
        T[f"q{i}"] = {s: (f"q{i+1}" if i < m else TRAP) if s in LAM else "q0" for s in SIGMA}
    return _dong_goi(Q, "q0", [q for q in Q if q != TRAP], T)


def dfa_r2() -> dict:
    """Vừa làm ca N thì ngày sau bắt buộc '-'."""
    Q = ["q_safe", "q_after_N", TRAP]
    T = {
        "q_safe":    {"M": "q_safe", "A": "q_safe", "N": "q_after_N", "-": "q_safe"},
        "q_after_N": {"M": TRAP, "A": TRAP, "N": TRAP, "-": "q_safe"},
        TRAP:        {s: TRAP for s in SIGMA},
    }
    return _dong_goi(Q, "q_safe", ["q_safe", "q_after_N"], T)


def dfa_r3(k: int, L: int = CUA_SO) -> dict:
    """Trạng thái = mẫu làm/nghỉ của L−1 ngày gần nhất (1 = làm, 0 = nghỉ).

    Đọc ký hiệu mới: cửa sổ L ngày = (L−1 bit cũ) + bit mới. Nếu tổng > k thì
    bẫy; ngược lại trượt cửa sổ đi một ngày. Trước ngày đầu coi như nghỉ, nên
    trạng thái đầu là toàn 0 — điều này không bao giờ tạo vi phạm giả.
    Chỉ giữ trạng thái ĐẠT TỚI được từ trạng thái đầu.
    """
    w = L - 1
    dau = "w" + "0" * w
    Q, T, hang = [dau], {}, [dau]
    while hang:
        q = hang.pop()
        bits = q[1:]
        T[q] = {}
        for s in SIGMA:
            v = "1" if s in LAM else "0"
            if bits.count("1") + int(v) > k:
                T[q][s] = TRAP
            else:
                q2 = "w" + bits[1:] + v
                T[q][s] = q2
                if q2 not in Q:
                    Q.append(q2)
                    hang.append(q2)
    Q.append(TRAP)
    T[TRAP] = {s: TRAP for s in SIGMA}
    Q = sorted(q for q in Q if q != TRAP) + [TRAP]
    return _dong_goi(Q, dau, [q for q in Q if q != TRAP], T)


def dfa_r4(c: int) -> dict:
    """Bộ đếm có chặn t = #M − #A trên tiền tố. Chỉ cần 2c+1 trạng thái +bẫy:
    chính vì có CHẶN nên ngôn ngữ chính quy. Bỏ chặn (đòi #M = #A trên cả
    chuỗi) thì không còn chính quy nữa — xem pumping_proof.md (3.4b, 3.4c)."""
    ten = lambda t: f"d{t:+d}" if t else "d0"
    Q = [ten(t) for t in range(-c, c + 1)] + [TRAP]
    T = {TRAP: {s: TRAP for s in SIGMA}}
    for t in range(-c, c + 1):
        T[ten(t)] = {}
        for s in SIGMA:
            t2 = t + (s == "M") - (s == "A")
            T[ten(t)][s] = ten(t2) if abs(t2) <= c else TRAP
    return _dong_goi(Q, "d0", [q for q in Q if q != TRAP], T)


def _dong_goi(Q, q0, F, T) -> dict:
    # đúng 5 khóa, đúng thứ tự của bản cũ
    return {"states": list(Q), "alphabet": list(SIGMA), "start": q0,
            "accepting": list(F), "transitions": {q: dict(T[q]) for q in Q}}


# ---------------------------------------------------------------------------
# Vị từ BRUTE-FORCE độc lập — định nghĩa luật thẳng trên chuỗi, không qua DFA.
# DFA nào lệch vị từ của nó trên dù chỉ một chuỗi là sai.
# ---------------------------------------------------------------------------
def p_r1(w, m=R1_MAX_LIEN_TIEP):
    cur = 0
    for ch in w:
        cur = cur + 1 if ch in LAM else 0
        if cur > m:
            return False
    return True


def p_r2(w):
    return not any(w[i] == "N" and w[i + 1] != "-" for i in range(len(w) - 1))


def p_r3(w, k, L=CUA_SO):
    b = [ch in LAM for ch in w]
    # mọi cửa sổ, kể cả cửa sổ ngắn ở đầu chuỗi (coi như trước đó nghỉ)
    return all(sum(b[max(0, i - L + 1): i + 1]) <= k for i in range(len(b)))


def p_r4(w, c):
    t = 0
    for ch in w:
        t += (ch == "M") - (ch == "A")
        if abs(t) > c:
            return False
    return True


def chay(d: dict, w: str) -> bool:
    q = d["start"]
    for ch in w:
        q = d["transitions"][q][ch]
    return q in d["accepting"]


def kiem_schema(d: dict, ten: str) -> list[str]:
    loi = []
    if list(d.keys()) != ["states", "alphabet", "start", "accepting", "transitions"]:
        loi.append(f"{ten}: khóa phải đúng thứ tự states/alphabet/start/accepting/transitions, "
                   f"đang là {list(d.keys())}")
    Q, S = set(d["states"]), d["alphabet"]
    if len(Q) != len(d["states"]):
        loi.append(f"{ten}: trạng thái bị trùng")
    if S != SIGMA:
        loi.append(f"{ten}: alphabet phải là {SIGMA}")
    if d["start"] not in Q:
        loi.append(f"{ten}: start không thuộc states")
    if not set(d["accepting"]) <= Q:
        loi.append(f"{ten}: accepting không nằm trong states")
    if set(d["transitions"]) != Q:
        loi.append(f"{ten}: transitions không phủ đúng mọi trạng thái")
    for q, hang in d["transitions"].items():
        if set(hang) != set(S):
            loi.append(f"{ten}: {q} thiếu/thừa ký hiệu (DFA phải ĐẦY ĐỦ)")
        for s, q2 in hang.items():
            if q2 not in Q:
                loi.append(f"{ten}: δ({q},{s}) = {q2} không thuộc states")
    return loi


def tu_kiem(dfas: dict, k: int, c: int, chuoi_that: dict, do_dai: int = 8) -> list[str]:
    vt = {"r1": p_r1, "r2": p_r2, "r3": lambda w: p_r3(w, k), "r4": lambda w: p_r4(w, c)}
    loi = []
    for ten, d in dfas.items():
        loi_schema = kiem_schema(d, ten)      # chỉ bỏ qua DFA NÀY nếu chính nó hỏng schema
        loi += loi_schema
        if loi_schema:
            continue
        for L in range(do_dai + 1):
            for t in itertools.product(SIGMA, repeat=L):
                w = "".join(t)
                if chay(d, w) != vt[ten](w):
                    loi.append(f"{ten}: lệch vị từ tại {w!r} (DFA={chay(d, w)})")
                    break
            if loi and loi[-1].startswith(ten):
                break
        for gt, w in chuoi_that.items():
            if chay(d, w) != vt[ten](w):
                loi.append(f"{ten}: lệch vị từ trên chuỗi thật của {gt}")
                break
    return loi


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sinh + tự kiểm 4 DFA (req 3.1, 3.4a)")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm 4 file hiện có, không ghi")
    a = ap.parse_args(argv)

    goc = Path(__file__).resolve().parent.parent
    hc = goc / "data" / "processed" / "m3_calibration.json"
    st = goc / "data" / "processed" / "m3_real_strings.json"
    if not hc.exists() or not st.exists():
        print("[build_dfas] LỖI: chạy m3_automata/strings_from_data.py trước", file=sys.stderr)
        return 1
    ts = json.loads(hc.read_text(encoding="utf-8"))["tham_so"]
    k, c = int(ts["k"]), int(ts["c"])
    chuoi = json.loads(st.read_text(encoding="utf-8"))["strings"]

    thu_muc = goc / "m3_automata"
    doc = lambda i: json.loads((thu_muc / f"dfa_r{i}.json").read_text(encoding="utf-8"))
    if a.check:
        dfas = {f"r{i}": doc(i) for i in (1, 2, 3, 4)}
    else:
        # R1, R2 bản của Kiệt ĐÚNG: giữ nguyên file, chỉ kiểm. Chỉ sinh lại R3, R4.
        dfas = {"r1": doc(1), "r2": doc(2), "r3": dfa_r3(k), "r4": dfa_r4(c)}

    loi = tu_kiem(dfas, k, c, chuoi)
    tong = sum(4 ** L for L in range(9))
    print(f"[build_dfas] tham số: R1 ≤ {R1_MAX_LIEN_TIEP} ngày liên tiếp (chính sách) · "
          f"R3 k = {k} · R4 c = {c} (hiệu chỉnh từ dữ liệu)")
    for ten, d in dfas.items():
        nhan = sum(chay(d, w) for w in chuoi.values())
        print(f"  dfa_{ten}: {len(d['states']):>3} trạng thái · chấp nhận "
              f"{nhan}/{len(chuoi)} giám thị thật")
    if loi:
        print("  HỎNG:")
        for l in loi[:10]:
            print("   -", l)
        return 1
    print(f"  ĐẠT: schema đúng, DFA đầy đủ, khớp vị từ brute-force trên toàn bộ {tong:,} "
          f"chuỗi dài ≤ 8 và {len(chuoi)} chuỗi thật")

    if not a.check:
        for ten in ("r3", "r4"):
            (thu_muc / f"dfa_{ten}.json").write_text(
                json.dumps(dfas[ten], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  Đã ghi m3_automata/dfa_r3.json, dfa_r4.json (R1, R2 giữ nguyên bản gốc)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
