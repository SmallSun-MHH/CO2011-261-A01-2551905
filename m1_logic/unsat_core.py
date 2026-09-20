#!/usr/bin/env python3
"""
unsat_core.py — Yêu cầu 1.2 (phần UNSAT): trích MINIMAL unsatisfiable core.

Nhiệm vụ 4 trong IAP_tracker. Đi chung cặp với cnf_encoder.py (nhiệm vụ 3):
cnf_encoder lo nhánh SAT và báo cáo model, file này lo nhánh UNSAT và báo cáo
lõi bất khả thỏa tối thiểu.

    python m1_logic/unsat_core.py                      # tự dò ngưỡng bất khả thỏa
    python m1_logic/unsat_core.py --pool 8             # ép còn 8 giám thị
    python m1_logic/unsat_core.py --maxload 1          # ép trần 1 ca/người/ngày

Đọc cùng một file instance mà slice_builder.py sinh ra (data/instance_slice.json),
nên không phải duy trì hai định dạng dữ liệu.

------------------------------------------------------------------------------
HAI ĐIỂM PHẢI TỰ GIẢI THÍCH TRONG DECISIONS.md — AI không viết thay được
------------------------------------------------------------------------------
[GT-1] Vì sao lát nguyên bản LUÔN khả thỏa.
       capacity[j] của slice_builder đúng bằng số người thực tế được xếp vào ca j
       trong lịch gốc, mà lịch gốc là một lời giải hợp lệ có thật. Nên baseline
       chính là một nhân chứng SAT. Muốn có UNSAT thì BẮT BUỘC phải siết thêm —
       không thể cứ cắt bừa rồi mong nó bất khả thỏa.

[GT-2] Vì sao phép siết ở đây là tình huống vận hành CÓ THẬT, không phải bịa.
       Thu hẹp tập giám thị mô phỏng ngày có dịch bệnh / trùng lịch hội đồng,
       khi chỉ còn một phần nhân sự trực được. Câu hỏi mà nhà quản lý thật sự
       hỏi là: "còn bao nhiêu người thì lịch vẫn xếp được?" — và ngưỡng N* mà
       script này dò ra chính là câu trả lời.
------------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Glucose3


# ==========================================================================
# 1. Mã hóa CNF — mỗi NHÓM ràng buộc gắn một selector literal
# ==========================================================================
# Vì sao cần selector: solver chỉ trả về số hiệu biến, không trả về tên luật.
# Ta viết lại mỗi mệnh đề C thành (¬s ∨ C) với s là một biến mới đại diện cho
# nhóm luật đó, rồi giải với assumptions = [tất cả s]. Core trả về là tập con
# các s, ánh xạ ngược ra tên luật đọc được.
class Encoding:
    def __init__(self):
        self.pool = IDPool()
        self.groups: dict[str, list[list[int]]] = {}
        self.kind: dict[str, str] = {}

    def x(self, i: str, j: str) -> int:
        """x[i][j] = 1 nếu giám thị i coi ca j."""
        return self.pool.id(("x", i, j))

    def sel(self, name: str) -> int:
        return self.pool.id(("sel", name))

    def add(self, name: str, kind: str, clauses: list[list[int]]):
        if not clauses:          # nhóm rỗng thì bỏ qua, tránh làm bẩn core
            return
        self.groups[name] = [list(c) for c in clauses]
        self.kind[name] = kind

    def cnf(self, active: list[str]) -> list[list[int]]:
        out = []
        for name in active:
            s = self.sel(name)
            for c in self.groups[name]:
                out.append([-s] + c)
        return out


def derive_busy(inst: dict) -> list[list[str]]:
    """Suy ra Busy(i,j) từ lịch gốc — vá chỗ slice_builder.py để trống.

    Lập luận: nếu giám thị i ĐÃ được xếp vào ca j trong lịch thật, và ca k
    chồng giờ với ca j, thì tại ca k người đó thật sự không khả dụng. Đây là
    suy luận từ dữ liệu, không phải giả định bịa ra.

    Nếu bỏ bước này thì nhóm ràng buộc availability rỗng, và lõi bất khả thỏa
    sẽ không bao giờ chứa mệnh đề availability — lệch hẳn với dạng lõi mà đề
    bài mô tả (một availability + một capacity + một eligibility).
    """
    if inst.get("busy"):
        return inst["busy"]
    ke = defaultdict(set)
    for a, b in inst.get("overlap", []):
        ke[a].add(b)
        ke[b].add(a)
    ra = set()
    for i, j in inst.get("baseline", []):
        for k in ke[j]:
            ra.add((i, k))
    return sorted([i, k] for i, k in ra)


def build(inst: dict, pool_size: int | None = None,
          maxload: int | None = None) -> Encoding:
    """Dịch instance thành CNF theo đúng H1–H5 trong m1_logic/spec.md."""
    enc = Encoding()
    I_full = list(inst["invigilators"])
    J = list(inst["shifts"])
    cap = inst["capacity"]
    campus_of = inst.get("campus_of", {})
    overlap = [tuple(p) for p in inst.get("overlap", [])]
    eligible = {tuple(p) for p in inst.get("eligible", [])} or None

    # --- Phép siết 1: thu hẹp tập giám thị trực được ---
    # Người bị loại = không khả dụng CẢ NGÀY -> mệnh đề đơn vị, họ availability.
    I = I_full if pool_size is None else I_full[:pool_size]
    for i in I_full[len(I):]:
        enc.add(f"UNAVAIL[{i} nghỉ cả ngày]", "availability",
                [[-enc.x(i, j)] for j in J])

    # --- H2 khả dụng: Busy(i,j) -> ¬Assign(i,j) ---
    for i, j in derive_busy(inst):
        if i in I and j in J:
            enc.add(f"AVAIL[{i}@{j}]", "availability", [[-enc.x(i, j)]])

    # --- H3 đủ điều kiện: Assign(i,j) -> Eligible(i,j) ---
    if eligible is not None:
        for i in I:
            for j in J:
                if (i, j) not in eligible:
                    enc.add(f"ELIG[{i}@{j}]", "eligibility", [[-enc.x(i, j)]])

    # --- H4 toàn vẹn: chỉ xếp vào ca đã có cơ sở xác định ---
    for j in J:
        if not campus_of.get(j):
            enc.add(f"CAMPUS[{j} thiếu cơ sở]", "well-formedness",
                    [[-enc.x(i, j)] for i in I])

    # --- H5 sức chứa: đúng cap[j] người mỗi ca ---
    # Tách at-least và at-most thành hai nhóm để lõi chỉ được ra là THIẾU người
    # hay THỪA người — thông tin này quan trọng khi biện luận trong report.
    for j in J:
        lits = [enc.x(i, j) for i in I]
        k = cap[j]
        if not lits:
            continue
        # at-least-k: nếu k lớn hơn số người còn lại thì ràng buộc tự mâu thuẫn
        # -> mã hóa bằng mệnh đề rỗng (chỉ còn ¬selector). pysat không nhận bound > n.
        if k > len(lits):
            ge_cl = [[]]
        elif k > 0:
            ge_cl = list(CardEnc.atleast(lits=lits, bound=k, vpool=enc.pool,
                                         encoding=EncType.seqcounter).clauses)
        else:
            ge_cl = []
        # at-most-k: k >= n thì luôn đúng, không cần mệnh đề nào
        le_cl = [] if k >= len(lits) else list(
            CardEnc.atmost(lits=lits, bound=k, vpool=enc.pool,
                           encoding=EncType.seqcounter).clauses)
        enc.add(f"CAP_GE[{j} cần >= {k}]", "capacity", ge_cl)
        enc.add(f"CAP_LE[{j} cần <= {k}]", "capacity", le_cl)

    # --- H1 không trùng ca chồng giờ ---
    da_xet = set()
    for j, k in overlap:
        if j == k or (k, j) in da_xet:
            continue
        da_xet.add((j, k))
        for i in I:
            enc.add(f"OVERLAP[{i}: {j} vs {k}]", "eligibility",
                    [[-enc.x(i, j), -enc.x(i, k)]])

    # --- Phép siết 2: trần số ca mỗi người (S2 chuyển thành ràng buộc CỨNG) ---
    if maxload is not None:
        for i in I:
            lits = [enc.x(i, j) for j in J]
            if maxload >= len(lits):
                continue
            le = CardEnc.atmost(lits=lits, bound=maxload, vpool=enc.pool,
                                encoding=EncType.seqcounter)
            enc.add(f"MAXLOAD[{i} <= {maxload} ca]", "fatigue", list(le.clauses))

    return enc


# ==========================================================================
# 2. Giải, trích lõi, tối thiểu hóa
# ==========================================================================
def solve(enc: Encoding, gia_dinh: list[str]):
    """Trả về (sat, model) hoặc (False, core_dạng_tên)."""
    with Glucose3(bootstrap_with=enc.cnf(gia_dinh)) as s:
        assumps = [enc.sel(n) for n in gia_dinh]
        if s.solve(assumptions=assumps):
            return True, s.get_model()
        nguoc = {enc.sel(n): n for n in gia_dinh}
        core = s.get_core() or []
        return False, sorted(nguoc[abs(l)] for l in core if abs(l) in nguoc)


def minimize(enc: Encoding, core: list[str]) -> list[str]:
    """Deletion-based MUS.

    QUAN TRỌNG: solver.get_core() KHÔNG tối thiểu, nó chỉ là MỘT tập con bất
    khả thỏa. Đề bài đòi chữ "minimal", nên phải co lại: thử bỏ từng phần tử,
    còn UNSAT thì bỏ hẳn, thành SAT thì phần tử đó thiết yếu và phải giữ.
    Số lần gọi solver là O(|core|).
    """
    mus = list(core)
    i = 0
    while i < len(mus):
        thu = mus[:i] + mus[i + 1:]
        sat, _ = solve(enc, thu)
        if not sat:
            mus = thu            # bỏ được -> giữ nguyên i
        else:
            i += 1               # phải giữ -> xét phần tử kế
    return mus


def verify_minimal(enc: Encoding, mus: list[str]) -> list[dict]:
    """Bằng chứng CHẠY ĐƯỢC cho tính tối thiểu — đúng thứ tiêu chí Rigor đòi.

    Toàn bộ MUS phải UNSAT, và bỏ BẤT KỲ phần tử nào cũng phải SAT trở lại.
    """
    rows = []
    sat, _ = solve(enc, mus)
    rows.append({"bo_ra": None, "ket_qua": "SAT" if sat else "UNSAT",
                 "mong_doi": "UNSAT", "dat": not sat})
    for c in mus:
        sat, _ = solve(enc, [d for d in mus if d != c])
        rows.append({"bo_ra": c, "ket_qua": "SAT" if sat else "UNSAT",
                     "mong_doi": "SAT", "dat": sat})
    return rows


def tim_nguong(inst: dict, maxload: int | None) -> int:
    """Tìm N* = số giám thị LỚN NHẤT mà lịch vẫn bất khả thỏa.

    Tính đơn điệu: tập giám thị càng lớn càng dễ xếp, nên UNSAT với mọi N <= N*
    và SAT với mọi N > N*. Do đó chặt nhị phân được.
    """
    n = len(inst["invigilators"])
    lo, hi, ket_qua = 0, n, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        enc = build(inst, pool_size=mid, maxload=maxload)
        sat, _ = solve(enc, sorted(enc.groups))
        if not sat:
            ket_qua, lo = mid, mid + 1
        else:
            hi = mid - 1
    return ket_qua


# ==========================================================================
# 3. Chạy
# ==========================================================================
def main():
    ap = argparse.ArgumentParser(description="Trích minimal unsat core cho yêu cầu 1.2")
    ap.add_argument("instance", nargs="?", default="data/instance_slice.json")
    ap.add_argument("--pool", type=int, default=None,
                    help="ép tập giám thị còn N người (phép siết)")
    ap.add_argument("--maxload", type=int, default=None,
                    help="ép trần số ca mỗi người (phép siết)")
    ap.add_argument("--out", default="m1_logic/out")
    a = ap.parse_args()

    inst = json.loads(Path(a.instance).read_text(encoding="utf-8"))
    I, J = inst["invigilators"], inst["shifts"]
    print(f"Instance : {a.instance}")
    print(f"  ngày {inst['meta']['date']} · {len(I)} giám thị · {len(J)} ca · "
          f"tổng sức chứa {sum(inst['capacity'].values())}")
    suy_ra = derive_busy(inst)
    print(f"  Busy suy ra từ lịch gốc: {len(suy_ra)} cặp "
          f"({'có sẵn trong file' if inst.get('busy') else 'file để trống, tự suy ra'})")
    if len(I) >= 3:
        print(f"  [đối chiếu Appendix A M1/Q1] at-most-2 vét cạn trên {len(I)} người "
              f"cần C({len(I)},3) = {math.comb(len(I), 3):,} mệnh đề cho MỘT ca")

    # --- Bước 1: xác nhận lát nguyên bản KHẢ THỎA ---
    enc0 = build(inst)
    sat0, _ = solve(enc0, sorted(enc0.groups))
    print(f"\n[1] Lát nguyên bản: {'SAT' if sat0 else 'UNSAT'}"
          f"{'  (đúng như dự đoán — lịch gốc là nhân chứng)' if sat0 else ''}")

    # --- Bước 2: siết cho tới khi bất khả thỏa ---
    pool, maxload = a.pool, a.maxload
    if pool is None and maxload is None:
        pool = tim_nguong(inst, None)
        if pool < 0:
            print("Không siết được thành UNSAT bằng cách thu hẹp tập giám thị.")
            return 1
        print(f"[2] Dò ngưỡng: lịch bất khả thỏa khi tập trực còn <= {pool} người "
              f"(N* = {pool}/{len(I)})")
    else:
        print(f"[2] Siết theo tham số: pool={pool} · maxload={maxload}")

    enc = build(inst, pool_size=pool, maxload=maxload)
    ten = sorted(enc.groups)
    n_cl = sum(len(v) for v in enc.groups.values())
    theo_ho = defaultdict(int)
    for t in ten:
        theo_ho[enc.kind[t]] += 1
    print(f"    {len(ten)} nhóm ràng buộc · {n_cl:,} mệnh đề CNF")
    for k, v in sorted(theo_ho.items()):
        print(f"      {k:<16} {v} nhóm")

    sat, kq = solve(enc, ten)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if sat:
        print("\n[3] Vẫn SAT — chưa đủ siết. Giảm --pool hoặc --maxload.")
        return 1

    # --- Bước 3: lõi thô -> tối thiểu hóa ---
    print(f"\n[3] Lõi THÔ từ solver: {len(kq)} nhóm (chưa tối thiểu)")
    mus = minimize(enc, kq)
    print(f"[4] Sau deletion-based MUS: {len(mus)} nhóm")
    for t in mus:
        print(f"      [{enc.kind[t]:<15}] {t}")

    # --- Bước 4: chứng minh tính tối thiểu bằng code ---
    print("\n[5] Kiểm chứng tính tối thiểu:")
    rows = verify_minimal(enc, mus)
    for r in rows:
        nhan = "toàn bộ MUS" if r["bo_ra"] is None else f"bỏ {r['bo_ra']}"
        print(f"      {'ĐẠT ' if r['dat'] else 'HỎNG'} {nhan:<48} -> {r['ket_qua']}")
    if not all(r["dat"] for r in rows):
        print("\nCHƯA tối thiểu — không được đánh dấu Xong trong bảng theo dõi.")
        return 1

    ho = sorted({enc.kind[t] for t in mus})
    print(f"\n[6] Lõi gồm {len(mus)} mệnh đề thuộc {len(ho)} họ: {', '.join(ho)}")
    print("    Kết luận duy nhất được phép rút ra (Appendix A M1/Q2, đáp án C):")
    print("    LÁT NÀY bất khả thỏa; muốn khả thi phải BỎ hoặc NỚI một trong các")
    print("    luật trên. Không hàm mục tiêu nào và không phép nới lỏng LP nào cứu được.")

    out = {
        "instance": a.instance,
        "team_id": inst["meta"].get("team_id"),
        "lat_nguyen_ban_sat": sat0,
        "phep_siet": {"pool": pool, "maxload": maxload,
                      "tong_giam_thi": len(I),
                      "nguong_N_sao": pool if a.pool is None and a.maxload is None else None},
        "busy_suy_ra_tu_baseline": len(suy_ra),
        "satisfiable": False,
        "core_tho": kq,
        "unsat_core": mus,
        "ho_rang_buoc": {t: enc.kind[t] for t in mus},
        "kiem_chung_toi_thieu": rows,
    }
    p = Path(a.out) / "unsat_core.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
