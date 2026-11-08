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

- **Co mat:** _(dien: ai du, ai vang)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
- **Phan viec tuan toi:** _(dien)_

## 2026-10-03 (week-04: 2026-09-28 - 2026-10-04)

**Bang chung git co that trong tuan** (sinh tu `git log`, khong sua):
  - `5f18d1b` 2026-10-04 · 2551918 Nguyen Phong Phu · m2: mo hinh CP-SAT loi muc tieu tu dien, va trong so mem + MaxLoad trong soft.py, sua ghim python-sat (req 2.2-2.5, 2.7)
  - `221301f` 2026-10-02 · 2551907 Tran Tuan Kiet · Thêm hàm phạt soft constraints S1 S2 cho Module 2 (Mã YC 2.5)

**Tag tuan:** `week-04`

- **Co mat:** _(dien: ai du, ai vang)_
- **Da ra quyet dinh gi:** _(dien bang loi cua chinh nguoi viet — day la phan de
  bai dung de kiem quyen tac gia, khong chep tu cho khac)_
- **Vuong mac:** _(dien)_
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
