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

    # 7. Kiểm định tính trung thực (tuần 12). Các mục 3–6 phần lớn đúng theo cách dựng
    #    (F* = l̄ do b được giải từ chính ràng buộc đó), nên cần thêm các phép thử có thể HỎNG.
    print("  --- Kiểm định trung thực (tuần 12) ---")
    import inspect
    import io
    import tempfile
    import tokenize

    # 7a. Không còn hằng số a viết tay trong mã M4 (chỉ được đọc từ m4_params.json)
    lit = []
    for py in sorted(m4_dir.glob("*.py")):
        if py.name == "identify.py":  # dùng 0.760528 như MỘT điểm thử của đẳng thức F* = l̄
            continue
        toks = tokenize.generate_tokens(io.StringIO(py.read_text(encoding="utf-8")).readline)
        lit += [f"{py.name}:{t.start[0]}" for t in toks if t.type == tokenize.NUMBER and t.string.startswith("0.7605")]
    if lit:
        err(f"Còn hằng số a = 0.7605… viết tay trong mã (phải đọc từ m4_params.json): {', '.join(lit)}")
    else:
        ok("Không còn hằng số a viết tay trong m4_dynamics/*.py — a chỉ đến từ m4_params.json")

    # 7b. Thiếu dữ liệu thì Xích Markov phải DỪNG, không dùng số đếm dựng sẵn
    try:
        from m4_dynamics.perturbation import analyze_availability_markov_chain
        with tempfile.TemporaryDirectory() as td:
            try:
                analyze_availability_markov_chain(Path(td), a=0.5)
                err("analyze_availability_markov_chain vẫn trả kết quả khi KHÔNG có m3_real_strings.json (số liệu giả)")
            except SystemExit:
                ok("Thiếu m3_real_strings.json thì Xích Markov dừng hẳn (không còn ma trận đếm dựng sẵn)")
    except Exception as exc:
        err(f"Không kiểm được nhánh thiếu dữ liệu của Xích Markov: {exc}")

    # 7c. Số đếm chuyển trạng thái trong perturbation.json = đếm lại độc lập từ dữ liệu
    m3s = ROOT / "data" / "processed" / "m3_real_strings.json"
    if pert_path.exists() and m3s.exists():
        loai = lambda ch: 0 if ch == "-" else (1 if ch in ("M", "A") else 2)
        dem = [[0] * 3 for _ in range(3)]
        for chuoi in json.loads(m3s.read_text(encoding="utf-8")).get("strings", {}).values():
            for x, y in zip(chuoi, chuoi[1:]):
                dem[loai(x)][loai(y)] += 1
        da_ghi = json.loads(pert_path.read_text(encoding="utf-8")).get("availability_markov_chain", {}).get("transition_counts")
        if da_ghi == dem:
            ok(f"Ma trận đếm chuyển trạng thái khớp đếm lại độc lập từ dữ liệu thật ({sum(map(sum, dem))} bước chuyển)")
        else:
            err(f"Ma trận đếm trong perturbation.json {da_ghi} ≠ đếm lại từ dữ liệu {dem}")
    else:
        warn("Không đối chiếu được ma trận đếm Xích Markov (thiếu perturbation.json hoặc m3_real_strings.json)")

    # 7d. Demo ILP trong recurrence.py dùng tham số hiệu chỉnh, không có mặc định a=0.8/b=1.0
    try:
        from m4_dynamics import recurrence as _rec
        co_mac_dinh = [f"{fn}.{ten}" for fn in ("vong_kin", "quet_mu")
                       for ten, ts in inspect.signature(getattr(_rec, fn)).parameters.items()
                       if ten in ("a", "b", "r", "r_rho") and ts.default is not inspect.Parameter.empty]
        if co_mac_dinh:
            err(f"Demo ILP còn tham số mặc định khác mô hình báo cáo: {co_mac_dinh}")
        else:
            ok("vong_kin/quet_mu bắt buộc nhận (a, b, r) — main() truyền đúng giá trị từ m4_params.json")
    except Exception as exc:
        err(f"Không kiểm được chữ ký vong_kin/quet_mu: {exc}")

    # 7e. Giới hạn nhận dạng tham số đã được đo và công bố (identify.py)
    idf = m4_dir / "out" / "identify.json"
    if idf.exists():
        d = json.loads(idf.read_text(encoding="utf-8"))
        xd = d.get("xac_dinh_a", {})
        hu = d.get("hieu_ung_met_moi", {}).get("tai_mle", {})
        dt = d.get("dang_thuc_F_sao_bang_l_bar", {})
        if ("a_calibrate_trong_vung_95" in xd and xd.get("vung_tin_cay_95") and "p" in hu
                and float(dt.get("lech_lon_nhat", 1)) < 1e-9):
            ok(
                f"identify.json: F* = l̄ là đẳng thức (lệch {float(dt['lech_lon_nhat']):.1e} trên {len(dt.get('cac_thu', []))} cặp a, r); "
                f"vùng 95% của a = {xd['vung_tin_cay_95']}, a đang dùng "
                f"{'trong' if xd['a_calibrate_trong_vung_95'] else 'NGOÀI'} vùng (Δℓ = {xd['delta_loglik_a_calibrate']:+.2f}); "
                f"hiệu ứng ngày trước β = {hu.get('beta'):.3f} (p = {hu.get('p'):.3f})"
            )
        else:
            err("identify.json thiếu một trong: đẳng thức F* = l̄, vùng tin cậy 95% của a, kiểm định hiệu ứng")
    else:
        err("Thiếu m4_dynamics/out/identify.json — chạy python m4_dynamics/identify.py")

    # 7f. Luận điểm công bằng: luật nào cân bằng tải, và mệt mỏi THẬT có hội tụ về điểm không
    fa = m4_dir / "out" / "fairness_ablation.json"
    if fa.exists():
        d = json.loads(fa.read_text(encoding="utf-8"))
        L = d.get("luat", {})
        if d.get("W+F_tai_tao_rolling_horizon") is not True:
            err("fairness_ablation: luật W+F KHÔNG tái tạo được chuỗi tải của rolling_horizon.json — phép so sánh vô nghĩa")
        elif not all(L.get(k, {}).get("rang_buoc_cung_dat_moi_ky") for k in ("OL", "W", "F", "W+F")):
            err("fairness_ablation: có luật vi phạm ràng buộc cứng")
        else:
            ok(f"Ablation công bằng (60 kỳ): trải tải tích luỹ OL={L['OL']['tai_tich_luy_trai']}, "
               f"W={L['W']['tai_tich_luy_trai']}, F={L['F']['tai_tich_luy_trai']} (max {L['F']['tai_tich_luy_trai_max_tu_ky_7']} từ kỳ 7), "
               f"W+F={L['W+F']['tai_tich_luy_trai']}; W+F tái tạo đúng rolling_horizon.json")
            bd = float(L["W+F"]["F_raw_bien_do_6_ky_cuoi_max"])
            ok(f"Mệt mỏi thật F_raw về quỹ đạo chu kỳ 6 (biên độ {bd:.3f}), trung bình chu kỳ lệch F* "
               f"{float(L['W+F']['F_raw_tb_6_ky_cuoi_lech_F_sao_max']):.1e} — 'hội tụ < 1e-3' là của mệt mỏi trung bình chu kỳ")
    else:
        err("Thiếu m4_dynamics/out/fairness_ablation.json — chạy python m4_dynamics/fairness_ablation.py")

    par = ROOT / "data" / "processed" / "m4_params.json"
    if par.exists() and json.loads(par.read_text(encoding="utf-8")).get("calibration_note"):
        ok("m4_params.json ghi rõ: a là quy ước, F* = l̄ là ràng buộc chuẩn hoá (không phải bằng chứng khớp dữ liệu)")
    else:
        err("m4_params.json thiếu calibration_note — đừng trình bày F* = l̄ như kết quả khớp dữ liệu")

    print("-" * 74)
    print(f"TỔNG KẾT MODULE 4: {passed} ĐẠT · {warned} CẢNH BÁO · {failed} HỎNG")
    print("=" * 74)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

