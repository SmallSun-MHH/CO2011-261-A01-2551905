#!/usr/bin/env python3
"""
cnf_encoder.py — Mã hóa bài toán phân công giám thị thành CNF và giải SAT (Yêu cầu 1.2).

Hai chế độ:
  1. SAT (feasibility): giải instance gốc, trả lịch phân công hợp lệ.
  2. UNSAT (unsat-core): siết instance cho bất khả thỏa, trích lõi mâu thuẫn
     bằng selector-literal + Glucose3.solve(assumptions=...).

Người làm: (điền tên thành viên)
Reviewed:  (điền tên reviewer)
"""

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

from pysat.formula import CNF, IDPool
from pysat.solvers import Glucose3
from pysat.card import CardEnc, EncType


# ---------------------------------------------------------------------------
#  Hàm tiện ích
# ---------------------------------------------------------------------------

def _var(vpool: IDPool, invig: str, shift: str) -> int:
    """Trả về biến Boolean x_{invig, shift}."""
    return vpool.id(f"{invig}_{shift}")


# ---------------------------------------------------------------------------
#  Xây dựng CNF từ instance JSON
# ---------------------------------------------------------------------------

def build_cnf(data: dict, *, use_selectors: bool = False):
    """
    Mã hóa instance thành CNF.

    Parameters
    ----------
    data : dict
        Instance JSON đã load (output của slice_builder).
    use_selectors : bool
        Nếu True, mỗi nhóm ràng buộc có một selector literal riêng.
        Selector literal dương ⇒ nhóm ràng buộc được kích hoạt.
        Dùng cho chế độ trích Unsat Core (assumptions = selectors).

    Returns
    -------
    cnf : CNF
    vpool : IDPool
    selectors : dict[str, int]   — mapping tên nhóm → selector variable
    stats : dict                  — thống kê
    """
    I = data["invigilators"]
    J = data["shifts"]

    vpool = IDPool()
    cnf = CNF()
    selectors: dict[str, int] = {}
    stats = defaultdict(int)

    def x(i, j):
        return _var(vpool, i, j)

    def _sel(group_name: str) -> int | None:
        """Tạo / lấy selector literal cho nhóm ràng buộc."""
        if not use_selectors:
            return None
        if group_name not in selectors:
            selectors[group_name] = vpool.id(f"__sel_{group_name}")
        return selectors[group_name]

    def _add_clause(clause: list[int], group: str):
        sel = _sel(group)
        if sel is not None:
            cnf.append([-sel] + clause)       # sel → (clause)
        else:
            cnf.append(clause)
        stats[group] += 1

    # ── H1: No double-booking (Overlap) ──────────────────────────────────
    for pair in data.get("overlap", []):
        if len(pair) == 2:
            s1, s2 = pair
            if s1 in J and s2 in J:
                for i in I:
                    _add_clause([-x(i, s1), -x(i, s2)], "H1_overlap")

    # ── H2: Availability (Busy) ─────────────────────────────────────────
    for item in data.get("busy", []):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            i_id, j_id = item
            if j_id in J:
                _add_clause([-x(i_id, j_id)], "H2_busy")

    # ── H3: Eligibility ─────────────────────────────────────────────────
    eligible_set = {tuple(e) for e in data.get("eligible", []) if isinstance(e, list)}
    for i in I:
        for j in J:
            if (i, j) not in eligible_set:
                _add_clause([-x(i, j)], "H3_eligible")

    # ── H4: Well-formedness (campus exists) ──────────────────────────────
    campus_of = data.get("campus_of", {})
    for j in J:
        if j not in campus_of or not campus_of[j]:
            for i in I:
                _add_clause([-x(i, j)], "H4_campus")

    # ── H5: Exact capacity ──────────────────────────────────────────────
    capacities = data.get("capacity", {})
    for j in J:
        K = capacities.get(j, 1)
        shift_vars = [x(i, j) for i in I]
        card_clauses = CardEnc.equals(
            lits=shift_vars, bound=K,
            encoding=EncType.seqcounter, vpool=vpool,
        )
        sel = _sel("H5_capacity")
        for cl in card_clauses.clauses:
            if sel is not None:
                cnf.append([-sel] + cl)
            else:
                cnf.append(cl)
        stats["H5_capacity"] += len(card_clauses.clauses)

    return cnf, vpool, selectors, dict(stats)


# ---------------------------------------------------------------------------
#  Giải SAT (feasibility)
# ---------------------------------------------------------------------------

def solve_sat(data: dict) -> dict:
    """
    Giải instance ở chế độ feasibility.

    Returns
    -------
    dict với:
      status : "SAT" | "UNSAT"
      assignments : list[(invig, shift)]   — nếu SAT
      stats : dict                          — thống kê CNF
      time_s : float                        — thời gian (giây)
    """
    t0 = time.perf_counter()
    cnf, vpool, _, stats = build_cnf(data, use_selectors=False)
    elapsed_build = time.perf_counter() - t0

    result: dict = {
        "stats": {
            "num_vars": vpool.top,
            "num_clauses": len(cnf.clauses),
            "clauses_per_group": stats,
            "build_time_s": round(elapsed_build, 4),
        },
    }

    t1 = time.perf_counter()
    with Glucose3(bootstrap_with=cnf) as solver:
        sat = solver.solve()
        elapsed_solve = time.perf_counter() - t1

        if sat:
            model = solver.get_model()
            assignments = []
            for var_id in model:
                if var_id > 0:
                    name = vpool.obj(var_id)
                    if name and "_" in name and not name.startswith("__"):
                        parts = name.split("_", 1)
                        assignments.append((parts[0], parts[1]))
            result["status"] = "SAT"
            result["assignments"] = assignments
        else:
            result["status"] = "UNSAT"
            result["assignments"] = []

    result["stats"]["solve_time_s"] = round(elapsed_solve, 4)
    result["stats"]["total_time_s"] = round(elapsed_build + elapsed_solve, 4)
    return result


# ---------------------------------------------------------------------------
#  Trích Unsat Core (yêu cầu 1.2 phần UNSAT)
# ---------------------------------------------------------------------------

def solve_unsat_core(data: dict) -> dict:
    """
    Giải instance với selector-literal để trích lõi bất khả thỏa.

    Quy trình:
      1. Mã hóa CNF, mỗi nhóm ràng buộc gắn một selector literal.
      2. Gọi solver.solve(assumptions=all_selectors).
      3. Nếu UNSAT → solver.get_core() trả về MỘT tập con bất khả thỏa
         của các assumptions. LƯU Ý: tập này KHÔNG bảo đảm tối thiểu.
         Lõi tối thiểu (MUS) cùng phép chứng minh tính tối thiểu nằm ở
         m1_logic/unsat_core.py (deletion-based MUS).
      4. Ánh xạ core literals ngược về tên nhóm ràng buộc.

    Returns
    -------
    dict với:
      status : "SAT" | "UNSAT"
      core_groups : list[str]      — tên nhóm trong lõi (nếu UNSAT)
      core_literals : list[int]    — raw literal IDs (nếu UNSAT)
      stats : dict
    """
    t0 = time.perf_counter()
    cnf, vpool, selectors, stats = build_cnf(data, use_selectors=True)
    elapsed_build = time.perf_counter() - t0

    # Ánh xạ ngược: var_id → group name
    sel_to_name = {v: k for k, v in selectors.items()}
    assumptions = list(selectors.values())  # kích hoạt tất cả nhóm

    result: dict = {
        "stats": {
            "num_vars": vpool.top,
            "num_clauses": len(cnf.clauses),
            "clauses_per_group": stats,
            "num_selector_groups": len(selectors),
            "selector_map": {k: v for k, v in selectors.items()},
            "build_time_s": round(elapsed_build, 4),
        },
    }

    t1 = time.perf_counter()
    with Glucose3(bootstrap_with=cnf) as solver:
        sat = solver.solve(assumptions=assumptions)
        elapsed_solve = time.perf_counter() - t1

        if sat:
            result["status"] = "SAT"
            result["core_groups"] = []
            result["core_literals"] = []
        else:
            core = solver.get_core()
            core_groups = [sel_to_name.get(abs(lit), f"unknown_{lit}") for lit in core]
            result["status"] = "UNSAT"
            result["core_literals"] = core
            result["core_groups"] = core_groups

    result["stats"]["solve_time_s"] = round(elapsed_solve, 4)
    result["stats"]["total_time_s"] = round(elapsed_build + elapsed_solve, 4)
    return result


# ---------------------------------------------------------------------------
#  Tạo instance bất khả thỏa (siết ràng buộc)
# ---------------------------------------------------------------------------

def make_infeasible(data: dict) -> dict:
    """
    Tao ban sao instance da duoc siet cho bat kha thoa.

    Chien thuat: dat capacity cua MOI ca = n_inv (toan bo giam thi).
    Khi co >= 2 ca, moi ca yeu cau dung n_inv nguoi, nhung moi nguoi
    chi co the duoc dem 1 lan trong mot ràng buoc exactly-equals
    (CardEnc.equals noi tai dam bao dieu nay). Tong demand = n_inv * n_shifts
    >> n_inv => pigeonhole principle => UNSAT.

    Day la phuong phap "squeeze" — phan anh tinh huong thuc te khi thieu
    nhan luc giam thi vao ngay cao diem.
    """
    import copy

    tight = copy.deepcopy(data)
    n_inv = len(tight["invigilators"])
    n_shifts = len(tight["shifts"])

    if n_shifts <= 1 or n_inv == 0:
        return tight

    # Siet: moi ca can dung n_inv nguoi => pigeonhole with >= 2 shifts
    forced_cap = n_inv
    for j in tight["shifts"]:
        tight["capacity"][j] = forced_cap

    # Them overlap: moi cap ca deu chong gio => 1 nguoi chi duoc 1 ca
    tight["overlap"] = []
    shifts = tight["shifts"]
    for idx, s1 in enumerate(shifts):
        for s2 in shifts[idx + 1:]:
            tight["overlap"].append([s1, s2])

    tight["meta"]["squeeze"] = {
        "method": "capacity_plus_overlap_squeeze",
        "forced_capacity_per_shift": forced_cap,
        "total_demand": forced_cap * n_shifts,
        "total_supply": n_inv,
        "num_overlap_pairs": len(tight["overlap"]),
        "note": (
            f"Moi ca can {forced_cap} nguoi, tat ca ca chong gio "
            f"=> moi nguoi chi duoc 1 ca => can {forced_cap * n_shifts} "
            f"nhung chi co {n_inv} => UNSAT"
        ),
    }
    return tight


# ---------------------------------------------------------------------------
#  Toy instance (giữ lại để backward-compatible)
# ---------------------------------------------------------------------------

def solve_toy_instance():
    """Chạy ví dụ nhỏ từ đề bài (2 giám thị, 1 ca)."""
    print("=== TOY INSTANCE (Worked Example) ===")
    cnf = CNF()
    cnf.append([-1])         # Busy(CB1, s) → ¬Assign(CB1, s)
    cnf.append([1, 2])       # Cap(s, 1): ít nhất 1
    cnf.append([-1, -2])     # Cap(s, 1): nhiều nhất 1

    with Glucose3(bootstrap_with=cnf) as solver:
        if solver.solve():
            print("  Kết quả: SAT")
            for val in solver.get_model():
                if val == 1:
                    print("  Assign(CB1, s) = True")
                if val == 2:
                    print("  Assign(CB2, s) = True")
        else:
            print("  Kết quả: UNSAT")
    print("=" * 40 + "\n")


# ---------------------------------------------------------------------------
#  In báo cáo
# ---------------------------------------------------------------------------

def print_report(result: dict, mode: str = "sat"):
    """In báo cáo kết quả ra terminal."""
    st = result["stats"]
    print(f"\n{'='*60}")
    print(f"  CNF ENCODER -- Bao cao Module 1.2 ({mode.upper()})")
    print(f"{'='*60}")
    print(f"  Tong bien CNF      : {st['num_vars']}")
    print(f"  Tong menh de CNF   : {st['num_clauses']}")
    print(f"  Thoi gian build     : {st['build_time_s']}s")
    print(f"  Thoi gian solve     : {st['solve_time_s']}s")
    print(f"  Tong thoi gian      : {st['total_time_s']}s")
    print(f"  Menh de theo nhom  :")
    for group, count in st["clauses_per_group"].items():
        print(f"    {group:20s} : {count}")

    if result["status"] == "SAT":
        print(f"\n  [OK] Trang thai: SAT (Kha thoa)")
        if "assignments" in result:
            print(f"  So luot gan: {len(result['assignments'])}")
            print(f"  {'-'*30}")
            for inv, shift in result["assignments"]:
                print(f"    Giam thi {inv} -> Ca {shift}")
    else:
        print(f"\n  [FAIL] Trang thai: UNSAT (Bat kha thoa)")
        if "core_groups" in result and result["core_groups"]:
            print(f"  Loi mau thuan (Unsat Core) gom {len(result['core_groups'])} nhom:")
            for g in result["core_groups"]:
                print(f"    > {g}")
        if "core_literals" in result:
            print(f"  Raw core literals: {result['core_literals']}")

    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
#  Pipeline chính: gọi từ run_all.py hoặc chạy trực tiếp
# ---------------------------------------------------------------------------

def run_m1_cnf(data: dict) -> dict:
    """
    Chạy toàn bộ pipeline CNF/SAT cho Module 1.2.

    1. Giải SAT trên instance gốc.
    2. Siết instance → giải lại → trích Unsat Core.

    Returns dict tổng hợp cả hai kết quả.
    """
    # -- Phan 1: Feasibility (SAT) --
    print("\n[m1_cnf] -- Phan 1: Kiem tra kha thi (SAT) --")
    sat_result = solve_sat(data)
    print_report(sat_result, mode="sat")

    # -- Phan 2: Infeasibility (UNSAT + Core) --
    print("[m1_cnf] -- Phan 2: Siet instance -> trich Unsat Core --")
    tight_data = make_infeasible(data)
    unsat_result = solve_unsat_core(tight_data)
    print_report(unsat_result, mode="unsat-core")

    return {
        "sat": sat_result,
        "unsat": unsat_result,
        "squeeze_info": tight_data["meta"].get("squeeze", {}),
    }


# ---------------------------------------------------------------------------
#  CLI: chạy trực tiếp  python m1_logic/cnf_encoder.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    solve_toy_instance()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    json_path = repo_root / "data" / "instance_slice.json"

    if not json_path.exists():
        sys.exit(f"[cnf_encoder] Không tìm thấy {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    run_m1_cnf(data)