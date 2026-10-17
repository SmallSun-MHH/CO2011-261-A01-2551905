"""
Module 2 — yêu cầu 2.10 (Phản ví dụ cho một mô hình sai): nêu một lựa chọn mô hình hợp lý
nhưng sai (nới ILP thành LP liên tục cho phép x = 0.5; bỏ ràng buộc overlap) và đưa ra
một lịch cụ thể mà mô hình sai chấp nhận, chỉ ra vì sao lịch đó không hợp lệ.

Người làm: 2551920 Nguyễn Quang Phúc
"""

import sys
from pathlib import Path

import pulp

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

CBC = pulp.PULP_CBC_CMD(msg=False)


def solve(model):
    model.solve(CBC)
    return pulp.LpStatus[model.status]


def build(invigs, shifts, cap, overlaps, integer, use_overlap=True, minmax=False):
    m = pulp.LpProblem("iap_small", pulp.LpMinimize)
    cat = "Binary" if integer else "Continuous"
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=1, cat=cat)
         for i in invigs for j in shifts}
    for j in shifts:
        m += pulp.lpSum(x[i, j] for i in invigs) == cap[j]
    if use_overlap:
        for a, b in overlaps:
            for i in invigs:
                m += x[i, a] + x[i, b] <= 1
    if minmax:
        t = pulp.LpVariable("t", lowBound=0)
        for i in invigs:
            m += t >= pulp.lpSum(x[i, j] for j in shifts)
        m += t
    else:
        m += 0
    return m, x


def show(x):
    return {k: round(v.value(), 3) for k, v in x.items() if v.value() and v.value() > 1e-9}


print("=" * 70)
print("A. Min-max: LP-relaxation cho dap an tot hon thuc te (x = 0.5)")
print("=" * 70)
I, J, cap = ["A", "B"], ["s"], {"s": 1}
lp, xl = build(I, J, cap, [], integer=False, minmax=True)
ip, xi = build(I, J, cap, [], integer=True, minmax=True)
assert solve(lp) == "Optimal" and solve(ip) == "Optimal"
t_lp, t_ip = pulp.value(lp.objective), pulp.value(ip.objective)
print(f"  LP : x = {show(xl)}  -> dinh tai t = {t_lp}")
print(f"  ILP: x = {show(xi)}  -> dinh tai t = {t_ip}")
assert abs(t_lp - 0.5) < 1e-6 and abs(t_ip - 1) < 1e-6
assert any(abs(v.value() - 0.5) < 1e-6 for v in xl.values()), "LP phai cho x = 0.5"
print("  => LP xep 'nua nguoi A + nua nguoi B' cho ca s va bao dinh tai 0.5.")
print("     Khong co lich thuc nao co dinh tai < 1 (mot nguoi nhan 0 hoac 1 ca).")
print("     Gap = ZILP - ZLP = 0.5 > 0: LP khong nhan dang duoc doan nay.\n")

print("=" * 70)
print("B. Tinh kha thi: LP noi 'xep duoc', thuc te KHONG xep duoc")
print("=" * 70)
I = ["A", "B"]
J = ["j1", "j2", "j3"]
cap = {j: 1 for j in J}
ov = [("j1", "j2"), ("j1", "j3"), ("j2", "j3")]
lp, xl = build(I, J, cap, ov, integer=False)
ip, xi = build(I, J, cap, ov, integer=True)
s_lp, s_ip = solve(lp), solve(ip)
print(f"  LP : {s_lp}")
print(f"       x = {show(xl)}")
print(f"  ILP: {s_ip}")
assert s_lp == "Optimal", "LP phai kha thi"
assert s_ip == "Infeasible", "ILP phai infeasible"
frac = [k for k, v in xl.items() if 1e-6 < v.value() < 1 - 1e-6]
assert frac, "nghiem LP phai co thanh phan phan so"
print(f"  Thanh phan phan so trong nghiem LP: {len(frac)}/{len(xl)}")
print("  => 3 ca trung gio doi mot can 3 nguoi KHAC nhau nhung chi co 2 giam thi: ILP infeasible")
print("     la dung. LP lai khong tim ra vi rang buoc doi mot x_ia + x_ib <= 1 cho phep")
print("     x = 0.5 cho tat ca bien (0.5 + 0.5 = 1). Moi cap deu 'ok' nhung tong thi khong.")

strong = pulp.LpProblem("clique", pulp.LpMinimize)
xs = {(i, j): pulp.LpVariable(f"c_{i}_{j}", lowBound=0, upBound=1) for i in I for j in J}
for j in J:
    strong += pulp.lpSum(xs[i, j] for i in I) == 1
for i in I:
    strong += pulp.lpSum(xs[i, j] for j in J) <= 1
strong += 0
assert solve(strong) == "Infeasible"
print("  Them rang buoc clique sum_j x_ij <= 1 (moi nguoi toi da 1 trong 3 ca) -> LP cung")
print("  infeasible: cat bo duoc nghiem 0.5. Day la huong lam chat mo hinh (tightening).\n")

print("=" * 70)
print("C. Bo rang buoc overlap (mo hinh sai khac): mot nguoi ngoi 2 ca cung luc")
print("=" * 70)
I, J, cap = ["A"], ["j", "k"], {"j": 1, "k": 1}
ov = [("j", "k")]
wrong, xw = build(I, J, cap, ov, integer=True, use_overlap=False)
right, xr = build(I, J, cap, ov, integer=True, use_overlap=True)
s_w, s_r = solve(wrong), solve(right)
print(f"  Bo overlap : {s_w}, x = {show(xw)}")
print(f"  Co overlap : {s_r}")
assert s_w == "Optimal" and s_r == "Infeasible"
assert xw["A", "j"].value() == 1 and xw["A", "k"].value() == 1
print("  => Mo hinh sai tra ve lich 'hop le' trong do A coi hai ca trung gio cung luc.")
print("     Mo hinh dung bao infeasible (chi co 1 giam thi cho 2 ca trung gio).")

print()
print("=" * 70)
print("D. Tren lat du lieu that cua nhom: dinh tai LP-relaxation vs ILP")
print("=" * 70)
_goc = Path(__file__).resolve().parent.parent
_inst = next((p for p in (_goc / "data" / "instance_slice.json",
                          _goc / "m1_logic" / "instance_slice.json") if p.exists()), None)
if _inst is None:
    print("  (khong thay instance_slice.json -> bo qua phan D)")
else:
    import json
    sys.path.insert(0, str(_goc))
    from m2_ilp.crosscheck_pulp import _cung
    from m2_ilp.model import build_params

    params = build_params(json.loads(_inst.read_text(encoding="utf-8-sig")))
    Ids, Js = params["I"], params["J"]

    def dinh_tai(integer):
        m = pulp.LpProblem("d", pulp.LpMinimize)
        cat = "Binary" if integer else "Continuous"
        x = {(i, j): pulp.LpVariable(f"x_{a}_{b}", lowBound=0, upBound=1, cat=cat)
             for a, i in enumerate(Ids) for b, j in enumerate(Js)}
        _cung(m, x, params)
        t = pulp.LpVariable("t", lowBound=0)
        for i in Ids:
            m += t >= pulp.lpSum(x[i, j] for j in Js)
        m += t
        assert solve(m) == "Optimal"
        return pulp.value(t), x

    t_lp, x_lp = dinh_tai(False)
    t_ip, _ = dinh_tai(True)
    n_frac = sum(1 for v in x_lp.values() if 1e-6 < v.value() < 1 - 1e-6)
    print(f"  |I|={len(Ids)} |J|={len(Js)} tong capacity={sum(int(v) for v in params['capacity'].values())}")
    print(f"  Dinh tai LP-relaxation (x lien tuc): {t_lp:.4f}   (so bien phan so: {n_frac})")
    print(f"  Dinh tai ILP (x nhi phan)          : {t_ip:.4f}")
    assert t_lp <= t_ip + 1e-9, "LP-relaxation khong the te hon ILP khi minimize"
    if t_ip - t_lp > 1e-6:
        print(f"  => LP bao dinh tai {t_lp:.2f} < {t_ip:.0f}: khong ai co the nhan {t_lp:.2f} ca. "
              f"Phan vi du that tren du lieu cua nhom.")
    else:
        print("  => Tren lat nay LP-relaxation tinh co trung dinh tai voi ILP (gap = 0), nen KHONG")
        print("     co phan vi du truc tiep o day. Phan vi du A-C o tren van dung o dang tong quat.")

print("\nOK - cac phan vi du deu duoc kiem chung bang code.")
