#!/usr/bin/env python3
"""m4_dynamics/fairness_ablation.py — Task 18 (điểm nối M2 ↔ M4) + mục tiêu tuần 12
"nối vào luận điểm công bằng".

Tác giả: 2551918 Nguyễn Phong Phú (có AI hỗ trợ — khai báo trong README §4).

Câu hỏi: trong vòng lặp đóng của rolling_horizon.py, CÁI GÌ làm cho tải tích luỹ
đều nhau — trạng thái mệt mỏi F hay chỉ là tải tích luỹ W?

Hàm compute_feedback_lambdas() xếp hạng giám thị theo khoá (tải 5 kỳ gần nhất,
tải tích luỹ) TRƯỚC, rồi mới tới F (chỉ để phá hoà). Vì vậy script so 4 luật
phản hồi trên CÙNG lát dữ liệu, cùng F(0), cùng 60 kỳ, cùng solve_week của M2:

  OL    : vòng hở, λ = 0.
  W     : chỉ xếp theo tải (5 kỳ gần nhất, tích luỹ); F không tham gia.
  F     : chỉ xếp theo mệt mỏi THẬT F_raw (phương trình F_{n+1} = aF + b·tải − r·nghỉ
          với tải nguyên từng kỳ); tải tích luỹ không tham gia.
  W+F   : luật đang dùng trong rolling_horizon.py (W trước, F_eff phá hoà). Script
          kiểm lại rằng chạy luật này ở đây ra ĐÚNG chuỗi tải trong rolling_horizon.json.

Và đo hai thứ cho mỗi luật:
  * công bằng tải: độ trải tải tích luỹ max − min, Jain;
  * mệt mỏi THẬT F_raw ở cuối: độ trải, và trung bình 6 kỳ cuối so với F*.
    (F_eff mà simulate.py dùng để chấm hội tụ được lái bởi tải TRUNG BÌNH TRƯỢT 6 kỳ,
    nên khi xoay vòng đều nó về F* gần như theo định nghĩa; F_raw mới là nghiệm của
    phương trình mệt mỏi với tải thật.)

Ghi m4_dynamics/out/fairness_ablation.json. Thiếu dữ liệu thì dừng, không dùng số giả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from m2_ilp.model import solve_week  # noqa: E402
from m4_dynamics.recurrence import (  # noqa: E402
    compute_feedback_lambdas,
    load_or_fit_params,
    step_fatigue_vector,
)
from m4_dynamics.rolling_horizon import (  # noqa: E402
    DEFAULT_INSTANCE,
    SEED_INT,
    jain_index,
    load_m2_params,
)

OUT = Path(__file__).resolve().parent / "out"
N_KY = 60
CHU_KY = 6          # 18 / gcd(18, 21)
LUAT = ("OL", "W", "F", "W+F")


def chay(params: dict, calib: dict, f0: np.ndarray, luat: str, n_ky: int = N_KY) -> dict:
    I = list(params["I"])
    n = len(I)
    a, b, r = float(calib["a"]), float(calib["b"]), float(calib["r"])
    M = float(calib.get("max_load_ref", 2.0))
    l_bar = float(calib["l_bar"])

    f_eff = f0.copy()
    f_raw = f0.copy()
    cum = np.zeros(n, dtype=int)
    trai_theo_ky: list[int] = []
    tai_ls: list[list[int]] = []
    f_raw_ls = [f_raw.copy()]
    cung_dat = True

    for _ in range(n_ky):
        gan5 = np.sum(np.asarray(tai_ls[-5:], dtype=int), axis=0) if tai_ls else np.zeros(n, dtype=int)
        khoa_w = {I[k]: (int(gan5[k]), int(cum[k])) for k in range(n)}
        if luat == "OL":
            lam = None
        elif luat == "W":
            lam = compute_feedback_lambdas({i: 0.0 for i in I}, khoa_w)
        elif luat == "F":
            lam = compute_feedback_lambdas({I[k]: float(f_raw[k]) for k in range(n)}, None)
        elif luat == "W+F":
            lam = compute_feedback_lambdas({I[k]: float(f_eff[k]) for k in range(n)}, khoa_w)
        else:
            raise ValueError(luat)

        kq = solve_week(params, lambdas=lam, seed_int=SEED_INT, verbose=False)
        cung_dat &= bool(kq.get("kiem_rang_buoc_cung", {}).get("tat_ca_dat", False))
        tai = np.array([int(kq["load"][i]) for i in I], dtype=int)
        cum += tai
        trai_theo_ky.append(int(cum.max() - cum.min()))
        tai_ls.append([int(x) for x in tai])

        # cập nhật ĐÚNG như rolling_horizon.py để W+F tái tạo được kết quả của nó
        gan = np.asarray(tai_ls[-CHU_KY:], dtype=float)
        tb = (gan.sum(axis=0) + (CHU_KY - len(gan)) * l_bar) / CHU_KY
        moi_eff = step_fatigue_vector({I[k]: float(f_eff[k]) for k in range(n)},
                                      {I[k]: float(tb[k]) for k in range(n)}, a, b, r, M)
        moi_raw = step_fatigue_vector({I[k]: float(f_raw[k]) for k in range(n)},
                                      {I[k]: float(tai[k]) for k in range(n)}, a, b, r, M)
        f_eff = np.array([moi_eff[i] for i in I])   # dict trả về theo thứ tự sorted(id)
        f_raw = np.array([moi_raw[i] for i in I])
        f_raw_ls.append(f_raw.copy())

    f_star = float(calib["F_star"])
    cuoi = np.asarray(f_raw_ls[-CHU_KY:])
    tb_chu_ky = cuoi.mean(axis=0)
    return {
        "luat": luat,
        "rang_buoc_cung_dat_moi_ky": bool(cung_dat),
        "tai_tich_luy_trai": int(cum.max() - cum.min()),
        "tai_tich_luy_jain": round(jain_index(cum), 6),
        "tai_tich_luy_trai_max_tu_ky_7": max(trai_theo_ky[CHU_KY:]),
        "tai_tich_luy_trai_ky_30_60": [trai_theo_ky[29], trai_theo_ky[-1]],
        "F_raw_trai_cuoi": round(float(f_raw.max() - f_raw.min()), 6),
        "F_raw_tb_6_ky_cuoi_lech_F_sao_max": float(np.max(np.abs(tb_chu_ky - f_star))),
        "F_raw_bien_do_6_ky_cuoi_max": round(float(np.max(cuoi.max(axis=0) - cuoi.min(axis=0))), 6),
        "F_eff_lech_F_sao_max_cuoi": float(np.max(np.abs(f_eff - f_star))),
        "lich_tai": tai_ls,
    }


def main() -> int:
    m3 = ROOT / "data" / "processed" / "m3_real_strings.json"
    if not DEFAULT_INSTANCE.exists() or not m3.exists():
        raise SystemExit("[fairness_ablation] Thiếu data/instance_slice.json hoặc m3_real_strings.json — "
                         "chạy `python run_all.py --seed 43003334` trước. Không dùng số giả.")
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        params = load_m2_params(DEFAULT_INSTANCE)
    with contextlib.redirect_stdout(io.StringIO()):
        calib = load_or_fit_params()
    rng = np.random.default_rng(43003334)  # cùng F(0) với rolling_horizon.run_comparison
    f0 = np.clip(float(calib["F_star"]) + rng.uniform(-0.45, 0.55, size=len(params["I"])), 0.1, 2.8)

    kq = {l: chay(params, calib, f0, l) for l in LUAT}

    # Đối chiếu: luật W+F ở đây phải tái tạo đúng chuỗi tải của rolling_horizon.json
    rh_path = OUT / "rolling_horizon.json"
    tai_tao = None
    if rh_path.exists():
        rh = json.loads(rh_path.read_text(encoding="utf-8"))
        tai_tao = rh["closed_loop"]["history_loads"] == kq["W+F"]["lich_tai"]

    def giong(x: str, y: str) -> float:
        A, B = np.asarray(kq[x]["lich_tai"]), np.asarray(kq[y]["lich_tai"])
        return float((A == B).mean())

    print("[m4_fairness_ablation] Cái gì làm tải tích luỹ đều nhau? (60 kỳ, cùng F(0), cùng solve_week M2)")
    print(f"  {'luật':>5} {'5/5 cứng':>9} {'trải tải':>9} {'max≥kỳ7':>8} {'Jain':>9} {'trải F_raw':>11} "
          f"{'biên độ F_raw':>14} {'|TB6(F_raw)−F*|':>16} {'|F_eff−F*|':>11}")
    for l in LUAT:
        k = kq[l]
        print(f"  {l:>5} {str(k['rang_buoc_cung_dat_moi_ky']):>9} {k['tai_tich_luy_trai']:>9} "
              f"{k['tai_tich_luy_trai_max_tu_ky_7']:>8} "
              f"{k['tai_tich_luy_jain']:>9.6f} {k['F_raw_trai_cuoi']:>11.4f} {k['F_raw_bien_do_6_ky_cuoi_max']:>14.4f} "
              f"{k['F_raw_tb_6_ky_cuoi_lech_F_sao_max']:>16.2e} {k['F_eff_lech_F_sao_max_cuoi']:>11.2e}")
    print(f"  Lịch W+F trùng lịch W ở {giong('W', 'W+F'):.0%} ô (người, kỳ); trùng lịch F ở {giong('F', 'W+F'):.0%}.")
    if tai_tao is not None:
        print(f"  W+F tái tạo đúng chuỗi tải của rolling_horizon.json: {tai_tao}")

    w, f, wf, ol = kq["W"], kq["F"], kq["W+F"], kq["OL"]
    ket_luan = {
        "W_du_de_can_bang_tai": w["tai_tich_luy_trai"] <= wf["tai_tich_luy_trai"],
        "F_mot_minh_giu_trai_tai_bi_chan": f["tai_tich_luy_trai_max_tu_ky_7"] <= 2,
        "F_raw_hoi_tu_ve_diem": wf["F_raw_bien_do_6_ky_cuoi_max"] < 1e-3,
        "F_raw_tb_chu_ky_ve_F_sao": wf["F_raw_tb_6_ky_cuoi_lech_F_sao_max"] < 1e-3,
    }
    print("  ⇒ " + ("Trong luật W+F hiện tại, xếp hạng do tải W quyết định trước (F chỉ phá hoà): riêng W đã "
                    "cho độ trải 0 như W+F, nên con số 'spread = 0' KHÔNG chứng minh được vai trò của mệt mỏi."
                    if ket_luan["W_du_de_can_bang_tai"] else "Bỏ F thì công bằng tải kém đi: F có đóng góp."))
    print(f"  ⇒ Luận điểm công bằng đúng nằm ở luật F: chỉ biết mệt mỏi thật F_raw, không sổ sách tải, độ trải tải "
          f"tích luỹ vẫn ≤ {f['tai_tich_luy_trai_max_tu_ky_7']} ca suốt kỳ 7–60 (vòng hở: {ol['tai_tich_luy_trai']} ca và "
          f"tăng tuyến tính) — phản hồi mệt mỏi một mình đã giữ bất công BỊ CHẶN; thêm W chỉ đưa độ trải từ "
          f"{f['tai_tich_luy_trai']} về {wf['tai_tich_luy_trai']}."
          if ket_luan["F_mot_minh_giu_trai_tai_bi_chan"]
          else f"  ⇒ Chỉ dùng F_raw thì độ trải tải lên tới {f['tai_tich_luy_trai_max_tu_ky_7']} ca.")
    print("  ⇒ Mệt mỏi thật F_raw KHÔNG hội tụ về một điểm: nó về một quỹ đạo tuần hoàn chu kỳ 6 với biên độ "
          f"{wf['F_raw_bien_do_6_ky_cuoi_max']:.3f}, mà trung bình mỗi chu kỳ khớp F* tới "
          f"{wf['F_raw_tb_6_ky_cuoi_lech_F_sao_max']:.1e}. 'Hội tụ về F* < 1e-3' của simulate.py là của F_eff "
          "(lái bởi tải trung bình trượt), nên báo cáo phải nói rõ đó là mệt mỏi TRUNG BÌNH CHU KỲ.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fairness_ablation.json").write_text(json.dumps({
        "n_ky": N_KY, "chu_ky_xoay_vong": CHU_KY, "F_sao": calib["F_star"],
        "luat": {l: {k: v for k, v in kq[l].items() if k != "lich_tai"} for l in LUAT},
        "ty_le_trung_lich": {"W_vs_W+F": giong("W", "W+F"), "F_vs_W+F": giong("F", "W+F"),
                              "OL_vs_W+F": giong("OL", "W+F")},
        "W+F_tai_tao_rolling_horizon": tai_tao,
        "ket_luan": ket_luan,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  Đã ghi m4_dynamics/out/fairness_ablation.json")
    return 0 if all(kq[l]["rang_buoc_cung_dat_moi_ky"] for l in LUAT) else 1


if __name__ == "__main__":
    raise SystemExit(main())
