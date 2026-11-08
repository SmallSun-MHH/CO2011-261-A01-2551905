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

## Module 2

### D9 — Mục tiêu từ điển hai pha (Lexicographic) thay vì tổng trọng số một pha (YC 2.3–2.4)
Dự kiến: Pha 1 tìm tải cực đại nhỏ nhất $t^* = 2$; Pha 2 cố định ràng buộc $t \le t^*$ rồi tối thiểu hóa độ lệch $L_1$ cùng phạt mềm $\sum_i |l_i - q| + w_1 S_1 + w_2 S_2$ (đạt $\text{L1} = 3$, vi phạm S1 = 0, S2 = 0).
Lý do (AI phân tích, cả nhóm rà soát): Nếu gộp $t$ vào chung một hàm mục tiêu một pha với hệ số tự chọn, việc chọn trọng số cho $t$ mang tính chủ quan và có thể đánh đổi tải cực đại lấy phạt mềm nhỏ. Giải từ điển hai pha đảm bảo ưu tiên tuyệt đối việc san bằng đỉnh tải $t^*$ trước, rồi mới tối ưu công bằng $L_1$ và ưu tiên mềm trong không gian nghiệm tối ưu của Pha 1.

### D10 — Biến trung gian cho `AddAbsEquality` và một nguồn duy nhất cho tải lý tưởng $q$ (YC 2.4, 2.8)
Dự kiến: Phép đối chứng PuLP (`m2_ilp/crosscheck_pulp.py`) trên 60 cấu hình phát hiện tại cấu hình #11 (14 giám thị, có người nhận tải $l_i = 0$ với $q = 1$) rằng `model.AddAbsEquality(d, l_i - q)` trong OR-Tools không lấy trị tuyệt đối khi truyền trực tiếp biểu thức affine, trả về $d = -1$ thay vì $1$. Đồng thời hai file từng tính $q$ lệch nhau khi có ca thiếu thông tin cơ sở.
Lý do (AI phân tích, cả nhóm rà soát): Đưa hiệu $l_i - q$ vào biến nguyên trung gian `hieu` trước khi gọi `AddAbsEquality(d, hieu)`, và gom định nghĩa $q = \text{round}(\sum_j \text{cap}_j / |I|)$ về một hàm duy nhất `model.tai_ly_tuong(params)` để CP-SAT, PuLP và bộ kiểm thử dùng chung. Sau khi sửa, 60/60 cấu hình đối chứng khớp tuyệt đối.

### D11 — Trích lịch phân công thực tế làm Baseline thay vì tự bịa heuristic (YC 2.9)
Dự kiến: Lịch gốc trong dataset (`instance['baseline']`, 21 lượt gán) thỏa cả 5 ràng buộc cứng nhưng phân công `CB010` tới 3 ca (vượt `MaxLoad = 2`), gây 3 vi phạm cơ sở (S1) và 1 vi phạm tải (S2), Jain $= 0.8448$, Gini $= 0.1296$, tổng phạt $= 7.74$. Nghiệm CP-SAT đạt 7 thắng – 1 hòa – 0 thua (Jain $= 0.9074$, Gini $= 0.1190$, 0 vi phạm S1/S2, tổng phạt $= 3.99$, hòa ở $\text{L1} = 3$).
Lý do (AI phân tích, cả nhóm rà soát): Đối sánh trực tiếp với lịch phân công thật từ dữ liệu gốc khách quan và có ý nghĩa thực tiễn hơn so với việc tự viết một heuristic tham lam yếu làm vật đối chứng. Cả hai lịch đều được đo bằng cùng một hàm `baseline.tinh_chi_so`.

## Module 3

### D12 — Hiệu chỉnh $k = 4, c = 5$ từ dữ liệu thật (ngưỡng 90%), giữ $m = 2$ làm chính sách (YC 3.1)
Dự kiến: Trên 73 chuỗi lịch thật dài 27 ngày (ghép từ 9 ngày thi bằng phép lặp có hạt giống), giá trị nhỏ nhất để $\ge 90\%$ giám thị thỏa mãn là $k = 4$ ca/cửa sổ 7 ngày (70/73 = 95.9% thỏa) và $c = 5$ cho độ lệch tiền tố $|{\#M} - {\#A}| \le c$ (71/73 = 97.3% thỏa). Với R1 (không quá $m$ ngày làm liên tiếp), ngưỡng 90% trên lịch thật là $m = 4$, nhưng nhóm giữ $m = 2$ (45/73 = 61.6% thỏa trên lịch thật).
Lý do (AI phân tích, cả nhóm rà soát): Hiệu chỉnh $k, c$ từ dữ liệu giúp R3, R4 bám sát thực tế vận hành (tránh đặt $c = 1$ tùy tiện khiến 66/73 giám thị vi phạm), trong khi giữ $m = 2$ ở R1 phản ánh đúng quyết định chính sách của nhóm nhằm xóa bỏ tình trạng giám thị phải coi thi 3–4 ngày liên tiếp trong lịch thủ công.

### D13 — Sinh tự động DFA R3, R4 từ tham số hiệu chỉnh và kiểm chứng vị từ vét cạn (YC 3.1, 3.4a)
Dự kiến: `m3_automata/build_dfas.py` sinh DFA R3 (theo dõi hậu tố 6 ngày gần nhất có $\le 4$ ca: $1 + \sum_{w=0}^4 \binom{6}{w} = 58$ trạng thái) và DFA R4 (theo dõi hiệu $\#M - \#A \in [-5, +5]$ cùng bẫy: 12 trạng thái) trực tiếp từ `m3_calibration.json`, rồi đối chiếu cả 4 DFA với vị từ độc lập trên toàn bộ $\sum_{L=0}^8 4^L = 87{,}381$ chuỗi và 73 chuỗi thật (0 lệch).
Lý do (AI phân tích, cả nhóm rà soát): Viết tay DFA nhiều trạng thái rất dễ sai (bản viết tay đầu tiên của R3 chỉ có 4 trạng thái và bị phép kiểm luật thừa trong `product_minimize.py` phát hiện $L(R_2) \subseteq L(R_3)$). Sinh tự động kết hợp kiểm chứng vét cạn và tìm chuỗi nhân chứng cho từng luật (`MMM`, `NM`, `MM-MM-M`, `MM-MM--MM`) chứng minh cả 4 DFA đều đúng và không luật nào thừa.

### D14 — Bảng nhân chứng hậu tố phân biệt Myhill–Nerode cho 11.935 cặp trạng thái (YC 3.2)
Dự kiến: Giao đồng bộ 4 DFA có $4 \times 3 \times 58 \times 12 = 8{,}352$ trạng thái lý thuyết, 3.108 trạng thái đạt tới, và thu gọn bằng Hopcroft còn 155 trạng thái (154 chấp nhận + 1 bẫy). Hàm `bang_myhill_nerode` trong `m3_automata/product_minimize.py` tìm hậu tố phân biệt ngắn nhất $z \in \Sigma^*$ cho toàn bộ $\binom{155}{2} = 11{,}935$ cặp trạng thái phân biệt (100% cặp có nhân chứng hợp lệ với $|z| \le 10$, 0 nhân chứng sai).
Lý do (AI phân tích, cả nhóm rà soát): Theo định lý Myhill–Nerode, DFA 155 trạng thái đạt tới là tối thiểu khi và chỉ khi mọi cặp trạng thái phân biệt đều có ít nhất một hậu tố $z$ làm một bên chấp nhận và một bên bác bỏ. Việc xuất tường minh nhân chứng $z$ ngắn nhất cho cả 11.935 cặp giúp kiểm chứng độc lập kết quả Hopcroft bằng bằng chứng hữu hạn có thể kiểm tra trực tiếp.

### D15 — Đổi mục tiêu sang biến thiếu hụt để chứng minh tối ưu Pha 2 khi nhúng `AddAutomaton` (YC 3.3)
Dự kiến: Trên bài toán 73 giám thị $\times$ 27 ngày (472 ngày-công, tải lý tưởng $q = 6$, phần dư $r = 472 - 73 \times 6 = 34$), Pha 1 chứng minh $t^* = 7$. Ở Pha 2, nếu tối thiểu hóa trực tiếp $\sum_i |l_i - 6|$ bằng `AddAbsEquality`, nhánh-cận của CP-SAT chỉ thấy cận dưới LP bằng 0 nên không đóng được gap (kẹt ở 36 vs 34 sau 90 giây). Nhờ đồng nhất thức $\sum_i |l_i - q| = r + 2\sum_i \max(0, q - l_i) = 34 + 2\sum_i s_i$ với biến thiếu hụt $s_i \ge \max(0, 6 - l_i)$, CP-SAT tìm được nghiệm có $\sum_i s_i = 0$ (mọi giám thị nhận 6 hoặc 7 ngày công) và chứng minh tối ưu toàn cục $\text{L1}^* = 34$ tức thì.
Lý do (AI phân tích, cả nhóm rà soát): Biến đổi đại số sang tổng thiếu hụt $\sum_i s_i \ge 0$ làm cận dưới tự nhiên của biến quyết định trùng khít với giá trị tối ưu bằng 0, giúp bộ giải đóng khoảng cách tối ưu (optimality gap) ngay lập tức mà không thay đổi tập nghiệm tối ưu của bài toán.

