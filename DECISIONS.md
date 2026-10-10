# Design decisions

Mỗi mục: quyết định gì, vì sao, đã loại phương án nào.
Phần "Dự kiến" là số liệu chạy ra từ code. Phần "Lý do" do AI phân tích dự án và lập kế hoạch, cả nhóm đọc lại và chịu trách nhiệm.

## Module 1

### D1 — Đơn vị phân công là (MS Ca thi, Cơ sở), không phải MS Ca thi
Dự kiến: ca `20260528_3` lúc 13g00 diễn ra ở CẢ HAI cơ sở. Nếu gộp làm một thì
`overlap` và `busy` luôn rỗng, tức ràng buộc cứng H1 và H2 biến mất khỏi mô hình.
Sau khi tách: 6 ca, 1 cặp chồng giờ, 15 cặp bận.
Lý do (AI phân tích, cả nhóm rà soát): Gộp ca thì hai cơ sở thành một, H1 và H2 không còn tác dụng. Tách ra mới đúng với thực tế, nên bọn mình bỏ cách gộp.

### D2 — Vì sao lát nguyên bản luôn khả thỏa
Dự kiến: `capacity[j]` bằng đúng số người thực tế trong lịch gốc, nên lịch gốc
chính là một nhân chứng SAT. Không thể cắt lát bất kỳ rồi mong ra UNSAT.
Lý do (AI phân tích, cả nhóm rà soát): Capacity lấy từ lịch gốc nên lịch gốc luôn là một nghiệm đúng. Muốn có ca UNSAT thì phải tự siết thêm (xem D3).

### D3 — Phép siết để tạo lát bất khả thỏa
Dự kiến: thu hẹp tập giám thị trực. Ngưỡng N* = 14/18. Lõi tối thiểu gồm
`AVAIL[CB010 @ 20260528_3@Co so 2]` + `CAP_GE[20260528_3@Co so 2 can >= 14]`.
Tình huống vận hành đúng sau phép siết (AI phân tích, cả nhóm rà soát): Nếu chỉ còn dưới 14 giám thị mà ca 13g00 ở Cơ sở 2 vẫn cần 14 người thì không đủ người. Lõi chỉ ra hai nguyên nhân: CB010 không rảnh và sức chứa của ca đó.

### D4 — Busy suy từ lịch gốc; Eligible = mọi cặp
Dự kiến: dataset không có dữ liệu chuyên môn, mà đề chỉ cho phép mô phỏng
3 thứ (preference vị trí, ca đêm, trọng số soft). Nên không bịa eligibility.
Lý do (AI phân tích, cả nhóm rà soát): Dataset không có thông tin chuyên môn nên cho mọi cặp đều đủ điều kiện, không bịa thêm. Lịch bận lấy từ các ca trùng giờ trong lịch gốc.

### D5 — Cột "Nhiệm vụ" (CBCT / Thư ký / Trưởng HD) có tính hết vào capacity không
Lý do (AI phân tích, cả nhóm rà soát): Chưa có dữ liệu để biết, nên tạm tính capacity là tổng số người trong lịch gốc, không phân biệt chức vụ. Đây là giả định, cần hỏi lại đề.

### D6 — Mã hóa sức chứa bằng seqcounter thay vì vét cạn
Dự kiến: at-most-2 vét cạn trên 18 người cần C(18,3) = 816 mệnh đề cho MỘT ca.
Lý do (AI phân tích, cả nhóm rà soát): Vét cạn bùng nổ khi số giám thị tăng, còn seqcounter chỉ thêm số biến phụ tăng theo số người, nên bọn mình chọn seqcounter.

### D7 — Vì sao có cả cnf_encoder.py lẫn unsat_core.py
Dự kiến: `solver.get_core()` trả về MỘT tập con bất khả thỏa, không bảo đảm
tối thiểu. `unsat_core.py` có lại bằng deletion-based MUS và chứng minh:
bỏ bất kỳ mệnh đề nào trong lõi thì bài toán trở lại khả thỏa.
Lý do (AI phân tích, cả nhóm rà soát): `cnf_encoder.py` kiểm tra khả thi nhanh và trả một lõi bất kỳ. `unsat_core.py` mới đảm bảo lõi tối thiểu. Tách hai file để mỗi file làm một việc.

### D8 — Ai sinh location preference: M1 hay M2
Dự kiến: m1_logic/slice_builder.py ban đầu tự sinh field 'prefer' bằng seed,
trùng với task 'sinh preference vị trí 3 loại' được giao riêng cho M2
(m2_ilp/preprocess.py). Nếu cả 2 cùng sinh độc lập, sẽ ra 2 giá trị Prefer(i,c)
khác nhau cho cùng 1 người giữa M1 và M2 dù dùng chung seed_int (khác thứ tự
rút số ngẫu nhiên).
Quyết định: M2 (m2_ilp/preprocess.py) là CHỦ SỞ HỮU DUY NHẤT của bước sinh
Prefer(i,c). Đã xóa đoạn sinh 'prefer' khỏi m1_logic/slice_builder.py.
Lý do (AI phân tích, cả nhóm rà soát): Hai nơi cùng sinh sẽ ra hai kết quả khác nhau cho một người. Preference chỉ dùng ở M2 nên để M2 giữ một nơi duy nhất.
