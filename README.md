# CO2011 SEM261 — Invigilator Assignment Problem (team repository)

Created from the course template with **"Use this template"** (not a fork). Keep this repo **private**
and add your class's instructor as a collaborator.

## First 15 minutes (Day 1)
1. Rename this repo to your **team ID**: `CO2011-261-<group>-<smallest student ID>`
   (`group ∈ {L, CC, A01, TN01}`), e.g. `CO2011-261-L-2252107`. Use it exactly everywhere.
2. Each member sets their git identity:
   `git config user.name "2252345 Nguyen Van A"` and `git config user.email "2252345@hcmut.edu.vn"`.
3. Generate your seed: `python tools/make_seed.py CO2011-261-L-2252107 > data/seed.txt`.
4. Read the assignment brief (on the LMS / course page); fill `MEETINGS.md` after your first meeting.

## Layout
```
run_all.py          # THE entry point: python run_all.py --seed $(cat data/seed.txt)
requirements.txt    # pin your versions
tools/make_seed.py  # seed + soft-weights from your team ID (do not edit)
data/               # dataset + seed.txt
m1_logic/  m2_ilp/  m3_automata/  m4_dynamics/  app/  report/
CHECKPOINTS.md  CONTRIBUTIONS.md  DECISIONS.md  MEETINGS.md
```

## Every week
Push a tagged commit `week-01 … week-14` with a `CHECKPOINTS.md` entry; tag milestones `m1 … m5`, then `submission`.
`python run_all.py --seed $(cat data/seed.txt)` must reproduce every number in your report from a clean clone.

Declare any AI-tool use in this README. Full rules, rubric (Appendix B), and the red **CRITICAL** items are in the brief.

## Khai báo sử dụng công cụ AI

> Theo §4 của đề: *"declare any AI-tool use in README.md"*. Đề cho phép dùng AI như công cụ;
> điều bị phạt là không khai báo. Mỗi thành viên tự điền và tự chịu trách nhiệm dòng của mình.

**Công cụ:** Claude (Anthropic), qua giao diện Cowork; Gemini/Antigravity trong giai đoạn rà soát cuối M2.

**Cách nhóm dùng AI ở giai đoạn rà soát M2:** AI được dùng để phân tích phần dự án do các thành viên trước đó làm, đánh giá tiến độ và độ tối ưu của code, lập kế hoạch hoàn thiện, soạn nháp phần lý do trong `DECISIONS.md` và điền các ô khai báo còn thiếu. Nhóm đọc lại, chạy lại `python tools/check_m2.py` và chịu trách nhiệm về nội dung.

**Thang mức độ:** 0 không dùng · 1 hỏi khái niệm, không lấy code · 2 người viết, AI rà soát ·
3 AI sinh nháp, người viết lại và kiểm chứng · 4 AI sinh phần lớn, người đọc hiểu, sửa và kiểm chứng bằng phép kiểm chạy được.

| Hạng mục / file | Người phụ trách | Mức | AI đã làm gì | Kiểm chứng bằng cách nào |
|---|---|---|---|---|
| Kế hoạch 14 tuần, bảng phân việc, bảng theo dõi | 2551918 Nguyễn Phong Phú | 4 | Đọc đề, đề xuất lịch mốc, chia 25 đầu việc theo mô hình Lead + Reviewer | Đối chiếu mốc và trọng số với §3, §6 của đề |
| `m1_logic/unsat_core.py` (1.2, phần UNSAT) | 2551918 Nguyễn Phong Phú | 4 | Sinh khung: CNF có selector literal, deletion-based MUS, chặt nhị phân tìm ngưỡng N\*, phép kiểm tính tối thiểu | Chạy trên lát ngày 28/05/2026 của dataset thật: N\* = 14/18, MUS 2 nhóm, 3/3 phép kiểm tối thiểu ĐẠT |
| `m1_logic/slice_builder.py` — suy `busy` từ lịch gốc | 2551905 Trần Anh Khôi | 3 | Phát hiện `busy` để rỗng làm mất ràng buộc H2, đề xuất suy từ lịch gốc qua quan hệ chồng giờ | `busy` từ 0 lên 15 cặp trên dữ liệu thật |
| `m1_logic/slice_builder.py` — đơn vị ca `(MS Ca thi, Cơ sở)`, đọc seed | 2551918 Nguyễn Phong Phú | 4 | Phát hiện một MS Ca thi mở đồng thời ở hai cơ sở nên `overlap` luôn rỗng; phát hiện `data/seed.txt` bị ghi UTF-16 | `overlap` từ 0 lên 1 cặp; seed đọc đúng 43003334 |
| `m1_logic/cnf_encoder.py` — sửa đường dẫn instance, chặn cấm-toàn-bộ khi thiếu `eligible` | 2551918 Nguyễn Phong Phú | 3 | Phát hiện script tìm `instance_slice.json` sai thư mục nên nhánh lát dữ liệu chưa từng chạy | Nhánh lát dữ liệu chạy ra SAT, 21 lượt gán |
| `m2_ilp/preprocess.py` (2.1, 2.6) | 2551909 Trần Bùi Bảo Long | 3 | AI sinh nháp phần trích I/J/capacity/busy/campus và sinh preference vị trí từ seed; người viết lại, chốt D8 (preprocess là chủ sở hữu duy nhất của Prefer(i,c)) | `python tools/check_m2.py`: schema 5 file JSON đạt, tái lập cùng seed giống hệt, đổi seed thì khác |
| Áp quyết định D8: bỏ sinh `prefer` khỏi `m1_logic/slice_builder.py` | 2551918 Nguyễn Phong Phú | 4 | Đối chiếu D8 với code và phát hiện văn bản D8 khai đã xoá nhưng code vẫn sinh; sinh đoạn vá và chú thích lý do | `python tools/check_m2.py` đọc `slice_builder.py` bằng AST, xác nhận không còn định danh `prefer` trong code; `data/instance_slice.json` sinh lại không còn field đó |
| `run_all.py` — nối nhánh `stage m2` vào `m2_ilp/preprocess.py` | 2551918 Nguyễn Phong Phú | 4 | Phát hiện nhánh m2 còn là đoạn giữ chỗ chưa cài (`pass`) nên `preprocess.py` không ai gọi; sinh lời gọi, thêm nhánh nạp lại instance khi chạy `--stage m2` một mình | `python run_all.py --seed 43003334` thoát 0 và đi qua M2; `--stage m2` khi thiếu `instance_slice.json` báo lỗi và thoát 1 |
| `tools/check_m2.py` — cổng tự kiểm M2 | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ script kiểm: schema 5 file JSON đầu ra, D8 một chủ sở hữu, phép thử tái lập (cùng seed giống hệt, đổi seed phải khác), tổng cột % trong ledger | Tự chạy trên repo: 7 mục ĐẠT; cố tình đổi seed để xác nhận phép thử tái lập thật sự bắt được lỗi |
| `m2_ilp/soft.py` (2.5, bản gốc) | 2551907 Trần Tuấn Kiệt | 3 | AI sinh nháp hàm phạt S1 (ưu tiên cơ sở) và S2 (giới hạn tải) theo `spec.md`; người viết lại và đối chiếu đặc tả | `python m2_ilp/soft.py` so trọng số với `make_seed.py`; `check_m2.py` kiểm S1, S2 trên nghiệm (0 vi phạm) |
| `m2_ilp/model.py` (2.2–2.4 + 2.7) — mô hình CP-SAT lõi | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ khung: 108 biến nhị phân, 5 ràng buộc cứng dịch 1-1 từ `spec.md`, mục tiêu từ điển hai pha (min-max rồi L1 + phạt mềm), hàm `solve_week(params, lambdas)` để M4 tái dùng, và phần tự kiểm lại 5 ràng buộc cứng trên nghiệm | `python m2_ilp/model.py` → t\*=2, 21 lượt gán đúng tổng capacity, lệch L1=3, 5/5 ràng buộc cứng kiểm lại ĐẠT; chạy 3 lần ra nghiệm y hệt |
| `m2_ilp/soft.py` — vá trọng số, MaxLoad, thang nhân | 2551918 Nguyễn Phong Phú | 4 | Phát hiện bản gốc tự rút `rng.uniform` và **không làm tròn** nên dùng 0.7054693790735072 thay vì 0.71 của `make_seed.py`; phát hiện bỏ sót trọng số thứ ba và cứng `MaxLoad=3` trong khi dữ liệu có `max_load` theo từng người | `python m2_ilp/soft.py` so trực tiếp với đầu ra `tools/make_seed.py --weights`: [0.71, 1.62, 1.33] trùng từng số |
| `requirements.txt` — sửa ghim python-sat | 2551918 Nguyễn Phong Phú | 3 | Phát hiện `python-sat==1.8.dev13` không tồn tại trên PyPI nên `pip install -r requirements.txt` thất bại trên máy sạch; đề xuất 1.8.dev14 và ghi rõ bộ ghim nhắm Python 3.11–3.12 | `tools/check_m2.py` hỏi PyPI từng phiên bản: 9/9 gói tồn tại và có wheel cho cp311/cp312 |
| `tools/check_m2.py` — thêm 4 phép kiểm M2 | 2551918 Nguyễn Phong Phú | 4 | Sinh phép kiểm: trọng số phải trùng `make_seed.py`; không file nào trong `m2_ilp/` được tự rút `rng.uniform`; 5 ràng buộc cứng trên nghiệm; tính tất định qua hai lần giải; `requirements.txt` tồn tại thật trên PyPI | Tự chạy: 15 ĐẠT. Cố tình bỏ `round()` khỏi trọng số để xác nhận phép kiểm bắt được lỗi |
| `m2_ilp/crosscheck_pulp.py` (2.8), `counterexample_lp_relax.py` (2.10) | 2551920 Nguyễn Quang Phúc | Chờ tác giả xác nhận | Tác giả tự cập nhật mức dùng AI; nhóm đã rà soát code và chạy kiểm chứng | `crosscheck_pulp.py` khớp 60/60 cấu hình; `counterexample_lp_relax.py` ra nghiệm lẻ x=0.5 với gap 0.5 |
| `m2_ilp/model.py` — sửa `AddAbsEquality`, gom `q` về một nguồn | 2551918 Nguyễn Phong Phú | 4 | Truy ra từ phép đối chứng của Phúc thất bại ở trial 11 rằng `AddAbsEquality(d, li − q)` không lấy trị tuyệt đối khi truyền biểu thức affine; sinh bản sửa dùng biến trung gian và hàm `tai_ly_tuong` | `crosscheck_pulp.py` 60/60 instance khớp; phép kiểm hồi quy trong `check_m2.py` cho tải 0, q=1 phải ra độ lệch 1 |
| `m2_ilp/baseline.py` + `benchmark.py` (2.9) | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ: trích lịch gốc từ `instance['baseline']`, một hàm chỉ số dùng chung cho cả hai lịch (Jain, Gini, L1, S1, S2), đo runtime 5 lần | 7 thắng · 1 hoà · 0 thua; `benchmark.py` thoát 1 nếu thua bất kỳ chỉ số nào |
| `m3_automata/strings_from_data.py` (3.1) | 2551920 Nguyễn Quang Phúc | Chờ tác giả xác nhận | Tác giả tự cập nhật mức dùng AI; nhóm đã rà soát code và chạy kiểm chứng | Sinh 73 chuỗi × 27 ngày tất định từ seed; hiệu chỉnh k=4 (95.9% thỏa), c=5 (97.3% thỏa) |
| `m3_automata/dfa_r1.json` … `dfa_r4.json` (3.1, 3.4a, bản gốc) | 2551907 Trần Tuấn Kiệt | Chờ tác giả xác nhận | Tác giả tự cập nhật mức dùng AI; R1, R2 giữ nguyên, R3, R4 được sinh lại bằng `build_dfas.py` | `build_dfas.py --check` kiểm 87.381 chuỗi dài ≤ 8 + 73 chuỗi thật |
| `m3_automata/pumping_proof.md`, `check_pumping.py` (3.4b, 3.4c) | 2551909 Trần Bùi Bảo Long | Chờ tác giả xác nhận | Tác giả tự cập nhật mức dùng AI; nhóm đã rà soát chứng minh và script | `check_pumping.py` qua 6/6 phép kiểm; `pumping_proof.md` 108 dòng |
| `m3_automata/build_dfas.py` — sinh lại R3, R4 từ tham số hiệu chỉnh | 2551918 Nguyễn Phong Phú | 4 | Phát hiện R3 gốc mã hóa sai luật và bị R2 bao trùm, R4 gốc dùng c=1 không từ dữ liệu; sinh bộ dựng DFA từ k, c và bộ vị từ brute-force độc lập | Khớp vị từ trên 87.381 chuỗi dài ≤ 8 + 73 chuỗi thật; `--check` chạy trên bản gốc bắt được cả hai lỗi |
| `m3_automata/product_minimize.py` (3.2) | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ: tích đồng bộ, Hopcroft, BFS trên tích để chứng minh tương đương, phép kiểm luật thừa | Tương đương chính xác + tối thiểu đã chứng minh; chạy trên DFA gốc báo đúng R3 thừa |
| `m3_automata/product_minimize.py` — bảng nhân chứng Myhill–Nerode (3.2), `DECISIONS.md` (D9–D15), rà soát M2–M3 | 2551905 Trần Anh Khôi | 3 | AI hỗ trợ cài đặt `bang_myhill_nerode` tìm hậu tố phân biệt ngắn nhất cho toàn bộ C(155,2)=11.935 cặp trạng thái và soạn nháp D9–D15 từ số liệu thực nghiệm; người đọc hiểu, kiểm tra và đối chiếu | `product_minimize.py` xác nhận 11.935/11.935 cặp có nhân chứng độ dài ≤ 10 (0 nhân chứng sai); `check_m1.py`, `check_m2.py`, `check_m3.py` đạt toàn bộ mục kỹ thuật |
| `m3_automata/regular_to_ilp.py` (3.3) | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ mô hình `AddAutomaton`; khi pha 2 bế tắc (90s, khoảng cách 36/34) đề xuất đồng nhất thức Σ\|tải − q\| = r + 2·thiếu hụt để đổi sang mục tiêu có cận dưới 0 | Mỗi lịch đầu ra chạy lại qua DFA tối thiểu và 4 DFA gốc; nhu cầu từng ngày khớp; cả hai pha OPTIMAL |
| `tools/check_m3.py` — cổng tự kiểm M3 | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ | Tự chạy: 8 mục kỹ thuật ĐẠT |
| `m1_logic/cnf_encoder.py` (bản gốc) | 2551907 Trần Tuấn Kiệt | 3 | AI sinh nháp bộ mã hóa CNF (H1, H2, H5 bằng seqcounter); người viết lại, sau đó Khôi viết lại phần lớn ở commit 7c3d296 | Chạy `run_all.py`: lát dữ liệu ra SAT, 21 lượt gán; phép kiểm tối thiểu của `unsat_core.py` đạt |
| `m1_logic/spec.md` (1.1) | 2551909 Trần Bùi Bảo Long | 3 | AI sinh nháp chữ ký vị từ và 5 ràng buộc cứng + 2 mềm; người viết lại và chốt | Mỗi ràng buộc trong `spec.md` có một phép kiểm tương ứng ở `model.py` (5/5 ràng buộc cứng tự kiểm trên nghiệm đạt) |
| `m1_logic/bang_logic_to_lp.py` (1.3) | 2551920 Nguyễn Quang Phúc | 3 | AI sinh nháp ánh xạ 6 dạng mệnh đề sang ràng buộc tuyến tính; người viết lại và đối chiếu | `run_all.py` in `[m1_lp] OK - LP khớp SAT` trên ví dụ mẫu |
| `m1_logic/slice_builder.py` (bản gốc) | 2551905 Trần Anh Khôi | 3 | AI sinh nháp phần cắt lát ngày cao điểm 28/05/2026 từ dataset; người viết lại | `run_all.py` sinh `data/instance_slice.json`: 18 giám thị, 6 ca, 21 lượt gán khớp lịch gốc |
| `m4_dynamics/calibrate.py` (4.1, Task 16) | 2551907 Trần Tuấn Kiệt | Chờ tác giả xác nhận | Tác giả tự cập nhật mức dùng AI; nhóm đã rà soát code và kiểm chứng tích hợp | `m4_dynamics/calibrate.py` xuất `data/processed/m4_params.json` (`a=0.760528, b=0.33925249, r=0.139692, F*=1.16666667`, sai số `2.2e-16`); `check_m4.py` đạt 18/18 |
| `m4_dynamics/recurrence.py` (4.1–4.2), `rolling_horizon.py` (4.3), `simulate.py` (4.3) | 2551905 Trần Anh Khôi (phối hợp Phúc, Long, Phú) | 4 | AI hỗ trợ thiết kế phương trình sai phân mệt mỏi $F_{i,n+1}$, chứng minh Lyapunov, hàm phản hồi $\lambda_i(F_{i,n})$ vượt ngưỡng đối ngẫu $(0.71, 1.95)$, và vòng lặp đóng $N=60$ kỳ kết nối `solve_week` của M2 | `python tools/check_m4.py`: spread tải tích lũy = 0 ca (Jain = 1.0000), sai số hội tụ $\max_i |F_{i,60}-F^*| = 2.33\times 10^{-6} < 10^{-3}$ |
| `m4_dynamics/perturbation.py` (4.4), `tools/check_m4.py`, `DECISIONS.md` (D16–D19) | 2551905 Trần Anh Khôi | 4 | AI hỗ trợ mô phỏng cú sốc nghỉ ốm đột xuất (`CB003`, `CB005`), phân tích độ nhạy $\gamma$, kiểm chứng chéo Xích Markov 3 trạng thái từ `m3_real_strings.json` và xây dựng cổng kiểm định `check_m4.py` | 5/5 ràng buộc cứng ĐẠT trong tâm chấn, hồi phục sau $\tau_{\text{rec}}=20 \le 21$ kỳ, Xích Markov ergodic ($\pi_{\text{Rest}}=0.7520 \approx a$, $\tau_{\text{mix}}=8$) |
| `app/app.py`, `app/views/plan.py`, `app/views/dynamics.py`, `app/README.md`, `run_all.py` (M5) | 2551905 Trần Anh Khôi (Lead M5) | 4 | AI hỗ trợ xây dựng giao diện Streamlit 3 tab nạp động từ các tệp JSON/PNG tiền tính toán (M1–M4) và tích hợp bộ giải kịch bản trực tiếp (What-if CP-SAT, DFA 155 trạng thái trace, Rolling-horizon simulator) | `python run_all.py --seed 43003334 --stage m5` và kiểm thử tải ứng dụng Streamlit |
| `m4_dynamics/identify.py`, `m4_dynamics/fairness_ablation.py`; rà soát trung thực M4 (`calibrate.py`, `recurrence.py`, `perturbation.py`); sửa M5 (`app/__init__.py`, chặn số mặc định viết tay); `tools/check_m4.py` mục 7 | 2551918 Nguyễn Phong Phú | 4 | AI sinh `identify.py` (logit có hiệu ứng ngày, profile likelihood của $a$, độ nhạy theo $a$) và `fairness_ablation.py` (so 4 luật phản hồi, tách $F_{\text{raw}}$ khỏi $F_{\text{eff}}$), phát hiện $F^* = \bar\ell$ đúng theo cách dựng, ma trận đếm Markov dựng sẵn và lỗi app không mở được; người kiểm lại từng kết luận trước khi đưa vào repo | `identify.py` chạy lại ra cùng số; `run_all.py --stage m5` báo lỗi khi gỡ `app/__init__.py`, `check_m4.py` mục 7 báo HỎNG khi thêm lại hằng số $a$ hay ma trận đếm dựng sẵn (đã thử cả ba); `streamlit run app/app.py` mở được cả 3 tab |

**Không do AI tạo ra:** việc chọn lát dữ liệu và phép siết ở 1.2 cùng lập luận vận hành đứng sau;
`MEETINGS.md`, `CHECKPOINTS.md`. **Có AI hỗ trợ:** phần lý do `[GT-1]`–`[GT-8]` trong `DECISIONS.md` do AI soạn nháp từ số liệu có trong repo (mức 3), cả nhóm đọc lại và chịu trách nhiệm. Mọi con số trong báo cáo tái tạo từ `python run_all.py --seed $(cat data/seed.txt)` trên dữ liệu thật.

**Kiểm soát đầu ra AI:**
1. Mỗi file do AI sinh đi kèm phép kiểm chạy được (ví dụ `unsat_core.py` tự chứng minh tính tối thiểu của lõi).
2. Một đề xuất của AI bị bác sau khi kiểm chứng: nghi `cnf.extend()` nhận `CNFPlus` sẽ lỗi — chạy thử thì không lỗi, không sửa.
3. Một lỗi do chính AI đưa vào đã bị phát hiện và sửa: bản vá `normalize_seed` ban đầu âm thầm băm một seed hỏng thành số khác
   thay vì báo lỗi. Đã đổi thành dừng hẳn khi seed không phải số nguyên.
4. Tuần 12: rà soát phát hiện một số kết luận M4 trình bày như kiểm chứng nhưng đúng theo cách dựng ("$F^*$ khớp $\bar\ell$", "$\pi_{\text{Rest}}$ khớp $a$"), cùng một ma trận đếm Markov dựng sẵn dùng làm fallback. Đã giữ nguyên giá trị nhưng sửa lời mô tả, bỏ số liệu dựng sẵn, và ghi giới hạn vào `m4_dynamics/README.md` §6. Một lỗi do chính AI đưa vào khi rà soát: bản đầu của `identify.py` lấy vùng tin cậy của $a$ là [min; max] các điểm được chấp nhận, ra kết luận sai "$a$ không xác định được, vùng phủ cả lưới"; xem biểu đồ hồ sơ hợp lý mới thấy vùng không liên thông và $a = 0.7605$ nằm ngoài vùng 95% — đã sửa thành hợp các đoạn.
5. Quy ước của nhóm là mọi thay đổi đi qua pull request có Reviewer khác người viết. Thực tế: tuần 3–4 vẫn push thẳng vào `main`. Từ tuần 7 nhóm có PR (#3 của Phúc, #4 của Long), nhưng các lần push ngày 23/10 của 2551918 đã **vượt luật bảo vệ nhánh** (GitHub ghi `Bypassed rule violations`). Ghi đúng như vậy.

