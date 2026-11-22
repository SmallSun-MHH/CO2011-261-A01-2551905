"""Tab 1 (M5) — Lịch Phân Công & Chẩn Đoán Xung Đột (M1 SAT/MUS + M2 CP-SAT vs Baseline).

Tác giả Chính: Trần Bùi Bảo Long (2551909) · Phối hợp: Trần Anh Khôi (2551905)
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from m2_ilp.baseline import chi_so, trich_baseline
from m2_ilp.model import build_params, solve_week
from m2_ilp.preprocess import run as run_preprocess


def _load_json_safe(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {}


def render_plan_tab(repo_root: Path, seed_int: int = 43003334) -> None:
    """Hiển thị Tab 1: Kết quả M1 (SAT/UNSAT/MUS) và M2 (CP-SAT 2 pha vs Lịch gốc)."""
    st.subheader("1. Tổng quan Khả thi Logic (M1) & Tối ưu hóa Lịch trực (M2)")

    inst_path = repo_root / "data" / "instance_slice.json"
    m1_mus_path = repo_root / "m1_logic" / "out" / "unsat_core.json"
    m2_sol_path = repo_root / "m2_ilp" / "out" / "solution.json"

    instance = _load_json_safe(inst_path)
    m1_mus = _load_json_safe(m1_mus_path)
    m2_sol = _load_json_safe(m2_sol_path)

    if not instance:
        st.error("Chưa tìm thấy `data/instance_slice.json`. Hãy chạy `python run_all.py --seed 43003334` trước.")
        return

    m2_data = run_preprocess(instance, seed_int=seed_int)
    base_params = build_params(instance, m2_data)
    if not m2_sol:
        m2_sol = solve_week(base_params, seed_int=seed_int, verbose=False)

    base_metrics = chi_so(base_params, trich_baseline(instance), seed_int)

    # ---- Hàng KPI tổng hợp M1 & M2 ----
    c1, c2, c3, c4 = st.columns(4)
    sat_ok = m1_mus.get("lat_nguyen_ban_sat", True)
    mus_list = m1_mus.get("unsat_core", [])
    n_star = m1_mus.get("phep_siet", {}).get("nguong_N_sao", 14)
    n_busy = m1_mus.get("busy_suy_ra_tu_baseline", len(instance.get("busy", [])))
    c1.metric(
        "Trạng thái M1 (SAT & MUS)",
        f"{'SAT' if sat_ok else 'UNSAT'} (5/5 Cứng)",
        f"Busy={n_busy} cặp · MUS={len(mus_list)} nhóm (N*={n_star}/18)",
    )
    base_obj = float(base_metrics.get("phat_co_trong_so", 7.74))
    sol_obj = float(m2_sol.get("objective", 3.99))
    c2.metric(
        "Mục tiêu Pha 2 (CP-SAT)",
        f"{sol_obj:.2f}",
        f"Giảm {base_obj - sol_obj:.2f} so với Lịch gốc ({base_obj:.2f})",
    )
    f_info = m2_sol.get("fairness", {})
    c3.metric(
        "Chuẩn cực đại t* (Min-Max)",
        f"{m2_sol.get('t_star', 2)} ca/người",
        f"Khoảng tải: {f_info.get('tai_nho_nhat', 1)}–{f_info.get('tai_lon_nhat', 2)} ca (L1={f_info.get('lech_L1_quanh_q', 3)})",
    )
    s_info = m2_sol.get("soft", {})
    c4.metric(
        "Vi phạm Ràng buộc Mềm",
        f"S1={s_info.get('vi_pham_S1_loc', 0)} · S2={s_info.get('vi_pham_S2_load', 0)}",
        "w_loc=0.71, w_load=1.62, w_fair=1.33",
    )

    st.markdown("---")

    # ---- Khu vực thử nghiệm kịch bản tương tác trực tiếp (What-if Scenario) ----
    st.markdown("### 🎛️ Mô phỏng Kịch bản Tương tác Trực tiếp (What-If Scenario Solver)")
    col_cfg1, col_cfg2 = st.columns([2, 1])
    with col_cfg1:
        unavailable_staff = st.multiselect(
            "Chọn giám thị vắng mặt đột xuất (khóa Busy(i, j) = True trên mọi ca trong ngày):",
            options=base_params["I"],
            default=[],
            help="Khung 13g00 cần tổng cộng 15 giám thị ở 2 ca trùng giờ (CS1: 1, CS2: 14). Khi khóa từ 4 giám thị trở lên (chỉ còn <= 14 người rảnh), bài toán lập tức chuyển sang INFEASIBLE.",
        )
    with col_cfg2:
        custom_max_load = st.slider(
            "Ngưỡng tải mềm MaxLoad (ca/ngày):",
            min_value=1,
            max_value=3,
            value=2,
            step=1,
            help="Ngưỡng mềm S2 phạt khi số ca của một giám thị vượt quá MaxLoad.",
        )

    sim_params = copy.deepcopy(base_params)
    for i_id in sim_params["I"]:
        sim_params["max_load"][i_id] = int(custom_max_load)
    for s_id in unavailable_staff:
        for j_id in sim_params["J"]:
            sim_params["busy"][f"{s_id}|{j_id}"] = True

    live_sol = solve_week(sim_params, seed_int=seed_int, verbose=False)

    if not live_sol.get("feasible", False):
        st.error(
            f"**Kịch bản VÔ NGHIỆM ({live_sol.get('status')}):** "
            f"Khi {len(unavailable_staff)} giám thị vắng mặt ({', '.join(unavailable_staff)}), "
            f"5 ràng buộc cứng (H1–H5) mâu thuẫn! Hai ca trùng giờ lúc 13g00 "
            f"(`20260528_3@Cơ sở 1` cần 1 và `20260528_3@Cơ sở 2` cần 14) đòi hỏi ít nhất **15 giám thị khác nhau**, "
            f"trong khi số giám thị khả dụng còn lại ({18 - len(unavailable_staff)} người) hoặc bị kẹt lịch bận H2 không đáp ứng đủ."
        )
    else:
        if unavailable_staff or custom_max_load != 2:
            st.success(
                f"**Kịch bản KHẢ THI ({live_sol['status']}):** "
                f"Đã giải lại trực tiếp trong `{live_sol['runtime_s']*1000:.1f} ms` · "
                f"Min-max $t^* = {live_sol['t_star']}$ ca/người · "
                f"Objective = `{live_sol['objective']:.2f}` · "
                f"Tự kiểm 5/5 ràng buộc cứng: **{'ĐẠT' if live_sol['kiem_rang_buoc_cung']['tat_ca_dat'] else 'HỎNG'}**."
            )

        # ---- Hiển thị Ma trận phân công 18 x 6 ----
        st.markdown("#### 📋 Bảng Phân công Chi tiết Giám thị × Ca thi (`x[i, j] ∈ {0, 1}`)")
        assigned_set = {(i, j) for i, j in live_sol["assignment"]}
        rows = []
        for i_id in sim_params["I"]:
            pref_c = sim_params["preferences"].get(i_id, {}).get("prefer_campus")
            pref_label = pref_c if pref_c else "Linh hoạt (cả 2 CS)"
            row_data: dict[str, Any] = {
                "Giám thị": i_id,
                "Nguyện vọng": pref_label,
                "Trạng thái": "Nghỉ đột xuất" if i_id in unavailable_staff else "Sẵn sàng",
            }
            for j_id in sim_params["J"]:
                campus_j = sim_params["campus"].get(j_id, "")
                is_busy = sim_params["busy"].get(f"{i_id}|{j_id}", False)
                if (i_id, j_id) in assigned_set:
                    match_flag = "✓" if (pref_c is None or campus_j == pref_c) else "✓ (khác CS)"
                    row_data[f"{j_id} ({campus_j})"] = match_flag
                elif is_busy:
                    row_data[f"{j_id} ({campus_j})"] = "Bận (H2)"
                else:
                    row_data[f"{j_id} ({campus_j})"] = "—"
            row_data["Tổng tải (ca)"] = int(live_sol["load"].get(i_id, 0))
            rows.append(row_data)

        df_assign = pd.DataFrame(rows)
        st.dataframe(df_assign, use_container_width=True, hide_index=True)

        # ---- Đối sánh trực quan CP-SAT vs Lịch gốc (Baseline) ----
        st.markdown("#### 📊 Đối sánh Phân phối Tải: CP-SAT 2 Pha (Lexicographic) vs Lịch gốc (Baseline)")
        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            df_load_cmp = pd.DataFrame({
                "Giám thị": sim_params["I"],
                "CP-SAT 2 pha (M2)": [int(live_sol["load"].get(i, 0)) for i in sim_params["I"]],
                "Lịch gốc (Baseline)": [int(base_metrics["tai"].get(i, 0)) for i in sim_params["I"]],
            }).set_index("Giám thị")
            st.bar_chart(df_load_cmp)
        with col_b2:
            df_summary_cmp = pd.DataFrame([
                {
                    "Chỉ số": "Tải lớn nhất (max load)",
                    "CP-SAT (M2)": live_sol["fairness"]["tai_lon_nhat"],
                    "Lịch gốc (Baseline)": base_metrics["tai_lon_nhat"],
                },
                {
                    "Chỉ số": "Tải nhỏ nhất (min load)",
                    "CP-SAT (M2)": live_sol["fairness"]["tai_nho_nhat"],
                    "Lịch gốc (Baseline)": base_metrics["tai_nho_nhat"],
                },
                {
                    "Chỉ số": "Độ lệch L1 quanh q=1",
                    "CP-SAT (M2)": live_sol["fairness"]["lech_L1_quanh_q"],
                    "Lịch gốc (Baseline)": base_metrics["lech_L1_quanh_q"],
                },
                {
                    "Chỉ số": "Vi phạm cơ sở S1",
                    "CP-SAT (M2)": live_sol["soft"]["vi_pham_S1_loc"],
                    "Lịch gốc (Baseline)": base_metrics["vi_pham_S1_loc"],
                },
                {
                    "Chỉ số": "Vi phạm vượt tải S2",
                    "CP-SAT (M2)": live_sol["soft"]["vi_pham_S2_load"],
                    "Lịch gốc (Baseline)": base_metrics["vi_pham_S2_load"],
                },
                {
                    "Chỉ số": "Tổng hàm mục tiêu Pha 2",
                    "CP-SAT (M2)": live_sol["objective"],
                    "Lịch gốc (Baseline)": base_metrics["phat_co_trong_so"],
                },
            ])
            st.dataframe(df_summary_cmp, use_container_width=True, hide_index=True)

    # ---- Chẩn đoán Lõi Mâu thuẫn Tối tiểu (M1 MUS) ----
    with st.expander("🔍 Chẩn đoán Lõi Mâu thuẫn Tối tiểu (M1 MUS — Minimal Unsatisfiable Subset)", expanded=False):
        if m1_mus:
            siet = m1_mus.get("phep_siet", {})
            mus_core = m1_mus.get("unsat_core", [])
            ho_rb = m1_mus.get("ho_rang_buoc", {})
            kc_tt = m1_mus.get("kiem_chung_toi_thieu", [])
            dat_tt = all(item.get("dat", False) for item in kc_tt) if kc_tt else False
            st.markdown(
                f"- **Phép siết bất khả thỏa (D3):** thu hẹp tập giám thị xuống ngưỡng `N* = {siet.get('nguong_N_sao', 14)}/{siet.get('tong_giam_thi', 18)}` người.\n"
                f"- **Kích thước lõi MUS:** `{len(mus_core)}` nhóm ràng buộc tối tiểu "
                f"(họ: `{', '.join(sorted(set(ho_rb.values())))}`).\n"
                f"- **Chứng minh tính tối thiểu (Deletion-based MUS):** `{'ĐẠT' if dat_tt else 'CHƯA ĐẠT'}` "
                f"({len(kc_tt)} phép thử — bỏ bất kỳ mệnh đề nào trong lõi đều trở lại `SAT`)."
            )
            if mus_core:
                df_mus = pd.DataFrame([
                    {"Nhóm ràng buộc trong MUS": g, "Họ ràng buộc": ho_rb.get(g, "—")}
                    for g in mus_core
                ])
                st.dataframe(df_mus, use_container_width=True, hide_index=True)
            if kc_tt:
                st.caption("Kết quả kiểm chứng xóa từng phần tử khỏi MUS:")
                st.dataframe(pd.DataFrame(kc_tt), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu `m1_logic/out/unsat_core.json`.")
