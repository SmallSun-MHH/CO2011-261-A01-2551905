# Contribution ledger (who did what) + signed % table

Cot "Primary owner" lay tu lich su git da gom danh tinh bang .mailmap.
Cot "%" va "Signature" do tung thanh vien tu dien va tu ky.

## Module 1 — Logic (yeu cau 1.1–1.3)

| Req | File | Primary owner | Reviewer | Ghi chu |
|---|---|---|---|---|
| 1.1 | `m1_logic/spec.md` | 2551909 Tran Bui Bao Long | 2551907 Tran Tuan Kiet | Chu ky vi tu, 5 rang buoc cung + 2 mem |
| 1.2 | `m1_logic/slice_builder.py` | 2551905 Tran Anh Khoi | 2551918 Nguyen Phong Phu | Cat lat ngay cao diem 28/05/2026 |
| 1.2 | `m1_logic/cnf_encoder.py` | 2551907 Tran Tuan Kiet | 2551905 Tran Anh Khoi | **Ban dau do Kiet viet (commit 330c4c7, e3eaa44); Khoi viet lai phan lon tai 7c3d296** |
| 1.2 | `m1_logic/unsat_core.py` | 2551918 Nguyen Phong Phu | 2551905 Tran Anh Khoi | MUS kieu deletion-based + phep chung minh tinh toi thieu |
| 1.3 | `m1_logic/bang_logic_to_lp.py` | 2551920 Nguyen Quang Phuc | 2551909 Tran Bui Bao Long | Anh xa 6 dang menh de sang rang buoc tuyen tinh |
| — | `run_all.py`, `tools/check_m1.py`, `.mailmap` | 2551918 Nguyen Phong Phu | 2551920 Nguyen Quang Phuc | Ha tang tai tao va tu kiem |

## Module 2 — LP / ILP (yeu cau 2.1–2.10)

| Req | File | Primary owner | Reviewer | Ghi chu |
|---|---|---|---|---|
| 2.1, 2.6 | `m2_ilp/preprocess.py` | 2551909 Tran Bui Bao Long | 2551905 Tran Anh Khoi | Trich I/J/capacity/busy/campus; chu so huu duy nhat Prefer(i,c) — D8 |
| 2.2–2.4, 2.7 | `m2_ilp/model.py` | 2551918 Nguyen Phong Phu | 2551905 Tran Anh Khoi | CP-SAT tu dien hai pha; sua loi AddAbsEquality 23/10 |
| 2.5 | `m2_ilp/soft.py` | 2551907 Tran Tuan Kiet | 2551905 Tran Anh Khoi | Ban goc cua Kiet; Phu va trong so lam tron va MaxLoad (5f18d1b) |
| 2.8 | `m2_ilp/crosscheck_pulp.py` | 2551920 Nguyen Quang Phuc | 2551905 Tran Anh Khoi | Doi chung PuLP; chinh no bat duoc loi AddAbsEquality |
| 2.9 | `m2_ilp/baseline.py`, `benchmark.py` | 2551918 Nguyen Phong Phu | 2551905 Tran Anh Khoi | **Theo phan viec la task cua Khoi (TV5)**; Phu lam 23/10 khi qua han 08/10; Khoi ra soat va kiem chung |
| 2.10 | `m2_ilp/counterexample_lp_relax.py` | 2551920 Nguyen Quang Phuc | 2551905 Tran Anh Khoi | Phan vi du LP-relaxation x = 0.5 |

## Module 3 — Automata (yeu cau 3.1–3.4)

| Req | File | Primary owner | Reviewer | Ghi chu |
|---|---|---|---|---|
| 3.1 | `m3_automata/strings_from_data.py` | 2551920 Nguyen Quang Phuc | 2551905 Tran Anh Khoi | Chuoi that 73 x 27 ngay; hieu chinh k = 4, c = 5 |
| 3.1, 3.4a | `m3_automata/dfa_r1.json`, `dfa_r2.json` | 2551907 Tran Tuan Kiet | 2551905 Tran Anh Khoi | Dung, giu nguyen |
| 3.1, 3.4a | `m3_automata/dfa_r3.json`, `dfa_r4.json` | 2551907 Tran Tuan Kiet (ban goc), 2551918 Nguyen Phong Phu (sinh lai) | 2551905 Tran Anh Khoi | Ban goc sai luat (R3) va sai tham so (R4); sinh lai 08/11 bang `build_dfas.py` |
| 3.2 | `m3_automata/product_minimize.py` | 2551918 Nguyen Phong Phu, 2551905 Tran Anh Khoi | 2551905 Tran Anh Khoi | **Task 13**: Phu viet khung tich + Hopcroft + kiem luat thua (08/11); Khoi bo sung bang nhan chung hau to phan biet Myhill-Nerode cho 11.935 cap trang thai (08/11) |
| 3.3 | `m3_automata/regular_to_ilp.py` | 2551918 Nguyen Phong Phu | 2551905 Tran Anh Khoi | Task 14 |
| 3.4b, 3.4c | `m3_automata/pumping_proof.md`, `check_pumping.py` | 2551909 Tran Bui Bao Long | 2551905 Tran Anh Khoi | Giao voi M*A* roi bo de bom |
| — | `tools/check_m2.py`, `tools/check_m3.py` | 2551918 Nguyen Phong Phu, 2551905 Tran Anh Khoi | 2551905 Tran Anh Khoi | Cong tu kiem M2, M3 (Khoi bo sung kiem bang Myhill-Nerode trong `check_m3.py`) |

Cot Reviewer ghi nguoi DA THUC SU doc code, chay kiem chung va duyet (Khoi `2551905` ra soat toan bo M2–M3 ngay 08/11/2026).

## Ghi chu ve danh tinh git

Truoc 20/09/2026 mot so commit mang danh tinh khong dung quy dinh cua de bai.
Tat ca da duoc anh xa trong `.mailmap`, **khong viet lai lich su**:

| Danh tinh trong commit | La ai |
|---|---|
| `Sun LowShine <phu.nguyengriffin@hcmut.edu.vn>` | 2551918 Nguyen Phong Phu |
| `JunWinpro <jundeptrainhat@gmail.com>` | 2551905 Tran Anh Khoi |
| `2252345 Nguyen Van A <2252345@hcmut.edu.vn>` | 2551905 Tran Anh Khoi (dat nham danh tinh vi du trong README mau) |
| Cac email dang ten cua Khoi, Kiet, Long, Phuc | Email truong cua chinh ho |

Tu 20/09/2026 moi thanh vien dung `MSSV Ho Ten <MSSV@hcmut.edu.vn>`.

## Bang % dong gop (tung nguoi tu dien va ky)

| Member | Contribution % | Signature |
|---|---|---|
| 2551905 Tran Anh Khoi | 20% |Khoi|
| 2551907 Tran Tuan Kiet | 20% | Kiet |
| 2551909 Tran Bui Bao Long | 20% | Long  |
| 2551918 Nguyen Phong Phu | 20% | Phu |
| 2551920 Nguyen Quang Phuc | 20% | Phuc |
