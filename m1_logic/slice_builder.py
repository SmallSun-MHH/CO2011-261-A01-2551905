#!/usr/bin/env python3
"""
slice_builder.py  —  Cắt lát (slice) dataset thật thành instance nhỏ cho SAT/CNF.

Yêu cầu 1.2 của đề: "a small slice of the data" đủ nhỏ để SAT solver chạy được,
nhưng vẫn giữ nguyên cấu trúc bài toán (nhiều ca, nhiều giám thị, 2 cơ sở,
overlap, capacity).

Chiến lược cắt:
  1. Chọn 1 ngày cao điểm (nhiều ca thi + nhiều giám thị nhất).
  2. Trích tập giám thị (I), tập ca thi (J), capacity mỗi ca, cơ sở mỗi ca.
  3. Xây dựng Overlap(j,k) từ giờ thi (ca trùng giờ => overlap).
  4. Xây dựng Busy(i,j) giả lập: giám thị đã được gán ở ca j thì coi là
     "baseline assignment" — ta dùng baseline này để kiểm chứng SAT.
  5. Sinh Eligible(i,j) = True cho mọi cặp (mặc định, đơn giản hóa).
  6. Sinh Prefer(i,c) từ seed (3 loại: prefer CS1, prefer CS2, no preference).
  7. Sinh MaxLoad(i) = ceil(len(J) / len(I)) + 1 (công bằng + buffer).
  8. Xuất JSON instance cho cnf_encoder.py dùng.

Tác giả: Trần Anh Khôi (2551905)
Task:    STT 2 trong IAP_tracker
"""

import argparse
import csv
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path


def load_dataset(csv_path: str) -> list[dict]:
    """Đọc dataset CSV thành list of dicts."""
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def find_peak_date(rows: list[dict]) -> str:
    """Tìm ngày tốt nhất cho SAT instance.

    Ưu tiên (theo thứ tự):
      1. Ngày có CẢ 2 cơ sở (Cơ sở 1 và Cơ sở 2) — để ràng buộc S1
         (location preference) có nghĩa.
      2. Trong số đó, chọn ngày có nhiều ca thi nhất (nhiều overlap).
      3. Nếu hòa, chọn ngày có nhiều giám thị nhất nhưng ≤ 30
         (đủ nhỏ cho SAT, đủ lớn để có ý nghĩa).
    Fallback: nếu không có ngày nào đủ 2 cơ sở, chọn ngày nhiều
    assignments nhất.
    """
    # Thu thập thống kê theo ngày
    date_info: dict[str, dict] = defaultdict(
        lambda: {"campuses": set(), "shifts": set(), "invs": set(), "count": 0}
    )
    for row in rows:
        date = row["Ngày"].strip()
        if not date:
            continue
        campus = row.get("Cơ sở", "").strip()
        shift = row["MS Ca thi"].strip()
        inv = row["MS của CÁN BỘ COI THI"].strip()

        date_info[date]["count"] += 1
        if campus:
            date_info[date]["campuses"].add(campus)
        date_info[date]["shifts"].add(shift)
        date_info[date]["invs"].add(inv)

    # Ưu tiên ngày 2 cơ sở, nhiều ca, kích thước vừa phải
    def score(date: str) -> tuple:
        info = date_info[date]
        n_campuses = len(info["campuses"])
        n_shifts = len(info["shifts"])
        n_invs = len(info["invs"])
        # Ưu tiên 2 campus, rồi nhiều shift, rồi ≤30 invigilators
        size_ok = 1 if 10 <= n_invs <= 30 else 0
        return (n_campuses >= 2, n_shifts, size_ok, n_invs)

    peak_date = max(date_info.keys(), key=score)
    return peak_date


def parse_hour(hour_str: str) -> float:
    """Chuyển '09g30' -> 9.5, '13g00' -> 13.0, '18g15' -> 18.25."""
    hour_str = hour_str.strip()
    parts = hour_str.replace("g", ".").split(".")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return h + m / 60.0


def build_instance(rows: list[dict], target_date: str, seed: int) -> dict:
    """Xây dựng instance SAT từ các dòng thuộc ngày target_date.

    Returns:
        dict chứa tất cả thông tin cần cho CNF encoder:
        {
            "meta": {...},
            "invigilators": [...],
            "shifts": [...],
            "campuses": [...],
            "capacity": {shift_id: int},
            "campus_of": {shift_id: campus},
            "overlap": [[j1, j2], ...],
            "busy": [[invigilator, shift_id], ...],
            "eligible": [[invigilator, shift_id], ...],
            "prefer": {invigilator: campus_or_null},
            "max_load": {invigilator: int},
            "baseline": [[invigilator, shift_id], ...],
        }
    """
    # --- Lọc dữ liệu theo ngày ---
    day_rows = [r for r in rows if r["Ngày"].strip() == target_date]
    if not day_rows:
        raise ValueError(f"Không tìm thấy dữ liệu cho ngày {target_date}")

    # --- Trích tập J (shifts) và I (invigilators) ---
    shifts_info: dict[str, dict] = {}  # shift_id -> {hour, campus, capacity}
    invigilators: set[str] = set()

    for row in day_rows:
        sid = row["MS Ca thi"].strip()
        cb_id = row["MS của CÁN BỘ COI THI"].strip()
        hour_str = row["GIỜ"].strip()
        campus = row.get("Cơ sở", "").strip()

        invigilators.add(cb_id)

        if sid not in shifts_info:
            shifts_info[sid] = {
                "hour": hour_str,
                "hour_num": parse_hour(hour_str),
                "campus": campus if campus else None,
                "capacity": 0,
                "label": row["Ca thi"].strip(),
            }
        shifts_info[sid]["capacity"] += 1

    I = sorted(invigilators)
    J = sorted(shifts_info.keys())
    campuses = sorted({v["campus"] for v in shifts_info.values() if v["campus"]})

    # --- Xây Overlap(j, k): hai ca trùng giờ ---
    # Mỗi ca có 1 giờ bắt đầu + 150 phút => giờ kết thúc = bắt đầu + 2.5h
    DURATION_HOURS = 150.0 / 60.0  # 2.5 giờ
    overlaps = []
    for i_idx, j1 in enumerate(J):
        s1 = shifts_info[j1]["hour_num"]
        e1 = s1 + DURATION_HOURS
        for j2 in J[i_idx + 1:]:
            s2 = shifts_info[j2]["hour_num"]
            e2 = s2 + DURATION_HOURS
            # Trùng nếu khoảng thời gian giao nhau
            if s1 < e2 and s2 < e1:
                overlaps.append([j1, j2])

    # --- Baseline assignment (lịch thực tế) ---
    baseline = []
    for row in day_rows:
        sid = row["MS Ca thi"].strip()
        cb_id = row["MS của CÁN BỘ COI THI"].strip()
        baseline.append([cb_id, sid])

    # --- Busy(i, j): giám thị i bận ở ca j ---
    # Từ dữ liệu thật, nếu giám thị KHÔNG được gán vào ca j nhưng ca j
    # overlap với một ca khác mà họ ĐÃ được gán -> ta suy ra họ "bận"
    # tại ca j. Tuy nhiên, để đơn giản cho SAT toy instance,
    # ta chỉ đánh dấu busy nếu giám thị hoàn toàn KHÔNG xuất hiện ở ngày
    # đó cho một ca nào đó (= không có trong tập eligible giả lập).
    # Ở đây ta để trống — mọi giám thị đều "available" cho mọi ca.
    busy: list[list[str]] = []

    # --- Eligible(i, j): mặc định tất cả đều eligible ---
    eligible = []
    for inv in I:
        for shift in J:
            eligible.append([inv, shift])

    # --- Prefer(i, c): sinh từ seed ---
    rng = random.Random(seed)
    prefer: dict[str, str | None] = {}
    for inv in I:
        # 3 loại: prefer CS1, prefer CS2, no preference (None)
        choice = rng.choice(campuses + [None])
        prefer[inv] = choice

    # --- MaxLoad(i): phân bổ công bằng + buffer 1 ---
    avg_load = len(J) / max(len(I), 1)
    max_load_val = math.ceil(avg_load) + 1
    max_load = {inv: max_load_val for inv in I}

    # --- Capacity ---
    capacity = {sid: shifts_info[sid]["capacity"] for sid in J}

    # --- Campus_of ---
    campus_of = {sid: shifts_info[sid]["campus"] for sid in J}

    # --- Shift labels (cho debug / báo cáo) ---
    shift_labels = {sid: shifts_info[sid]["label"] for sid in J}

    instance = {
        "meta": {
            "description": "SAT instance sliced from real exam data",
            "source": "Dataset_Anonymized_Invigilator_Assignment_Problem",
            "date": target_date,
            "team_id": "CO2011-261-A01-2551905",
            "seed": seed,
            "num_invigilators": len(I),
            "num_shifts": len(J),
            "num_assignments": len(baseline),
            "total_capacity": sum(capacity.values()),
        },
        "invigilators": I,
        "shifts": J,
        "shift_labels": shift_labels,
        "campuses": campuses,
        "capacity": capacity,
        "campus_of": campus_of,
        "overlap": overlaps,
        "busy": busy,
        "eligible": eligible,
        "prefer": prefer,
        "max_load": max_load,
        "baseline": baseline,
    }

    return instance


def print_summary(instance: dict) -> None:
    """In tóm tắt instance ra console."""
    m = instance["meta"]
    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║   SLICE BUILDER — Instance Summary               ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  Date:           {m['date']:<32s}║")
    print(f"║  Invigilators:   {m['num_invigilators']:<32d}║")
    print(f"║  Shifts:         {m['num_shifts']:<32d}║")
    print(f"║  Total capacity: {m['total_capacity']:<32d}║")
    print(f"║  Assignments:    {m['num_assignments']:<32d}║")
    print(f"║  Seed:           {m['seed']:<32d}║")
    print(f"╚══════════════════════════════════════════════════╝")
    print()

    print("Shifts:")
    for sid in instance["shifts"]:
        cap = instance["capacity"][sid]
        camp = instance["campus_of"][sid] or "N/A"
        label = instance["shift_labels"].get(sid, "")
        print(f"  {sid}  cap={cap}  campus={camp}")

    print()
    print(f"Overlaps: {len(instance['overlap'])} pairs")
    for j1, j2 in instance["overlap"]:
        print(f"  {j1} <-> {j2}")

    print()
    print(f"Busy entries: {len(instance['busy'])}")
    print(f"Eligible entries: {len(instance['eligible'])}")
    print(f"Baseline assignments: {len(instance['baseline'])}")


def main():
    ap = argparse.ArgumentParser(
        description="Cắt lát dataset thành instance nhỏ cho SAT/CNF"
    )
    ap.add_argument(
        "--seed", type=int, required=True,
        help="Seed từ data/seed.txt"
    )
    ap.add_argument(
        "--date", type=str, default=None,
        help="Ngày cụ thể (YYYY-MM-DD HH:MM:SS). Mặc định: ngày cao điểm."
    )
    ap.add_argument(
        "--data", type=str, default=None,
        help="Đường dẫn file CSV dataset. Mặc định: data/dataset.csv"
    )
    ap.add_argument(
        "--output", type=str, default=None,
        help="Đường dẫn file JSON output. Mặc định: data/instance_slice.json"
    )
    ap.add_argument(
        "--quiet", action="store_true",
        help="Không in tóm tắt ra console."
    )
    args = ap.parse_args()

    # --- Xác định đường dẫn ---
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data"

    csv_path = args.data or str(data_dir / "dataset.csv")
    output_path = args.output or str(data_dir / "instance_slice.json")

    # --- Load & slice ---
    if not os.path.exists(csv_path):
        sys.exit(f"[slice_builder] ERROR: Không tìm thấy dataset: {csv_path}")

    rows = load_dataset(csv_path)

    if args.date:
        target_date = args.date
    else:
        target_date = find_peak_date(rows)

    instance = build_instance(rows, target_date, args.seed)

    # --- Xuất JSON ---
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(instance, f, ensure_ascii=False, indent=2)

    if not args.quiet:
        print_summary(instance)
        print(f"\n[slice_builder] Instance saved to: {output_path}")


if __name__ == "__main__":
    main()
