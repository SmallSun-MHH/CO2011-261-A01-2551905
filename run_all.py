#!/usr/bin/env python3
"""
run_all.py  -  THE single entry point for the CO2011 SEM261 assignment.

Grading runs exactly:  python run_all.py --seed $(cat data/seed.txt)
It must reproduce EVERY number in your report from a clean clone, with no manual steps.
Fill in each stage to call your module code; keep the CLI and the stage order stable.

This skeleton ships in the course template repository ("Use this template", not a fork).
"""
import argparse
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="from data/seed.txt")
    ap.add_argument("--stage", default="all",
                    choices=["all", "m1", "m2", "m3", "m4", "m5"])
    a = ap.parse_args()

    repo_root = Path(__file__).resolve().parent
    seed_str = str(a.seed)

    # ══════════════════════════════════════════════════════════════════════
    #  Module 1 — Logic: SAT feasibility / unsat core, logic→LP table
    # ══════════════════════════════════════════════════════════════════════
    if a.stage in ("all", "m1"):
        print(f"\n{'='*60}")
        print(f"  MODULE 1 -- Logic & SAT  (seed={a.seed})")
        print(f"{'='*60}")

        # --- Bước 1.0: Cắt lát dữ liệu → instance JSON ---
        from m1_logic.slice_builder import run_slice_builder
        instance = run_slice_builder(seed_raw=seed_str)

        # --- Bước 1.2: CNF/SAT + Unsat Core ---
        from m1_logic.cnf_encoder import run_m1_cnf
        m1_result = run_m1_cnf(instance)

        # --- Bước 1.3: Logic → LP bridge (worked example) ---
        # --- Bước 1.2b: Lõi bất khả thỏa TỐI THIỂU (deletion-based MUS) ---
        import subprocess
        rc = subprocess.run([sys.executable, "m1_logic/unsat_core.py",
                             "data/instance_slice.json"], cwd=repo_root).returncode
        if rc != 0:
            sys.exit("[run_all] LOI: m1_logic/unsat_core.py that bai")

        from m1_logic.bang_logic_to_lp import (
            availability_constraint, exact_capacity,
        )
        import pulp

        model = pulp.LpProblem("worked_example_check", pulp.LpMinimize)
        invigilators_toy = ["CB1", "CB2"]
        shift_toy = "s"
        x = pulp.LpVariable.dicts(
            "x", [(i, shift_toy) for i in invigilators_toy], cat="Binary",
        )
        model += availability_constraint(x, "CB1", shift_toy)
        model += exact_capacity(x, invigilators_toy, shift_toy, 1)
        model += 0
        model.solve(pulp.PULP_CBC_CMD(msg=False))
        lp_result = {i: int(x[i, shift_toy].value()) for i in invigilators_toy}
        print(f"\n[m1_lp] Worked example LP: {lp_result}")
        assert lp_result == {"CB1": 0, "CB2": 1}, "LP khong khop SAT!"
        print("[m1_lp] OK - LP khop SAT (a1=0, a2=1)\n")

    if a.stage in ("all", "m2"):
        pass  # TODO: m2_ilp    -> build & solve the seeded ILP, report fairness vs baseline
    if a.stage in ("all", "m3"):
        pass  # TODO: m3_automata-> load DFAs, product/minimization, regular->ILP, pumping
    if a.stage in ("all", "m4"):
        pass  # TODO: m4_dynamics-> recurrence, equilibrium, stability, plots
    if a.stage in ("all", "m5"):
        pass  # TODO: (optional) precompute artifacts the Streamlit app loads

    print(f"[run_all] seed={a.seed} stage={a.stage}: done.")


if __name__ == "__main__":
    main()
