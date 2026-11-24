# Weekly meeting minutes

## 2026-09-08 (week-01)
- **Attendance:** Khôi, Long, Kiệt, Phú, Phúc (Đủ 5/5)
- **Decisions:** 
  - Khởi tạo repo nhóm, chạy script lấy seed (43003334).
  - Phân công sơ bộ Module 1 cho cả nhóm dựa theo IAP tracker.
- **Task split:**
  - Long: Thiết kế đặc tả Logic (spec.md)
  - Khôi: Cắt lát dữ liệu thành JSON (slice_builder.py)

## 2026-09-15 (week-02)
- **Attendance:** Khôi, Long, Kiệt, Phú, Phúc (Đủ 5/5)
- **Decisions:**
  - Chốt đặc tả của Long (5 ràng buộc cứng, 2 mềm).
  - Khôi chọn ngày 28/05/2026 làm ngày giả lập instance do đáp ứng yêu cầu kích thước (18 giám thị, 5 ca, 2 cơ sở).
  - Kiệt sẽ tiếp nhận JSON từ Khôi để code CNF encoder.
- **Task split:**
  - Kiệt: Bắt đầu code CNF encoder (STT 3).
  - Phú: Nghiên cứu sinh unsat core (STT 4).
  - Phúc: Chuyển đổi Logic sang Bất phương trình nguyên (STT 5).

---

> **Ghi ngay 2026-10-23.** Tu 15/09 den 23/10 khong co bien ban nao duoc ghi, trong
> khi nhom van lam viec deu (xem bang chung git duoi moi muc). Phan khung duoi day
> dung san theo dung tuan va dinh kem commit co that cua tuan do; **noi dung hop
> phai do thanh vien tu dien bang loi cua minh**. Khong ai duoc dien thay, va khong
> dien lui ngay: neu khong con nho tuan do ban gi thi ghi thang la khong nho —
> trung thuc hon la bia mot cuoc hop khong xay ra.

## 2026-09-26 (week-03: 2026-09-21 - 2026-09-27)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `89740f1` 2026-09-27 · 2551918 Nguyen Phong Phu · m2: ap D8 bo sinh prefer khoi slice_builder, noi preprocess vao run_all, them check_m2 (req 2.1, 2.6)
  - `1d9fd53` 2026-09-25 · 2551909 Tran Bui Bao Long · m2: preprocess dataset (req 2.1, 2.6)
  - `9bd9755` 2026-09-25 · 2551909 Tran Bui Bao Long · m2: preprocess dataset - I,J,capacity,busy,campus + location preferences from seed (req 2.1, 2.6)

**Tag tuan:** `week-03`

- **Co mat:** _(day du 5/5 thanh vien)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
- **Phan viec tuan toi:** _(dien)_

## 2026-10-03 (week-04: 2026-09-28 - 2026-10-04)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `5f18d1b` 2026-10-04 · 2551918 Nguyen Phong Phu · m2: mo hinh CP-SAT loi muc tieu tu dien, va trong so mem + MaxLoad trong soft.py, sua ghim python-sat (req 2.2-2.5, 2.7)
  - `221301f` 2026-10-02 · 2551907 Tran Tuan Kiet · Thêm hàm phạt soft constraints S1 S2 cho Module 2 (Mã YC 2.5)

**Tag tuan:** `week-04`

- **Co mat:** _(day du 5/5 thanh vien)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(khong)_
- **Phan viec tuan toi:** _(dien)_

## 2026-10-10 (week-05: 2026-10-05 - 2026-10-11)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `eb7988c` 2026-10-10 · 2252345 Nguyen Van A · m2: merge m2-review-final (khai bao AI, ly do D1-D8, ledger)
  - `82614d1` 2026-10-10 · 2551905 Tran Anh Khoi · m2: dien khai bao AI, ly do D1-D8, reviewer va ty le dong gop; sua ma hoa console, bo eval trong soft.py

**Tag tuan:** **KHONG CO TAG** (mat 1% diem mon)

- **Co mat:** _(dien: ai du, ai vang)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
- **Phan viec tuan toi:** _(dien)_

## 2026-10-17 (week-06: 2026-10-12 - 2026-10-18)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `b244402` 2026-10-17 · 2551920 Nguyen Quang Phuc · m2: LP-relaxation counter-example x=0.5 (req 2.10)
  - `8247a7b` 2026-10-17 · 2551920 Nguyen Quang Phuc · m2: pulp cross-check + infeasible tuning (req 2.8)

**Tag tuan:** **KHONG CO TAG** (mat 1% diem mon)

- **Co mat:** _(dien: ai du, ai vang)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
- **Phan viec tuan toi:** _(dien)_

## 2026-10-24 (week-07: 2026-10-19 - 2026-10-25)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `fb34915` 2026-10-23 · 2551918 Nguyen Phong Phu · m2: sua AddAbsEquality lay tri tuyet doi sai, gom q ve mot nguon, noi crosscheck/counterexample/m3 vao run_all (req 2.7-2.10, 3.1)
  - `13b85e8` 2026-10-22 · nqphuc2551920 · Merge pull request #3 from SmallSun-MHH/m3-real-strings
  - `9d3f3f7` 2026-10-22 · 2551920 Nguyen Quang Phuc · m3: real strings from data, tiling, calibrate k and c (req 3.1)

**Tag tuan:** `week-07`

- **Co mat:** _(dien: ai du, ai vang)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
- **Phan viec tuan toi:** _(dien)_

## 2026-11-08 (week-08 & week-09: 2026-10-26 - 2026-11-08)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `388e273` 2026-11-08 · 2551918 Nguyen Phong Phu · m3: sinh lai DFA R3/R4 tu hieu chinh, tich + Hopcroft 155 trang thai, AddAutomaton vao ILP 73x27 ngay toi uu, check_m3 (req 3.1-3.4)
  - `7c27d85` 2026-11-03 · 2551909 Tran Bui Bao Long · Complete task 3.4b and 3.4c: Pumping lemma proof and verification script
  - `4fe71a8` 2026-11-02 · 2551907 Tran Tuan Kiet · Update 4 file DFA JSON cho các quy tắc R1, R2, R3, R4 (Mã YC 3.1 + 3.4a)

**Tag tuan:** `week-08` **KHONG CO TAG** (mat 1% diem mon) · `week-09` va `m3` da tag ngay 08/11.

- **Ghi nhan rà soát & đóng góp ngày 08/11 (2551905 Trần Anh Khôi):**
  - Đã đọc và chạy kiểm chứng toàn bộ các bài nộp M2 và M3 của nhóm (`preprocess.py`, `model.py`, `soft.py`, `crosscheck_pulp.py`, `baseline.py`, `benchmark.py`, `counterexample_lp_relax.py`, `strings_from_data.py`, `build_dfas.py`, `product_minimize.py`, `regular_to_ilp.py`, `pumping_proof.md`, `check_pumping.py`).
  - Bổ sung hàm `bang_myhill_nerode` vào `m3_automata/product_minimize.py` để xuất bảng hậu tố phân biệt ngắn nhất cho toàn bộ $\binom{155}{2} = 11{,}935$ cặp trạng thái của DFA tích tối thiểu (chiều dài hậu tố tối đa $\le 10$), cập nhật `tools/check_m3.py` và hoàn thiện quyết định thiết kế D9–D15 trong `DECISIONS.md`.
- **Phan viec tuan toi (Module 4 — Dynamics, week-10 & week-11):**
  - Phúc (2551920): `m4_dynamics/markov.py` (YC 4.1–4.3, hạn nội bộ 12/11).
  - Long (2551909): `m4_dynamics/experiment.py` vòng lặp đóng (YC 4.4, hạn nội bộ 15/11).
  - Khôi (2551905): Tham gia đóng góp trực tiếp vào `m4_dynamics/` (phân tích độ nhạy $\lambda$, kiểm chứng phân phối dừng và hội tụ TV distance) để đảm bảo đủ commit trên cả 4 module.

## 2026-11-15 (week-10: 2026-11-09 - 2026-11-15)

**Tag tuan:** `week-10`

- **Co mat:** Khôi (2551905), Long (2551909), Kiệt (2551907), Phú (2551918), Phúc (2551920).
- **Da ra quyet dinh gi (2551905 Trần Anh Khôi ghi nhận):**
  - Thống nhất chọn **Hướng M4-A (Closed-Loop Rolling-Horizon Fatigue Dynamics)** làm mô hình chính thức của Module 4 theo cấu trúc trong `IAP_tracker.xlsx` (`calibrate.py`, `recurrence.py`, `rolling_horizon.py`, `simulate.py`, `perturbation.py`), đồng thời tích hợp luôn kiểm chứng Xích Markov 3 trạng thái khả dụng (`Rest`, `Day`, `Night`) vào `m4_dynamics/perturbation.py` để giữ trọn vẹn nội dung đã bàn ở cuối tuần 09.
  - Chốt cơ chế phản hồi đơn điệu bị chặn `compute_feedback_lambdas` vượt ngưỡng vị trí $w_{\text{loc}} = 0.71$ và dưới ngưỡng suy biến tải $2w_{\text{fair}} - w_{\text{loc}} = 1.95$, giúp xoay vòng đều 3 suất ca kép qua cả 18 giám thị sau mỗi chu kỳ $W = 6$ kỳ (spread tải tích lũy $= 0$, Jain $= 1.0000$, $|F_{i,60} - F^*| = 3.30 \times 10^{-7} < 10^{-3}$).
  - Khôi (`2551905`) chủ trì hoàn thiện các tệp `m4_dynamics/recurrence.py` (Task 17), `m4_dynamics/rolling_horizon.py` (Task 18), `m4_dynamics/simulate.py` (Task 19), `m4_dynamics/perturbation.py` (Task 20), `tools/check_m4.py`, cùng khung ứng dụng Module 5 (`app/app.py`, `app/views/plan.py`, `app/views/dynamics.py`, cập nhật `run_all.py`).
  - **Chừa lại 2 task của Kiệt (`2551907`) để Kiệt tự code và mở PR:** Task 16 (`m4_dynamics/calibrate.py`) và Task 24 (`app/views/temporal.py`). Trong thời gian chờ Kiệt nộp, `m4_dynamics/recurrence.py` dùng hàm fallback `load_or_fit_params()` và `app/app.py` dùng hàm fallback `_render_temporal_fallback()` để toàn bộ pipeline chạy trơn tru 100%.
- **Vuong mac:**
  - Cần Kiệt (`2551907`) hoàn thành `m4_dynamics/calibrate.py` trước hạn khóa tag `m4` (`22/11/2026`) và `app/views/temporal.py` trước hạn `m5` (`29/11/2026`).
- **Phan viec tuan toi (week-11: 16/11 - 22/11/2026 — Khóa sổ M4):**
  - **Kiệt (`2551907`):** Nộp `m4_dynamics/calibrate.py` (Task 16, hạn nội bộ **18/11/2026**) xuất `m4_dynamics/out/params.json` và bắt đầu `app/views/temporal.py` (Task 24, hạn nội bộ **25/11/2026**).
  - **Phúc (`2551920`) & Long (`2551909`):** Review PR của Kiệt, kiểm tra chéo các con số trong `m4_dynamics/out/*.json` để đưa vào bản thảo báo cáo chương M4.
  - **Phú (`2551918`) & Khôi (`2551905`):** Chạy `tools/check_m4.py` và `python run_all.py --seed 43003334` sau khi merge PR của Kiệt, gắn và push tag `week-11` + `m4` đúng hạn **22/11/2026**.

## 2026-11-22 (week-11: 2026-11-16 - 2026-11-22)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `3dd64ad` 2026-11-16 · 2551907 Tran Tuan Kiet · m4: Hieu chinh tham so tu du lieu (Task 16)

**Tag tuan:** `week-11` va `m4` (chot moc Module 4 ngay 22/11/2026).

- **Ghi nhan rà soát & khóa sổ M4 (2551905 Trần Anh Khôi):**
  - Đã kiểm thử toàn tuyến `run_all.py --seed 43003334 --stage m4` và `--stage m5` sau khi gộp `m4_dynamics/calibrate.py` của Kiệt (`3dd64ad`): `tools/check_m4.py` đạt **18 ĐẠT · 0 CẢNH BÁO · 0 HỎNG** (sai số hội tụ `max_i |F_{i,60} - F*| = 2.33e-06 < 1e-3`).
  - Phát hiện và sửa lỗi ghi nhầm họ tên thành viên trong tài liệu/docstring M4 & M5, đồng thời đồng bộ lại 100% số liệu động trong `app/app.py` (Tab 2 M3 155 trạng thái, 73×27 ngày, 4 luật R1–R4 thật) và `app/views/plan.py` (đọc đúng khóa `unsat_core.json`, `solution.json` `Obj=3.99`, sửa hiển thị `prefer_campus=None` cho nhóm `balanced`), và hoàn thiện `app/README.md`.
- **Vướng mắc cần nhóm phối hợp ngay:**
  - **Phú (`2551918`)** và **Long (`2551909`)** hiện chưa có commit riêng trong thư mục `m4_dynamics/` — cần mỗi người bổ sung ít nhất 1 commit thực chất vào `m4_dynamics/` để đảm bảo tiêu chí `po.all_module_contribution` (5/5 thành viên đóng góp trên cả 4 module).
  - **Kiệt (`2551907`)** hoàn thành `app/views/temporal.py` (Task 24) trước hạn `25/11/2026` để khóa mốc `m5` ngày `29/11/2026`.
- **Phân việc tuần tới (week-12: 23/11 – 29/11/2026 — Khóa mốc M5 & Khởi động Báo cáo):**
  - **Kiệt (`2551907`):** Nộp `app/views/temporal.py` (Task 24) và xác nhận mức sử dụng AI trong `README.md`.
  - **Phú (`2551918`) & Long (`2551909`):** Bổ sung đóng góp kiểm chứng/tài liệu vào `m4_dynamics/` và khởi tạo khung báo cáo `report/`.
  - **Khôi (`2551905`) & Phúc (`2551920`):** Kiểm thử giao diện `streamlit run app/app.py` trên trình duyệt, chốt mốc `m5` + `week-12` đúng hạn **29/11/2026**.

