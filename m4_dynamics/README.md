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
- **Hệ số nhớ mệt mỏi tự nhiên (QUY ƯỚC, không phải ước lượng, và nằm ngoài vùng tin cậy 95% của dữ liệu — xem §6):** $a = \frac{1499}{1971} \approx 0.760528 \in (0, 1)$, tức tỷ lệ ngày nghỉ.
- **Tải trung bình & Nghỉ trung bình mỗi kỳ:** $\bar{\ell} = \frac{21}{18} = \frac{7}{6} \approx 1.166667$ ca/kỳ; $\bar{\rho} = 2 - \frac{7}{6} = \frac{5}{6} \approx 0.833333$ ca nghỉ/kỳ.
- **Hệ số phục hồi & tích lũy mệt mỏi:** $r = (1 - a)\frac{\bar{\ell}}{L_{\max}} \approx 0.139692$; $b = (1 - a) + r\frac{\bar{\rho}}{\bar{\ell}} \approx 0.339252$.
- **Điểm bất động giải tích duy nhất:**
  $$F^* = \frac{b\bar{\ell} - r\bar{\rho}}{1 - a} = \bar{\ell} = \frac{7}{6} \approx 1.166667$$
  Đẳng thức $F^* = \bar{\ell}$ đúng **theo cách dựng**: $b$ được giải ra từ chính ràng buộc này, nên nó đúng với mọi $(a, r)$ (xem §6). Đây là phép chuẩn hoá thang đo của $F$ (đơn vị "ca/kỳ"), không phải bằng chứng mô hình khớp dữ liệu.
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
| `m4_dynamics/identify.py` | Tuần 12 — Dữ liệu nói được gì về $(a, b, r)$: đẳng thức $F^*=\bar\ell$, hiệu ứng ngày trước (logit có hiệu ứng ngày), profile likelihood của $a$, độ nhạy thí nghiệm nhiễu loạn theo $a$ | **Nguyễn Phong Phú (`2551918`)** | Hoàn thành (`out/identify.json`, `identify_profile.png`) |
| `m4_dynamics/perturbation.py` | Task 20 — Nhiễu loạn nghỉ ốm đột xuất, thời gian hồi phục $\tau_{\text{rec}}$, độ nhạy $\gamma$ & Xích Markov | **Trần Anh Khôi (`2551905` — Lead M4 Perturbation)** | Hoàn thành (`out/perturbation.json`, `perturbation_recovery.png`) |

---

## 5. Cách chạy kiểm tra

```powershell
.\.venv\Scripts\python.exe m4_dynamics/calibrate.py
.\.venv\Scripts\python.exe m4_dynamics/recurrence.py
.\.venv\Scripts\python.exe m4_dynamics/rolling_horizon.py
.\.venv\Scripts\python.exe m4_dynamics/simulate.py
.\.venv\Scripts\python.exe m4_dynamics/perturbation.py
.\.venv\Scripts\python.exe m4_dynamics/identify.py
.\.venv\Scripts\python.exe tools/check_m4.py
```

---

## 6. Giới hạn của mô hình (rà soát tuần 12 — `m4_dynamics/identify.py`)

Phần này ghi rõ cái gì **được dữ liệu ủng hộ** và cái gì **chỉ là quy ước**, để báo cáo và slide không nói quá. Mọi con số dưới đây do `identify.py` tính lại từ `data/processed/m3_real_strings.json` (73 giám thị × 27 ngày, 472 ngày làm) và ghi trong `out/identify.json`.

1. **$F^* = \bar\ell$ là đẳng thức, không phải kết quả khớp.** Với $b = (1-a) + r\bar\rho/\bar\ell$, ta có $F^* = \bar\ell$ cho mọi $a \in (0,1)$, $r$. `identify.py` thử 8 cặp $(a, r)$ khác nhau: độ lệch lớn nhất $4\times10^{-15}$ (sai số làm tròn). "Sai số hiệu chỉnh $2.2\times10^{-16}$" trong `m4_params.json` vì vậy không đo độ khớp nào.
2. **Dữ liệu có tín hiệu "làm hôm trước → ít làm hôm nay".** Hồi quy logistic $P(\text{làm}_t) = \sigma(\alpha_t + \beta H_t(a))$ với hiệu ứng cố định theo ngày $\alpha_t$ (khử việc có ngày nhiều ca, ngày ít ca) và $H_t(a) = \sum_{s<t} a^{t-1-s}\,\text{làm}_s$: tại $a = 0$ (chỉ hôm trước), $\beta = -0.398$, $z = -2.54$, $p = 0.011$. Dấu âm phản ánh cách xếp lịch giãn ca, chưa phải đo mệt mỏi sinh học.
3. **Dữ liệu không ủng hộ $a = 0.7605$.** Profile likelihood trên lưới $a \in \{0, 0.05, \dots, 0.95\}$: MLE $a = 0$; vùng tin cậy 95% (ngưỡng $\Delta\ell = -1.92$) là $[0; 0.25] \cup \{0.95\}$ — **không liên thông** (điểm $0.95$ ở biên lưới). Tại $a = 0.7605$: $\Delta\ell = -3.11$, tức **nằm ngoài** vùng 95%, và ở đó $\beta = -0.058$ ($p = 0.59$) không còn ý nghĩa. Giá trị $a = 0.760528$ (= tỷ lệ ngày nghỉ) vì vậy là **quy ước**, không phải ước lượng; $b$, $r$ cũng không được ước lượng. Giới hạn của phép thử: logit này đo xu hướng **xếp lịch** (có hiệu ứng ngày, không có hiệu ứng riêng từng giám thị), không đo mệt mỏi sinh học — nó là bằng chứng chống lại việc gọi $a$ là "ước lượng từ dữ liệu", chưa phải một ước lượng thay thế.
4. **Kết luận nào đứng vững bất kể $a$.** Lặp lại thí nghiệm nhiễu loạn (cú sốc `CB003`, `CB005` kỳ 19–20, 60 kỳ) với $a \in \{0.3, 0.5, 0.7605, 0.9\}$:

   | $a$ | 5/5 ràng buộc cứng | vọt lố | hồi phục (1e-2) | cận lý thuyết | sai số cuối | chênh tải tích luỹ cuối |
   |---|---|---|---|---|---|---|
   | 0.30 | đạt | 0.445 | 10 kỳ | 12 | 0 | 0 |
   | 0.50 | đạt | 0.356 | 12 kỳ | 13 | 0 | 0 |
   | 0.7605 | đạt | 0.567 | 20 kỳ | 21 | 3.5e-05 | 0 |
   | 0.90 | đạt | 0.720 | **không kịp trong 60 kỳ** | 46 | 1.3e-02 | 0 |

   - **Đứng vững:** giữ 5/5 ràng buộc cứng và chênh tải tích luỹ cuối = 0 ở mọi $a$ đã thử.
   - **Phụ thuộc $a$:** thời gian hồi phục (10 → 20 kỳ, và không hồi phục kịp khi $a = 0.9$). Báo cáo phải nêu "$\tau_{\text{rec}} = 20$ kỳ" là con số **tại quy ước $a = 0.7605$**, không phải tính chất của dữ liệu.
5. **Xích Markov không kiểm chứng độc lập $a$.** $\pi_{\text{Rest}}$ ước lượng từ chính các chuỗi gần bằng tỷ lệ ngày nghỉ, mà $a$ được định nghĩa là tỷ lệ ngày nghỉ — "$\pi_{\text{Rest}} \approx a$" là hệ quả định nghĩa. Từ tuần 12 `perturbation.py` đọc $a$ từ `m4_params.json` và dừng hẳn khi thiếu dữ liệu (trước đó có ma trận đếm dựng sẵn không lấy từ dữ liệu nào làm fallback).
6. **Cái gì làm tải đều nhau — luận điểm công bằng (`fairness_ablation.py`).** Hàm `compute_feedback_lambdas()` xếp hạng theo tải (5 kỳ gần nhất, tích luỹ) **trước**, $F$ chỉ để phá hoà. So 4 luật trên cùng lát dữ liệu, cùng $F(0)$, 60 kỳ, cùng `solve_week`:

   | Luật | 5/5 cứng | trải tải tích luỹ kỳ 60 | trải lớn nhất kỳ 7–60 | Jain |
   |---|---|---|---|---|
   | OL (vòng hở, $\lambda = 0$) | đạt | 60 | 60 (tăng tuyến tính) | 0.9074 |
   | W (chỉ tải) | đạt | 0 | 1 | 1.0000 |
   | F (chỉ mệt mỏi thật $F_{\text{raw}}$) | đạt | 2 | 2 | 0.99996 |
   | W+F (luật hiện tại) | đạt | 0 | 1 | 1.0000 |

   Luật W+F chạy lại ở đây tái tạo **đúng** chuỗi tải trong `rolling_horizon.json`. Hệ quả: con số "spread = 0" của luật hiện tại không chứng minh vai trò của mệt mỏi, vì riêng W đã cho 0. Luận điểm công bằng đúng là luật F: bộ điều khiển **chỉ biết trạng thái mệt mỏi**, không giữ sổ tải, vẫn giữ bất công tải tích luỹ **bị chặn** ($\le 2$ ca suốt kỳ 7–60), trong khi vòng hở tăng tuyến tính tới 60 ca. Thêm W chỉ đưa 2 về 0. Với luật tỷ lệ đơn giản $\lambda_i = \mu F_i$ (demo `recurrence.py --ilp-demo`), độ trải mệt mỏi còn $\approx 0.63$–$0.84$ — kết quả phụ thuộc thiết kế luật điều khiển, không riêng phương trình mệt mỏi.
7. **"Hội tụ về $F^*$ < $10^{-3}$" là của mệt mỏi trung bình chu kỳ.** `rolling_horizon.py` theo dõi hai quỹ đạo: $F_{\text{eff}}$ (cập nhật bằng tải **trung bình trượt 6 kỳ**) và $F_{\text{raw}}$ (cập nhật bằng tải thật từng kỳ — đúng phương trình ở §1). `simulate.py` chấm hội tụ trên $F_{\text{eff}}$ ($2.3\times10^{-6}$). Mệt mỏi thật $F_{\text{raw}}$ **không** hội tụ về một điểm (tải là số nguyên 1 hoặc 2): nó về một quỹ đạo tuần hoàn chu kỳ 6 với biên độ $0.443$, và **trung bình mỗi chu kỳ** khớp $F^*$ tới $2.4\times10^{-6}$ (`raw_pulse_cycle_mean_max_err` trong `simulation.json`). Báo cáo phải phát biểu đúng như vậy.

`tools/check_m4.py` (mục 7) kiểm các điểm trên bằng phép thử **có thể hỏng**: không còn hằng số $a$ viết tay trong mã, Xích Markov dừng khi thiếu dữ liệu, ma trận đếm khớp phép đếm lại độc lập, demo ILP bắt buộc nhận $(a, b, r)$, `identify.json` có đủ các kết quả trên.

