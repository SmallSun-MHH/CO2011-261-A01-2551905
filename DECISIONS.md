# Design decisions (your own words)

Moi muc: quyet dinh gi, VI SAO, va da loai phuong an nao.
Phan "Du kien" la so lieu chay ra tu code; phan "Ly do" tung nguoi tu viet.

## Module 1

### D1 — Don vi phan cong la (MS Ca thi, Co so), khong phai MS Ca thi
Du kien: ca `20260528_3` luc 13g00 dien ra o CA HAI co so. Neu gop lam mot thi
`overlap` va `busy` luon rong, tuc rang buoc cung H1 va H2 bien mat khoi mo hinh.
Sau khi tach: 6 ca, 1 cap chong gio, 15 cap ban.
Ly do (tu viet): [GT-1]

### D2 — Vi sao lat nguyen ban luon kha thoa
Du kien: `capacity[j]` bang dung so nguoi thuc te trong lich goc, nen lich goc
chinh la mot nhan chung SAT. Khong the cat lat bat ky roi mong ra UNSAT.
Ly do (tu viet): [GT-2]

### D3 — Phep siet de tao lat bat kha thoa
Du kien: thu hep tap giam thi truc. Nguong N* = 14/18. Loi toi thieu gom
`AVAIL[CB010 @ 20260528_3@Co so 2]` + `CAP_GE[20260528_3@Co so 2 can >= 14]`.
Tinh huong van hanh dung sau phep siet (tu viet): [GT-3]

### D4 — Busy suy tu lich goc; Eligible = moi cap
Du kien: dataset khong co du lieu chuyen mon, ma de chi cho phep mo phong
3 thu (preference vi tri, ca dem, trong so soft). Nen khong bia eligibility.
Ly do (tu viet): [GT-4]

### D5 — Cot "Nhiem vu" (CBCT / Thu ky / Truong HD) co tinh het vao capacity khong
Ly do (tu viet): [GT-5]

### D6 — Ma hoa suc chua bang seqcounter thay vi vet can
Du kien: at-most-2 vet can tren 18 nguoi can C(18,3) = 816 menh de cho MOT ca.
Ly do (tu viet): [GT-6]

### D7 — Vi sao co ca cnf_encoder.py lan unsat_core.py
Du kien: `solver.get_core()` tra ve MOT tap con bat kha thoa, khong bao dam
toi thieu. `unsat_core.py` co lai bang deletion-based MUS va chung minh:
bo bat ky menh de nao trong loi thi bai toan tro lai kha thoa.
Ly do (tu viet): [GT-7]

### D8 — Ai sinh location preference: M1 hay M2
Du kien: m1_logic/slice_builder.py ban dau tu sinh field 'prefer' bang seed,
trung voi task 'sinh preference vi tri 3 loai' duoc giao rieng cho M2
(m2_ilp/preprocess.py). Neu ca 2 cung sinh doc lap, se ra 2 gia tri Prefer(i,c)
khac nhau cho cung 1 nguoi giua M1 va M2 du dung chung seed_int (khac thu tu
rut so ngau nhien).
Quyet dinh: M2 (m2_ilp/preprocess.py) la CHU SO HUU DUY NHAT cua buoc sinh
Prefer(i,c). Da xoa doan sinh 'prefer' khoi m1_logic/slice_builder.py.
Ly do (tu viet): [GT-8]
