# Module 3 — Automata (yêu cầu 3.1 – 3.4)

Chạy cả module: `python run_all.py --seed $(cat data/seed.txt) --stage m3`
Tự kiểm: `python tools/check_m3.py`

## Bảng chữ cái và bốn luật

Σ = {M, A, N, -} — mỗi ngày một ký hiệu: ca sáng / chiều / đêm / nghỉ.

| Luật | Nội dung | Tham số | Nguồn tham số | DFA |
|---|---|---|---|---|
| R1 | không quá m ngày làm liên tiếp | m = 2 | quyết định chính sách của nhóm (03/09) | `dfa_r1.json` — 4 trạng thái |
| R2 | làm ca N thì hôm sau phải nghỉ | — | — | `dfa_r2.json` — 3 trạng thái |
| R3 | tối đa k ca trong mọi cửa sổ 7 ngày | k = 4 | hiệu chỉnh từ dữ liệu thật (≥ 90% giám thị thỏa) | `dfa_r3.json` — 58 trạng thái |
| R4 | \|#M − #A\| ≤ c tại mọi tiền tố | c = 5 | hiệu chỉnh từ dữ liệu thật (≥ 90% giám thị thỏa) | `dfa_r4.json` — 12 trạng thái |

Cả bốn là DFA **an toàn**: mọi trạng thái trừ `trap` đều chấp nhận, `trap` hút. Schema mỗi file đúng 5 khóa
`states, alphabet, start, accepting, transitions`, DFA đầy đủ.

## File

| Yêu cầu | File | Việc |
|---|---|---|
| 3.1 | `strings_from_data.py` | dựng chuỗi lịch thật của 73 giám thị × 27 ngày từ dataset, hiệu chỉnh k và c |
| 3.1, 3.4a | `dfa_r1.json` … `dfa_r4.json` | bốn DFA |
| 3.1, 3.4a | `build_dfas.py` | sinh R3, R4 từ tham số hiệu chỉnh; kiểm cả 4 khớp vị từ brute-force trên mọi chuỗi dài ≤ 8 và mọi chuỗi thật |
| 3.2 | `product_minimize.py` → `dfa_product_min.json` | tích, tối thiểu hóa Hopcroft, chứng minh tương đương và tối thiểu, phát hiện luật thừa |
| 3.3 | `regular_to_ilp.py` | `AddAutomaton` của CP-SAT: lịch 27 ngày phải được DFA tối thiểu chấp nhận |
| 3.4b, 3.4c | `pumping_proof.md`, `check_pumping.py` | L = {#M = #A} không chính quy: giao với M\*A\* rồi bổ đề bơm |

## Kết quả (tái tạo được, seed 43003334)

**3.2** — 8,352 trạng thái lý thuyết → 3,108 đạt tới → **155 sau tối thiểu**
(154 chấp nhận + 1 bẫy). Tương đương với DFA tích được chứng minh bằng BFS trên tích (không lấy mẫu);
tính tối thiểu được chứng minh theo hai cách độc lập: (i) chạy lại Hopcroft không gộp thêm được gì, và (ii) lập bảng hậu tố phân biệt ngắn nhất theo định lý Myhill–Nerode cho toàn bộ $\binom{155}{2} = 11{,}935$ cặp trạng thái phân biệt (mọi cặp đều có nhân chứng $z \in \Sigma^*$ độ dài $\le 10$ sao cho đúng một trong hai trạng thái dẫn tới chấp nhận; ba cặp cần hậu tố dài nhất 10 là `(s56, s57)` với `--MM-MM--M`, `(s56, s63)` với `--AA-AA--A`, `(s57, s63)` với `--M--MM-MM`). Cả 4 luật đều cần thiết — mỗi luật có một chuỗi
chỉ mình nó chặn: R1 `MMM`, R2 `NM`,
R3 `MM-MM-M`, R4 `MM-MM--MM`.

**3.3** — phủ đúng 472 ngày-công của lịch thật, từng ngày, từng ca:

| | lịch thật | ILP + DFA |
|---|---|---|
| giám thị vi phạm R1 / R2 / R3 / R4 | 28 / 4 / 3 / 2 | 0 / 0 / 0 / 0 |
| giám thị thỏa cả 4 luật | 42 / 73 | 73 / 73 |
| tải lớn nhất (ngày làm) | 9 | **7** (tối ưu, đã chứng minh) |
| khoảng tải | 7 | 1 |
| lệch L1 quanh q = 6 | 86 | **34** (chạm cận dưới, đã chứng minh) |

Đơn giản hóa đã nêu: mô hình 3.3 coi mọi giám thị làm được mọi ca, và được xếp lại người tự do.

## Một lỗi đã được bắt, nên ghi vào báo cáo

Bản DFA viết tay đầu tiên (commit `4fe71a8`) có `dfa_r3` mã hóa "không hai ca N liền nhau" thay vì cửa sổ 7 ngày,
và `dfa_r4` dùng c = 1 tự đặt (chỉ 7/73 giám thị thật thỏa). Phép kiểm luật thừa trong `product_minimize.py` chạy trên bản đó
báo **R3 THỪA** — L(R2) ⊆ L(R3 cũ), nên tích thực chất chỉ còn 3 luật và tối thiểu chỉ còn 10 trạng thái. Đã sinh lại R3, R4
bằng `build_dfas.py` từ tham số hiệu chỉnh; R1, R2 giữ nguyên vì đúng.
