#!/usr/bin/env python3
"""
m2_ilp/soft.py — Module 2, yêu cầu 2.5: hai ràng buộc mềm thành hàm phạt.

Tác giả gốc: 2551907 Trần Tuấn Kiệt (commit 221301f).
Đã vá ba chỗ, xem phần "NHỮNG GÌ ĐÃ SỬA" ở dưới.

S1 — ưu tiên cơ sở (spec.md §3):
        Viol_loc(i,j) ≡ Assign(i,j) ∧ ca j ở cơ sở khác nguyện vọng của i
        góp vào objective:  w_loc · Σ_{i,j} Viol_loc(i,j)
    Người có nguyện vọng `balanced` (prefer_campus = None) KHÔNG có vi phạm nào —
    đúng định nghĩa, vì họ không ưu tiên cơ sở nào.

S2 — giới hạn mệt mỏi (spec.md §3):
        Viol_load(i) ≡ Load(i) > MaxLoad(i)
        góp vào objective:  w_load · Σᵢ Viol_load(i)
    Ở đây Viol_load(i) là biến NGUYÊN đo lượng vượt, không phải cờ nhị phân:
    vượt 2 ca bị phạt gấp đôi vượt 1 ca. `spec.md` chỉ nói "n > m → Viol_load(i)"
    nên cả hai cách đều đọc được từ đặc tả; chọn dạng nguyên vì nó khiến solver
    thực sự giảm mức vượt thay vì chấp nhận vượt thật nhiều cho cùng một mức phạt.

NHỮNG GÌ ĐÃ SỬA so với bản gốc
------------------------------
1. **Trọng số sai số.** Bản gốc tự rút `rng.uniform(0.5, 2.0)` và KHÔNG làm tròn,
   ra 0.7054693790735072 / 1.624761211975245. `tools/make_seed.py` (và script
   chấm, vốn trùng nhau từng byte) làm tròn 2 chữ số → 0.71 / 1.62 / 1.33.
   Lệch ngay từ trọng số thì mọi con số trong báo cáo lệch theo và người chấm
   tính lại sẽ không ra cùng kết quả. Nay lấy qua `model.soft_weights_from_seed`,
   một nguồn duy nhất.
2. **Bỏ sót trọng số thứ ba.** Bản gốc gán `_` cho trọng số 3. Đề cho đúng ba
   trọng số; số thứ ba dùng cho số hạng công bằng L1 ở pha 2 của `model.py`.
3. **MaxLoad cứng bằng 3.** Bản gốc nhận `max_load: int = 3`. Dữ liệu thật có
   `instance["max_load"]` theo TỪNG người (lát 28/05/2026: mọi người = 2). Nay
   đọc từ dữ liệu; tham số `max_load_mac_dinh` chỉ còn là lưới an toàn.
4. Thang nhân đổi từ 1000 về `model.SCALE` (= 100) để dùng chung một thang với
   số hạng công bằng — trộn hai thang khác nhau trong cùng objective thì trọng số
   mất ý nghĩa tương đối.
"""
from __future__ import annotations

from typing import Any

try:
    from m2_ilp.model import SCALE, soft_weights_from_seed
except ModuleNotFoundError:          # khi chay truc tiep `python m2_ilp/soft.py`
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from m2_ilp.model import SCALE, soft_weights_from_seed


def _as_int_coef(w: float) -> int:
    return int(round(w * SCALE))


def build_soft_penalty_terms(
    model,
    x: dict,
    params: dict,
    seed_int: int,
    max_load_mac_dinh: int = 2,
) -> list:
    """Trả danh sách biểu thức phạt (đã nhân hệ số nguyên) để cộng vào Minimize().

    model   — cp_model.CpModel()
    x       — dict biến nhị phân x[(i, j)]
    params  — đầu ra của m2_ilp.model.build_params() (gộp preprocess + instance)
    """
    I: list = params.get("I", [])
    J: list = params.get("J", [])
    campus: dict = params.get("campus", {})
    preferences: dict = params.get("preferences", {})
    max_load: dict = params.get("max_load", {}) or {}

    w_loc, w_load, _w_fair = soft_weights_from_seed(seed_int)
    c_loc, c_load = _as_int_coef(w_loc), _as_int_coef(w_load)

    cac_hang_phat: list = []

    # ---- S1: ưu tiên cơ sở ----
    for i in I:
        pref_campus = preferences.get(i, {}).get("prefer_campus")
        if not pref_campus:          # balanced -> không có nguyện vọng -> không vi phạm
            continue
        for j in J:
            co_so_ca = campus.get(j)
            if co_so_ca and co_so_ca != pref_campus:
                cac_hang_phat.append(c_loc * x[i, j])

    # ---- S2: giới hạn mệt mỏi ----
    for i in I:
        nguong = int(max_load.get(i, max_load_mac_dinh))
        vuot = model.NewIntVar(0, len(J), f"viol_load_S2[{i}]")
        tong_ca = sum(x[i, j] for j in J)
        # vuot >= tong_ca - nguong, và vuot >= 0 do miền biến -> vuot = max(0, ...)
        # trong bài toán TỐI THIỂU hóa nên solver luôn đẩy vuot xuống cận dưới.
        model.Add(vuot >= tong_ca - nguong)
        cac_hang_phat.append(c_load * vuot)

    return cac_hang_phat


# ---------------------------------------------------------------------------
# Tự kiểm: trọng số phải trùng tools/make_seed.py từng số
# ---------------------------------------------------------------------------
def _tu_kiem() -> int:
    import subprocess
    import sys
    from pathlib import Path

    goc = Path(__file__).resolve().parent.parent
    team_id = "CO2011-261-A01-2551905"
    seed_int = int((goc / "data" / "seed.txt").read_text(encoding="utf-8-sig").strip())

    cua_toi = soft_weights_from_seed(seed_int)
    ra = subprocess.run([sys.executable, str(goc / "tools" / "make_seed.py"),
                         team_id, "--weights"],
                        capture_output=True, text=True, check=True).stdout
    chinh_thuc = eval(ra.split("soft_weights =")[1].strip())  # noqa: S307 - đọc list số

    print(f"  make_seed.py  : {chinh_thuc}")
    print(f"  soft.py dùng  : {cua_toi}")
    if cua_toi != chinh_thuc:
        print("  HỎNG — trọng số KHÁC script chấm")
        return 1
    print("  ĐẠT — trùng từng số")
    return 0


if __name__ == "__main__":
    raise SystemExit(_tu_kiem())
