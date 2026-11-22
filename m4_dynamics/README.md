# Module 4 — Hệ Động lực Mệt mỏi & Lập lịch Vòng lặp đóng (Dynamical Systems)

## 1. Lựa chọn hướng mô hình hóa (M4-A + Kiểm chứng chéo M4-B/M4-C)

Nhóm lựa chọn **Hướng M4-A (Closed-Loop Rolling-Horizon Fatigue Dynamics)** làm mô hình chính thức cho Module 4 (xem `DECISIONS.md` mục **D16, D17**), kết hợp:
- Hàm thế năng Lyapunov đa chiều $V(F^{(n)}) = \frac{1}{2}\sum_{i \in I}(F_{i,n} - F^*)^2$ để chứng minh sự co đồng thời của toàn bộ $|I| = 18$ quỹ đạo giám thị về cùng điểm cân bằng công bằng $F^*$;
- Kiểm chứng chéo Xích Markov khả dụng 3 trạng thái `{"Rest (-)", "Day (M/A)", "Night (N)"}` từ chuỗi lịch thực tế 73 giám thị × 27 ngày (`data/processed/m3_real_strings.json`) để đối chiếu xác suất nghỉ dừng $\pi_{\text{Rest}}$ với hệ số suy giảm mệt mỏi $a$.

### Vì sao phương trình tích lũy thô $w_{n+1} = w_n + A_n x_n$ KHÔNG phải là hệ động lực có điểm cân bằng?
Phương trình cộng dồn số ca trực tích lũy $w_{n+1} = w_n + \ell_n$ có ma trận Jacobi $J = \frac{\partial w_{n+1}}{\partial w_n} = I_{|I|}$ với mọi trị riêng $\mu_i = 1$ nằm ngay trên đường tròn đơn vị (suy biến trung tính). Phương trình điểm bất động $w^* = w^* + \bar{\ell}$ đòi hỏi $\bar{\ell} = 0$, mâu thuẫn với tổng nhu cầu coi thi dương $\sum_{j \in J}\text{Cap}(j) = 21 > 0$. Do đó $w_n \sim n\bar{\ell} \to +\infty$ phân kỳ tuyến tính. Hệ động lực thực sự có điểm cân bằng ổn định phải mô hình hóa trạng thái **mệt mỏi có suy giảm sinh học** $0 < a < 1$:

$$F_{i,n+1} = a F_{i,n} + b \hat{\ell}_{i,n} - r \hat{\rho}_{i,n}, \qquad \hat{\rho}_{i,n} = L_{\max} - \hat{\ell}_{i,n}$$

---

## 2. Hiệu chỉnh tham số, Điểm bất động $F^*$ và Phân tích ổn định

Từ lát dữ liệu thật (`data/instance_slice.json`, $|I|=18, |J|=6, \sum_j \text{Cap}(j)=21, L_{\max}=2$) và chuỗi lịch thực tế 73 giám thị × 27 ngày (`m3_real_strings.json`, 1.499 ngày nghỉ / 1.971 ngày-người):
- **Hệ số nhớ mệt mỏi tự nhiên:** $a = \frac{1499}{1971} \approx 0.760528 \in (0, 1)$.
- **Tải trung bình & Nghỉ trung bình mỗi kỳ:** $\bar{\ell} = \frac{21}{18} = \frac{7}{6} \approx 1.166667$ ca/kỳ; $\bar{\rho} = 2 - \frac{7}{6} = \frac{5}{6} \approx 0.833333$ ca nghỉ/kỳ.
- **Hệ số phục hồi & tích lũy mệt mỏi:** $r = (1 - a)\frac{\bar{\ell}}{L_{\max}} \approx 0.139692$; $b = (1 - a) + r\frac{\bar{\rho}}{\bar{\ell}} \approx 0.339252$.
- **Điểm bất động giải tích duy nhất:**
  $$F^* = \frac{b\bar{\ell} - r\bar{\rho}}{1 - a} = \bar{\ell} = \frac{7}{6} \approx 1.166667$$
- **Phân loại ổn định:** Đạo hàm (bán kính phổ Jacobi) tại $F^*$ là $|f'(F^*)| = a = 0.760528 < 1 \implies$ **$F^*$ là điểm bất động ổn định tiệm cận toàn cục (Asymptotically Stable / Global Contraction)**.

---

## 3. Luật phản hồi đóng $\lambda_i(F_{i,n})$ kết nối trực tiếp vào `m2_ilp/model.py`

Tại đầu mỗi kỳ $n$, vector mệt mỏi hiện tại $F^{(n)}$ và tải tích lũy $W^{(n)}$ được ánh xạ sang trọng số phạt cá nhân $\lambda_{i,n} = \phi_\gamma(F_{i,n}, W_{i,n})$ đưa trực tiếp vào tham số `lambdas` của `solve_week(params, lambdas)` trong `m2_ilp/model.py` (không sửa đổi bất kỳ ràng buộc cứng H1–H5 nào):
- **Ngưỡng dưới vượt rào cản cơ sở ($w_{\text{loc}} = 0.71$):** Trên lát cắt có 8 giám thị ưu tiên Cơ sở 2 (`near_cs2`), trong khi ca thứ 2 trong ngày luôn nằm ở Cơ sở 1 (chịu phạt $S_1 = w_{\text{loc}} = 0.71$). Để xoay vòng đều 3 suất ca kép qua tất cả 18 giám thị với chu kỳ cơ bản $W = \frac{18}{\gcd(18, 21)} = 6$ kỳ, 15 giám thị không nằm trong nhóm 3 người ít mệt mỏi nhất được gán $\lambda_{i,n} \ge 0.88 > w_{\text{loc}} = 0.71$.
- **Ngưỡng trên bảo toàn tải tối thiểu ($2w_{\text{fair}} - w_{\text{loc}} = 1.95$):** Độ trải cực đại $\max_i \lambda_{i,n} - \min_k \lambda_{k,n} \le 1.65 < 2w_{\text{fair}} - w_{\text{loc}} = 1.95$ đảm bảo không có giám thị nào bị đẩy xuống 0 ca trong các kỳ bình thường ($\ell_{i,n} \in \{1, 2\}$).

---

## 4. Cấu trúc tệp và Phân công nhiệm vụ

| Tệp | Nhiệm vụ | Thành viên phụ trách | Trạng thái |
|---|---|---|---|
| `m4_dynamics/calibrate.py` | Task 16 — Ước lượng tham số $(a, b, r)$ xuất `data/processed/m4_params.json` | **Trần Tuấn Kiệt (`2551907`)** | Hoàn thành (`commit 3dd64ad`, `data/processed/m4_params.json`) |
| `m4_dynamics/recurrence.py` | Task 17 — Phương trình sai phân, điểm bất động $F^*$, chứng minh Lyapunov & trị riêng 1 | **Nguyễn Quang Phúc (`2551920`)** & **Trần Anh Khôi (`2551905`)** | Hoàn thành (`out/recurrence_analysis.json`) |
| `m4_dynamics/rolling_horizon.py` | Task 18 — Vòng lặp đóng $N=60$ kỳ gọi `solve_week(params, lambdas)` vs Open-loop | **Trần Bùi Bảo Long (`2551909`)** & **Trần Anh Khôi (`2551905`)** | Hoàn thành (`out/rolling_horizon.json`) |
| `m4_dynamics/simulate.py` | Task 19 — Kiểm định hội tụ $|F_{i,N} - F^*| < 10^{-3}$ (Autograder 5 điểm) & xuất 2 biểu đồ | **Nguyễn Phong Phú (`2551918`)** & **Trần Anh Khôi (`2551905`)** | Hoàn thành (`out/simulation.json`, `fatigue_trajectories.png`, `fairness_convergence.png`) |
| `m4_dynamics/perturbation.py` | Task 20 — Nhiễu loạn nghỉ ốm đột xuất, thời gian hồi phục $\tau_{\text{rec}}$, độ nhạy $\gamma$ & Xích Markov | **Trần Anh Khôi (`2551905` — Lead M4 Perturbation)** | Hoàn thành (`out/perturbation.json`, `perturbation_recovery.png`) |

---

## 5. Cách chạy kiểm tra

```powershell
.\.venv\Scripts\python.exe m4_dynamics/calibrate.py
.\.venv\Scripts\python.exe m4_dynamics/recurrence.py
.\.venv\Scripts\python.exe m4_dynamics/rolling_horizon.py
.\.venv\Scripts\python.exe m4_dynamics/simulate.py
.\.venv\Scripts\python.exe m4_dynamics/perturbation.py
.\.venv\Scripts\python.exe tools/check_m4.py
```
