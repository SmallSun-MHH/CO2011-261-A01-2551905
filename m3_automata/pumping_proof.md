# Module 3 — Chứng minh L = {w : #M(w) = #A(w)} không chính quy (Yêu cầu 3.4b, 3.4c)

**File repo:** `m3_automata/pumping_proof.md` · **Phép kiểm chạy được:** `m3_automata/check_pumping.py`

Bảng chữ cái của lịch trực: Σ = {M, A, N, -} (sáng / chiều / đêm / nghỉ, mỗi ngày một ký hiệu).
Quy tắc "cân bằng sáng–chiều tuyệt đối" trên toàn kỳ:

```
L = { w ∈ Σ* : #M(w) = #A(w) }
```

**Mệnh đề.** L không phải ngôn ngữ chính quy.

Hướng chứng minh đúng như đề yêu cầu: (1) giao L với một ngôn ngữ chính quy để thu được {Mⁿ Aⁿ}, (2) chứng minh {Mⁿ Aⁿ} không chính quy bằng bổ đề bơm, (3) dùng tính đóng của lớp ngôn ngữ chính quy dưới phép giao để kết luận về L.

---

## 1. Công cụ sử dụng

**Bổ đề bơm (cho ngôn ngữ chính quy).** Nếu L′ chính quy thì tồn tại số nguyên p ≥ 1 (độ dài bơm) sao cho mọi w ∈ L′ có |w| ≥ p đều viết được w = xyz với

1. |xy| ≤ p,
2. |y| ≥ 1,
3. xyⁱz ∈ L′ với mọi i ≥ 0.

Bổ đề chỉ là điều kiện **cần**: dùng nó để chứng minh *không* chính quy bằng phản chứng, không bao giờ để chứng minh chính quy.

**Tính đóng dưới phép giao.** Nếu L₁, L₂ chính quy thì L₁ ∩ L₂ chính quy. Chứng minh bằng DFA tích: với D₁ = (Q₁, Σ, δ₁, s₁, F₁) và D₂ = (Q₂, Σ, δ₂, s₂, F₂), DFA tích có trạng thái Q₁ × Q₂, trạng thái đầu (s₁, s₂), chuyển δ((q₁,q₂), a) = (δ₁(q₁,a), δ₂(q₂,a)), tập chấp nhận F₁ × F₂.

---

## 2. Bước 1 — Ngôn ngữ chính quy M\*A\* và phép giao

**M\*A\* chính quy**: nó được mô tả bởi biểu thức chính quy `M*A*`, và có DFA đầy đủ 3 trạng thái:

| Trạng thái | Ý nghĩa | M | A | N | - |
|---|---|---|---|---|---|
| q₀ (đầu, chấp nhận) | đang đọc dãy M | q₀ | q₁ | bẫy | bẫy |
| q₁ (chấp nhận) | đã sang dãy A | bẫy | q₁ | bẫy | bẫy |
| bẫy | đã sai dạng | bẫy | bẫy | bẫy | bẫy |

**Khẳng định:** L ∩ M\*A\* = { Mⁿ Aⁿ : n ≥ 0 }.

*Chứng minh.* Lấy w ∈ M\*A\*, tức w = Mᵃ Aᵇ với a, b ≥ 0. Khi đó #M(w) = a và #A(w) = b. Vậy w ∈ L ⇔ a = b ⇔ w = Mⁿ Aⁿ với n = a = b. Hai chiều bao hàm đều suy ra từ chuỗi tương đương này. Lưu ý các ký hiệu N và - không xuất hiện trong chuỗi của M\*A\*, nên chúng không ảnh hưởng đến phép giao. ∎

Đặt **L′ = { Mⁿ Aⁿ : n ≥ 0 }**.

---

## 3. Bước 2 — L′ không chính quy (bổ đề bơm)

*Chứng minh bằng phản chứng.* Giả sử L′ chính quy, gọi p ≥ 1 là độ dài bơm của nó.

**Chọn chuỗi:** w = Mᵖ Aᵖ. Ta có w ∈ L′ và |w| = 2p ≥ p.

**Mọi cách tách hợp lệ:** giả sử w = xyz với |xy| ≤ p và |y| ≥ 1.
Vì |xy| ≤ p nên xy nằm trọn trong p ký tự M đầu tiên của w. Do đó

- x = Mᵃ,
- y = Mᵏ với k = |y| ≥ 1,
- z = Mᵖ⁻ᵃ⁻ᵏ Aᵖ.

**Bơm i = 2:** xy²z = Mᵖ⁺ᵏ Aᵖ. Chuỗi này có p + k ký tự M và p ký tự A, mà k ≥ 1 nên p + k ≠ p. Nó không có dạng Mⁿ Aⁿ, tức xy²z ∉ L′.

(Bơm i = 0 cũng cho kết quả tương tự: xz = Mᵖ⁻ᵏ Aᵖ có p − k < p ký tự M, nên cũng ∉ L′.)

Điều này mâu thuẫn với điều kiện 3 của bổ đề bơm. Vậy giả thiết sai: **L′ không chính quy.** ∎

**Vì sao chọn w = Mᵖ Aᵖ:** điều kiện |xy| ≤ p *ép* phần bơm y nằm hoàn toàn trong khối M. Chọn chuỗi khác (ví dụ (MA)ᵖ) thì y có thể chứa cả M lẫn A cân bằng và phép bơm không phá được tính cân bằng — chứng minh sẽ hỏng.

---

## 4. Bước 3 — Kết luận cho L (tính đóng dưới phép giao)

*Chứng minh bằng phản chứng.* Giả sử L chính quy. M\*A\* chính quy (Bước 1). Theo tính đóng dưới phép giao, L ∩ M\*A\* chính quy. Nhưng L ∩ M\*A\* = L′ (Bước 1), và L′ không chính quy (Bước 2). Mâu thuẫn. Vậy **L không chính quy.** ∎

**Nhận xét trung thực về phương pháp.** Trên L, có thể áp dụng bổ đề bơm trực tiếp với cùng chuỗi w = Mᵖ Aᵖ và lập luận y ⊆ Mᵏ cũng chạy được. Đường vòng qua phép giao vẫn đáng dùng vì nó tách rõ hai việc: ép chuỗi về dạng "khối M rồi khối A" (nhờ giao với ngôn ngữ chính quy đơn giản) để phép phân tích y trở nên mạch lạc, và nó cũng là kỹ thuật chuẩn khi bảng chữ cái có thêm ký hiệu (ở đây là N và -) làm chuỗi tùy ý khó phân tích. Đề bài yêu cầu đúng hướng này.

---

## 5. Yêu cầu 3.4c — Vì sao lịch thực tế dùng bản có chặn

**Bản có chặn là chính quy (3.4a):** quy tắc |#M − #A| ≤ c chỉ cần nhớ hiệu d = #M − #A ∈ {−c, …, c} kèm một trạng thái bẫy khi |d| vượt c. Đó là DFA hữu hạn có **2c + 2 trạng thái** (c = 2 → 6 trạng thái, đã kiểm bằng `check_pumping.py`).

**Bản cân bằng tuyệt đối (d = 0 trên toàn kỳ) không chính quy:** để đối chiếu #M với #A, bộ nhớ phải đếm được d ở mọi giá trị nguyên mà chuỗi có thể đạt, tức cần bộ nhớ **không bị chặn** — một DFA với số trạng thái hữu hạn K không phân biệt được các chuỗi Mⁿ với n > K (đây chính là điều bổ đề bơm vừa khai thác).

**Lưu ý chính xác về kỳ hữu hạn.** Một kỳ học thực tế có độ dài cố định T ngày, khi đó L ∩ Σᵀ là ngôn ngữ **hữu hạn**, và mọi ngôn ngữ hữu hạn đều chính quy. Vậy về mặt lý thuyết có DFA cho nó; nhưng DFA đó cần số trạng thái tăng tuyến tính theo T (phải nhớ vị trí và hiệu d), và khi giao nó với các DFA luật khác (quy tắc chuỗi ngày làm việc, ca đêm…) tích trạng thái phình lên rất nhanh. Vì vậy:

- Luật **cục bộ, nhớ ít** (chặn |#M − #A| ≤ c, không quá 2 ngày làm liên tiếp, ca đêm kèm ngày nghỉ) đi vào **DFA** và vào ILP qua ràng buộc chính quy (3.3).
- Luật **đếm toàn cục chính xác** (#M = #A) đưa thẳng vào **ILP** dưới dạng một đẳng thức tuyến tính trên biến nhị phân, ví dụ Σ_d x_{i,d,M} = Σ_d x_{i,d,A} cho mỗi giám thị i — một ràng buộc duy nhất, không cần bất kỳ automaton nào.

---

## 6. Kiểm chứng bằng code

`python m3_automata/check_pumping.py` (thoát 0 khi đạt cả 3):

| Phép kiểm | Nội dung | Kết quả |
|---|---|---|
| (1) Giao | L ∩ M\*A\* = {Mⁿ Aⁿ} trên **mọi** chuỗi độ dài ≤ 8 trên Σ = {M,A,N,-} | ĐẠT |
| (2) Bơm | Với p = 1…12, **mọi** cách tách w = Mᵖ Aᵖ = xyz thỏa |xy| ≤ p, |y| ≥ 1 đều bơm (i = 0 và i = 2) ra khỏi L′ | ĐẠT |
| (3) Bản có chặn | DFA bộ đếm c = 2 (6 trạng thái) chấp nhận đúng ngôn ngữ "mọi tiền tố có |#M − #A| ≤ 2" trên mọi chuỗi độ dài ≤ 8 | ĐẠT |

Phép kiểm là vét cạn trên miền hữu hạn nên chỉ **kiểm chứng** chứ không thay thế chứng minh ở các mục 2–4; chứng minh đúng với mọi p nhờ lập luận y ⊆ Mᵏ.

## 7. Liên hệ với Appendix A (đề bài)

Câu M3-Q2: đáp án là quy tắc "số ca sáng bằng số ca chiều trên toàn kỳ", chứng minh qua L ∩ M\*A\* = {Mⁿ Aⁿ} — đúng hướng của file này. Quy tắc "tối đa 3 ca trong cửa sổ 7 ngày" và "không hai đêm liên tiếp" đều chính quy (nhớ hữu hạn), nên không phải đáp án.
