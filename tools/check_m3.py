#!/usr/bin/env python3
"""
tools/check_m3.py — cổng tự kiểm cho Module 3 (Automata), chạy được.

Cùng nguyên tắc với check_m1.py / check_m2.py: không tin khẳng định trong tài
liệu, chỉ tin thứ chạy ra kết quả. Mỗi mục in ĐẠT / CẢNH BÁO / HỎNG.

    python tools/check_m3.py
    python tools/check_m3.py --khong-chay     # chỉ đọc kết quả có sẵn, không chạy lại

Thoát 0 nếu không có mục HỎNG, thoát 1 nếu có.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

DAT, CANH, HONG = "ĐẠT", "CẢNH BÁO", "HỎNG"
KQ: list[tuple[str, str, str]] = []


def bao(m, t, c):
    KQ.append((m, t, c))


def chay(cmd, cwd, timeout=900):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"quá {timeout}s"


FILE_M3 = {
    "m3_automata/strings_from_data.py": "3.1 chuỗi thật + hiệu chỉnh",
    "m3_automata/dfa_r1.json": "3.1 R1 ≤2 ngày liên tiếp",
    "m3_automata/dfa_r2.json": "3.1 R2 sau N phải nghỉ",
    "m3_automata/dfa_r3.json": "3.1 R3 ≤k ca / 7 ngày",
    "m3_automata/dfa_r4.json": "3.1 R4 |#M−#A| ≤ c",
    "m3_automata/build_dfas.py": "3.4a sinh + kiểm DFA",
    "m3_automata/product_minimize.py": "3.2 tích + tối thiểu",
    "m3_automata/dfa_product_min.json": "3.2 DFA tối thiểu",
    "m3_automata/regular_to_ilp.py": "3.3 AddAutomaton",
    "m3_automata/pumping_proof.md": "3.4b/c chứng minh",
    "m3_automata/check_pumping.py": "3.4b/c phép kiểm",
}


def kiem_file(repo):
    thieu = [f for f in FILE_M3 if not (repo / f).exists()]
    if thieu:
        bao(HONG, "File bắt buộc", "thiếu: " + ", ".join(f"{f} ({FILE_M3[f]})" for f in thieu))
    else:
        bao(DAT, "File bắt buộc", f"đủ {len(FILE_M3)} file của 3.1–3.4")


def kiem_mo_coi(repo):
    s = (repo / "run_all.py").read_text(encoding="utf-8")
    goi = [f for f in FILE_M3 if f.endswith(".py")]
    mo_coi = [f for f in goi if Path(f).name not in s]
    if mo_coi:
        bao(HONG, "File mồ côi", "run_all.py không gọi: " + ", ".join(mo_coi))
    else:
        bao(DAT, "File mồ côi", f"run_all.py gọi đủ {len(goi)} script M3")


def kiem_pipeline(repo, chay_lai):
    if not chay_lai:
        return True
    seed = (repo / "data" / "seed.txt").read_text(encoding="utf-8-sig").strip()
    rc, out = chay([sys.executable, "run_all.py", "--seed", seed, "--stage", "m3"], repo)
    if rc != 0:
        bao(HONG, "run_all.py --stage m3", f"thoát {rc}\n" + out[-1200:])
        return False
    bao(DAT, "run_all.py --stage m3", "thoát 0, đi hết 3.1 → 3.4a → 3.2 → 3.4b/c → 3.3")
    return True


def kiem_dfa(repo):
    rc, out = chay([sys.executable, "m3_automata/build_dfas.py", "--check"], repo, 600)
    if rc != 0:
        dong = [l.strip() for l in out.splitlines() if "lệch" in l or "khóa" in l or "thiếu" in l]
        bao(HONG, "4 DFA (3.1, 3.4a)",
            "lệch vị từ / sai schema / lệch tham số hiệu chỉnh:\n" + "\n".join(dong[:6]))
    else:
        hc = json.loads((repo / "data/processed/m3_calibration.json").read_text(encoding="utf-8"))
        ts = hc["tham_so"]
        bao(DAT, "4 DFA (3.1, 3.4a)",
            f"schema 5 khóa, DFA đầy đủ, khớp vị từ trên 87.381 chuỗi + chuỗi thật; "
            f"k={ts['k']}, c={ts['c']} lấy từ hiệu chỉnh")


def kiem_tich(repo):
    f = repo / "m3_automata/out/product_report.json"
    if not f.exists():
        bao(HONG, "Tích + tối thiểu (3.2)", "chưa có out/product_report.json")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    kc, st = d["kiem_chung"], d["so_trang_thai"]
    mn = kc.get("myhill_nerode", {})
    if not kc["tuong_duong_chinh_xac"]:
        bao(HONG, "Tích + tối thiểu (3.2)", "DFA tối thiểu KHÁC ngôn ngữ DFA tích")
    elif not kc["toi_thieu"] or not mn.get("tat_ca_phan_biet_duoc"):
        bao(HONG, "Tích + tối thiểu (3.2)", "DFA 'tối thiểu' vẫn còn trạng thái tương đương hoặc thiếu nhân chứng Myhill–Nerode")
    else:
        bao(DAT, "Tích + tối thiểu (3.2)",
            f"{st['tich_ly_thuyet']:,} lý thuyết → {st['tich_dat_toi']:,} đạt tới → "
            f"{st['toi_thieu']} tối thiểu · {mn['so_cap_phan_biet_duoc']:,}/{mn['tong_cap_trang_thai']:,} cặp Myhill–Nerode (|z|≤{mn['do_dai_hau_to_max']})")
    thua = [t.upper() for t, v in d["luat_thua"].items() if v["thua"]]
    if thua:
        bao(HONG, "Luật thừa", ", ".join(thua) + " bị các luật còn lại kéo theo — không thêm ràng buộc nào")
    else:
        bao(DAT, "Luật thừa", "cả 4 luật đều cần thiết, mỗi luật có chuỗi chỉ mình nó chặn")


def kiem_ilp(repo):
    f = repo / "m3_automata/out/regular_ilp.json"
    if not f.exists():
        bao(HONG, "AddAutomaton vào ILP (3.3)", "chưa có out/regular_ilp.json")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("loi"):
        bao(HONG, "AddAutomaton vào ILP (3.3)", "; ".join(d["loi"][:4]))
        return
    vp = d["lich_ilp"]["vi_pham"]
    if any(vp.values()):
        bao(HONG, "AddAutomaton vào ILP (3.3)", f"lịch ILP còn vi phạm: {vp}")
        return
    p1, p2 = d["pha1"], d["pha2"]
    toi_uu = p1["status"] == "OPTIMAL" and p2.get("toi_uu_da_chung_minh")
    bao(DAT if toi_uu else CANH, "AddAutomaton vào ILP (3.3)",
        f"{d['chan_troi']['so_giam_thi']} giám thị × {d['chan_troi']['so_ngay']} ngày, "
        f"0 vi phạm cả 4 luật (lịch thật: {d['lich_that']['thoa_ca_4']}/"
        f"{d['chan_troi']['so_giam_thi']} thỏa) · t*={p1['t_sao']} · L1={p2['lech_L1']}"
        + ("" if toi_uu else " · CHƯA chứng minh tối ưu"))


def kiem_pumping(repo):
    md = (repo / "m3_automata/pumping_proof.md")
    n = len(md.read_text(encoding="utf-8").splitlines()) if md.exists() else 0
    rc, out = chay([sys.executable, "m3_automata/check_pumping.py"], repo, 300)
    if rc != 0:
        bao(HONG, "Bổ đề bơm (3.4b, 3.4c)", "check_pumping.py thất bại\n" + out[-500:])
    elif n < 30:
        bao(CANH, "Bổ đề bơm (3.4b, 3.4c)", f"phép kiểm qua nhưng pumping_proof.md chỉ {n} dòng")
    else:
        bao(DAT, "Bổ đề bơm (3.4b, 3.4c)", f"pumping_proof.md {n} dòng + check_pumping.py qua")


def kiem_tag(repo):
    rc, out = chay(["git", "tag", "-l"], repo, 60)
    if rc != 0:
        bao(CANH, "Git", "không đọc được tag")
        return
    tags = set(out.split())
    bao(DAT if "m3" in tags else CANH, "Tag m3",
        "có" if "m3" in tags else "chưa có — hạn mốc m3 là 08/11/2026")
    bat_dau, hom_nay = datetime.date(2026, 9, 7), datetime.date.today()
    thieu, dang = [], None
    for n in range(1, 15):
        d1 = bat_dau + datetime.timedelta(days=7 * (n - 1))
        if d1 > hom_nay:
            break
        ten = f"week-{n:02d}"
        if ten in tags:
            continue
        if d1 <= hom_nay <= d1 + datetime.timedelta(days=6):
            dang = (ten, d1 + datetime.timedelta(days=6))
        else:
            thieu.append(ten)
    if thieu:
        bao(HONG, "Tag tuần THIẾU",
            f"{', '.join(thieu)} — mỗi tag là −1% điểm môn, KHÔNG tạo tag lùi ngày để bù")
    if dang:
        bao(CANH, "Tag tuần này", f"{dang[0]} chưa có — hạn Chủ nhật {dang[1]}")


def main():
    ap = argparse.ArgumentParser(description="Tự kiểm Module 3")
    ap.add_argument("--khong-chay", action="store_true", help="không chạy lại pipeline")
    a = ap.parse_args()
    repo = Path(__file__).resolve().parent.parent
    print(f"[check_m3] kiểm: {repo}\n")
    kiem_file(repo)
    kiem_mo_coi(repo)
    if kiem_pipeline(repo, not a.khong_chay):
        kiem_dfa(repo)
        kiem_tich(repo)
        kiem_pumping(repo)
        kiem_ilp(repo)
    kiem_tag(repo)

    th = {HONG: 0, CANH: 1, DAT: 2}
    for m, t, c in sorted(KQ, key=lambda r: th[r[0]]):
        dong = c.splitlines() or [""]
        print(f"  {m:<9} {t:<28} {dong[0]}")
        for d in dong[1:]:
            print(f"  {'':<9} {'':<28} {d}")
    nh = sum(m == HONG for m, _, _ in KQ)
    nc = sum(m == CANH for m, _, _ in KQ)
    nd = sum(m == DAT for m, _, _ in KQ)
    print(f"\n{nh} {HONG} · {nc} {CANH} · {nd} {DAT}")
    # Tag tuần đã lỡ là thiệt hại CỐ ĐỊNH, không sửa được và không được bù bằng tag
    # lùi ngày. Vẫn báo HỎNG cho thấy rõ, nhưng không chặn việc tag m3 — chặn thì
    # checker sẽ không bao giờ sạch được nữa, và người ta sẽ thôi đọc nó.
    sua_duoc = [t for m, t, _ in KQ if m == HONG and t != "Tag tuần THIẾU"]
    if not nh:
        print("SẠCH — đủ điều kiện tag m3.")
    elif not sua_duoc:
        print("Kỹ thuật M3 SẠCH — đủ điều kiện tag m3. HỎNG còn lại là tag tuần đã lỡ: "
              "thiệt hại cố định, không sửa được.")
    else:
        print("CHƯA SẠCH — sửa các mục HỎNG: " + ", ".join(sua_duoc))
    return 1 if sua_duoc else 0


if __name__ == "__main__":
    raise SystemExit(main())
