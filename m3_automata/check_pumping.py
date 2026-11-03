#!/usr/bin/env python3
"""
m3_automata/check_pumping.py
Phép kiểm chạy được cho m3_automata/pumping_proof.md (req 3.4b, 3.4c).

Kiểm 3 điều bằng vét cạn (hữu hạn, không phải chứng minh, chỉ là kiểm chứng):
  (1) L ∩ M*A* == {M^n A^n}  trên mọi chuỗi độ dài <= N_MAX over {M,A,N,-}
  (2) Với mỗi p = 1..P_MAX: MỌI cách tách w = M^p A^p = xyz thỏa |xy|<=p, |y|>=1
      đều bơm ra khỏi {M^n A^n} (i=0 và i=2) -> không có độ dài bơm p nào dùng được
  (3) Phiên bản có chặn |#M-#A|<=c là chính quy: DFA bộ đếm có 2c+2 trạng thái
      (-c..c và bẫy) chấp nhận đúng ngôn ngữ đó trên mọi chuỗi độ dài <= N_MAX
"""
import itertools
import re
import sys

SIGMA = "MAN-"
N_MAX = 8
P_MAX = 12
C = 2


def in_L(w):                       # L = {w : #M = #A}
    return w.count("M") == w.count("A")


def in_MstarAstar(w):              # M*A*
    return re.fullmatch(r"M*A*", w) is not None


def in_Lprime(w):                  # {M^n A^n : n >= 0}
    n = len(w) // 2
    return w == "M" * n + "A" * n


def kiem_giao():
    sai = 0
    for n in range(N_MAX + 1):
        for t in itertools.product(SIGMA, repeat=n):
            w = "".join(t)
            if (in_L(w) and in_MstarAstar(w)) != in_Lprime(w):
                sai += 1
                print("  SAI:", repr(w))
    return sai == 0


def kiem_bom():
    for p in range(1, P_MAX + 1):
        w = "M" * p + "A" * p
        for xy in range(1, p + 1):             # |xy| <= p
            for x_len in range(0, xy):         # |y| = xy - x_len >= 1
                x, y, z = w[:x_len], w[x_len:xy], w[xy:]
                for i in (0, 2):
                    if in_Lprime(x + y * i + z):
                        print(f"  SAI: p={p} x={x!r} y={y!r} i={i} van thuoc L'")
                        return False
    return True


def dfa_bounded(w, c=C):           # trạng thái = hiệu #M-#A trong [-c, c], hoặc BẪY
    d = 0
    for ch in w:
        d += (ch == "M") - (ch == "A")
        if abs(d) > c:
            return False           # vào trạng thái bẫy, không thoát ra
    return True


def kiem_bounded():
    for n in range(N_MAX + 1):
        for t in itertools.product(SIGMA, repeat=n):
            w = "".join(t)
            # "mọi tiền tố đều có |#M-#A|<=c" (nghĩa của bẫy), không chỉ cả chuỗi
            pref_ok = all(abs(w[:k].count("M") - w[:k].count("A")) <= C
                          for k in range(len(w) + 1))
            if dfa_bounded(w) != pref_ok:
                return False
    return True


if __name__ == "__main__":
    kq = {
        f"(1) L ∩ M*A* = {{M^n A^n}} (moi chuoi do dai <= {N_MAX})": kiem_giao(),
        f"(2) khong co tach xyz nao bom duoc M^pA^p, p=1..{P_MAX}": kiem_bom(),
        f"(3) DFA bo dem |#M-#A|<={C} ({2*C+2} trang thai) dung": kiem_bounded(),
    }
    for k, v in kq.items():
        print(("DAT   " if v else "HONG  ") + k)
    sys.exit(0 if all(kq.values()) else 1)
