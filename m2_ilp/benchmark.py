#!/usr/bin/env python3
"""
m2_ilp/benchmark.py — Module 2, yêu cầu 2.9 (phần 2/2)
=====================================================================
So nghiệm của mô hình CP-SAT với lịch GỐC, trên cùng một bộ chỉ số, cùng một
instance, cùng một seed — rồi kết luận thắng hay thua ở từng chỉ số.

Nguyên tắc để con số nói được điều gì:
  1. Mọi chỉ số tính bằng `baseline.chi_so`, MỘT hàm duy nhất cho cả hai lịch.
     Hai hàm riêng thì rất dễ đo hai thứ khác nhau rồi tự tuyên bố mình hơn.
  2. Lịch gốc phải được kiểm lại bằng chính 5 ràng buộc cứng của ta. Nếu chính
     nó cũng vi phạm thì phải nói ra, không giấu — và khi đó "thắng" có nghĩa
     khác hẳn.
  3. Runtime đo nhiều lần lấy trung vị, vì một lần chạy nói lên rất ít.
  4. Chỉ số nào HOÀ thì ghi là hoà. Không gộp vào cột thắng.

Thoát 0 khi nghiệm không thua baseline ở bất kỳ chỉ số nào và thắng ít nhất
một chỉ số; thoát 1 nếu thua — để `run_all.py` và CI dừng ngay.

Cách dùng:
    python m2_ilp/benchmark.py
    python m2_ilp/benchmark.py --lap 7
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from m2_ilp.baseline import chi_so, trich_baseline
from m2_ilp.model import build_params, solve_week

# (khóa, nhãn, hướng tốt)  — "min" nghĩa là nhỏ hơn thì tốt hơn
CHI_SO_SO_SANH = [
    ("tai_lon_nhat",     "tải lớn nhất",        "min"),
    ("khoang_tai",       "khoảng tải",          "min"),
    ("lech_L1_quanh_q",  "lệch L1 quanh q",     "min"),
    ("jain",             "Jain (càng cao càng đều)", "max"),
    ("gini",             "Gini (càng thấp càng đều)", "min"),
    ("vi_pham_S1_loc",   "vi phạm S1 (cơ sở)",  "min"),
    ("vi_pham_S2_load",  "vi phạm S2 (vượt tải)", "min"),
    ("phat_co_trong_so", "tổng phạt có trọng số", "min"),
]


def so_sanh(cua_ta: dict, cua_goc: dict) -> list[dict]:
    kq = []
    for khoa, nhan, huong in CHI_SO_SO_SANH:
        a, b = cua_ta[khoa], cua_goc[khoa]
        if a == b:
            trang_thai = "hoà"
        elif (a < b) == (huong == "min"):
            trang_thai = "thắng"
        else:
            trang_thai = "THUA"
        kq.append({"chi_so": nhan, "khoa": khoa, "cpsat": a, "baseline": b,
                   "huong_tot": huong, "ket_qua": trang_thai})
    return kq


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="So nghiệm CP-SAT với lịch gốc (req 2.9)")
    ap.add_argument("--instance", default="data/instance_slice.json")
    ap.add_argument("--seed-file", default="data/seed.txt")
    ap.add_argument("--lap", type=int, default=5, help="số lần chạy để đo runtime")
    ap.add_argument("--out", default="m2_ilp/out/benchmark.json")
    a = ap.parse_args(argv)

    goc = Path(__file__).resolve().parent.parent
    seed_int = int((goc / a.seed_file).read_text(encoding="utf-8-sig").strip())
    instance = json.loads((goc / a.instance).read_text(encoding="utf-8-sig"))

    from m2_ilp.preprocess import run as run_preprocess
    m2_data = run_preprocess(instance, seed_int=seed_int,
                             out_dir=str(goc / "data" / "processed"))
    params = build_params(instance, m2_data)

    # --- lịch gốc ---
    asg_goc = trich_baseline(instance)
    m_goc = chi_so(params, asg_goc, seed_int)

    # --- nghiệm của ta, đo runtime nhiều lần ---
    thoi_gian, kq = [], None
    for _ in range(max(1, a.lap)):
        t0 = time.perf_counter()
        kq = solve_week(params, seed_int=seed_int, time_limit_s=60.0, verbose=False)
        thoi_gian.append(time.perf_counter() - t0)
    if not kq.get("feasible"):
        print(f"[benchmark] LỖI: mô hình không khả thi ({kq['status']})", file=sys.stderr)
        return 1
    m_ta = chi_so(params, kq["assignment"], seed_int)

    bang = so_sanh(m_ta, m_goc)
    thang = sum(1 for r in bang if r["ket_qua"] == "thắng")
    hoa = sum(1 for r in bang if r["ket_qua"] == "hoà")
    thua = sum(1 for r in bang if r["ket_qua"] == "THUA")

    print(f"\n{'='*72}")
    print(f"  [benchmark] CP-SAT  vs  lịch gốc — ngày {instance['meta'].get('date','?')}, "
          f"seed {seed_int}")
    print(f"{'='*72}")
    print(f"  {'chỉ số':<28}{'CP-SAT':>12}{'lịch gốc':>12}   kết quả")
    print(f"  {'-'*66}")
    for r in bang:
        f = (lambda v: f"{v:.4f}" if isinstance(v, float) else str(v))
        print(f"  {r['chi_so']:<28}{f(r['cpsat']):>12}{f(r['baseline']):>12}   {r['ket_qua']}")
    print(f"  {'-'*66}")
    print(f"  {thang} thắng · {hoa} hoà · {thua} thua")

    tg = {"trung_vi_s": round(statistics.median(thoi_gian), 4),
          "nho_nhat_s": round(min(thoi_gian), 4),
          "lon_nhat_s": round(max(thoi_gian), 4), "so_lan_lap": len(thoi_gian)}
    print(f"\n  Runtime CP-SAT ({tg['so_lan_lap']} lần): trung vị {tg['trung_vi_s']}s "
          f"(min {tg['nho_nhat_s']}s, max {tg['lon_nhat_s']}s)")
    print(f"  Lịch gốc là dữ liệu có sẵn, không tốn thời gian giải — so runtime chỉ để "
          f"cho thấy chi phí tính toán của ta là chấp nhận được, không phải để hơn thua.")

    rb_goc = m_goc["rang_buoc_cung"]
    if not rb_goc["tat_ca_dat"]:
        xau = [k for k, v in rb_goc.items() if k != "tat_ca_dat" and not v]
        print(f"\n  LƯU Ý: lịch gốc vi phạm chính các ràng buộc cứng {', '.join(xau)}. "
              f"Nên mọi so sánh dưới đây là so với một lịch KHÔNG hợp lệ.")
    else:
        print(f"\n  Lịch gốc thỏa đủ 5 ràng buộc cứng, nên đây là so sánh công bằng: "
              f"cùng một miền nghiệm hợp lệ.")

    if m_goc["vi_pham_S2_load"]:
        print(f"  Lịch gốc để {', '.join(m_goc['nguoi_vuot_tai'])} trực "
              f"{m_goc['tai_lon_nhat']} ca, vượt MaxLoad = "
              f"{params['max_load'].get(m_goc['nguoi_vuot_tai'][0], '?')}. "
              f"Mô hình đưa tải lớn nhất về {m_ta['tai_lon_nhat']}.")

    (goc / a.out).parent.mkdir(parents=True, exist_ok=True)
    (goc / a.out).write_text(json.dumps(
        {"seed": seed_int, "ngay": instance["meta"].get("date"),
         "cpsat": m_ta, "baseline": m_goc, "so_sanh": bang,
         "tong_ket": {"thang": thang, "hoa": hoa, "thua": thua},
         "runtime_cpsat": tg},
        ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\n  Đã ghi {(goc / a.out).relative_to(goc)}")

    if thua:
        print("  => THUA baseline ở ít nhất một chỉ số — chưa đạt yêu cầu 2.9.")
        return 1
    if not thang:
        print("  => Hoà toàn bộ: không chứng minh được mô hình hơn lịch gốc.")
        return 1
    print(f"  => ĐẠT: thắng {thang} chỉ số, không thua chỉ số nào.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
