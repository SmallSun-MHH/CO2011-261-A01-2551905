#!/usr/bin/env python3
"""
m2_ilp/baseline.py — Module 2, yêu cầu 2.9 (phần 1/2)
=====================================================================
Trích lịch phân công GỐC (baseline) từ dữ liệu thật và tính các chỉ số
công bằng trên đó, để `benchmark.py` có cái mà so.

`data/instance_slice.json` giữ nguyên lịch gốc của ngày được cắt lát trong
trường `baseline`: danh sách cặp [giám thị, ca] đúng như trường đã phân công
trong `data/dataset.csv`. Đây KHÔNG phải số liệu mô phỏng.

Các chỉ số đều tính được cho MỘT lịch bất kỳ, nên dùng chung một hàm cho cả
lịch gốc lẫn nghiệm của solver — nếu viết hai hàm riêng thì rất dễ vô tình
đo hai thứ khác nhau rồi tuyên bố mình thắng.

Chỉ số dùng:
  · tải lớn nhất / nhỏ nhất / khoảng tải   — thô nhưng là thứ giám thị cảm nhận
  · độ lệch L1 quanh q = ⌊ΣCap(gán được)/|I|⌋  — chính là số hạng công bằng
    trong hàm mục tiêu pha 2 của `model.py`, nên so sánh mới cùng thước đo
  · chỉ số công bằng Jain  J = (Σxᵢ)² / (n·Σxᵢ²) ∈ (0, 1]
    1 là chia đều tuyệt đối. Chuẩn trong lý thuyết chia sẻ tài nguyên, không
    phụ thuộc đơn vị và không phụ thuộc số người.
  · hệ số Gini  ∈ [0, 1], 0 là chia đều tuyệt đối. Báo cả hai vì Jain nhạy ở
    vùng gần đều, Gini nhạy ở vùng lệch nhiều.
  · số vi phạm mềm S1 (ưu tiên cơ sở) và S2 (vượt MaxLoad), cùng tiền phạt
    quy theo đúng ba trọng số sinh từ Team ID.

Cách dùng:
    python m2_ilp/baseline.py
    from m2_ilp.baseline import trich_baseline, chi_so
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from m2_ilp.model import _kiem_nghiem, build_params, soft_weights_from_seed, tai_ly_tuong


def trich_baseline(instance: dict) -> list[list[str]]:
    """Lịch gốc, chuẩn hóa về list [i, j] đã sắp xếp."""
    raw = instance.get("baseline") or []
    return sorted([str(i), str(j)] for i, j in raw)


# ---------------------------------------------------------------------------
# Chỉ số công bằng — dùng chung cho mọi lịch
# ---------------------------------------------------------------------------
def _jain(xs: list[int]) -> float:
    """(Σx)² / (n·Σx²). Bằng 1 khi mọi người tải như nhau."""
    n = len(xs)
    mau = n * sum(v * v for v in xs)
    return (sum(xs) ** 2) / mau if mau else 1.0


def _gini(xs: list[int]) -> float:
    """0 = chia đều tuyệt đối. Tính theo định nghĩa chênh lệch tuyệt đối trung bình."""
    n = len(xs)
    tb = sum(xs) / n if n else 0
    if n == 0 or tb == 0:
        return 0.0
    tong_lech = sum(abs(a - b) for a in xs for b in xs)
    return tong_lech / (2 * n * n * tb)


def chi_so(params: dict, assignment: list, seed_int: int) -> dict:
    """Mọi chỉ số của MỘT lịch. Dùng y hệt cho baseline và cho nghiệm solver."""
    w_loc, w_load, w_fair = soft_weights_from_seed(seed_int)
    I = params["I"]
    q = tai_ly_tuong(params)

    tai = {i: 0 for i in I}
    for i, _ in assignment:
        if i in tai:
            tai[i] += 1
    xs = [tai[i] for i in I]

    vi_pham_loc = 0
    for i, j in assignment:
        uu_tien = params["preferences"].get(i, {}).get("prefer_campus")
        if uu_tien and params["campus"].get(j) and params["campus"][j] != uu_tien:
            vi_pham_loc += 1

    vuot = {i: max(0, tai[i] - int(params["max_load"].get(i, 10 ** 9))) for i in I}
    vi_pham_load = sum(vuot.values())
    nguoi_vuot = sorted(i for i, v in vuot.items() if v > 0)

    lech_l1 = sum(abs(v - q) for v in xs)
    kiem = _kiem_nghiem(params, assignment)

    return {
        "so_luot_gan": len(assignment),
        "q_ideal": q,
        "tai": tai,
        "tai_lon_nhat": max(xs) if xs else 0,
        "tai_nho_nhat": min(xs) if xs else 0,
        "khoang_tai": (max(xs) - min(xs)) if xs else 0,
        "lech_L1_quanh_q": lech_l1,
        "jain": round(_jain(xs), 6),
        "gini": round(_gini(xs), 6),
        "vi_pham_S1_loc": vi_pham_loc,
        "vi_pham_S2_load": vi_pham_load,
        "nguoi_vuot_tai": nguoi_vuot,
        "phat_co_trong_so": round(
            w_fair * lech_l1 + w_loc * vi_pham_loc + w_load * vi_pham_load, 4),
        "trong_so": {"w_loc": w_loc, "w_load": w_load, "w_fair": w_fair},
        "rang_buoc_cung": kiem,
    }


# ---------------------------------------------------------------------------
def _in_bang(ten: str, m: dict) -> None:
    rb = m["rang_buoc_cung"]
    xau = [k for k, v in rb.items() if k != "tat_ca_dat" and not v]
    print(f"  {ten}")
    print(f"    lượt gán          : {m['so_luot_gan']}")
    print(f"    tải               : {m['tai_nho_nhat']}–{m['tai_lon_nhat']} "
          f"(khoảng {m['khoang_tai']}), q = {m['q_ideal']}")
    print(f"    lệch L1 quanh q   : {m['lech_L1_quanh_q']}")
    print(f"    Jain / Gini       : {m['jain']:.4f} / {m['gini']:.4f}")
    print(f"    vi phạm S1 / S2   : {m['vi_pham_S1_loc']} / {m['vi_pham_S2_load']}"
          + (f"  (vượt tải: {', '.join(m['nguoi_vuot_tai'])})" if m["nguoi_vuot_tai"] else ""))
    print(f"    phạt có trọng số  : {m['phat_co_trong_so']}")
    print(f"    ràng buộc cứng    : {'5/5 ĐẠT' if rb['tat_ca_dat'] else 'VI PHẠM ' + ', '.join(xau)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Trích baseline và đo chỉ số công bằng (req 2.9)")
    ap.add_argument("--instance", default="data/instance_slice.json")
    ap.add_argument("--seed-file", default="data/seed.txt")
    ap.add_argument("--out", default="m2_ilp/out/baseline.json")
    a = ap.parse_args(argv)

    goc = Path(__file__).resolve().parent.parent
    seed_int = int((goc / a.seed_file).read_text(encoding="utf-8-sig").strip())
    instance = json.loads((goc / a.instance).read_text(encoding="utf-8-sig"))

    from m2_ilp.preprocess import run as run_preprocess
    m2_data = run_preprocess(instance, seed_int=seed_int,
                             out_dir=str(goc / "data" / "processed"))
    params = build_params(instance, m2_data)

    asg = trich_baseline(instance)
    if not asg:
        print("[baseline] LỖI: instance_slice.json không có trường 'baseline'", file=sys.stderr)
        return 1

    m = chi_so(params, asg, seed_int)
    print(f"\n[baseline] Lịch GỐC ngày {instance['meta'].get('date', '?')} "
          f"(trích thẳng từ dataset, không mô phỏng)")
    _in_bang("lịch gốc", m)

    rb = m["rang_buoc_cung"]
    if not rb["tat_ca_dat"]:
        xau = [k for k, v in rb.items() if k != "tat_ca_dat" and not v]
        print(f"\n  GHI CHÚ: chính lịch gốc cũng vi phạm {', '.join(xau)}. Đây là phát hiện "
              f"có giá trị cho báo cáo, không phải lỗi dữ liệu — nêu rõ trong phần nhận xét.")

    out = goc / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"assignment": asg, "chi_so": m},
                              ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\n[baseline] Đã ghi {out.relative_to(goc)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
