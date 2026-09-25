#!/usr/bin/env python3
"""
m2_ilp/preprocess.py
=====================================================================
Module 2 — Linear & Integer Programming
Yêu cầu 2.1 (trích tập/tham số) + 2.6 (tiền xử lý dữ liệu)

Trích I, J, sức chứa, khả dụng (busy), cơ sở (campus) TỪ CHÍNH
data/instance_slice.json mà m1_logic/slice_builder.py đã dựng — không
đọc lại CSV thô từ đầu, để M2 "extend cùng một model, cùng một repo"
với M1 (đúng nguyên tắc chủ đạo §2 của đề bài), và để thừa hưởng các
bản vá của Module 1 (đơn vị ca = (MS Ca thi, Cơ sở), busy suy từ lịch
gốc — xem DECISIONS.md D1, D4).

Sinh THÊM đúng một thứ mà dataset không có: preference vị trí 3 loại
(near_cs1 / near_cs2 / balanced) — phần duy nhất đề cho phép mô phỏng
(Assignment Brief §1). Toàn bộ ngẫu nhiên lấy từ MỘT random.Random(seed_int)
riêng của module này, seed_int được truyền vào từ run_all.py, KHÔNG tự
đọc/hash data/seed.txt lần nữa (seed_int đã là int sẵn, xem make_seed.py).

Cách dùng chính thức — gọi từ run_all.py, tái dùng `instance` đã có sẵn
trong bộ nhớ từ bước m1 (không đọc lại file):
    from m2_ilp.preprocess import run as run_m2_preprocess
    m2_data = run_m2_preprocess(instance, seed_int=a.seed)

Cách chạy ĐỘC LẬP để test module này riêng:
    python m2_ilp/preprocess.py --instance data/instance_slice.json \
        --seed-file data/seed.txt --out-dir data/processed
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOCATION_CATEGORIES = ("near_cs1", "near_cs2", "balanced")


# ---------------------------------------------------------------------------
# 1. Seed handling
# ---------------------------------------------------------------------------
def make_rng(seed_int: int) -> random.Random:
    """RNG RIÊNG của module preprocess (M2), tách khỏi rng dùng cho soft
    weights trong tools/make_seed.py — cả hai cùng khởi tạo từ seed_int
    nhưng là hai đối tượng random.Random độc lập, nên thứ tự rút số của
    module này không ảnh hưởng tới soft_weights() và ngược lại."""
    return random.Random(seed_int)


# ---------------------------------------------------------------------------
# 2. Trích I, J, capacity, busy, campus TỪ instance_slice.json (M1)
# ---------------------------------------------------------------------------
@dataclass
class M2Params:
    I: list[str] = field(default_factory=list)
    J: list[str] = field(default_factory=list)
    capacity: dict[str, int] = field(default_factory=dict)
    busy: dict[str, bool] = field(default_factory=dict)   # key "i|j"
    campus: dict[str, str] = field(default_factory=dict)
    campuses: list[str] = field(default_factory=list)     # tên cơ sở thật, lấy từ data
    meta: dict[str, Any] = field(default_factory=dict)


def _normalize_invigilators(raw: Any) -> list[str]:
    """instance['invigilators'] có thể là list[str] (ID) hoặc list[dict]
    (mỗi giám thị 1 dict có 'id'). Chấp nhận cả hai để không phụ thuộc
    cứng vào việc slice_builder.py đổi định dạng."""
    if not raw:
        return []
    if isinstance(raw[0], str):
        return sorted(set(raw))
    if isinstance(raw[0], dict):
        return sorted({str(x.get("id") or x.get("invigilator_id")) for x in raw})
    raise TypeError(f"Không nhận diện được định dạng instance['invigilators']: {type(raw[0])}")


def _normalize_shifts_flat(
    shift_ids: list[str], capacity_src: dict, campus_src: dict
) -> tuple[list[str], dict[str, int], dict[str, str]]:
    """Dạng THẬT trong data/instance_slice.json (đã xác nhận với dữ liệu thật
    28/05/2026): instance['shifts'] là list ID phẳng (chuỗi), còn
    instance['capacity'] và instance['campus_of'] là 2 dict riêng ở cấp cao
    nhất, cùng khóa với id trong 'shifts'."""
    J = sorted(str(j) for j in shift_ids)
    missing_cap = [j for j in J if j not in capacity_src]
    missing_campus = [j for j in J if j not in campus_src]
    if missing_cap or missing_campus:
        raise KeyError(
            f"Ca thi thiếu dữ liệu: thiếu capacity cho {missing_cap}, "
            f"thiếu campus_of cho {missing_campus}."
        )
    capacity = {j: int(capacity_src[j]) for j in J}
    campus = {j: str(campus_src[j]) for j in J}
    return J, capacity, campus


def _normalize_shifts_nested(raw: list[dict]) -> tuple[list[str], dict[str, int], dict[str, str]]:
    """Dạng DỰ PHÒNG (chỉ dùng khi test với fixture cũ, KHÔNG phải dạng thật
    của dataset): mỗi phần tử shifts là 1 dict lồng {id, capacity, campus}."""
    J, capacity, campus = [], {}, {}
    for s in raw:
        sid = str(s.get("id") or s.get("shift_id") or s.get("ma_ca"))
        cap = s.get("capacity") or s.get("capacity_required") or s.get("suc_chua")
        cam = s.get("campus") or s.get("campus_of") or s.get("co_so")
        if sid is None or cap is None or cam is None:
            raise KeyError(f"Ca thi (dạng lồng) thiếu id/capacity/campus: {s}")
        J.append(sid)
        capacity[sid] = int(cap)
        campus[sid] = str(cam)
    return sorted(J), capacity, campus


def _normalize_busy(raw: Any) -> dict[str, bool]:
    """instance['busy'] theo D4/DECISIONS.md được suy từ lịch gốc qua quan
    hệ chồng giờ. Có thể là:
      - dict {"i|j": true/false}
      - list các cặp [i, j] (nghĩa là (i,j) đang busy)
    Chuẩn hóa về dict {"i|j": bool}."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): bool(v) for k, v in raw.items()}
    if isinstance(raw, list):
        out: dict[str, bool] = {}
        for pair in raw:
            i, j = pair[0], pair[1]
            out[f"{i}|{j}"] = True
        return out
    raise TypeError(f"Không nhận diện được định dạng instance['busy']: {type(raw)}")


def extract_params_from_instance(instance: dict) -> M2Params:
    """Đầu vào `instance` chính là dict đã nạp từ data/instance_slice.json
    (hoặc trả về trực tiếp bởi m1_logic.slice_builder.run_slice_builder)."""
    out = M2Params(meta=instance.get("meta", {}))
    out.I = _normalize_invigilators(instance.get("invigilators"))

    shifts_raw = instance.get("shifts")
    if shifts_raw and isinstance(shifts_raw[0], str):
        out.J, out.capacity, out.campus = _normalize_shifts_flat(
            shifts_raw, instance.get("capacity") or {}, instance.get("campus_of") or {}
        )
    elif shifts_raw and isinstance(shifts_raw[0], dict):
        out.J, out.capacity, out.campus = _normalize_shifts_nested(shifts_raw)
    else:
        out.J, out.capacity, out.campus = [], {}, {}

    out.busy = _normalize_busy(instance.get("busy"))
    out.campuses = sorted(instance.get("campuses") or set(out.campus.values()))

    if not out.I or not out.J:
        raise ValueError(
            "instance rỗng (I hoặc J trống) — kiểm tra data/instance_slice.json "
            "đã được m1_logic/slice_builder.py sinh ra chưa."
        )
    return out


# ---------------------------------------------------------------------------
# 3. Sinh location preference 3 loại — PHẦN DUY NHẤT được mô phỏng
#    (Assignment Brief §1: "location preferences in three categories ...
#    may be simulated, and every such assumption must be stated")
# ---------------------------------------------------------------------------
def generate_location_preferences(
    invigilators: list[str], campuses: list[str], rng: random.Random
) -> dict[str, dict[str, Any]]:
    """near_cs1 -> ưu tiên campuses[0] | near_cs2 -> ưu tiên campuses[1] |
    balanced -> không ưu tiên. Tên cơ sở LẤY TỪ DATA (instance['campuses']),
    KHÔNG hard-code 'CS1'/'CS2' — dataset thật dùng tên 'Cơ sở 1'/'Cơ sở 2'.
    rng.choice (đã seed) chọn đều cho từng giám thị, KHÔNG gán theo index/thứ
    tự xuất hiện để tránh thiên lệch đoán trước được."""
    if len(campuses) != 2:
        raise ValueError(
            f"Đề bài giả định đúng 2 cơ sở (§1: 'near Campus 1'/'near Campus 2'), "
            f"nhưng instance['campuses'] = {campuses}. Kiểm tra lại dữ liệu."
        )
    campus_of_category = {"near_cs1": campuses[0], "near_cs2": campuses[1]}  # balanced -> None
    prefs: dict[str, dict[str, Any]] = {}
    for i in invigilators:
        category = rng.choice(LOCATION_CATEGORIES)
        prefs[i] = {"category": category, "prefer_campus": campus_of_category.get(category)}
    return prefs


# ---------------------------------------------------------------------------
# 4. I/O & entry point chính thức
# ---------------------------------------------------------------------------
def _save_json(obj: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def run(instance: dict, seed_int: int, out_dir: str = "data/processed") -> dict:
    """
    Gọi từ run_all.py:
        from m2_ilp.preprocess import run as run_m2_preprocess
        m2_data = run_m2_preprocess(instance, seed_int=a.seed)

    `instance` là dict trả về bởi m1_logic.slice_builder.run_slice_builder(),
    KHÔNG đọc lại data/instance_slice.json từ đĩa trong trường hợp này —
    tránh đọc file 2 lần trong cùng một lượt chạy run_all.py và luôn đồng
    bộ với đúng bản instance mà M1 vừa kiểm chứng SAT.
    """
    rng = make_rng(seed_int)
    params = extract_params_from_instance(instance)

    if instance.get("prefer"):
        print(
            "[m2_preprocess] LƯU Ý: instance_slice.json còn field 'prefer' cũ "
            "(trước khi áp quyết định D8) -> ĐÃ BỎ QUA, M2 tự sinh lại từ "
            "seed_int theo đúng quyết định. Nếu thấy dòng này thường xuyên, "
            "nhắc Khôi xóa hẳn đoạn sinh 'prefer' khỏi m1_logic/slice_builder.py."
        )
    preferences = generate_location_preferences(params.I, params.campuses, rng)

    _save_json({"I": params.I, "J": params.J}, os.path.join(out_dir, "sets.json"))
    _save_json(params.capacity, os.path.join(out_dir, "capacity.json"))
    _save_json(params.busy, os.path.join(out_dir, "busy.json"))
    _save_json(params.campus, os.path.join(out_dir, "campus.json"))
    _save_json(preferences, os.path.join(out_dir, "preferences.json"))

    print(f"[m2_preprocess] |I|={len(params.I)} |J|={len(params.J)} "
          f"(ngày {params.meta.get('date', '?')})")
    print(f"[m2_preprocess] seed_int={seed_int} -> đã sinh {len(preferences)} preference vị trí")
    print(f"[m2_preprocess] đã ghi 5 file JSON vào {out_dir}/")

    return {
        "I": params.I,
        "J": params.J,
        "capacity": params.capacity,
        "busy": params.busy,
        "campus": params.campus,
        "preferences": preferences,
    }


# ---------------------------------------------------------------------------
# 5. CLI — CHỈ để test module này độc lập; run_all.py KHÔNG dùng phần này.
# ---------------------------------------------------------------------------
def _load_seed_int_standalone(seed_file: str) -> int:
    p = Path(seed_file)
    if not p.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {seed_file}. Chạy trước: "
            f"python tools/make_seed.py <TEAM_ID> > data/seed.txt"
        )
    raw = p.read_text(encoding="utf-8-sig").strip()
    if not raw.isdigit():
        raise ValueError(f"{seed_file} phải chỉ chứa chữ số (xem tools/check_m1.py mục seed.txt)")
    return int(raw)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Chạy độc lập m2_ilp/preprocess.py để test (req 2.1, 2.6)")
    p.add_argument("--instance", default="data/instance_slice.json",
                    help="File JSON do m1_logic/slice_builder.py sinh ra")
    p.add_argument("--seed-file", default="data/seed.txt")
    p.add_argument("--out-dir", default="data/processed")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        seed_int = _load_seed_int_standalone(args.seed_file)
        instance = json.loads(Path(args.instance).read_text(encoding="utf-8-sig"))
        run(instance, seed_int=seed_int, out_dir=args.out_dir)
    except (FileNotFoundError, KeyError, ValueError, TypeError) as e:
        print(f"[m2_preprocess] LỖI: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())