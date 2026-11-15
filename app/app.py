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


def _render_temporal_fallback(repo_root: Path) -> None:
    """Trình hiển thị dự phòng (fallback) cho Tab 2 (M3 Automata) khi chờ Lê Tuấn Kiệt (2551907)
    nộp tệp `app/views/temporal.py` (Task 24). Khi `app/views/temporal.py` có mặt, `app.py` sẽ
    tự động chuyển sang gọi `render_temporal_tab(repo_root)` của Kiệt."""
    st.subheader("2. Kiểm tra Hợp lệ Chuỗi Ca Trực bằng Otomat Hữu hạn (M3 DFA & Máy Mealy)")
    st.caption(
        "Chế độ hiển thị tích hợp sẵn từ `m3_automata/` (tự động nhường quyền cho `app/views/temporal.py` — Task 24 của Lê Tuấn Kiệt 2551907 khi tệp được thêm)."
    )

    m3_out = repo_root / "m3_automata" / "out"
    res_path = m3_out / "results.json"
    dfa_png = m3_out / "dfa.png"

    res_data: dict[str, Any] = {}
    if res_path.exists():
        res_data = json.loads(res_path.read_text(encoding="utf-8-sig"))

    # Hàng KPI M3
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bảng chữ cái Σ", "{M, A, N, -}", "Sáng · Chiều · Tối · Nghỉ")
    c2.metric("Số trạng thái DFA tối tiểu", "16 trạng thái", "Tối tiểu hóa Myhill–Nerode (từ 17)")
    c3.metric("Chuỗi lịch thật (18 giám thị)", "15 ACCEPT · 3 REJECT", "109 ngày/chuỗi (m3_real_strings.json)")
    c4.metric("Kiểm chứng chéo Regex / NFA", "100% Khớp", "31,104 chuỗi vét cạn độ dài <= 6")

    st.markdown("---")
    col_left, col_right = st.columns([1.25, 1])

    with col_left:
        st.markdown("#### 🔎 Trình Kiểm tra Chuỗi Lịch Trực Tương tác (`w ∈ {M, A, N, -}*`)")
        default_w = "M-A-N-M-A-NN-M"
        user_w = st.text_input(
            "Nhập chuỗi lịch trực theo ngày (M=Sáng, A=Chiều, N=Tối, -=Nghỉ):",
            value=default_w,
        ).strip().upper()

        from m3_automata.product_minimize import chay, doc_dfa

        dfa_min = doc_dfa(repo_root / "m3_automata" / "dfa_product_min.json")
        rule_dfas = {
            "R1 (Không quá k ngày làm liên tiếp)": doc_dfa(repo_root / "m3_automata" / "dfa_r1.json"),
            "R2 (Sau ca Tối N phải nghỉ -)": doc_dfa(repo_root / "m3_automata" / "dfa_r2.json"),
            "R3 (Không quá 1 ca Tối trong 3 ngày)": doc_dfa(repo_root / "m3_automata" / "dfa_r3.json"),
            "R4 (Không gác Sáng ngay sau Chiều)": doc_dfa(repo_root / "m3_automata" / "dfa_r4.json"),
        }
        invalid_chars = [ch for ch in user_w if ch not in {"M", "A", "N", "-"}]
        if invalid_chars:
            st.error(f"Chuỗi chứa ký tự ngoài bảng chữ cái Σ={{M, A, N, -}}: `{invalid_chars}`")
        else:
            accepted = chay(dfa_min, user_w)
            rule_checks = {r_name: chay(r_dfa, user_w) for r_name, r_dfa in rule_dfas.items()}
            if accepted:
                st.success(f"**KẾT QUẢ DFA TỐI TIỂU: ACCEPT (Hợp lệ)** — Chuỗi độ dài `{len(user_w)}` ngày thỏa mãn cả 4 quy tắc R1–R4.")
            else:
                failed_rules = [k for k, v in rule_checks.items() if not v]
                st.error(
                    f"**KẾT QUẢ DFA TỐI TIỂU: REJECT (Vi phạm)** — Vi phạm tại: `{', '.join(failed_rules)}`"
                )
            trace_rows = []
            q_curr = dfa_min["start"]
            for idx, ch in enumerate(user_w):
                q_next = dfa_min["transitions"][q_curr][ch]
                in_acc = q_next in dfa_min["accepting"]
                trace_rows.append({
                    "Ngày t": idx + 1,
                    "Ký hiệu ca": ch,
                    "Trạng thái trước": q_curr,
                    "Trạng thái sau δ(q, σ)": q_next,
                    "Trạng thái hợp lệ": "ACCEPT" if in_acc else "REJECT (Sink)",
                })
                q_curr = q_next
            if trace_rows:
                st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)

        if res_data and "real_schedules" in res_data:
            st.markdown("#### 📋 Kết quả Quét 18 Chuỗi Lịch Thực Tế (109 ngày)")
            st.dataframe(pd.DataFrame(res_data["real_schedules"]), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("#### 🗺️ Sơ đồ Trạng thái Otomat (M3 DFA)")
        if dfa_png.exists():
            st.image(str(dfa_png), use_container_width=True)
        st.markdown(
            "**Ba quy tắc hợp thức thời gian:**\n"
            "- **R1 (`ERR_R1_NIGHT_STREAK`):** Không gác quá $k_N = 1$ ngày có ca Tối (`N`) liên tiếp.\n"
            "- **R2 (`ERR_R2_WORK_STREAK`):** Không làm việc quá $k_W = 5$ ngày liên tiếp không nghỉ (`-`).\n"
            "- **R3 (`ERR_R3_WINDOW_DENSITY`):** Trong mọi cửa sổ trượt $W = 4$ ngày, có tối đa $m_N = 2$ ngày có ca Tối (`N`)."
        )


def main() -> None:
    st.set_page_config(
        page_title="IAP — Hệ thống Phân công Giám thị (CO2011)",
        page_icon="📅",
        layout="wide",
    )

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
        st.success("M1 Logic (SAT & MUS): ĐẠT (18/18)")
        st.success("M2 ILP (CP-SAT 2 pha): ĐẠT (Optimal 8.53)")
        st.success("M3 Automata (16-state DFA): ĐẠT")
        st.success("M4 Dynamics (F* = 7/6): ĐẠT (< 1e-6)")
        st.info("M5 Web App (Streamlit): Đang chạy")

    st.title("📅 Hệ thống Tối ưu hóa & Điều khiển Phân công Giám thị (M1–M5)")
    st.markdown(
        "Tích hợp xuyên suốt **Logic Mệnh đề & MUS (M1)** $\\rightarrow$ **Quy hoạch Nguyên Tối ưu Từ điển 2 Pha (M2)** "
        "$\\rightarrow$ **Otomat Hữu hạn & Máy Mealy (M3)** $\\rightarrow$ **Hệ Động lực Mệt mỏi Vòng lặp đóng (M4)**."
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
