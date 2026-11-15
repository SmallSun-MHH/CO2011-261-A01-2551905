"""
Module 4: Dẫn xuất F(n+1) = a·F(n) + b·load(g(F(n))) - r·rest, tìm điểm bất động duy nhất, phân loại ổn định.

Người làm: 2551920 Nguyễn Quang Phúc
"""

import contextlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from m2_ilp.model import build_params, solve_week
from m2_ilp.preprocess import run as run_preprocess


def nap_tham_so():
    seed = int((REPO / "data" / "seed.txt").read_text(encoding="utf-8-sig").strip())
    instance = json.loads((REPO / "data" / "instance_slice.json").read_text(encoding="utf-8-sig"))
    with contextlib.redirect_stdout(io.StringIO()):
        m2_data = run_preprocess(instance, seed_int=seed)
    return build_params(instance, m2_data), seed


def giai(params, seed, lambdas=None):
    return solve_week(params, lambdas, seed_int=seed, verbose=False)


def kiem_bo_de(params, seed, luoi=(0, 0.5, 1, 2, 4, 8)):
    tong0 = sum(giai(params, seed)["load"].values())
    bac_thang = {}
    for i in params["I"]:
        tai = []
        for lam in luoi:
            kq = giai(params, seed, {i: lam})
            assert sum(kq["load"].values()) == tong0
            tai.append(kq["load"][i])
        assert all(x >= y for x, y in zip(tai, tai[1:])), (i, tai)
        bac_thang[i] = tai
    co_giam = [i for i, t in bac_thang.items() if t[0] > t[-1]]
    print(f"[1] Bổ đề trên ILP thật: {len(bac_thang)} giám thị x {len(luoi)} mức λ, tải KHÔNG tăng ở cả {len(bac_thang)}.")
    print(f"    {len(co_giam)}/{len(bac_thang)} giám thị có tải giảm khi λ tăng. λ = {list(luoi)}")
    for i in co_giam[:3]:
        print(f"    {i}: tải theo λ = {bac_thang[i]}")
    print(f"    Tổng tải mỗi lần giải luôn bằng {tong0}.")


def vong_kin(params, seed, a=0.8, b=1.0, r_rho=0.3, mu=0.5, n_tuan=30):
    I = params["I"]
    F = {i: 0.0 for i in I}
    tong0 = None
    m0 = 0.0
    print(f"\n[2] Vòng kín 30 tuần trên ILP thật. Tham số MINH HỌA: "
          f"a={a}, b={b}, r·ρ={r_rho}, λᵢ = {mu}·Fᵢ")
    print(f"    {'tuần':>4} {'F trung bình':>13} {'công thức đóng':>15} {'độ lệch max-min':>16} {'tải max':>8}")
    for n in range(n_tuan + 1):
        kq = giai(params, seed, {i: mu * F[i] for i in I})
        tai = kq["load"]
        T = sum(tai.values())
        tong0 = T if tong0 is None else tong0
        assert T == tong0
        trung_binh = sum(F.values()) / len(I)
        f_sao = (b * tong0 / len(I) - r_rho) / (1 - a)
        dong = f_sao + a ** n * (m0 - f_sao)
        assert abs(trung_binh - dong) < 1e-9, (n, trung_binh, dong)
        if n in (0, 1, 2, 3, 5, 10, 20, 30):
            print(f"    {n:4d} {trung_binh:13.6f} {dong:15.6f} {max(F.values()) - min(F.values()):16.4f} {max(tai.values()):8d}")
        F = {i: a * F[i] + b * tai[i] - r_rho for i in I}
    print(f"    F̄* = (b·T/|I| − r·ρ)/(1−a) = {f_sao:.6f}; trung bình khớp công thức đóng đến 1e-9 ở mọi tuần.")

    lam = a
    if abs(lam) < 1:
        loai = "ON DINH tiệm cận"
    elif abs(lam) == 1:
        loai = "BIEN on dinh"
    else:
        loai = "KHONG ON DINH"

    print(f"    Trị riêng λ = a = {lam:.4f}")
    print(f"    Phân loại: {loai}")


def quet_mu(params, seed, a=0.8, b=1.0, r_rho=0.3, n_tuan=60):
    I = params["I"]
    print(f"\n[3] Quét độ dốc μ của λᵢ = μ·Fᵢ trên ILP thật ({n_tuan} tuần):")
    print(f"    {'μ':>5} {'max−min F':>10} {'F lớn nhất':>11} {'tỉ lệ (người, tuần) đổi tải':>28}")
    for mu in (0, 0.5, 2, 8):
        F = {i: 0.0 for i in I}
        lich_su = []
        for _ in range(n_tuan):
            tai = giai(params, seed, {i: mu * F[i] for i in I})["load"]
            lich_su.append(tai)
            F = {i: a * F[i] + b * tai[i] - r_rho for i in I}
        doi = sum(lich_su[k][i] != lich_su[k - 1][i] for i in I for k in range(n_tuan - 10, n_tuan)) / (10 * len(I))
        print(f"    {mu:5} {max(F.values()) - min(F.values()):10.4f} {max(F.values()):11.4f} {doi:28.2f}")


def so_sanh_bo_tich_luy(a=0.8, increment=1.0):
    print("\n[4] So sánh với bộ tích lũy workload:")

    print(f"    Fatigue: trị riêng λ = {a}")
    print("    Nếu 0 < a < 1: sai lệch so với cân bằng giảm dần.")

    print("    Workload: W(n+1) = W(n) + U")
    print("    Đạo hàm dW(n+1)/dW(n) = 1")
    print("    Trị riêng λ = 1")

    if increment > 0:
        print("    Không có điểm bất động hữu hạn khi U > 0.")
        print("    Workload tăng liên tục, không tự hồi phục.")


def main():
    params, seed = nap_tham_so()
    kiem_bo_de(params, seed)
    vong_kin(params, seed)
    quet_mu(params, seed)
    so_sanh_bo_tich_luy()


if __name__ == "__main__":
    main()
