#!/usr/bin/env python3
"""
m4_dynamics/identify.py — Module 4, M4-A: dữ liệu nói được gì về (a, b, r)?
=====================================================================
`calibrate.py` (task 16) chọn tham số sao cho điểm bất động khớp tải trung bình:

    F* = (b·l̄ − r·ρ̄) / (1 − a)  =  l̄,   với  b = (1 − a) + r·ρ̄/l̄.

Thay b vào:  b·l̄ − r·ρ̄ = (1 − a)·l̄  ⇒  F* = l̄  với MỌI a và MỌI r. Tức "F* khớp
l̄ với sai số 2.2e-16" là một ĐẲNG THỨC đại số đúng sẵn theo cách dựng b, không
phải bằng chứng hiệu chỉnh. File này làm ba việc mà phép khớp đó không làm được:

  1. ĐẲNG THỨC — chạy thật F* = l̄ với (a, r) bất kỳ, để không ai còn trình bày nó
     như một phép kiểm chứng.

  2. DỮ LIỆU THẬT CÓ HIỆU ỨNG MỆT MỎI KHÔNG — hồi quy logit trên 73 giám thị ×
     27 ngày thật (task 11, Phúc):
         P(làm ngày t) = σ( α_t + β · H_t(a) ),   H_t(a) = Σ_{s<t} a^{t−1−s} · làm_s
     α_t là hiệu ứng RIÊNG từng ngày, hút hết nhu cầu (ngày thi cao điểm ai cũng
     đi làm). β < 0 có ý nghĩa nghĩa là: cùng một ngày, người vừa làm nhiều thì ít
     được xếp làm hơn — đúng chiều mô hình mệt mỏi.

  3. a CÓ XÁC ĐỊNH ĐƯỢC TỪ DỮ LIỆU KHÔNG — hồ sơ hợp lý (profile likelihood) theo
     a trên lưới [0; 0,95], khoảng tin cậy 95% theo tỷ số hợp lý (ngưỡng χ²₁/2 =
     1,92). Vùng tin cậy có thể KHÔNG liên thông nên được báo dưới dạng hợp các
     đoạn (không lấy [min; max]). Kết quả trên dữ liệu thật: dữ liệu ưu tiên trí
     nhớ ngắn, và a = 0,760528 trong calibrate.py (đúng bằng tỷ lệ ngày nghỉ) nằm
     NGOÀI vùng 95% — a là QUY ƯỚC của nhóm, không phải ước lượng.

  4. ĐỘ NHẠY — vì a không được dữ liệu ủng hộ, chạy lại thí nghiệm nhiễu loạn của
     perturbation.py (task 20) với nhiều giá trị a, để báo cáo thấy kết luận nào
     đứng vững bất kể a, kết luận nào phụ thuộc a.

Cách chạy:  python m4_dynamics/identify.py
Đầu ra:     m4_dynamics/out/identify.json, m4_dynamics/out/identify_profile.png
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "m4_dynamics" / "out"
LUOI_A = [round(x, 2) for x in np.arange(0.0, 0.951, 0.05)]
NGUONG_LR = 1.92            # χ²₁(0,95) / 2
A_DO_NHAY = [0.3, 0.5, None, 0.9]   # None = giá trị của calibrate.py


# ---------------------------------------------------------------------------
def doc_chuoi() -> np.ndarray:
    p = ROOT / "data" / "processed" / "m3_real_strings.json"
    if not p.exists():
        # KHÔNG có dữ liệu dự phòng gõ tay: thiếu dữ liệu thật thì dừng hẳn.
        raise SystemExit("[m4_identify] LỖI: chưa có data/processed/m3_real_strings.json — "
                         "chạy `python run_all.py --seed $(cat data/seed.txt)` (hoặc "
                         "m3_automata/strings_from_data.py) trước.")
    S = json.loads(p.read_text(encoding="utf-8"))["strings"]
    return np.array([[1.0 if c != "-" else 0.0 for c in s] for s in S.values()])


def lich_su(W: np.ndarray, a: float) -> np.ndarray:
    h = np.zeros_like(W)
    for t in range(1, W.shape[1]):
        h[:, t] = a * h[:, t - 1] + W[:, t - 1]
    return h


def logit_hieu_ung_ngay(W: np.ndarray, a: float, vong: int = 80) -> dict:
    """Logit có hiệu ứng cố định theo ngày α_t, hệ số chung β cho lịch sử H(a).
    Newton theo khối (α_t riêng từng ngày, β chung), bù Schur cho β."""
    h = lich_su(W, a)
    giu = (W.sum(0) > 0) & (W.sum(0) < W.shape[0])   # ngày ai cũng nghỉ / ai cũng làm: không mang tin
    X, Y = h[:, giu], W[:, giu]
    tb = Y.mean(0)
    al = np.log((tb + 1e-6) / (1 - tb + 1e-6))
    be = 0.0
    for _ in range(vong):
        p = 1 / (1 + np.exp(-(al[None, :] + be * X)))
        r, w = Y - p, p * (1 - p)
        g_al, h_al = r.sum(0), w.sum(0) + 1e-12
        c = (w * X).sum(0)
        h_be = (w * X * X).sum() - (c * c / h_al).sum()
        g_be = (r * X).sum() - (c * g_al / h_al).sum()
        d_be = g_be / h_be
        al += (g_al - c * d_be) / h_al
        be += d_be
        if abs(d_be) < 1e-12:
            break
    p = 1 / (1 + np.exp(-(al[None, :] + be * X)))
    ll = float((Y * np.log(p + 1e-12) + (1 - Y) * np.log(1 - p + 1e-12)).sum())
    se = float(1 / math.sqrt(h_be))
    z = be / se
    pval = math.erfc(abs(z) / math.sqrt(2))
    return {"a": a, "loglik": ll, "beta": float(be), "se": se, "z": float(z), "p": pval,
            "so_ngay_dung": int(giu.sum())}


def dang_thuc_F_sao(l_bar: float, rho_bar: float) -> list[dict]:
    rng = np.random.default_rng(0)
    kq = []
    for a, r in [(0.760528, 0.139692), (0.1, 0.9), (0.5, 0.0), (0.99, 5.0)] + \
                [(float(rng.uniform(0.01, 0.99)), float(rng.uniform(0, 3))) for _ in range(4)]:
        b = (1 - a) + r * rho_bar / l_bar
        F = (b * l_bar - r * rho_bar) / (1 - a)
        kq.append({"a": round(a, 6), "r": round(r, 6), "F_sao": F, "lech_l_bar": abs(F - l_bar)})
    return kq


def do_nhay_theo_a(calib: dict) -> list[dict]:
    from m4_dynamics.perturbation import load_m2_params, DEFAULT_INSTANCE, run_perturbation_experiment
    params = load_m2_params(DEFAULT_INSTANCE)
    l_bar, rho_bar, r = float(calib["l_bar"]), float(calib["rho_bar"]), float(calib["r"])
    kq = []
    for a in A_DO_NHAY:
        c = copy.deepcopy(calib)
        goc = a is None
        if not goc:
            c["a"] = a
            c["b"] = (1 - a) + r * rho_bar / l_bar          # cùng quy ước chuẩn hóa F* = l̄
            c["F_star"] = (c["b"] * l_bar - r * rho_bar) / (1 - a)
        p = run_perturbation_experiment(params=params, calib=c, n_periods=60, shock_start=18,
                                        shock_duration=2, shocked_invigilators=("CB003", "CB005"),
                                        fatigue_impulse=0.85)
        kq.append({
            "a": round(float(c["a"]), 6), "la_gia_tri_calibrate": goc,
            "rang_buoc_cung_dat": bool(p["all_hard_constraints_ok_during_and_after_shock"]),
            "vot_lo_so_voi_F_sao": round(float(p["peak_overshoot_to_F_star"]), 4),
            "hoi_phuc_ky_1e-2": p["recovery_time_periods_tol_1e_2"],
            "can_ly_thuyet_1e-2": p["theoretical_recovery_bound_tol_1e_2"],
            "sai_so_cuoi": float(p["final_max_dev_from_F_star"]),
            "chenh_tai_tich_luy_cuoi": p["final_cum_load_spread"],
        })
    return kq


def doan_lien_tiep(diem: list[float], luoi: list[float]) -> list[list[float]]:
    """Gom các điểm lưới được chấp nhận thành các đoạn liên tiếp. Vùng tin cậy theo
    tỷ số hợp lý có thể KHÔNG liên thông — không được lấy [min, max] của các điểm."""
    chi_so = sorted(luoi.index(x) for x in diem)
    doan: list[list[float]] = []
    for k in chi_so:
        if doan and luoi.index(doan[-1][1]) == k - 1:
            doan[-1][1] = luoi[k]
        else:
            doan.append([luoi[k], luoi[k]])
    return doan


def ve(ho_so: list[dict], a_mle: float, vung: list[list[float]], a_cal: float, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    A = [h["a"] for h in ho_so]
    L = [h["loglik"] - max(x["loglik"] for x in ho_so) for h in ho_so]
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=130)
    ax.plot(A, L, "o-", lw=1.6, ms=4, color="#2c6fbb")
    ax.axhline(-NGUONG_LR, ls="--", lw=1, color="#888")
    nhan = " ∪ ".join(f"[{u}; {v}]" for u, v in vung)
    for k, (u, v) in enumerate(vung):
        ax.axvspan(u - 0.02, v + 0.02, color="#2c6fbb", alpha=0.12,
                   label=f"vùng tin cậy 95%: a ∈ {nhan}" if k == 0 else None)
    ax.axvline(a_cal, color="#c0392b", lw=1.2, label=f"calibrate.py: a = {a_cal:.4f}")
    ax.set_xlabel("a (hệ số nhớ mệt mỏi)")
    ax.set_ylabel("log-likelihood − max")
    ax.set_title("Hồ sơ hợp lý theo a — 73 giám thị × 27 ngày thật, khử hiệu ứng ngày")
    ax.legend(fontsize=8, loc="upper center")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _json_numpy(o):
    """numpy.bool_ / numpy số không ghi thẳng ra JSON được."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(type(o).__name__)


# ---------------------------------------------------------------------------
def main() -> int:
    from m4_dynamics.recurrence import load_or_fit_params
    W = doc_chuoi()
    calib = load_or_fit_params()
    a_cal = float(calib["a"])
    n, T = W.shape

    print(f"[m4_identify] Dữ liệu nói được gì về (a, b, r)? — {n} giám thị × {T} ngày thật")

    # 1. đẳng thức
    dt = dang_thuc_F_sao(float(calib["l_bar"]), float(calib["rho_bar"]))
    lon_nhat = max(x["lech_l_bar"] for x in dt)
    print(f"\n  1. F* = l̄ là ĐẲNG THỨC: thử {len(dt)} cặp (a, r) bất kỳ, kể cả a=0,99 r=5 — "
          f"|F* − l̄| lớn nhất = {lon_nhat:.1e}.")
    print(f"     ⇒ 'F* khớp l̄' đúng sẵn theo cách giải b; KHÔNG dùng làm bằng chứng hiệu chỉnh.")

    # 2 + 3. hồ sơ hợp lý
    ho_so = [logit_hieu_ung_ngay(W, a) for a in LUOI_A]
    tot = max(ho_so, key=lambda h: h["loglik"])
    ci_a = [h["a"] for h in ho_so if tot["loglik"] - h["loglik"] <= NGUONG_LR]
    vung_95 = doan_lien_tiep(ci_a, LUOI_A)
    tai_cal = logit_hieu_ung_ngay(W, a_cal)
    delta_cal = float(tai_cal["loglik"] - tot["loglik"])
    a_cal_trong = bool(-delta_cal <= NGUONG_LR)

    print(f"\n  2. Hiệu ứng mệt mỏi (khử nhu cầu từng ngày bằng α_t):")
    print(f"     tại a = {tot['a']} (MLE): β = {tot['beta']:+.4f}, z = {tot['z']:+.2f}, p = {tot['p']:.3f}")
    print(f"     tại a = {a_cal:.4f} (calibrate.py): β = {tai_cal['beta']:+.4f}, z = {tai_cal['z']:+.2f}")
    co_hieu_ung = tot["beta"] < 0 and tot["p"] < 0.05
    print(f"     ⇒ {'CÓ hiệu ứng “làm hôm trước → ít được xếp hôm nay” có ý nghĩa (phản ánh cách xếp lịch giãn ca, chưa phải đo mệt mỏi sinh học).' if co_hieu_ung else 'KHÔNG thấy hiệu ứng mệt mỏi có ý nghĩa thống kê.'}")

    nhan_vung = " ∪ ".join(f"[{u}; {v}]" for u, v in vung_95)
    print(f"\n  3. Dữ liệu nói gì về a: MLE a = {tot['a']}, vùng tin cậy 95% (tỷ số hợp lý, Δℓ ≥ −{NGUONG_LR}) "
          f"a ∈ {nhan_vung} — {'KHÔNG liên thông' if len(vung_95) > 1 else 'liên thông'}.")
    print(f"     tại a = {a_cal:.4f} (calibrate.py): Δℓ = {delta_cal:+.2f} → "
          f"{'TRONG' if a_cal_trong else 'NGOÀI'} vùng tin cậy 95%.")
    if not a_cal_trong:
        print(f"     ⇒ Với mô hình logit này, dữ liệu ưu tiên trí nhớ NGẮN (a nhỏ); a = {a_cal:.4f} "
              f"(= tỷ lệ ngày nghỉ) là QUY ƯỚC và bị dữ liệu bác ở mức 5%. Lưu ý: logit đo xu hướng "
              f"XẾP LỊCH (không có hiệu ứng riêng từng giám thị), không đo mệt mỏi sinh học — nên đây "
              f"là bằng chứng chống lại việc gọi a là 'ước lượng từ dữ liệu', chưa phải ước lượng thay thế.")

    # 4. độ nhạy
    print(f"\n  4. Độ nhạy của thí nghiệm nhiễu loạn theo a (cùng cú sốc, cùng quy ước F* = l̄):")
    dn = do_nhay_theo_a(calib)
    print(f"     {'a':>8} {'5/5 cứng':>9} {'vọt lố':>8} {'hồi phục':>9} {'cận LT':>7} {'sai số cuối':>12} {'chênh tải':>10}")
    for r in dn:
        ghi = "  ← calibrate.py" if r["la_gia_tri_calibrate"] else ""
        print(f"     {r['a']:>8.4f} {str(r['rang_buoc_cung_dat']):>9} {r['vot_lo_so_voi_F_sao']:>8.4f} "
              f"{str(r['hoi_phuc_ky_1e-2']):>9} {str(r['can_ly_thuyet_1e-2']):>7} "
              f"{r['sai_so_cuoi']:>12.2e} {str(r['chenh_tai_tich_luy_cuoi']):>10}{ghi}")
    vung = all(r["rang_buoc_cung_dat"] for r in dn) and all(r["chenh_tai_tich_luy_cuoi"] == 0 for r in dn)
    hp = [r["hoi_phuc_ky_1e-2"] for r in dn if isinstance(r["hoi_phuc_ky_1e-2"], (int, float))]
    print(f"     ⇒ ĐỨNG VỮNG bất kể a: {'5/5 ràng buộc cứng và chênh tải tích lũy cuối = 0 ở mọi a thử.' if vung else 'KHÔNG — xem bảng.'}")
    if hp:
        print(f"     ⇒ PHỤ THUỘC a: thời gian hồi phục từ {min(hp)} tới {max(hp)} kỳ — báo cáo phải "
              f"nêu nó như một khoảng theo a, không phải một con số.")
    khong_kip = [r for r in dn if r["hoi_phuc_ky_1e-2"] is None]
    for r in khong_kip:
        print(f"     ⇒ CHÚ Ý: với a = {r['a']} hệ KHÔNG hồi phục tới 1e-2 trong 60 kỳ (cận lý thuyết "
              f"{r['can_ly_thuyet_1e-2']} kỳ sau cú sốc, sai số cuối {r['sai_so_cuoi']:.1e}). Kết luận "
              f"'hội tụ về F* trong dung sai' chỉ đúng khi a đủ nhỏ so với chân trời mô phỏng.")

    OUT.mkdir(parents=True, exist_ok=True)
    ve(ho_so, tot["a"], vung_95, a_cal, OUT / "identify_profile.png")
    (OUT / "identify.json").write_text(json.dumps({
        "du_lieu": {"so_giam_thi": n, "so_ngay": T, "ngay_lam": int(W.sum())},
        "dang_thuc_F_sao_bang_l_bar": {"mo_ta": "F* = l̄ với mọi a, r do b được giải từ chính ràng buộc này",
                                       "lech_lon_nhat": lon_nhat, "cac_thu": dt},
        "hieu_ung_met_moi": {"tai_mle": tot, "tai_a_calibrate": tai_cal, "co_y_nghia_05": co_hieu_ung},
        "xac_dinh_a": {"luoi": LUOI_A, "ho_so": ho_so, "a_mle": tot["a"], "nguong_lr": NGUONG_LR,
                       "vung_tin_cay_95": vung_95, "vung_lien_thong": len(vung_95) == 1,
                       "a_calibrate": a_cal, "delta_loglik_a_calibrate": delta_cal,
                       "a_calibrate_trong_vung_95": a_cal_trong,
                       "a_calibrate_la": "tỷ lệ ngày nghỉ — quy ước, không phải ước lượng",
                       "gioi_han_mo_hinh": "logit xu hướng xếp lịch có hiệu ứng ngày, không có hiệu ứng giám thị"},
        "do_nhay_nhieu_loan_theo_a": dn,
        "ket_luan_dung_vung_moi_a": vung,
        "a_khong_hoi_phuc_kip_60_ky": [r["a"] for r in dn if r["hoi_phuc_ky_1e-2"] is None],
    }, ensure_ascii=False, indent=2, default=_json_numpy) + "\n", encoding="utf-8")
    print(f"\n  Đã ghi m4_dynamics/out/identify.json và m4_dynamics/out/identify_profile.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
