#!/usr/bin/env python3
"""
slice_builder.py  —  Cắt lát (slice) dataset thật thành instance nhỏ cho SAT/CNF.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path


def load_dataset(csv_path: str) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def find_peak_date(rows: list[dict]) -> str:
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

    def score(date: str) -> tuple:
        info = date_info[date]
        n_campuses = len(info["campuses"])
        n_shifts = len(info["shifts"])
        n_invs = len(info["invs"])
        size_ok = 1 if 10 <= n_invs <= 30 else 0
        return (n_campuses >= 2, n_shifts, size_ok, n_invs)

    peak_date = max(date_info.keys(), key=score)
    return peak_date


def normalize_seed(raw: str) -> tuple[str, int]:
    """Đổi seed thô trong data/seed.txt thành số nguyên cho random.Random().

    Đề bài nói seed là "a 3-line BLAKE2 hash", nên nó có thể là hex chứ không
    phải số nguyên thập phân. int() thẳng sẽ ném ValueError và làm hỏng điều
    kiện tái tạo — mà tái tạo được là CỔNG chặn toàn bộ điểm code (§4).
    """
    raw = raw.strip()
    try:
        return raw, int(raw)
    except ValueError:
        pass
    try:
        return raw, int(raw, 16)
    except ValueError:
        pass
    return raw, int.from_bytes(
        hashlib.blake2b(raw.encode("utf-8"), digest_size=8).digest(), "big")


def parse_hour(hour_str: str) -> float:
    hour_str = hour_str.strip()
    parts = hour_str.replace("g", ".").split(".")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return h + m / 60.0


def build_instance(rows: list[dict], target_date: str, seed: int) -> dict:
    day_rows = [r for r in rows if r["Ngày"].strip() == target_date]
    if not day_rows:
        raise ValueError(f"Không tìm thấy dữ liệu cho ngày {target_date}")

    shifts_info: dict[str, dict] = {}
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

    DURATION_HOURS = 150.0 / 60.0
    overlaps = []
    for i_idx, j1 in enumerate(J):
        s1 = shifts_info[j1]["hour_num"]
        e1 = s1 + DURATION_HOURS
        for j2 in J[i_idx + 1:]:
            s2 = shifts_info[j2]["hour_num"]
            e2 = s2 + DURATION_HOURS
            if s1 < e2 and s2 < e1:
                overlaps.append([j1, j2])

    baseline = []
    for row in day_rows:
        sid = row["MS Ca thi"].strip()
        cb_id = row["MS của CÁN BỘ COI THI"].strip()
        baseline.append([cb_id, sid])

    # --- Busy(i, j): giám thị i bận ở ca j ---
    # Suy ra TỪ DỮ LIỆU THẬT, không bịa: nếu giám thị i đã được xếp vào ca j
    # trong lịch gốc, và ca k chồng giờ với ca j, thì tại ca k người đó thật sự
    # không khả dụng. Đây là hệ quả logic của chính lịch gốc.
    #
    # Vì sao KHÔNG để rỗng: nếu busy = [] thì ràng buộc cứng H2 (availability)
    # biến mất khỏi mô hình, lõi bất khả thỏa ở nhiệm vụ 4 sẽ không bao giờ
    # chứa mệnh đề availability, và mô hình ILP ở M2 mất một họ ràng buộc.
    ke_chong_gio: dict[str, set[str]] = defaultdict(set)
    for j1, j2 in overlaps:
        ke_chong_gio[j1].add(j2)
        ke_chong_gio[j2].add(j1)

    busy_set: set[tuple[str, str]] = set()
    for cb_id, sid in baseline:
        for sid_khac in ke_chong_gio[sid]:
            busy_set.add((cb_id, sid_khac))

    busy: list[list[str]] = sorted([i, j] for i, j in busy_set)

    eligible = []
    for inv in I:
        for shift in J:
            eligible.append([inv, shift])

    rng = random.Random(seed)
    prefer: dict[str, str | None] = {}
    for inv in I:
        choice = rng.choice(campuses + [None])
        prefer[inv] = choice

    avg_load = len(J) / max(len(I), 1)
    max_load_val = math.ceil(avg_load) + 1
    max_load = {inv: max_load_val for inv in I}

    capacity = {sid: shifts_info[sid]["capacity"] for sid in J}
    campus_of = {sid: shifts_info[sid]["campus"] for sid in J}
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=str, default=None,
                    help="seed thô; bỏ trống thì đọc từ --seed-file")
    ap.add_argument("--seed-file", type=str, default=None,
                    help="mặc định data/seed.txt (§4 của đề)")
    ap.add_argument("--date", type=str, default=None)
    ap.add_argument("--data", type=str, default=None)
    ap.add_argument("--output", type=str, default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data"
    csv_path = args.data or str(data_dir / "dataset.csv")
    output_path = args.output or str(data_dir / "instance_slice.json")

    if not os.path.exists(csv_path):
        sys.exit(f"[slice_builder] ERROR: Không tìm thấy dataset: {csv_path}")

    seed_raw = args.seed
    if seed_raw is None:
        seed_path = args.seed_file or str(data_dir / "seed.txt")
        if not os.path.exists(seed_path):
            sys.exit(f"[slice_builder] ERROR: Không tìm thấy seed: {seed_path}")
        seed_raw = Path(seed_path).read_text(encoding="utf-8").strip()
    seed_raw, seed_int = normalize_seed(seed_raw)

    rows = load_dataset(csv_path)
    target_date = args.date if args.date else find_peak_date(rows)
    instance = build_instance(rows, target_date, seed_int)
    instance["meta"]["seed_raw"] = seed_raw

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(instance, f, ensure_ascii=False, indent=2)
    if not args.quiet:
        print(f"[slice_builder] Instance saved to: {output_path}")


if __name__ == "__main__":
    main()
