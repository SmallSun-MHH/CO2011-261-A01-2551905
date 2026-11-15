"""Module 4 — Vòng lặp đóng Rolling-Horizon kết nối M4-A với M2 ILP (Task 18).

Tác giả Chính: Nguyễn Hoàng Long (2551909) · Phối hợp: Trần Anh Khôi (2551905)

Mô tả:
    Thực thi vòng lặp đóng (closed-loop rolling-horizon) qua N kỳ thi liên tiếp:
      1. Đầu kỳ n, đọc vector mệt mỏi hiện tại F^(n) và tổng tải tích lũy W^(n).
      2. Ánh xạ sang trọng số phản hồi từng giám thị lambda_i^(n) thông qua hàm
         đơn điệu bị chặn compute_feedback_lambdas() từ m4_dynamics.recurrence.
      3. Gọi trực tiếp hàm solve_week(params, lambdas) của Module 2 (m2_ilp/model.py)
         mà KHÔNG sửa đổi bất kỳ ràng buộc cứng C1..C5 nào của M2.
      4. Thu nhận tải thực tế l_{i,n} = sum_j x_{i,j,n}, kiểm tra 5/5 ràng buộc cứng,
         cập nhật tổng tải tích lũy W_{i,n+1} và trạng thái mệt mỏi F_{i,n+1}.
      5. Đối chiếu định lượng giữa Vòng lặp đóng (Closed-loop, lambda_i > 0) và
         Vòng lặp mở (Open-loop, lambda_i = 0) trên các thước đo công bằng:
         Jain's Fairness Index, hệ số Gini, độ trải cực đại (Max-Min Spread) và L1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from m2_ilp.model import build_params, solve_week
from m2_ilp.preprocess import run as run_preprocess
from m4_dynamics.recurrence import (
    compute_feedback_lambdas,
    load_or_fit_params,
    step_fatigue_vector,
)

OUT_DIR = Path(__file__).resolve().parent / "out"
DEFAULT_INSTANCE = ROOT / "data" / "instance_slice.json"
SEED_INT = 43003334


def load_m2_params(instance_path: Path = DEFAULT_INSTANCE, seed_int: int = SEED_INT) -> dict[str, Any]:
    """Đọc instance_slice.json, chạy preprocess M2 và trả về dict params cho solve_week."""
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8-sig"))
    m2_data = run_preprocess(instance, seed_int=seed_int)
    return build_params(instance, m2_data)


def jain_index(values: np.ndarray) -> float:
    """Chỉ số công bằng Jain: J(x) = (sum x_i)^2 / (|I| * sum x_i^2) in (0, 1]."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n == 0:
        return 1.0
    denom = float(n * np.sum(arr ** 2))
    if denom <= 1e-15:
        return 1.0
    return float((np.sum(arr) ** 2) / denom)


def gini_index(values: np.ndarray) -> float:
    """Hệ số bất bình đẳng Gini in [0, 1); bằng 0 khi phân phối hoàn toàn đồng đều."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    mean_val = float(np.mean(arr))
    if n == 0 or mean_val <= 1e-15:
        return 0.0
    diff_sum = float(np.sum(np.abs(arr[:, None] - arr[None, :])))
    return diff_sum / (2.0 * n * n * mean_val)


def run_rolling_horizon_mode(
    params: dict[str, Any],
    calib: dict[str, Any],
    n_periods: int = 60,
    closed_loop: bool = True,
    initial_fatigue: np.ndarray | None = None,
    gamma: float = 1.40,
) -> dict[str, Any]:
    """Chạy mô phỏng rolling-horizon qua n_periods kỳ thi (closed-loop hoặc open-loop)."""
    inv_ids = list(params["I"])
    n_inv = len(inv_ids)
    a = float(calib["a"])
    b = float(calib["b"])
    r = float(calib["r"])
    max_load = float(calib.get("max_load_ref", calib.get("max_load", 2.0)))
    f_star = float(calib["F_star"])

    # Khởi tạo trạng thái mệt mỏi ban đầu F^(0) phân tán thực tế quanh F*
    if initial_fatigue is not None:
        f_eff = np.asarray(initial_fatigue, dtype=float).copy()
    else:
        rng = np.random.default_rng(43003334)
        f_eff = np.clip(f_star + rng.uniform(-0.45, 0.55, size=n_inv), 0.1, 2.8)
    f_raw = f_eff.copy()

    cum_load = np.zeros(n_inv, dtype=int)
    history_f_eff: list[list[float]] = [
        [round(float(x), 6) for x in f_eff]
    ]
    history_f_raw: list[list[float]] = [
        [round(float(x), 6) for x in f_raw]
    ]
    history_loads: list[list[int]] = []
    history_cum_load: list[list[int]] = [[0] * n_inv]
    history_lambdas: list[list[float]] = []
    period_metrics: list[dict[str, Any]] = []

    all_hard_ok = True

    for step in range(n_periods):
        f_eff_dict = {inv_ids[idx]: float(f_eff[idx]) for idx in range(n_inv)}
        f_raw_dict = {inv_ids[idx]: float(f_raw[idx]) for idx in range(n_inv)}
        if history_loads:
            recent_5 = np.sum(np.asarray(history_loads[-5:], dtype=int), axis=0)
        else:
            recent_5 = np.zeros(n_inv, dtype=int)
        cum_dict = {
            inv_ids[idx]: (int(recent_5[idx]), int(cum_load[idx]))
            for idx in range(n_inv)
        }

        if closed_loop:
            lam_map = compute_feedback_lambdas(
                F_curr=f_eff_dict,
                cum_load=cum_dict,
                gamma=gamma,
            )
            lam_vec = [float(lam_map[i_id]) for i_id in inv_ids]
        else:
            lam_map = None
            lam_vec = [0.0] * n_inv

        history_lambdas.append([round(x, 6) for x in lam_vec])

        sol = solve_week(params, lambdas=lam_map, seed_int=SEED_INT, verbose=False)
        hard_ok = bool(sol.get("kiem_rang_buoc_cung", {}).get("tat_ca_dat", False))
        if not hard_ok:
            all_hard_ok = False

        loads_step = np.array(
            [int(sol["load"][i_id]) for i_id in inv_ids],
            dtype=int,
        )
        cum_load = cum_load + loads_step
        history_loads.append([int(x) for x in loads_step])
        history_cum_load.append([int(x) for x in cum_load])

        # Trung bình trượt trên cửa sổ chu kỳ xoay vòng W = 6 kỳ (từ các nghiệm nguyên
        # thực tế của solve_week; khi step + 1 < 6 thì bù phần chưa qua bằng l_bar)
        cycle_w = 6
        recent_loads = np.asarray(history_loads[-cycle_w:], dtype=float)
        if len(recent_loads) < cycle_w:
            pad_count = cycle_w - len(recent_loads)
            window_avg_load = (
                np.sum(recent_loads, axis=0) + pad_count * float(calib["l_bar"])
            ) / float(cycle_w)
        else:
            window_avg_load = np.mean(recent_loads, axis=0)

        avg_load_dict = {inv_ids[idx]: float(window_avg_load[idx]) for idx in range(n_inv)}
        raw_load_dict = {inv_ids[idx]: float(loads_step[idx]) for idx in range(n_inv)}

        # 1) Quỹ đạo mệt mỏi hiệu dụng F_eff (điều khiển bởi tải trung bình chu kỳ W=6 đóng vòng)
        f_eff_next = step_fatigue_vector(f_eff_dict, avg_load_dict, a, b, r, max_load)
        f_eff = np.array([f_eff_next[i_id] for i_id in inv_ids], dtype=float)
        # 2) Quỹ đạo mệt mỏi xung tức thời F_raw (điều khiển bởi tải nguyên từng kỳ l_{i,n})
        f_raw_next = step_fatigue_vector(f_raw_dict, raw_load_dict, a, b, r, max_load)
        f_raw = np.array([f_raw_next[i_id] for i_id in inv_ids], dtype=float)

        history_f_eff.append([round(float(x), 6) for x in f_eff])
        history_f_raw.append([round(float(x), 6) for x in f_raw])

        max_err_f_star = float(np.max(np.abs(f_eff - f_star)))
        mean_err_f_star = float(abs(np.mean(f_eff) - f_star))
        lyapunov_v = float(np.sum((f_eff - f_star) ** 2))

        period_metrics.append({
            "period": step + 1,
            "status": sol["status"],
            "hard_constraints_ok": hard_ok,
            "objective": round(float(sol["objective"]), 4),
            "load_min": int(np.min(loads_step)),
            "load_max": int(np.max(loads_step)),
            "cum_load_spread": int(np.max(cum_load) - np.min(cum_load)),
            "cum_load_l1": round(float(np.sum(np.abs(cum_load - np.mean(cum_load)))), 4),
            "cum_load_jain": round(jain_index(cum_load), 6),
            "cum_load_gini": round(gini_index(cum_load), 6),
            "fatigue_eff_mean": round(float(np.mean(f_eff)), 6),
            "fatigue_eff_spread": round(float(np.max(f_eff) - np.min(f_eff)), 6),
            "fatigue_eff_jain": round(jain_index(f_eff), 6),
            "fatigue_eff_gini": round(gini_index(f_eff), 6),
            "max_abs_err_to_F_star": round(max_err_f_star, 6),
            "mean_abs_err_to_F_star": round(mean_err_f_star, 6),
            "lyapunov_V": round(lyapunov_v, 8),
            "fatigue_raw_mean": round(float(np.mean(f_raw)), 6),
            "fatigue_raw_spread": round(float(np.max(f_raw) - np.min(f_raw)), 6),
        })

    final_metric = period_metrics[-1]
    return {
        "mode": "closed_loop" if closed_loop else "open_loop",
        "n_periods": n_periods,
        "all_hard_constraints_ok": all_hard_ok,
        "invigilator_ids": inv_ids,
        "F_star": round(f_star, 6),
        "final_summary": final_metric,
        "final_cum_load_per_invigilator": {
            inv_ids[idx]: int(cum_load[idx]) for idx in range(n_inv)
        },
        "final_fatigue_eff_per_invigilator": {
            inv_ids[idx]: round(float(f_eff[idx]), 6) for idx in range(n_inv)
        },
        "final_fatigue_raw_per_invigilator": {
            inv_ids[idx]: round(float(f_raw[idx]), 6) for idx in range(n_inv)
        },
        "history_fatigue_eff": history_f_eff,
        "history_fatigue_raw": history_f_raw,
        "history_loads": history_loads,
        "history_cum_load": history_cum_load,
        "history_lambdas": history_lambdas,
        "period_metrics": period_metrics,
    }


def run_comparison(
    instance_path: Path = DEFAULT_INSTANCE,
    n_periods: int = 60,
) -> dict[str, Any]:
    """Chạy đối sánh song song Closed-loop và Open-loop trên cùng điều kiện đầu."""
    params = load_m2_params(instance_path)
    calib = load_or_fit_params()

    rng = np.random.default_rng(43003334)
    f0 = np.clip(
        float(calib["F_star"]) + rng.uniform(-0.45, 0.55, size=len(params["I"])),
        0.1,
        2.8,
    )

    closed_res = run_rolling_horizon_mode(
        params=params,
        calib=calib,
        n_periods=n_periods,
        closed_loop=True,
        initial_fatigue=f0,
    )
    open_res = run_rolling_horizon_mode(
        params=params,
        calib=calib,
        n_periods=n_periods,
        closed_loop=False,
        initial_fatigue=f0,
    )

    cl_sum = closed_res["final_summary"]
    ol_sum = open_res["final_summary"]

    payload = {
        "module": "m4_dynamics.rolling_horizon",
        "instance": str(instance_path.relative_to(ROOT)).replace("\\", "/"),
        "n_periods": n_periods,
        "rotation_cycle_period_W": 6,
        "calibration_params": {
            "a": calib["a"],
            "b": calib["b"],
            "r": calib["r"],
            "F_star": calib["F_star"],
            "l_bar": calib["l_bar"],
            "rho_bar": calib["rho_bar"],
            "max_load": calib.get("max_load_ref", calib.get("max_load", 2.0)),
        },
        "initial_fatigue": [round(float(x), 6) for x in f0],
        "comparison_summary": {
            "closed_loop_all_hard_ok": closed_res["all_hard_constraints_ok"],
            "open_loop_all_hard_ok": open_res["all_hard_constraints_ok"],
            "closed_loop_cum_load_spread": cl_sum["cum_load_spread"],
            "open_loop_cum_load_spread": ol_sum["cum_load_spread"],
            "closed_loop_cum_load_jain": cl_sum["cum_load_jain"],
            "open_loop_cum_load_jain": ol_sum["cum_load_jain"],
            "closed_loop_cum_load_gini": cl_sum["cum_load_gini"],
            "open_loop_cum_load_gini": ol_sum["cum_load_gini"],
            "closed_loop_max_err_F_star": cl_sum["max_abs_err_to_F_star"],
            "open_loop_max_err_F_star": ol_sum["max_abs_err_to_F_star"],
            "closed_loop_fatigue_spread": cl_sum["fatigue_eff_spread"],
            "open_loop_fatigue_spread": ol_sum["fatigue_eff_spread"],
            "spread_reduction_ratio": round(
                1.0
                - (cl_sum["fatigue_eff_spread"] / max(ol_sum["fatigue_eff_spread"], 1e-9)),
                6,
            ),
        },
        "closed_loop": closed_res,
        "open_loop": open_res,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "rolling_horizon.json"
    out_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def main() -> int:
    payload = run_comparison(DEFAULT_INSTANCE, n_periods=60)
    cmp_sum = payload["comparison_summary"]
    print("[m4_rolling_horizon] Đối sánh Vòng lặp đóng vs Vòng lặp mở (N = 60 kỳ):")
    print(
        f"  Ràng buộc cứng C1..C5 : Closed-loop OK = {cmp_sum['closed_loop_all_hard_ok']} · "
        f"Open-loop OK = {cmp_sum['open_loop_all_hard_ok']}"
    )
    print(
        f"  Độ lệch tải tích lũy  : Closed-loop spread = {cmp_sum['closed_loop_cum_load_spread']} ca "
        f"(Jain = {cmp_sum['closed_loop_cum_load_jain']:.6f}, Gini = {cmp_sum['closed_loop_cum_load_gini']:.6f})"
    )
    print(
        f"                          Open-loop spread   = {cmp_sum['open_loop_cum_load_spread']} ca "
        f"(Jain = {cmp_sum['open_loop_cum_load_jain']:.6f}, Gini = {cmp_sum['open_loop_cum_load_gini']:.6f})"
    )
    print(
        f"  Sai số hội tụ |F-F*|  : Closed-loop = {cmp_sum['closed_loop_max_err_F_star']:.2e} vs "
        f"Open-loop = {cmp_sum['open_loop_max_err_F_star']:.4f}"
    )
    print("  Đã ghi m4_dynamics/out/rolling_horizon.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
