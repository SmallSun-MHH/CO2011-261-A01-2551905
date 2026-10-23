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
