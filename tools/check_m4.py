"""tools/check_m4.py — Cổng tự kiểm định Module 4 (Dynamical Systems & Rolling-Horizon).

Chạy:
    python tools/check_m4.py               # chạy lại toàn bộ M4 rồi kiểm định
    python tools/check_m4.py --khong-chay  # chỉ kiểm định trên các tệp JSON/PNG đã sinh
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Tự kiểm định Module 4 (M4-A).")
    parser.add_argument(
        "--khong-chay",
        action="store_true",
        help="Không chạy lại mô phỏng, chỉ kiểm tra đầu ra hiện có trong m4_dynamics/out/.",
    )
    args = parser.parse_args()

    passed = 0
    warned = 0
    failed = 0

    def ok(msg: str) -> None:
        nonlocal passed
        passed += 1
        print(f"  [ĐẠT]      {msg}")

    def warn(msg: str) -> None:
        nonlocal warned
        warned += 1
        print(f"  [CẢNH BÁO] {msg}")

    def err(msg: str) -> None:
        nonlocal failed
        failed += 1
        print(f"  [HỎNG]     {msg}")

    print("=" * 74)
    print("CỔNG KIỂM ĐỊNH MODULE 4 — HỆ ĐỘNG LỰC MỆT MỎI & ROLLING-HORIZON (M4-A)")
    print("=" * 74)

    # 1. Kiểm tra sự tồn tại của các tệp mã nguồn M4
    m4_dir = ROOT / "m4_dynamics"
    core_files = [
        ("m4_dynamics/recurrence.py", "Task 17 — Phương trình sai phân & Điểm bất động F*"),
        ("m4_dynamics/rolling_horizon.py", "Task 18 — Vòng lặp đóng kết nối M2 solve_week"),
        ("m4_dynamics/simulate.py", "Task 19 — Mô phỏng hội tụ & Xuất biểu đồ (Autograder)"),
        ("m4_dynamics/perturbation.py", "Task 20 — Nhiễu loạn nghỉ ốm, Độ nhạy & Xích Markov"),
        ("m4_dynamics/README.md", "Tài liệu kỹ thuật Module 4"),
    ]
    for rel, desc in core_files:
        p = ROOT / rel
        if p.exists() and p.stat().st_size > 200:
            ok(f"Có tệp {rel} ({desc})")
        else:
            err(f"Thiếu hoặc rỗng tệp {rel} ({desc})")

    calib_py = m4_dir / "calibrate.py"
    if calib_py.exists() and calib_py.stat().st_size > 100:
        ok("Có tệp m4_dynamics/calibrate.py (Task 16 — Trần Tuấn Kiệt 2551907)")
    else:
        warn(
            "Chưa có m4_dynamics/calibrate.py (Task 16 — Chừa lại cho Trần Tuấn Kiệt 2551907); "
            "hệ thống đang dùng cơ chế fallback chuẩn load_or_fit_params() trong recurrence.py."
        )

    # 2. Thực thi các mô-đun M4 nếu không bật --khong-chay
    if not args.khong_chay:
        try:
            from m4_dynamics.recurrence import analyze_recurrence_and_stability, load_or_fit_params
            from m4_dynamics.simulate import run_simulation
            from m4_dynamics.perturbation import run_all_perturbation_analyses

            calib = load_or_fit_params()
            analyze_recurrence_and_stability(calib)
            run_simulation(n_periods=60)
            run_all_perturbation_analyses(n_periods=60)
            ok("Thực thi thành công pipeline recurrence -> rolling_horizon -> simulate -> perturbation")
        except Exception as exc:
            err(f"Lỗi khi thực thi pipeline M4: {exc}")

    # 3. Kiểm định recurrence_analysis.json
    rec_path = m4_dir / "out" / "recurrence_analysis.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        params = rec.get("parameters", {})
        eq = rec.get("equilibrium", {})
        stab = rec.get("stability", {})
        why_not = rec.get("why_not_raw_accumulator", {})

        a = float(params.get("a", 0.0))
        b = float(params.get("b", 0.0))
        r = float(params.get("r", 0.0))
        if 0.0 < a < 1.0 and b > 0.0 and r > 0.0:
            ok(f"Tham số hiệu chỉnh hợp lệ: a={a:.6f} in (0,1), b={b:.6f}>0, r={r:.6f}>0")
        else:
            err(f"Tham số hiệu chỉnh không hợp lệ: a={a}, b={b}, r={r}")

        if eq.get("is_valid_fixed_point") and float(eq.get("fixed_point_equation_residual", 1.0)) < 1e-10:
            ok(f"Điểm bất động giải tích F* = {eq.get('F_star_analytical'):.6f} thỏa f(F*) = F* (sai số < 1e-10)")
        else:
            err("Điểm bất động F* không thỏa phương trình cân bằng")

        if stab.get("inside_unit_circle") and stab.get("lyapunov_monotone_decreasing"):
            ok(
                f"Phân loại ổn định: {stab.get('classification')} "
                f"(|f'(F*)| = {stab.get('jacobian_spectral_radius'):.6f} < 1, Lyapunov giảm nghiêm ngặt)"
            )
        else:
            err("Phân tích ổn định hoặc hàm Lyapunov không đạt")

        if why_not.get("has_nontrivial_fixed_point") is False:
            ok("Đã chứng minh phương trình tích lũy thô w_{n+1} = w_n + A_n x_n có trị riêng 1 (không có điểm cân bằng)")
        else:
            err("Thiếu chứng minh bác bỏ bộ tích lũy thô w_{n+1} = w_n + A_n x_n")
    else:
        err("Thiếu tệp m4_dynamics/out/recurrence_analysis.json")

    # 4. Kiểm định rolling_horizon.json
    rh_path = m4_dir / "out" / "rolling_horizon.json"
    if rh_path.exists():
        rh = json.loads(rh_path.read_text(encoding="utf-8"))
        cmp_s = rh.get("comparison_summary", {})
        if cmp_s.get("closed_loop_all_hard_ok") and cmp_s.get("open_loop_all_hard_ok"):
            ok("Vòng lặp đóng kết nối M2 solve_week giữ vững 5/5 ràng buộc cứng (H1..H5) suốt 60 kỳ")
        else:
            err("Vi phạm ràng buộc cứng M2 trong quá trình chạy rolling-horizon")

        cl_spread = int(cmp_s.get("closed_loop_cum_load_spread", 999))
        ol_spread = int(cmp_s.get("open_loop_cum_load_spread", 0))
        cl_jain = float(cmp_s.get("closed_loop_cum_load_jain", 0.0))
        if cl_spread == 0 and ol_spread >= 50 and abs(cl_jain - 1.0) < 1e-6:
            ok(
                f"Đối sánh công bằng tải tích lũy: Closed-loop spread = {cl_spread} ca (Jain = {cl_jain:.6f}) "
                f"vs Open-loop spread = {ol_spread} ca"
            )
        else:
            err(f"Độ lệch tải tích lũy không đạt kỳ vọng: CL={cl_spread}, OL={ol_spread}")
    else:
        err("Thiếu tệp m4_dynamics/out/rolling_horizon.json")

    # 5. Kiểm định simulation.json & 2 biểu đồ (Tiêu chuẩn Autograder 5 điểm)
    sim_path = m4_dir / "out" / "simulation.json"
    if sim_path.exists():
        sim = json.loads(sim_path.read_text(encoding="utf-8"))
        eq_v = sim.get("equilibrium_verification", {})
        max_err = float(eq_v.get("max_abs_err_to_F_star", 1.0))
        if eq_v.get("within_tolerance_1e_3") and max_err < 1e-3:
            ok(f"[Autograder 5.0đ] Hội tụ nghiệm mô phỏng về F*: max_i |F_{{i,N}} - F*| = {max_err:.2e} < 1e-3")
        else:
            err(f"[Autograder 5.0đ] Sai số hội tụ vượt ngưỡng 1e-3: {max_err}")

        for plot_key, plot_rel in sim.get("plots", {}).items():
            pp = ROOT / plot_rel
            if pp.exists() and pp.stat().st_size > 15_000:
                ok(f"Đã xuất biểu đồ {plot_rel} ({pp.stat().st_size // 1024} KB)")
            else:
                err(f"Thiếu hoặc hỏng biểu đồ {plot_rel}")
    else:
        err("Thiếu tệp m4_dynamics/out/simulation.json")

    # 6. Kiểm định perturbation.json & biểu đồ hồi phục
    pert_path = m4_dir / "out" / "perturbation.json"
    if pert_path.exists():
        pert_data = json.loads(pert_path.read_text(encoding="utf-8"))
        pe = pert_data.get("perturbation_experiment", {})
        mc = pert_data.get("availability_markov_chain", {})
        tau_rec = pe.get("recovery_time_periods_tol_1e_2")
        tau_bnd = pe.get("theoretical_recovery_bound_tol_1e_2")
        if (
            pe.get("all_hard_constraints_ok_during_and_after_shock")
            and tau_rec is not None
            and tau_bnd is not None
            and int(tau_rec) <= int(tau_bnd)
        ):
            ok(
                f"Phân tích nhiễu loạn nghỉ ốm: 5/5 ràng buộc cứng ĐẠT, hồi phục sau tau_rec = {tau_rec} kỳ "
                f"(<= cận lý thuyết {tau_bnd} kỳ), spread cuối = {pe.get('final_cum_load_spread')} ca"
            )
        else:
            err(f"Kiểm định nhiễu loạn chưa đạt: tau_rec={tau_rec}, tau_bnd={tau_bnd}")

        if mc.get("ergodic_irreducible_aperiodic") and mc.get("mixing_time_tv_1e_6") is not None:
            ok(
                f"Kiểm chứng chéo Xích Markov 3 trạng thái: Ergodic=True, SLEM={mc.get('SLEM_abs_lambda_2'):.4f}, "
                f"tau_mix(1e-6)={mc.get('mixing_time_tv_1e_6')} bước"
            )
        else:
            err("Kiểm chứng Xích Markov 3 trạng thái không đạt")

        p_plot = ROOT / pert_data.get("plot", "m4_dynamics/out/perturbation_recovery.png")
        if p_plot.exists() and p_plot.stat().st_size > 15_000:
            ok(f"Đã xuất biểu đồ {pert_data.get('plot')} ({p_plot.stat().st_size // 1024} KB)")
        else:
            err("Thiếu biểu đồ m4_dynamics/out/perturbation_recovery.png")
    else:
        err("Thiếu tệp m4_dynamics/out/perturbation.json")

    print("-" * 74)
    print(f"TỔNG KẾT MODULE 4: {passed} ĐẠT · {warned} CẢNH BÁO · {failed} HỎNG")
    print("=" * 74)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

