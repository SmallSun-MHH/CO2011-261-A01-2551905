"""Ứng dụng Web Tương tác Module 5 (Streamlit) — Bài toán Phân công Giám thị (IAP).

Tác giả Chính (M5 Lead): Trần Anh Khôi (2551905)
Nhóm: CO2011-261-A01-2551905 · Seed chuẩn: 43003334 · Trọng số mềm: [0.71, 1.62, 1.33]

Chạy ứng dụng:
    streamlit run app/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.views.dynamics import render_dynamics_tab
from app.views.plan import render_plan_tab


def _load_json_safe(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {}


def _render_temporal_fallback(repo_root: Path) -> None:
    """Trình hiển thị dự phòng (fallback) cho Tab 2 (M3 Automata) khi chờ Trần Tuấn Kiệt (2551907)
    nộp tệp `app/views/temporal.py` (Task 24). Khi `app/views/temporal.py` có mặt, `app.py` sẽ
    tự động chuyển sang gọi `render_temporal_tab(repo_root)` của Kiệt."""
    st.subheader("2. Kiểm tra Hợp lệ Chuỗi Ca Trực bằng Otomat Hữu hạn (M3 DFA & AddAutomaton)")
    st.caption(
        "Chế độ hiển thị tích hợp sẵn đọc trực tiếp từ `m3_automata/out/` (tự động nhường quyền cho "
        "`app/views/temporal.py` — Task 24 của Trần Tuấn Kiệt 2551907 khi tệp được thêm)."
    )

    m3_out = repo_root / "m3_automata" / "out"
    prod_report = _load_json_safe(m3_out / "product_report.json")
    reg_ilp = _load_json_safe(m3_out / "regular_ilp.json")
    calib_m3 = _load_json_safe(repo_root / "data" / "processed" / "m3_calibration.json")
    real_strings_data = _load_json_safe(repo_root / "data" / "processed" / "m3_real_strings.json")

    st_info = prod_report.get("so_trang_thai", {})
    kc_info = prod_report.get("kiem_chung", {})
    mn_info = kc_info.get("myhill_nerode", {})
    ts_m3 = calib_m3.get("tham_so", {"k": 4, "c": 5})
    ct_info = reg_ilp.get("chan_troi", {})
    lt_info = reg_ilp.get("lich_that", {})
    ilp_info = reg_ilp.get("lich_ilp", {})

    # Tuần 12: thiếu kết quả thật thì báo lỗi, không hiển thị số mặc định viết tay.
    thieu = [t for t, d in (("m3_automata/out/product_report.json", prod_report),
                            ("m3_automata/out/regular_ilp.json", reg_ilp),
                            ("data/processed/m3_calibration.json", calib_m3),
                            ("data/processed/m3_real_strings.json", real_strings_data)) if not d]
    if thieu:
        st.error("Thiếu kết quả M3: " + ", ".join(f"`{t}`" for t in thieu)
                 + ". Chạy `python run_all.py --stage m3` rồi tải lại trang.")
        return

    n_min = int(st_info.get("toi_thieu", 155))
    n_reach = int(st_info.get("tich_dat_toi", 3108))
    n_theory = int(st_info.get("tich_ly_thuyet", 8352))
    n_pairs = int(mn_info.get("so_cap_phan_biet_duoc", 11935))
    max_z = int(mn_info.get("do_dai_hau_to_max", 10))
    n_inv_m3 = int(ct_info.get("so_giam_thi", 73))
    n_days_m3 = int(ct_info.get("so_ngay", 27))
    real_pass = int(lt_info.get("thoa_ca_4", kc_info.get("giam_thi_that_thoa_ca_4", 42)))

    # Hàng KPI M3 lấy động từ product_report.json & regular_ilp.json
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bảng chữ cái Σ", "{M, A, N, -}", "Sáng · Chiều · Đêm · Nghỉ")
    c2.metric(
        "DFA tích tối thiểu (3.2)",
        f"{n_min} trạng thái",
        f"{n_theory:,} → {n_reach:,} → {n_min} · {n_pairs:,} cặp Myhill–Nerode (|z|≤{max_z})",
    )
    c3.metric(
        f"Lịch thật ({n_inv_m3} × {n_days_m3} ngày)",
        f"{real_pass}/{n_inv_m3} thỏa cả 4 luật",
        f"ILP + AddAutomaton: {n_inv_m3}/{n_inv_m3} thỏa (0 vi phạm)",
    )
    c4.metric(
        "Tối ưu ILP + DFA (3.3)",
        f"t* = {reg_ilp.get('pha1', {}).get('t_sao', 7)} · L1 = {reg_ilp.get('pha2', {}).get('lech_L1', 34)}",
        f"Lịch thật: t = {lt_info.get('chi_so', {}).get('tai_lon_nhat', 9)} · L1 = {lt_info.get('chi_so', {}).get('lech_L1_quanh_q', 86)}",
    )

    st.markdown("---")
    col_left, col_right = st.columns([1.25, 1])

    with col_left:
        st.markdown("#### 🔎 Trình Kiểm tra Chuỗi Lịch Trực Tương tác (`w ∈ {M, A, N, -}*`)")
        default_w = "MM-MM-M-NM"
        user_w = st.text_input(
            "Nhập chuỗi lịch trực theo ngày (M=Sáng, A=Chiều, N=Đêm, -=Nghỉ):",
            value=default_w,
        ).strip().upper()

        from m3_automata.product_minimize import chay, doc_dfa

        k_val = ts_m3.get("k", 4)
        c_val = ts_m3.get("c", 5)
        dfa_min = doc_dfa(repo_root / "m3_automata" / "dfa_product_min.json")
        rule_dfas = {
            "R1 (Không quá m=2 ngày làm liên tiếp)": doc_dfa(repo_root / "m3_automata" / "dfa_r1.json"),
            "R2 (Làm ca Đêm N thì hôm sau phải nghỉ -)": doc_dfa(repo_root / "m3_automata" / "dfa_r2.json"),
            f"R3 (Tối đa k={k_val} ca trong mọi cửa sổ 7 ngày)": doc_dfa(repo_root / "m3_automata" / "dfa_r3.json"),
            f"R4 (|#M − #A| ≤ c={c_val} tại mọi tiền tố)": doc_dfa(repo_root / "m3_automata" / "dfa_r4.json"),
        }
        invalid_chars = [ch for ch in user_w if ch not in {"M", "A", "N", "-"}]
        if invalid_chars:
            st.error(f"Chuỗi chứa ký tự ngoài bảng chữ cái Σ={{M, A, N, -}}: `{invalid_chars}`")
        else:
            accepted = chay(dfa_min, user_w)
            rule_checks = {r_name: chay(r_dfa, user_w) for r_name, r_dfa in rule_dfas.items()}
            if accepted:
                st.success(f"**KẾT QUẢ DFA TỐI THIỂU ({n_min} trạng thái): ACCEPT (Hợp lệ)** — Chuỗi độ dài `{len(user_w)}` ngày thỏa cả 4 luật R1–R4.")
            else:
                failed_rules = [k for k, v in rule_checks.items() if not v]
                st.error(
                    f"**KẾT QUẢ DFA TỐI THIỂU ({n_min} trạng thái): REJECT (Vi phạm)** — Vi phạm tại: `{', '.join(failed_rules)}`"
                )
            trace_rows = []
            q_curr = dfa_min["start"]
            acc_set = set(dfa_min["accepting"])
            for idx, ch in enumerate(user_w):
                q_next = dfa_min["transitions"][q_curr][ch]
                in_acc = q_next in acc_set
                trace_rows.append({
                    "Ngày t": idx + 1,
                    "Ký hiệu ca": ch,
                    "Trạng thái trước": q_curr,
                    "Trạng thái sau δ(q, σ)": q_next,
                    "Trạng thái hợp lệ": "ACCEPT" if in_acc else "REJECT (Trap)",
                })
                q_curr = q_next
            if trace_rows:
                st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)

        # Bảng quét chuỗi thật từ m3_real_strings.json
        real_strings = real_strings_data.get("strings", {})
        if real_strings:
            st.markdown(f"#### 📋 Kiểm tra {len(real_strings)} Chuỗi Lịch Thực Tế ({n_days_m3} ngày/người)")
            scan_rows = []
            for cb_id, seq in sorted(real_strings.items()):
                r1_ok = chay(rule_dfas["R1 (Không quá m=2 ngày làm liên tiếp)"], seq)
                r2_ok = chay(rule_dfas["R2 (Làm ca Đêm N thì hôm sau phải nghỉ -)"], seq)
                r3_ok = chay(rule_dfas[f"R3 (Tối đa k={k_val} ca trong mọi cửa sổ 7 ngày)"], seq)
                r4_ok = chay(rule_dfas[f"R4 (|#M − #A| ≤ c={c_val} tại mọi tiền tố)"], seq)
                scan_rows.append({
                    "Giám thị": cb_id,
                    "Chuỗi 27 ngày": seq,
                    "R1": "✓" if r1_ok else "✗",
                    "R2": "✓" if r2_ok else "✗",
                    "R3": "✓" if r3_ok else "✗",
                    "R4": "✓" if r4_ok else "✗",
                    "DFA tích": "ACCEPT" if (r1_ok and r2_ok and r3_ok and r4_ok) else "REJECT",
                })
            st.dataframe(pd.DataFrame(scan_rows), use_container_width=True, hide_index=True, height=260)

    with col_right:
        st.markdown("#### 📐 Bốn Luật Hợp thức Thời gian & Nhân chứng Cần thiết (3.1–3.2)")
        tung_dfa = st_info.get("tung_dfa", {"r1": 4, "r2": 3, "r3": 58, "r4": 12})
        luat_thua = prod_report.get("luat_thua", {})
        df_rules = pd.DataFrame([
            {
                "Luật": "R1",
                "Nội dung": "Không quá m = 2 ngày làm liên tiếp",
                "Số trạng thái": tung_dfa.get("r1", 4),
                "Chuỗi chỉ luật này chặn": luat_thua.get("r1", {}).get("chuoi_chi_luat_nay_cam", "MMM"),
            },
            {
                "Luật": "R2",
                "Nội dung": "Làm ca Đêm N thì hôm sau phải nghỉ (-)",
                "Số trạng thái": tung_dfa.get("r2", 3),
                "Chuỗi chỉ luật này chặn": luat_thua.get("r2", {}).get("chuoi_chi_luat_nay_cam", "NM"),
            },
            {
                "Luật": "R3",
                "Nội dung": f"Tối đa k = {k_val} ca trong mọi cửa sổ 7 ngày",
                "Số trạng thái": tung_dfa.get("r3", 58),
                "Chuỗi chỉ luật này chặn": luat_thua.get("r3", {}).get("chuoi_chi_luat_nay_cam", "MM-MM-M"),
            },
            {
                "Luật": "R4",
                "Nội dung": f"|#M − #A| ≤ c = {c_val} tại mọi tiền tố",
                "Số trạng thái": tung_dfa.get("r4", 12),
                "Chuỗi chỉ luật này chặn": luat_thua.get("r4", {}).get("chuoi_chi_luat_nay_cam", "MM-MM--MM"),
            },
        ])
        st.dataframe(df_rules, use_container_width=True, hide_index=True)

        st.markdown("#### 📊 Đối sánh Lịch thật vs ILP + `AddAutomaton` (3.3)")
        lt_vp = lt_info.get("vi_pham", {})
        ilp_vp = ilp_info.get("vi_pham", {})
        lt_cs = lt_info.get("chi_so", {})
        ilp_cs = ilp_info.get("chi_so", {})
        df_m3_cmp = pd.DataFrame([
            {"Chỉ số": "Vi phạm R1 / R2 / R3 / R4", "Lịch thật": f"{lt_vp.get('R1',28)} / {lt_vp.get('R2',4)} / {lt_vp.get('R3',3)} / {lt_vp.get('R4',2)}", "ILP + DFA": f"{ilp_vp.get('R1',0)} / {ilp_vp.get('R2',0)} / {ilp_vp.get('R3',0)} / {ilp_vp.get('R4',0)}"},
            {"Chỉ số": "Giám thị thỏa cả 4 luật", "Lịch thật": f"{real_pass} / {n_inv_m3}", "ILP + DFA": f"{n_inv_m3} / {n_inv_m3}"},
            {"Chỉ số": "Tải lớn nhất (ngày làm)", "Lịch thật": str(lt_cs.get("tai_lon_nhat", 9)), "ILP + DFA": str(ilp_cs.get("tai_lon_nhat", 7))},
            {"Chỉ số": "Khoảng tải (max − min)", "Lịch thật": str(lt_cs.get("khoang_tai", 7)), "ILP + DFA": str(ilp_cs.get("khoang_tai", 1))},
            {"Chỉ số": "Độ lệch L1 quanh q = 6", "Lịch thật": str(lt_cs.get("lech_L1_quanh_q", 86)), "ILP + DFA": str(ilp_cs.get("lech_L1_quanh_q", 34))},
        ])
        st.dataframe(df_m3_cmp, use_container_width=True, hide_index=True)

        if mn_info:
            st.info(
                f"**Chứng minh Myhill–Nerode (3.2):** Toàn bộ `{mn_info.get('so_cap_phan_biet_duoc', 11935):,}/"
                f"{mn_info.get('tong_cap_trang_thai', 11935):,}` cặp trạng thái của DFA tối thiểu "
                f"đều có hậu tố phân biệt ngắn nhất độ dài ≤ `{max_z}` (`{mn_info.get('so_nhan_chung_sai', 0)}` sai). "
                f"Khớp vị từ độc lập trên `{kc_info.get('so_chuoi_vet_can', 87381):,}` chuỗi dài ≤ 8 + `{kc_info.get('so_chuoi_that', 73)}` chuỗi thật."
            )


def main() -> None:
    st.set_page_config(
        page_title="IAP — Hệ thống Phân công Giám thị (CO2011)",
        page_icon="📅",
        layout="wide",
    )

    m2_sol = _load_json_safe(ROOT / "m2_ilp" / "out" / "solution.json")
    m3_prod = _load_json_safe(ROOT / "m3_automata" / "out" / "product_report.json")
    m4_sim = _load_json_safe(ROOT / "m4_dynamics" / "out" / "simulation.json")

    m1_core = _load_json_safe(ROOT / "m1_logic" / "out" / "unsat_core.json")

    # ---- Sidebar thông tin dự án & trạng thái 5 Module ----
    with st.sidebar:
        st.title("🎓 CO2011 — IAP")
        st.markdown(
            "**Đề tài:** Bài toán Phân công Giám thị (Invigilator Assignment Problem)\n\n"
            "- **Mã nhóm:** `CO2011-261-A01-2551905`\n"
            "- **Seed định danh:** `43003334`\n"
            "- **Trọng số mềm:**\n"
            "  - `w_loc = 0.71` (Ưu tiên cơ sở)\n"
            "  - `w_load = 1.62` (Ngưỡng tải mềm)\n"
            "  - `w_fair = 1.33` (Công bằng L1)"
        )
        st.markdown("---")
        st.markdown("### ✅ Trạng thái Pipeline M1–M5")
        # Tuần 12: trạng thái suy từ file kết quả có thật, không ghi cứng "ĐẠT".
        if m1_core:
            st.success("M1 Logic (SAT & MUS): có kết quả `m1_logic/out/unsat_core.json`")
        else:
            st.warning("M1: chưa có kết quả — chạy `run_all.py --stage m1`")
        if m2_sol:
            st.success(f"M2 ILP (CP-SAT 2 pha): t*={m2_sol.get('t_star')}, "
                       f"Obj={m2_sol.get('objective')}")
        else:
            st.warning("M2: chưa có `m2_ilp/out/solution.json`")
        if m3_prod:
            st.success(f"M3 Automata: DFA tối thiểu "
                       f"{m3_prod.get('so_trang_thai', {}).get('toi_thieu')} trạng thái")
        else:
            st.warning("M3: chưa có `m3_automata/out/product_report.json`")
        eq_m4 = m4_sim.get("equilibrium_verification", {})
        if eq_m4:
            st.success(f"M4 Dynamics: max|F−F*| = {float(eq_m4.get('max_abs_err_to_F_star', float('nan'))):.2e} "
                       f"(F* = l̄ do chuẩn hoá; a là quy ước — xem identify.py)")
        else:
            st.warning("M4: chưa có `m4_dynamics/out/simulation.json`")
        st.info("M5 Web App (Streamlit): đang chạy")

    st.title("📅 Hệ thống Tối ưu hóa & Điều khiển Phân công Giám thị (M1–M5)")
    st.markdown(
        "Tích hợp xuyên suốt **Logic Mệnh đề & MUS (M1)** $\\rightarrow$ **Quy hoạch Nguyên Tối ưu Từ điển 2 Pha (M2)** "
        "$\\rightarrow$ **Otomat Hữu hạn & `AddAutomaton` (M3)** $\\rightarrow$ **Hệ Động lực Mệt mỏi Vòng lặp đóng (M4)**."
    )

    tab1, tab2, tab3 = st.tabs([
        "📋 Tab 1: Phân công & Xung đột (M1 + M2)",
        "⏱️ Tab 2: Chuỗi ca & Otomat (M3)",
        "📈 Tab 3: Động lực Mệt mỏi & Công bằng (M4)",
    ])

    with tab1:
        render_plan_tab(ROOT, seed_int=43003334)

    with tab2:
        try:
            from app.views.temporal import render_temporal_tab  # type: ignore
            render_temporal_tab(ROOT)
        except ImportError:
            _render_temporal_fallback(ROOT)

    with tab3:
        render_dynamics_tab(ROOT)


if __name__ == "__main__":
    main()
