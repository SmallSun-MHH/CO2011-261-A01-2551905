# m1_logic — Module 1: Logic (yeu cau 1.1–1.3)

Chay toan bo Module 1 tu goc repo:

```
python run_all.py --seed $(cat data/seed.txt) --stage m1
```

| File | Req | Nguoi phu trach | Viec |
|---|---|---|---|
| `spec.md` | 1.1 | 2551909 Tran Bui Bao Long | Chu ky vi tu, 5 rang buoc cung + 2 mem dang bac nhat |
| `slice_builder.py` | 1.2 | 2551905 Tran Anh Khoi | Cat lat ngay cao diem -> `data/instance_slice.json` |
| `cnf_encoder.py` | 1.2 | 2551907 Tran Tuan Kiet / 2551905 Tran Anh Khoi | Ma hoa CNF, giai toy instance va lat du lieu |
| `unsat_core.py` | 1.2 | 2551918 Nguyen Phong Phu | Loi bat kha thoa TOI THIEU + phep chung minh |
| `bang_logic_to_lp.py` | 1.3 | 2551920 Nguyen Quang Phuc | Anh xa menh de sang rang buoc tuyen tinh 0/1 |
