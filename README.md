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

**Công cụ:** Claude (Anthropic), qua giao diện Cowork.

**Thang mức độ:** 0 không dùng · 1 hỏi khái niệm, không lấy code · 2 người viết, AI rà soát ·
3 AI sinh nháp, người viết lại và kiểm chứng · 4 AI sinh phần lớn, người đọc hiểu, sửa và kiểm chứng bằng phép kiểm chạy được.

| Hạng mục / file | Người phụ trách | Mức | AI đã làm gì | Kiểm chứng bằng cách nào |
|---|---|---|---|---|
| Kế hoạch 14 tuần, bảng phân việc, bảng theo dõi | 2551918 Nguyễn Phong Phú | 4 | Đọc đề, đề xuất lịch mốc, chia 25 đầu việc theo mô hình Lead + Reviewer | Đối chiếu mốc và trọng số với §3, §6 của đề |
| `m1_logic/unsat_core.py` (1.2, phần UNSAT) | 2551918 Nguyễn Phong Phú | 4 | Sinh khung: CNF có selector literal, deletion-based MUS, chặt nhị phân tìm ngưỡng N\*, phép kiểm tính tối thiểu | Chạy trên lát ngày 28/05/2026 của dataset thật: N\* = 14/18, MUS 2 nhóm, 3/3 phép kiểm tối thiểu ĐẠT |
| `m1_logic/slice_builder.py` — suy `busy` từ lịch gốc | 2551905 Trần Anh Khôi | 3 | Phát hiện `busy` để rỗng làm mất ràng buộc H2, đề xuất suy từ lịch gốc qua quan hệ chồng giờ | `busy` từ 0 lên 15 cặp trên dữ liệu thật |
| `m1_logic/slice_builder.py` — đơn vị ca `(MS Ca thi, Cơ sở)`, đọc seed | 2551918 Nguyễn Phong Phú | 4 | Phát hiện một MS Ca thi mở đồng thời ở hai cơ sở nên `overlap` luôn rỗng; phát hiện `data/seed.txt` bị ghi UTF-16 | `overlap` từ 0 lên 1 cặp; seed đọc đúng 43003334 |
| `m1_logic/cnf_encoder.py` — sửa đường dẫn instance, chặn cấm-toàn-bộ khi thiếu `eligible` | 2551918 Nguyễn Phong Phú | 3 | Phát hiện script tìm `instance_slice.json` sai thư mục nên nhánh lát dữ liệu chưa từng chạy | Nhánh lát dữ liệu chạy ra SAT, 21 lượt gán |
| `m2_ilp/preprocess.py` (2.1, 2.6) | 2551909 Trần Bùi Bảo Long | (điền) | (điền) | (điền) |
| Áp quyết định D8: bỏ sinh `prefer` khỏi `m1_logic/slice_builder.py` | 2551918 Nguyễn Phong Phú | 4 | Đối chiếu D8 với code và phát hiện văn bản D8 khai đã xoá nhưng code vẫn sinh; sinh đoạn vá và chú thích lý do | `python tools/check_m2.py` đọc `slice_builder.py` bằng AST, xác nhận không còn định danh `prefer` trong code; `data/instance_slice.json` sinh lại không còn field đó |
| `run_all.py` — nối nhánh `stage m2` vào `m2_ilp/preprocess.py` | 2551918 Nguyễn Phong Phú | 4 | Phát hiện nhánh m2 còn là `pass  # TODO` nên `preprocess.py` không ai gọi; sinh lời gọi, thêm nhánh nạp lại instance khi chạy `--stage m2` một mình | `python run_all.py --seed 43003334` thoát 0 và đi qua M2; `--stage m2` khi thiếu `instance_slice.json` báo lỗi và thoát 1 |
| `tools/check_m2.py` — cổng tự kiểm M2 | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ script kiểm: schema 5 file JSON đầu ra, D8 một chủ sở hữu, phép thử tái lập (cùng seed giống hệt, đổi seed phải khác), tổng cột % trong ledger | Tự chạy trên repo: 7 mục ĐẠT; cố tình đổi seed để xác nhận phép thử tái lập thật sự bắt được lỗi |
| `m2_ilp/soft.py` (2.5, bản gốc) | 2551907 Trần Tuấn Kiệt | (điền) | (điền) | (điền) |
| `m2_ilp/model.py` (2.2–2.4 + 2.7) — mô hình CP-SAT lõi | 2551918 Nguyễn Phong Phú | 4 | Sinh toàn bộ khung: 108 biến nhị phân, 5 ràng buộc cứng dịch 1-1 từ `spec.md`, mục tiêu từ điển hai pha (min-max rồi L1 + phạt mềm), hàm `solve_week(params, lambdas)` để M4 tái dùng, và phần tự kiểm lại 5 ràng buộc cứng trên nghiệm | `python m2_ilp/model.py` → t\*=2, 21 lượt gán đúng tổng capacity, lệch L1=3, 5/5 ràng buộc cứng kiểm lại ĐẠT; chạy 3 lần ra nghiệm y hệt |
| `m2_ilp/soft.py` — vá trọng số, MaxLoad, thang nhân | 2551918 Nguyễn Phong Phú | 4 | Phát hiện bản gốc tự rút `rng.uniform` và **không làm tròn** nên dùng 0.7054693790735072 thay vì 0.71 của `make_seed.py`; phát hiện bỏ sót trọng số thứ ba và cứng `MaxLoad=3` trong khi dữ liệu có `max_load` theo từng người | `python m2_ilp/soft.py` so trực tiếp với đầu ra `tools/make_seed.py --weights`: [0.71, 1.62, 1.33] trùng từng số |
| `requirements.txt` — sửa ghim python-sat | 2551918 Nguyễn Phong Phú | 3 | Phát hiện `python-sat==1.8.dev13` không tồn tại trên PyPI nên `pip install -r requirements.txt` thất bại trên máy sạch; đề xuất 1.8.dev14 và ghi rõ bộ ghim nhắm Python 3.11–3.12 | `tools/check_m2.py` hỏi PyPI từng phiên bản: 9/9 gói tồn tại và có wheel cho cp311/cp312 |
| `tools/check_m2.py` — thêm 4 phép kiểm M2 | 2551918 Nguyễn Phong Phú | 4 | Sinh phép kiểm: trọng số phải trùng `make_seed.py`; không file nào trong `m2_ilp/` được tự rút `rng.uniform`; 5 ràng buộc cứng trên nghiệm; tính tất định qua hai lần giải; `requirements.txt` tồn tại thật trên PyPI | Tự chạy: 15 ĐẠT. Cố tình bỏ `round()` khỏi trọng số để xác nhận phép kiểm bắt được lỗi |
| `m1_logic/cnf_encoder.py` (bản gốc) | 2551907 Trần Tuấn Kiệt | (điền) | (điền) | (điền) |
| `m1_logic/spec.md` (1.1) | 2551909 Trần Bùi Bảo Long | (điền) | (điền) | (điền) |
| `m1_logic/bang_logic_to_lp.py` (1.3) | 2551920 Nguyễn Quang Phúc | (điền) | (điền) | (điền) |
| `m1_logic/slice_builder.py` (bản gốc) | 2551905 Trần Anh Khôi | (điền) | (điền) | (điền) |

**Không do AI tạo ra:** `DECISIONS.md`; việc chọn lát dữ liệu và phép siết ở 1.2 cùng lập luận vận hành đứng sau;
`MEETINGS.md`, `CHECKPOINTS.md`. Mọi con số trong báo cáo tái tạo từ `python run_all.py --seed $(cat data/seed.txt)` trên dữ liệu thật.

**Kiểm soát đầu ra AI:**
1. Mỗi file do AI sinh đi kèm phép kiểm chạy được (ví dụ `unsat_core.py` tự chứng minh tính tối thiểu của lõi).
2. Một đề xuất của AI bị bác sau khi kiểm chứng: nghi `cnf.extend()` nhận `CNFPlus` sẽ lỗi — chạy thử thì không lỗi, không sửa.
3. Một lỗi do chính AI đưa vào đã bị phát hiện và sửa: bản vá `normalize_seed` ban đầu âm thầm băm một seed hỏng thành số khác
   thay vì báo lỗi. Đã đổi thành dừng hẳn khi seed không phải số nguyên.
4. Quy ước của nhóm là mọi thay đổi đi qua pull request có Reviewer khác người viết. Thực tế tuần 3 (21–27/09) và tuần 4 (28/09–04/10) **chưa làm được**: vẫn push trực tiếp vào `main`, chưa có pull request nào. Ghi lại đúng như vậy thay vì khai theo quy ước.

