# Module 1 — Đặc tả Logic (Yêu cầu 1.1)

**Đầu việc:** Ký hiệu vị từ (Assign, Busy, Overlap, AtCampus, Prefer) + viết 5 ràng buộc cứng và 2 ràng buộc mềm thành công thức bậc nhất (first-order logic).

**File repo:** `m1_logic/spec.md`

---

## 1. Miền và ký hiệu vị từ (predicate signature)

### 1.1 Miền (domains / sorts)

| Miền | Ký hiệu biến | Ý nghĩa |
|---|---|---|
| Invigilators | `i, i'` | tập giám thị `I` |
| Shifts (ca thi) | `j, k` | tập ca thi `J` |
| Campuses (cơ sở) | `c1, c2` | tập cơ sở, ví dụ `{CS1, CS2}` |

### 1.2 Vị từ đề bài yêu cầu

| Vị từ | Kiểu | Ý nghĩa |
|---|---|---|
| `Assign(i, j)` | biến quyết định | giám thị *i* được phân công coi thi ở ca *j* |
| `Busy(i, j)` | dữ liệu đầu vào | giám thị *i* không rảnh (bận việc khác / đã xin nghỉ) ở ca *j* |
| `Overlap(j, k)` | dữ liệu đầu vào | ca *j* và ca *k* trùng khoảng thời gian |
| `AtCampus(j, c1)` | dữ liệu đầu vào | ca *j* diễn ra tại cơ sở *c1* |
| `Prefer(i, c1)` | dữ liệu đầu vào | giám thị *i* ưu tiên (nguyện vọng) cơ sở *c1* |

### 1.3 Vị từ phụ trợ (cần thêm để viết đủ 5 ràng buộc cứng + 2 mềm)

| Vị từ | Kiểu | Ý nghĩa |
|---|---|---|
| `Eligible(i, j)` | dữ liệu đầu vào | *i* đủ điều kiện/chuyên môn để coi ca *j* |
| `Cap(j, n)` | dữ liệu đầu vào (hàm số hóa dưới dạng vị từ) | ca *j* cần đúng *n* giám thị |
| `MaxLoad(i, m)` | dữ liệu đầu vào | giám thị *i* nhận số ca tối đa cho phép là *m* trước khi bị coi là quá tải |

**Quy ước:**
- `Overlap` là **đối xứng** (`Overlap(j,k) ↔ Overlap(k,j)`) và **phản xạ‑âm** (`¬Overlap(j,j)` không xét, một ca không "trùng" với chính nó theo nghĩa xung đột).
- `Assign`, và các vị từ `Viol_*` bên dưới (biến vi phạm) là **biến quyết định / suy ra**, còn lại tất cả là **dữ liệu đầu vào cố định** (facts) lấy từ dataset hoặc seed.
- Miền là **hữu hạn** (tập giám thị, ca thi, cơ sở hữu hạn), nên các lượng từ `∀, ∃` được hiểu là duyệt hữu hạn — điều kiện cần để dịch sang CNF/ILP ở mục 1.2–1.3 của đề.

---

## 2. Năm ràng buộc cứng (hard constraints)

Ràng buộc cứng là **bắt buộc phải đúng tuyệt đối**; vi phạm bất kỳ ràng buộc nào khiến lịch phân công không hợp lệ (infeasible).

### H1 — Không trùng ca (no double-booking)

Một giám thị không được gán vào hai ca trùng thời gian.

```
∀i ∀j ∀k ( Overlap(j,k) ∧ Assign(i,j) → ¬Assign(i,k) )
```

*(Đây chính là công thức mẫu trong đề bài.)*

### H2 — Tôn trọng lịch bận / khả dụng (availability)

Không phân công giám thị vào ca mà người đó đang bận.

```
∀i ∀j ( Busy(i,j) → ¬Assign(i,j) )
```

### H3 — Đủ điều kiện chuyên môn (eligibility)

Chỉ phân công giám thị đủ điều kiện cho ca đó.

```
∀i ∀j ( Assign(i,j) → Eligible(i,j) )
```

### H4 — Toàn vẹn dữ liệu ca thi (well-formedness)

Chỉ phân công vào những ca đã có cơ sở (campus) xác định — đảm bảo mọi ca dùng để tối ưu hóa đều có dữ liệu đầy đủ, là tiền đề để ràng buộc mềm S1 (ưu tiên vị trí) có nghĩa.

```
∀i ∀j ( Assign(i,j) → ∃c1 AtCampus(j,c1) )
```

### H5 — Đúng sĩ số ca thi (capacity)

Mỗi ca *j* cần đúng *n* giám thị, dùng lượng từ đếm `∃^{=n}` (mở rộng chuẩn của FOL trên miền hữu hạn, cùng dạng với ví dụ "exactly one" trong đề).

```
∀j ∀n ( Cap(j,n) → (∃^{=n} i) Assign(i,j) )
```

> **Ghi chú kỹ thuật (liên hệ mục 1.2–1.3):** `∃^{=n}` không phải là lượng từ nguyên thủy của FOL — nó là viết tắt của một hội các bất đẳng thức đếm (`∃^{≥n} ∧ ∃^{≤n}`), và khi mã hóa CNF bằng phương pháp binomial brute-force, phần "at-most-n" một mình đã sinh ra tổ hợp chập (n+1) trên |I|, tức **impractical ở quy mô dữ liệu thật** (đây cũng là nội dung câu hỏi ôn tập Q1 – Module 1 trong Appendix A của đề). Vì vậy mục 1.3 (logic-to-LP bridge) sẽ dịch trực tiếp H5 thành một bất đẳng thức tuyến tính duy nhất: `Σᵢ xᵢⱼ = Cap(j)`, thay vì khai triển CNF đầy đủ.

---

## 3. Hai ràng buộc mềm (soft constraints)

Ràng buộc mềm **không cấm tuyệt đối** — vi phạm được cho phép nhưng bị phạt trong hàm mục tiêu (mục 2.5 của đề). Cách chuẩn: định nghĩa một vị từ "vi phạm" (`Viol_*`), sau đó cộng dồn có trọng số vào objective.

### S1 — Ưu tiên cơ sở (location preference)

Trạng thái lý tưởng (không bắt buộc): nếu *i* được gán vào ca *j* tại cơ sở *c*, thì *c* nên nằm trong nguyện vọng của *i*.

```
∀i ∀j ∀c1 ( Assign(i,j) ∧ AtCampus(j,c1) ∧ Prefer(i,c1) → Satisfied_loc(i,j) )
```

Vị từ vi phạm (được suy ra, dùng trong hàm mục tiêu):

```
Viol_loc(i,j) ≡ Assign(i,j) ∧ ∃c1 ∃c2 ( AtCampus(j,c1) ∧ Prefer(i,c2) ∧ c1 ≠ c2 )
```

Đóng góp vào hàm mục tiêu (tuyến tính hóa ở M2):

```
+ w_loc · Σ_{i,j} Viol_loc(i,j)
```

trong đó `w_loc` là một trong ba trọng số soft-constraint sinh từ `data/seed.txt`, thuộc khoảng `[0.5, 2.0]` (§1 của đề bài).

### S2 — Giới hạn mệt mỏi / tải làm việc (fatigue limit)

Dùng lại lượng từ đếm như H5, nhưng ở đây là **ràng buộc mềm**: tổng số ca của *i* không nên vượt quá `MaxLoad(i)`.

```
Load(i,n) ≡ (∃^{=n} j) Assign(i,j)

∀i ∀n ∀m ( Load(i,n) ∧ MaxLoad(i,m) ∧ n > m → Viol_load(i) )
```

Đóng góp vào hàm mục tiêu:

```
+ w_load · Σᵢ Viol_load(i)
```

---

## 4. Vì sao chia như trên (biện luận / Rigor)

- **H1–H3** là các ràng buộc quan hệ nhị nguyên thuần túy → mỗi cái dịch thẳng sang **một** bất đẳng thức tuyến tính / **một** dạng mệnh đề CNF, không tốn kém khi mở rộng quy mô.
- **H4** đảm bảo dữ liệu nhất quán (mọi ca có cơ sở xác định) — là điều kiện tiên quyết để S1 có nghĩa; nếu bỏ H4, `AtCampus` có thể không tồn tại và S1 sẽ đánh giá sai.
- **H5** và **S2** cố ý dùng chung một cấu trúc đếm `∃^{=n}` để làm nổi bật sự khác biệt cốt lõi giữa ràng buộc cứng và mềm (footnote 6 của đề): **H5** — đúng sĩ số là **bắt buộc**, không thương lượng; **S2** — vượt tải là **không mong muốn** nhưng có thể chấp nhận nếu đổi lại được lợi ích khác (ví dụ tránh infeasible khi thiếu nhân lực).
- **S1, S2** đều được viết theo mẫu `điều_kiện → Viol(...)`, để mục 1.3 (logic-to-LP bridge) dễ dàng dịch mỗi `Viol` thành một biến phạt nhị phân/liên tục cộng vào objective với trọng số `w` — đúng cấu trúc yêu cầu 2.5 của đề (soft constraints thành hàm phạt).

---

## 5. Ví dụ minh họa nhỏ (đối chiếu với Worked Example của đề)

Instance: 2 giám thị `{CB1, CB2}`, 1 ca `s` cần đúng 1 người; `Busy(CB1, s)` đúng.

- Từ H2: `Busy(CB1,s) → ¬Assign(CB1,s)`.
- Từ H5 với `Cap(s,1)`: đúng 1 trong 2 người được gán.
- Kết luận logic duy nhất thỏa mãn: `¬Assign(CB1,s) ∧ Assign(CB2,s)`.

Đây chính là lời giải khớp với ví dụ SAT trong đề bài (`a1=0, a2=1`), xác nhận đặc tả trên là đúng và nhất quán với phần 1.2 (CNF/SAT) sẽ triển khai tiếp theo.
