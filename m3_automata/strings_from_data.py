"""
Module 3 — yêu cầu 3.1: dựng chuỗi thật từ dữ liệu. Sắp xếp ca thi của từng giám thị theo
ngày/giờ thành chuỗi trên Σ = {M, A, N, -} (mỗi ngày một ký hiệu), tile thành nhiều tuần,
hiệu chỉnh k và c.

Người làm: 2551920 Nguyễn Quang Phúc
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SIGMA = ["M", "A", "N", "-"]
COL_DATE, COL_HOUR, COL_PERSON = "Ngày", "GIỜ", "MS của CÁN BỘ COI THI"
DAY_RULES = ("first", "last", "majority")


def parse_hour(text):
    m = re.fullmatch(r"\s*(\d{1,2})g(\d{2})\s*", text)
    if not m:
        raise ValueError(f"Không đọc được giờ: {text!r}")
    return int(m.group(1)) + int(m.group(2)) / 60


def load_sessions(csv_path):
    sessions, seen = [], set()
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            key = (r[COL_PERSON].strip(), dt.date.fromisoformat(r[COL_DATE].strip()[:10]),
                   parse_hour(r[COL_HOUR]))
            if key in seen:
                raise ValueError(f"Dòng trùng (người, ngày, giờ): {key}")
            seen.add(key)
            sessions.append(key)
    return sessions


def fit_slot_thresholds(hours):
    xs = sorted(set(hours))
    if len(xs) < 3:
        raise ValueError(f"Cần ít nhất 3 mốc giờ khác nhau để chia M/A/N, chỉ có {xs}")
    cuts = sorted(sorted(range(len(xs) - 1), key=lambda i: xs[i + 1] - xs[i], reverse=True)[:2])
    return [(xs[i] + xs[i + 1]) / 2 for i in cuts], xs


def slot_of(hour, thr):
    return "M" if hour < thr[0] else ("A" if hour < thr[1] else "N")


def day_symbol(hours, thr, rule):
    classes = [slot_of(h, thr) for h in sorted(hours)]
    if rule == "first":
        return classes[0]
    if rule == "last":
        return classes[-1]
    count = Counter(classes)
    best = max(count.values())
    return next(c for c in classes if count[c] == best)


def build_real_strings(sessions, thr, rule):
    d0 = min(d for _, d, _ in sessions)
    d1 = max(d for _, d, _ in sessions)
    n_days = (d1 - d0).days + 1
    per = defaultdict(lambda: defaultdict(list))
    for person, day, hour in sessions:
        per[person][(day - d0).days].append(hour)
    strings = {p: "".join(day_symbol(per[p][i], thr, rule) if i in per[p] else "-"
                          for i in range(n_days)) for p in sorted(per)}
    return strings, d0, d1, n_days


def loss_table(sessions, thr):
    per = defaultdict(list)
    for person, day, hour in sessions:
        per[(person, day)].append(hour)
    out = {}
    for rule in DAY_RULES:
        wrong = sum(sum(1 for h in hours if slot_of(h, thr) != day_symbol(hours, thr, rule))
                    for hours in per.values())
        out[rule] = {"phien_bi_bieu_dien_sai": wrong, "ty_le": round(wrong / len(sessions), 4)}
    return out


def tile(strings, cycles):
    return {p: s * cycles for p, s in strings.items()}


def n_work(s):
    return sum(c != "-" for c in s)


def max_window(s, w=7):
    return max(n_work(s[i:i + w]) for i in range(max(len(s) - w + 1, 1)))


def max_prefix_gap(s):
    run, best = 0, 0
    for c in s:
        run += (c == "M") - (c == "A")
        best = max(best, abs(run))
    return best


def max_run(s):
    return max((len(x) for x in re.split(r"-+", s)), default=0)


def share_table(values, candidates):
    n = len(values)
    return {v: round(sum(1 for x in values if x <= v) / n, 4) for v in candidates}


def smallest_meeting(table, accept):
    return next(v for v, share in table.items() if share >= accept)


def pooled_freq(strings):
    tot = Counter("".join(strings.values()))
    n = sum(tot.values())
    return {c: tot[c] / n for c in SIGMA}


def run(csv_path=None, out_dir=None, cycles=4, day_rule="majority", accept=0.90,
        c_from="real", quiet=False):
    csv_path = Path(csv_path) if csv_path else REPO / "data" / "dataset.csv"
    out = Path(out_dir) if out_dir else REPO / "data" / "processed"

    sessions = load_sessions(csv_path)
    thr, starts = fit_slot_thresholds([h for _, _, h in sessions])
    losses = loss_table(sessions, thr)
    real, d0, d1, n_days = build_real_strings(sessions, thr, day_rule)
    tiled = tile(real, cycles)
    horizon = n_days * cycles
    persons = sorted(real)
    n_person_days = len({(p, d) for p, d, _ in sessions})

    assert all(len(s) == n_days for s in real.values())
    assert all(len(s) == horizon for s in tiled.values())
    assert all(set(s) <= set(SIGMA) for s in list(real.values()) + list(tiled.values()))
    assert sum(n_work(s) for s in real.values()) == n_person_days
    f_real, f_tile = pooled_freq(real), pooled_freq(tiled)
    assert max(abs(f_real[ch] - f_tile[ch]) for ch in SIGMA) < 1e-12

    k_tab = share_table([max_window(real[p]) for p in persons], range(1, 8))
    k = smallest_meeting(k_tab, accept)
    gap_real = [max_prefix_gap(real[p]) for p in persons]
    gap_tile = [max_prefix_gap(tiled[p]) for p in persons]
    c_tab_real = share_table(gap_real, range(0, max(gap_real) + 1))
    c_tab_tile = share_table(gap_tile, range(0, max(gap_tile) + 1))
    c_real, c_tile = smallest_meeting(c_tab_real, accept), smallest_meeting(c_tab_tile, accept)
    c = c_real if c_from == "real" else c_tile

    run_tab = share_table([max_run(real[p]) for p in persons], range(1, max(max_run(real[p]) for p in persons) + 1))
    n_after = n_bad = 0
    for s in real.values():
        for i, ch in enumerate(s[:-1]):
            if ch == "N":
                n_after += 1
                n_bad += s[i + 1] != "-"
    per_week = [sum(n_work(x[i:i + 7]) for x in real.values()) for i in range(0, n_days, 7)]

    calib = {
        "tham_so": {"k": k, "c": c, "c_hieu_chinh_tren": c_from, "do_phu_chap_nhan": accept},
        "c_theo_chuoi_that": c_real,
        "c_theo_chuoi_tile": c_tile,
        "thong_ke_cho_DFA": {"so_ngay_lam_lien_tiep_toi_da_m": smallest_meeting(run_tab, accept),
                             "ca_N_khong_nghi_ngay_sau": n_bad, "tong_ca_N_co_ngay_sau": n_after},
        "bang_k_thuc": {str(x): v for x, v in k_tab.items()},
        "bang_c_thuc": {str(x): v for x, v in c_tab_real.items()},
        "bang_c_tile": {str(x): v for x, v in c_tab_tile.items()},
        "bang_ngay_lam_lien_tiep": {str(x): v for x, v in run_tab.items()},
        "chia_ca": {"mon_gio_bat_dau": starts, "nguong_M_A": thr[0], "nguong_A_N": thr[1]},
        "quy_tac_quy_doi_ngay": day_rule,
        "mat_mat_theo_quy_tac": losses,
        "tile": {"so_chu_ky": cycles, "so_ngay": horizon},
        "tai_theo_tuan_nguoi_ngay_lam_viec": per_week,
        "cua_so_that": {"bat_dau": str(d0), "ket_thuc": str(d1), "so_ngay": n_days,
                        "so_giam_thi": len(persons), "so_phien": len(sessions),
                        "so_nguoi_ngay_co_ca": n_person_days},
    }

    out.mkdir(parents=True, exist_ok=True)
    meta = {"alphabet": SIGMA, "day_rule": day_rule, "start": str(d0)}
    dump = lambda name, obj: (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    dump("m3_real_strings.json", {"meta": {**meta, "days": n_days}, "strings": real})
    dump("m3_tiled_strings.json", {"meta": {**meta, "days": horizon, "cycles": cycles}, "strings": tiled})
    dump("m3_calibration.json", calib)

    if not quiet:
        print(f"Dữ liệu: {len(sessions)} phiên, {len(persons)} giám thị, {n_days} ngày ({d0} → {d1})")
        print(f"Chia ca theo khoảng trống giờ bắt đầu {starts}: M < {thr[0]:.2f} <= A < {thr[1]:.2f} <= N")
        print("Mất mát khi quy đổi mỗi ngày về 1 ký hiệu (số phiên bị biểu diễn sai):")
        for r, v in losses.items():
            print(f"  {r:9s} {v['phien_bi_bieu_dien_sai']:4d} ({v['ty_le']:.1%})"
                  + ("   <- đang dùng" if r == day_rule else ""))
        print(f"Chuỗi thật: {dict(Counter(''.join(real.values())))}  (ngày làm việc = {n_person_days})")
        print(f"Tải theo tuần (người-ngày làm việc, tuần 1→): {per_week}")
        print(f"Tile: lặp nguyên cửa sổ {n_days} ngày x {cycles} = {horizon} ngày")
        print(f"k (≤ k ngày làm trong 7 ngày, ≥ {accept:.0%} giám thị đạt) = {k}")
        print("    giám thị đạt theo k:", {x: f"{v:.0%}" for x, v in k_tab.items()})
        print(f"c (|#M-#A| ≤ c tại mọi tiền tố, hiệu chỉnh trên chuỗi {c_from}, ≥ {accept:.0%} đạt) = {c}"
              f"   [thật: {c_real}, tile: {c_tile}]")
        print("    trên chuỗi thật:", {x: f"{v:.0%}" for x, v in c_tab_real.items()})
        print(f"Thống kê cho DFA: ngày làm liên tiếp tối đa m = {calib['thong_ke_cho_DFA']['so_ngay_lam_lien_tiep_toi_da_m']}; "
              f"ca N không được nghỉ ngay sau: {n_bad}/{n_after}")
        print(f"Đã ghi 3 file m3_*.json vào {out}")
    return {"real": real, "tiled": tiled, "calibration": calib}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dựng chuỗi thật, tile, hiệu chỉnh k và c (M3, req 3.1)")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--cycles", type=int, default=4)
    ap.add_argument("--day-rule", choices=DAY_RULES, default="majority")
    ap.add_argument("--accept", type=float, default=0.90)
    ap.add_argument("--c-from", choices=("real", "tile"), default="real")
    a = ap.parse_args(argv)
    run(a.csv, a.out_dir, a.cycles, a.day_rule, a.accept, a.c_from)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
