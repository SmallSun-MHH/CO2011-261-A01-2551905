# Module 5 — Ứng dụng Web Tương tác Streamlit (`app/`)

Ứng dụng tích hợp trực tiếp 4 module lõi của dự án **CO2011 — Invigilator Assignment Problem (IAP)** (`CO2011-261-A01-2551905`, seed `43003334`) trên cùng một giao diện trực quan.

## 1. Cách khởi chạy

1. Tạo trước các tệp đầu ra tiền tính toán (nếu chưa chạy):
   ```powershell
   .\.venv\Scripts\python.exe run_all.py --seed 43003334
   ```
2. Khởi chạy ứng dụng Streamlit:
   ```powershell
   .\.venv\Scripts\streamlit.exe run app/app.py
   ```

## 2. Kiến trúc 3 Tab tương tác

| Tab | File | Nội dung & Khả năng tương tác |
|---|---|---|
| **Tab 1: Phân công & Xung đột (M1 + M2)** | `app/views/plan.py` | Hiển thị KPI SAT/MUS (M1) và CP-SAT từ điển 2 pha vs Lịch gốc Baseline (M2: $t^* = 2$, $L_1 = 3$, mục tiêu $3.99$ vs $7.74$); bộ giải What-If trực tiếp cho phép khóa giám thị nghỉ đột xuất hoặc đổi `MaxLoad` và gọi `solve_week` trong ~25 ms; bảng chẩn đoán MUS tối thiểu từ `m1_logic/out/unsat_core.json`. |
| **Tab 2: Chuỗi ca & Otomat (M3)** | `app/views/temporal.py` *(Task 24)* / fallback tích hợp trong `app/app.py` | Hiển thị KPI động từ `m3_automata/out/product_report.json` và `regular_ilp.json` (155 trạng thái tối thiểu, 11.935/11.935 cặp Myhill–Nerode $|z|\le 10$, 73 giám thị × 27 ngày, ILP+`AddAutomaton` đạt $t^* = 7, L_1 = 34$, 0 vi phạm); trình kiểm tra vết chuỗi $w \in \{M, A, N, -\}^*$ tương tác trên DFA 155 trạng thái và 4 DFA luật R1–R4; bảng quét 73 chuỗi thật. |
| **Tab 3: Động lực Mệt mỏi & Công bằng (M4)** | `app/views/dynamics.py` | Hiển thị KPI $F^* = 7/6$, sai số hội tụ $< 10^{-5}$, 3 biểu đồ báo cáo (`fatigue_trajectories.png`, `fairness_convergence.png`, `perturbation_recovery.png`), bảng phân tích độ nhạy $\gamma$, ma trận Xích Markov 3 trạng thái và bộ chạy mô phỏng Rolling-Horizon trực tiếp theo thanh trượt $(\gamma, N)$. |

## 3. Hợp đồng tích hợp Task 24 (`app/views/temporal.py`)

`app/app.py` tự động kiểm tra và gọi `render_temporal_tab(repo_root: Path) -> None` từ `app/views/temporal.py` ngay khi tệp được bổ sung; nếu chưa có, ứng dụng sử dụng hàm dự phòng `_render_temporal_fallback(repo_root)` đọc trực tiếp dữ liệu thật từ `m3_automata/out/`.
