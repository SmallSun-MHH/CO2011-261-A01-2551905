# m1_logic — see the assignment brief section for this module.
### Công cụ đã dùng

- **Claude (Anthropic)** — phiên làm việc qua giao diện Cowork.

### Bảng khai báo theo hạng mục

Mỗi thành viên tự điền và tự chịu trách nhiệm phần của mình. Người khác không khai thay.

| Hạng mục / file | Người phụ trách | Mức | AI đã làm gì cụ thể | Đã kiểm chứng bằng cách nào |
|---|---|---|---|---|
| Kế hoạch 14 tuần, bảng phân việc, bảng theo dõi tiến độ | Nguyễn Phong Phú | 4 | Đọc đề, đề xuất lịch mốc, chia 25 đầu việc theo mô hình Lead + Reviewer, dựng bảng theo dõi | Đối chiếu từng mốc và từng trọng số điểm với §3 và §6 của đề |
| `contracts/` — hợp đồng dữ liệu và script sinh dữ liệu giả | Nguyễn Phong Phú | 4 | Đề xuất cơ chế cắt phụ thuộc giữa các thành viên, viết schema và các script sinh dữ liệu giả | `python contracts/make_all.py` tự kiểm 7/7 hợp đồng đạt |
| `m1_logic/unsat_core.py` (yêu cầu 1.2, phần UNSAT) | *(điền tên)* | 4 | Sinh toàn bộ khung: mã hóa CNF có selector literal, deletion-based MUS, chặt nhị phân tìm ngưỡng N\*, phép kiểm tính tối thiểu | Chạy trên instance thật do `slice_builder.py` sinh; 100% phép kiểm tính tối thiểu ĐẠT; lõi đối chiếu khớp dạng lõi mô tả ở Appendix A câu M1/Q2 |
| `m1_logic/slice_builder.py` — bản vá `busy` và `normalize_seed` | Trần Anh Khôi | 3 | Phát hiện `busy` bị để rỗng làm mất ràng buộc H2; đề xuất suy `busy` từ lịch gốc qua quan hệ chồng giờ; phát hiện `--seed` kiểu `int` vỡ khi seed là chuỗi BLAKE2 | Chạy lại toàn bộ chuỗi `slice_builder → unsat_core`; `busy` từ 0 lên 21 cặp; seed dạng hex nạp được |
| `m1_logic/cnf_encoder.py` (yêu cầu 1.2, phần SAT) | *(điền tên)* | *(điền)* | *(điền)* | *(điền)* |
| `m1_logic/spec.md` (yêu cầu 1.1) | *(điền tên)* | *(điền)* | *(điền)* | *(điền)* |
| `m1_logic/logic_to_lp.md` (yêu cầu 1.3) | *(điền tên)* | *(điền)* | *(điền)* | *(điền)* |
| *(bổ sung dòng cho M2, M3, M4, M5 khi làm tới)* | | | | |

### Những phần KHÔNG do AI tạo ra

- **`DECISIONS.md`** — toàn bộ lý do chọn hướng, chọn hàm mục tiêu, chọn bộ DFA, chọn phép siết để tạo lát bất khả thỏa, và những phương án đã loại, đều do thành viên tự viết bằng lời của mình.
- **Lựa chọn lát dữ liệu và phép siết ở yêu cầu 1.2** — việc chọn ngày cao điểm nào, siết theo cách nào, và lập luận vì sao phép siết đó phản ánh một tình huống vận hành có thật.
- **Mọi con số trong báo cáo** — tái tạo từ `python run_all.py --seed $(cat data/seed.txt)` chạy trên dữ liệu thật và seed riêng của nhóm. Không có con số nào lấy từ `contracts/fake/`, vốn chỉ dùng để phát triển và kiểm thử.
- **`MEETINGS.md` và `CHECKPOINTS.md`** — ghi trực tiếp trong và sau mỗi buổi họp hằng tuần.

### Cách nhóm kiểm soát chất lượng đầu ra của AI

1. Mỗi file do AI sinh đều đi kèm phép kiểm chạy được, không chấp nhận khẳng định suông. Ví dụ `unsat_core.py` tự chứng minh tính tối thiểu của lõi bằng cách bỏ từng mệnh đề và xác nhận bài toán trở lại khả thỏa.
2. Mỗi pull request có một Reviewer bắt buộc, khác người viết.
3. Một đề xuất của AI đã bị kiểm chứng và **bác bỏ**: nghi vấn `cnf.extend()` nhận đối tượng `CNFPlus` sẽ lỗi — chạy thử cho thấy pysat xử lý được, nên không sửa.
4. Mọi thư viện đều ghim phiên bản trong `requirements.txt`.

### Điều nhóm hiểu rõ

Đề bài kiểm tra quyền tác giả bằng các cơ chế không phụ thuộc văn phong code: seed riêng của từng nhóm, lịch sử commit theo tuần có truy vết tác giả, `DECISIONS.md` viết bằng lời riêng, phần sửa app trực tiếp trong video, và các câu hỏi cá nhân trong đề thi giữa kỳ và cuối kỳ. Nhóm không tìm cách làm cho sản phẩm trông như không dùng AI; nhóm khai đúng và bảo đảm mỗi thành viên giải thích được phần mình đứng tên.

---

*Cập nhật lần cuối: 18/09/2026 · Mã nhóm: CO2011-261-A01-2551905*
