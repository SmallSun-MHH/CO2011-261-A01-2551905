#!/usr/bin/env python3
"""
tools/check_m2.py — cổng tự kiểm cho Module 2 (LP / ILP), chạy được.

Cùng triết lý với tools/check_m1.py: KHÔNG tin bất cứ khẳng định nào trong
tài liệu, chỉ tin thứ chạy ra kết quả. Mỗi mục in ĐẠT / CẢNH BÁO / HỎNG.

    python tools/check_m2.py            # kiểm tại chỗ
    python tools/check_m2.py --clean    # clone sạch từ origin rồi kiểm

Thoát 0 nếu không có mục HỎNG nào, thoát 1 nếu có — để dùng trong CI hoặc
làm điều kiện trước khi (dời) tag m2.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):  # console Windows mac dinh cp1252
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

DAT, CANH, HONG = "ĐẠT", "CẢNH BÁO", "HỎNG"
_ket_qua: list[tuple[str, str, str]] = []


def bao(muc: str, ten: str, chi_tiet: str) -> None:
    _ket_qua.append((muc, ten, chi_tiet))


def chay(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    """Chạy một lệnh, trả (returncode, stdout+stderr). Không raise."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"quá {timeout}s"
    except OSError as e:
        return 127, str(e)


# ---------------------------------------------------------------------------
# 1. File bắt buộc của M2
# ---------------------------------------------------------------------------
FILE_M2 = ["m2_ilp/preprocess.py", "m2_ilp/model.py", "m2_ilp/soft.py",
           "run_all.py", "data/instance_slice.json", "data/seed.txt",
           "DECISIONS.md", "CONTRIBUTIONS.md"]


def kiem_file(repo: Path) -> None:
    thieu = [f for f in FILE_M2 if not (repo / f).exists()]
    if thieu:
        bao(HONG, "File bắt buộc", "thiếu: " + ", ".join(thieu))
    else:
        bao(DAT, "File bắt buộc", f"đủ {len(FILE_M2)} file")


# ---------------------------------------------------------------------------
# 2. D8: chỉ MỘT chủ sở hữu của Prefer(i,c)
# ---------------------------------------------------------------------------
def kiem_mot_chu_so_huu_prefer(repo: Path) -> None:
    sb = repo / "m1_logic" / "slice_builder.py"
    if sb.exists():
        # Đọc bằng AST, không grep chuỗi: chữ "preference" trong docstring/chú
        # thích KHÔNG phải là sinh dữ liệu. Chỉ tính biến tên `prefer` hoặc
        # khóa dict "prefer" thật sự xuất hiện trong CODE.
        try:
            cay = ast.parse(sb.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bao(HONG, "slice_builder.py", f"lỗi cú pháp: {e}")
            cay = None
        if cay is not None:
            la_docstring = set()
            for n in ast.walk(cay):
                if isinstance(n, (ast.Module, ast.FunctionDef,
                                  ast.AsyncFunctionDef, ast.ClassDef)):
                    if n.body and isinstance(n.body[0], ast.Expr) \
                            and isinstance(getattr(n.body[0], "value", None), ast.Constant) \
                            and isinstance(n.body[0].value.value, str):
                        la_docstring.add(id(n.body[0].value))
            dong = sorted({
                n.lineno for n in ast.walk(cay)
                if (isinstance(n, ast.Name) and n.id == "prefer")
                or (isinstance(n, ast.Constant) and n.value == "prefer"
                    and id(n) not in la_docstring)
            })
            if dong:
                bao(HONG, "D8 một chủ sở hữu",
                    f"slice_builder.py còn sinh 'prefer' (dòng "
                    f"{', '.join(map(str, dong))}) — trái với quyết định D8")
            else:
                bao(DAT, "D8 một chủ sở hữu",
                    "chỉ m2_ilp/preprocess.py sinh Prefer(i,c)")

    inst = repo / "data" / "instance_slice.json"
    if inst.exists():
        d = json.loads(inst.read_text(encoding="utf-8-sig"))
        if "prefer" in d:
            bao(HONG, "instance_slice.json",
                "còn field 'prefer' cũ — sinh lại bằng slice_builder.py")
        else:
            bao(DAT, "instance_slice.json", "không còn field 'prefer'")


# ---------------------------------------------------------------------------
# 3. run_all.py thật sự gọi M2 (không còn là TODO)
# ---------------------------------------------------------------------------
def kiem_run_all_noi_m2(repo: Path) -> None:
    s = (repo / "run_all.py").read_text(encoding="utf-8")
    m = re.search(r'if a\.stage in \("all", "m2"\):(.*?)(?=\n    if a\.stage|\n    print\(f"\[run_all\])',
                  s, re.S)
    if not m:
        bao(HONG, "run_all.py", "không tìm thấy nhánh stage m2")
        return
    than = m.group(1)
    thieu = [ten for ten, pat in (("preprocess", "preprocess"), ("model", "solve_week"))
             if pat not in than]
    if thieu:
        bao(HONG, "run_all.py",
            f"nhánh m2 chưa gọi: {', '.join(thieu)} — người chấm chạy "
            "`python run_all.py` sẽ không đi qua phần đó")
    elif re.search(r"^\s*pass\s*(#|$)", than, re.M):
        bao(CANH, "run_all.py", "nhánh m2 vẫn còn `pass`")
    else:
        bao(DAT, "run_all.py", "nhánh m2 gọi thật preprocess + solve_week")


# ---------------------------------------------------------------------------
# 4. Chạy pipeline & kiểm schema 5 file JSON đầu ra
# ---------------------------------------------------------------------------
SCHEMA = {
    "sets.json":        ("I", "J"),
    "capacity.json":    None,
    "busy.json":        None,
    "campus.json":      None,
    "preferences.json": None,
}
LOAI_PREF = {"near_cs1", "near_cs2", "balanced"}


def kiem_chay_va_schema(repo: Path) -> dict | None:
    seed = (repo / "data" / "seed.txt").read_text(encoding="utf-8-sig").strip()
    rc, out = chay([sys.executable, "run_all.py", "--seed", seed], repo)
    if rc != 0:
        bao(HONG, "run_all.py chạy", f"thoát {rc}\n" + out[-1500:])
        return None
    bao(DAT, "run_all.py chạy", "thoát 0, đi hết cả m1 và m2")

    od = repo / "data" / "processed"
    thieu = [f for f in SCHEMA if not (od / f).exists()]
    if thieu:
        bao(HONG, "Đầu ra M2", "thiếu: " + ", ".join(thieu))
        return None

    sets = json.loads((od / "sets.json").read_text(encoding="utf-8"))
    for khoa in SCHEMA["sets.json"]:
        if khoa not in sets or not sets[khoa]:
            bao(HONG, "sets.json", f"thiếu hoặc rỗng khóa '{khoa}'")
            return None
    I, J = sets["I"], sets["J"]

    cap = json.loads((od / "capacity.json").read_text(encoding="utf-8"))
    cam = json.loads((od / "campus.json").read_text(encoding="utf-8"))
    pref = json.loads((od / "preferences.json").read_text(encoding="utf-8"))
    busy = json.loads((od / "busy.json").read_text(encoding="utf-8"))

    loi = []
    if sorted(cap) != sorted(J):
        loi.append("capacity.json không phủ đúng J")
    if sorted(cam) != sorted(J):
        loi.append("campus.json không phủ đúng J")
    if sorted(pref) != sorted(I):
        loi.append("preferences.json không phủ đúng I")
    if any(not isinstance(v, int) or v < 0 for v in cap.values()):
        loi.append("capacity có giá trị không phải số nguyên >= 0")
    xau = [k for k, v in pref.items() if v.get("category") not in LOAI_PREF]
    if xau:
        loi.append(f"{len(xau)} preference sai loại (phải thuộc {sorted(LOAI_PREF)})")
    cs = sorted(set(cam.values()))
    for i, v in pref.items():
        c = v.get("prefer_campus")
        if v.get("category") == "balanced":
            if c is not None:
                loi.append(f"{i}: balanced nhưng prefer_campus={c!r}")
                break
        elif c not in cs:
            loi.append(f"{i}: prefer_campus={c!r} không có trong dữ liệu {cs}")
            break
    khoa_xau = [k for k in busy if "|" not in k]
    if khoa_xau:
        loi.append(f"busy.json có {len(khoa_xau)} khóa không đúng dạng 'i|j'")

    if loi:
        bao(HONG, "Schema đầu ra M2", " · ".join(loi))
    else:
        bao(DAT, "Schema đầu ra M2",
            f"|I|={len(I)} |J|={len(J)} · 5/5 file đúng schema · "
            f"cơ sở thật: {', '.join(cs)}")
    return {"I": I, "J": J, "pref": pref, "seed": seed}


# ---------------------------------------------------------------------------
# 5. Tái lập: cùng seed -> cùng preference; khác seed -> khác
# ---------------------------------------------------------------------------
def kiem_tai_lap(repo: Path, truoc: dict) -> None:
    goc = json.dumps(truoc["pref"], sort_keys=True, ensure_ascii=False)

    rc, out = chay([sys.executable, "m2_ilp/preprocess.py",
                    "--out-dir", "data/processed_test_same"], repo)
    if rc != 0:
        bao(HONG, "Tái lập", f"chạy lại thất bại (thoát {rc})")
        return
    lai = (repo / "data" / "processed_test_same" / "preferences.json")
    lan2 = json.dumps(json.loads(lai.read_text(encoding="utf-8")),
                      sort_keys=True, ensure_ascii=False)
    if lan2 != goc:
        bao(HONG, "Tái lập", "cùng seed mà ra preference khác nhau")
        return

    # khác seed thì phải ra khác — nếu không, seed không hề được dùng
    tam = repo / "data" / "seed_khac_tmp.txt"
    tam.write_text("1", encoding="utf-8")
    rc, _ = chay([sys.executable, "m2_ilp/preprocess.py",
                  "--seed-file", str(tam),
                  "--out-dir", "data/processed_test_diff"], repo)
    khac_nhau = None
    if rc == 0:
        f = repo / "data" / "processed_test_diff" / "preferences.json"
        khac_nhau = json.dumps(json.loads(f.read_text(encoding="utf-8")),
                               sort_keys=True, ensure_ascii=False) != goc
    tam.unlink(missing_ok=True)
    for d in ("processed_test_same", "processed_test_diff"):
        shutil.rmtree(repo / "data" / d, ignore_errors=True)

    if khac_nhau is False:
        bao(HONG, "Tái lập",
            "đổi seed mà preference không đổi — seed không thật sự được dùng")
    elif khac_nhau is None:
        bao(CANH, "Tái lập", "cùng seed tái lập ĐẠT; chưa kiểm được nhánh đổi seed")
    else:
        bao(DAT, "Tái lập",
            f"cùng seed ({truoc['seed']}) -> giống hệt; đổi seed -> khác")


# ---------------------------------------------------------------------------
# 5b. Trọng số mềm phải TRÙNG tools/make_seed.py từng số (yêu cầu 2.5)
# ---------------------------------------------------------------------------
def kiem_trong_so(repo: Path) -> None:
    ma = (
        "import sys, subprocess, json, re\n"
        "sys.path.insert(0, %r)\n"
        "from m2_ilp.model import soft_weights_from_seed\n"
        "seed = int(open(%r, encoding='utf-8-sig').read().strip())\n"
        "ra = subprocess.run([sys.executable, %r, 'CO2011-261-A01-2551905', '--weights'],"
        " capture_output=True, text=True).stdout\n"
        "ct = [float(v) for v in re.findall(r'[0-9]+\\.[0-9]+', ra.split('soft_weights')[1])]\n"
        "print(json.dumps({'code': soft_weights_from_seed(seed), 'make_seed': ct}))\n"
    ) % (str(repo), str(repo / "data" / "seed.txt"), str(repo / "tools" / "make_seed.py"))
    rc, out = chay([sys.executable, "-c", ma], repo, timeout=120)
    if rc != 0:
        bao(HONG, "Trọng số mềm", f"không kiểm được (thoát {rc})\n" + out[-500:])
        return
    try:
        d = json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        bao(HONG, "Trọng số mềm", "không đọc được kết quả so sánh")
        return
    if d["code"] != d["make_seed"]:
        bao(HONG, "Trọng số mềm",
            f"code dùng {d['code']} nhưng make_seed.py (= script chấm) cho "
            f"{d['make_seed']} — mọi con số trong báo cáo sẽ lệch")
    else:
        bao(DAT, "Trọng số mềm", f"{d['code']} — trùng make_seed.py từng số")

    # không file nào được tự rút trọng số mềm bằng rng riêng
    xau = []
    for f in sorted((repo / "m2_ilp").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        try:
            cay = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "uniform" and f.name != "model.py":
                xau.append(f"{f.name}:{n.lineno}")
    if xau:
        bao(HONG, "Nguồn trọng số",
            "rút trọng số bằng rng riêng tại " + ", ".join(xau) +
            " — phải lấy qua model.soft_weights_from_seed")
    else:
        bao(DAT, "Nguồn trọng số", "một nguồn duy nhất: model.soft_weights_from_seed")


# ---------------------------------------------------------------------------
# 5c. Nghiệm M2: 5 ràng buộc cứng + tính tất định (yêu cầu 2.2-2.4, 2.7)
# ---------------------------------------------------------------------------
def kiem_nghiem_m2(repo: Path) -> None:
    f = repo / "m2_ilp" / "out" / "solution.json"
    if not f.exists():
        bao(HONG, "Nghiệm M2", "không có m2_ilp/out/solution.json sau khi chạy run_all.py")
        return
    sol = json.loads(f.read_text(encoding="utf-8"))

    if not sol.get("feasible"):
        bao(HONG, "Nghiệm M2", f"không khả thi: {sol.get('status')}")
        return
    kiem = sol.get("kiem_rang_buoc_cung", {})
    xau = [k for k, v in kiem.items() if k != "tat_ca_dat" and not v]
    if xau:
        bao(HONG, "Ràng buộc cứng M2", "nghiệm vi phạm: " + ", ".join(xau))
    else:
        fa = sol.get("fairness", {})
        bao(DAT, "Ràng buộc cứng M2",
            f"5/5 ĐẠT trên nghiệm · {len(sol['assignment'])} lượt gán · "
            f"t*={sol.get('t_star')} · tải {fa.get('tai_nho_nhat')}-{fa.get('tai_lon_nhat')} · "
            f"lệch L1={fa.get('lech_L1_quanh_q')}")

    # sĩ số phải khớp tổng capacity
    inst = json.loads((repo / "data" / "instance_slice.json").read_text(encoding="utf-8-sig"))
    tong = sum(int(v) for v in inst["capacity"].values())
    if len(sol["assignment"]) != tong:
        bao(HONG, "Sĩ số M2",
            f"{len(sol['assignment'])} lượt gán nhưng tổng capacity = {tong}")
    else:
        bao(DAT, "Sĩ số M2", f"{tong} lượt gán = đúng tổng capacity")

    # tính tất định: giải lại 2 lần, bảng phân công phải y hệt
    hashes = []
    for k in (1, 2):
        rc, _ = chay([sys.executable, "m2_ilp/model.py", "--time-limit", "30",
                      "--out", f"m2_ilp/out/_tatdinh_{k}.json"], repo, timeout=300)
        if rc != 0:
            bao(CANH, "Tất định M2", "không chạy lại được để so sánh")
            return
        d = json.loads((repo / "m2_ilp" / "out" / f"_tatdinh_{k}.json")
                       .read_text(encoding="utf-8"))
        hashes.append(json.dumps([d["assignment"], d["objective"]], sort_keys=True))
        (repo / "m2_ilp" / "out" / f"_tatdinh_{k}.json").unlink(missing_ok=True)
    if hashes[0] != hashes[1]:
        bao(HONG, "Tất định M2",
            "hai lần giải ra bảng phân công khác nhau — đặt workers=1 trong solve_week")
    else:
        bao(DAT, "Tất định M2", "hai lần giải ra nghiệm y hệt")


# ---------------------------------------------------------------------------
# 5d. requirements.txt phải CÀI ĐƯỢC THẬT (DoD: clone sạch là chạy được)
# ---------------------------------------------------------------------------
PY_TAGS = ("cp311", "cp312")   # phiên bản Python mà bộ ghim này nhắm tới


def kiem_requirements(repo: Path) -> None:
    """Hỏi thẳng PyPI xem từng phiên bản đã ghim có TỒN TẠI và có wheel cho
    Python mục tiêu hay không. Không chạy `pip install --dry-run`: bộ giải phụ
    thuộc của pip mất nhiều phút cho bộ này, quá chậm để làm cổng tự kiểm."""
    import urllib.error
    import urllib.request

    f = repo / "requirements.txt"
    if not f.exists():
        bao(HONG, "requirements.txt", "không có file")
        return
    ghim = [l.strip() for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]
    chua_ghim = [l for l in ghim if "==" not in l]
    if chua_ghim:
        bao(HONG, "requirements.txt", "chưa ghim phiên bản: " + ", ".join(chua_ghim))
        return

    khong_ton_tai, khong_wheel, khong_kiem_duoc = [], [], []
    for dong in ghim:
        goi, ver = dong.split("==", 1)
        try:
            with urllib.request.urlopen(
                    f"https://pypi.org/pypi/{goi}/json", timeout=30) as r:
                d = json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            khong_kiem_duoc.append(goi)
            continue
        rel = d.get("releases", {})
        if ver not in rel:
            gan = sorted(v for v in rel if v.startswith(ver.rsplit(".", 1)[0]))[-3:]
            khong_ton_tai.append(f"{dong} (gần nhất có thật: {', '.join(gan) or '—'})")
            continue
        tep = [x["filename"] for x in rel[ver] if x["packagetype"] == "bdist_wheel"]
        thuan_py = any("-py3-" in t or "-py2.py3-" in t for t in tep)
        if not thuan_py and not any(tag in t for t in tep for tag in PY_TAGS):
            khong_wheel.append(dong)

    if khong_ton_tai:
        bao(HONG, "requirements.txt",
            "phiên bản KHÔNG tồn tại trên PyPI → `pip install -r` thất bại trên "
            "máy sạch: " + " · ".join(khong_ton_tai))
    elif khong_wheel:
        bao(HONG, "requirements.txt",
            f"không có wheel cho {'/'.join(PY_TAGS)}: " + ", ".join(khong_wheel))
    elif khong_kiem_duoc:
        bao(CANH, "requirements.txt",
            f"{len(ghim)} gói đều ghim ==; không hỏi được PyPI về: "
            + ", ".join(khong_kiem_duoc))
    else:
        bao(DAT, "requirements.txt",
            f"{len(ghim)} gói · đều ghim == · đều tồn tại và có wheel cho "
            f"{'/'.join(PY_TAGS)}")


# ---------------------------------------------------------------------------
# 5e. Hồi quy: AddAbsEquality phải trả TRỊ TUYỆT ĐỐI, kể cả khi âm
# ---------------------------------------------------------------------------
def kiem_tri_tuyet_doi(repo: Path) -> None:
    """Chặn đúng lớp lỗi đã gặp ngày 23/10.

    `AddAbsEquality(d, <biểu_thức>)` với một biểu thức affine KHÔNG lấy trị
    tuyệt đối trong ortools 9.12 — nó ràng `d == <biểu_thức>`. Khi biểu thức âm:
    miền d bắt đầu từ 0 -> INFEASIBLE; miền d có số âm -> SAI LẶNG LẼ.
    Hai phép kiểm: (a) chạy thật `_l1_deviation` trên một ca có tải < q;
    (b) quét mã, cấm truyền biểu thức (có dấu − hoặc +) vào AddAbsEquality.
    """
    ma = (
        "import sys, json\n"
        "sys.path.insert(0, %r)\n"
        "from ortools.sat.python import cp_model\n"
        "from m2_ilp.model import _l1_deviation\n"
        "m = cp_model.CpModel()\n"
        "li = m.NewIntVar(0, 4, 'li'); m.Add(li == 0)\n"
        "devs, q = _l1_deviation(m, {'CB': li}, 1, ['a','b','c','d'])\n"
        "s = cp_model.CpSolver(); st = s.Solve(m)\n"
        "print(json.dumps({'status': s.StatusName(st),"
        " 'dev': s.Value(devs[0]) if st in (2,4) else None}))\n"
    ) % str(repo)
    rc, out = chay([sys.executable, "-c", ma], repo, timeout=120)
    if rc != 0:
        bao(HONG, "Trị tuyệt đối L1", f"không chạy được phép kiểm (thoát {rc})\n" + out[-400:])
    else:
        try:
            d = json.loads(out.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            bao(HONG, "Trị tuyệt đối L1", "không đọc được kết quả")
            return
        if d.get("dev") == 1:
            bao(DAT, "Trị tuyệt đối L1", "tải 0 với q=1 -> độ lệch = 1 (đúng)")
        else:
            bao(HONG, "Trị tuyệt đối L1",
                f"tải 0 với q=1 phải cho độ lệch 1, nhưng được "
                f"status={d.get('status')} dev={d.get('dev')} — "
                "AddAbsEquality đang nhận biểu thức thay vì biến")

    xau = []
    for f in sorted((repo / "m2_ilp").glob("*.py")):
        try:
            cay = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in ("AddAbsEquality", "add_abs_equality") \
                    and len(n.args) >= 2 and isinstance(n.args[1], ast.BinOp):
                xau.append(f"{f.name}:{n.lineno}")
    if xau:
        bao(HONG, "AddAbsEquality",
            "truyền BIỂU THỨC (không phải biến) tại " + ", ".join(xau)
            + " — ortools không lấy trị tuyệt đối của biểu thức affine")
    else:
        bao(DAT, "AddAbsEquality", "chỉ nhận biến, không nhận biểu thức affine")


# ---------------------------------------------------------------------------
# 5f. Một nguồn duy nhất cho q, và mọi file M2/M3 đều được run_all.py gọi
# ---------------------------------------------------------------------------
def kiem_mot_nguon_q(repo: Path) -> None:
    xau = []
    for f in sorted((repo / "m2_ilp").glob("*.py")):
        if f.name == "model.py":
            continue
        src = f.read_text(encoding="utf-8")
        if re.search(r'sum\([^)]*capacity[^)]*\)\s*//', src):
            xau.append(f.name)
    if xau:
        bao(HONG, "Một nguồn cho q",
            "tự tính lại tải lý tưởng tại " + ", ".join(xau)
            + " — phải gọi model.tai_ly_tuong(params)")
    else:
        bao(DAT, "Một nguồn cho q", "chỉ model.tai_ly_tuong định nghĩa q")


def kiem_khong_mo_coi(repo: Path) -> None:
    """Người chấm chạy `python run_all.py`. File không được nó gọi coi như chưa có."""
    s = (repo / "run_all.py").read_text(encoding="utf-8")
    can = {
        "m2_ilp/preprocess.py": "preprocess",
        "m2_ilp/model.py": "solve_week",
        "m2_ilp/crosscheck_pulp.py": "crosscheck_pulp",
        "m2_ilp/counterexample_lp_relax.py": "counterexample_lp_relax",
        "m3_automata/strings_from_data.py": "strings_from_data",
        "m2_ilp/baseline.py": "baseline",
        "m2_ilp/benchmark.py": "benchmark",
    }
    mo_coi = [f for f, dau in can.items() if (repo / f).exists() and dau not in s]
    if mo_coi:
        bao(HONG, "File mồ côi",
            "có trong repo nhưng run_all.py không gọi: " + ", ".join(mo_coi))
    else:
        bao(DAT, "File mồ côi", "mọi file M2/M3 đã có đều được run_all.py gọi")

    thieu = [f for f in can if not (repo / f).exists()]
    if thieu:
        bao(CANH, "Đầu việc chưa có file", ", ".join(thieu))


# ---------------------------------------------------------------------------
# 5g. Yêu cầu 2.9 — nghiệm phải KHÔNG THUA lịch gốc ở bất kỳ chỉ số nào
# ---------------------------------------------------------------------------
def kiem_thang_baseline(repo: Path) -> None:
    f = repo / "m2_ilp" / "out" / "benchmark.json"
    if not f.exists():
        bao(HONG, "Thắng baseline (2.9)",
            "không có m2_ilp/out/benchmark.json sau khi chạy run_all.py")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    tk = d.get("tong_ket", {})
    thua = [r["chi_so"] for r in d.get("so_sanh", []) if r["ket_qua"] == "THUA"]
    if thua:
        bao(HONG, "Thắng baseline (2.9)", "THUA lịch gốc ở: " + ", ".join(thua))
    elif not tk.get("thang"):
        bao(HONG, "Thắng baseline (2.9)",
            "hoà toàn bộ — không chứng minh được mô hình hơn lịch gốc")
    else:
        bao(DAT, "Thắng baseline (2.9)",
            f"{tk['thang']} thắng · {tk.get('hoa', 0)} hoà · 0 thua · "
            f"runtime trung vị {d.get('runtime_cpsat', {}).get('trung_vi_s')}s")

    # baseline phai la lich GOC trich tu du lieu, khong phai so bia
    inst = json.loads((repo / "data" / "instance_slice.json").read_text(encoding="utf-8-sig"))
    n_goc = len(inst.get("baseline") or [])
    n_bm = d.get("baseline", {}).get("so_luot_gan")
    if n_goc and n_bm != n_goc:
        bao(HONG, "Nguồn baseline",
            f"benchmark dùng {n_bm} lượt gán nhưng instance['baseline'] có {n_goc}")
    else:
        bao(DAT, "Nguồn baseline",
            f"{n_goc} lượt gán, trích thẳng từ instance['baseline'] (dữ liệu thật)")


# ---------------------------------------------------------------------------
# 6. Ô khuyết trong tài liệu (chỉ người thật điền được)
# ---------------------------------------------------------------------------
O_KHUYET = [("DECISIONS.md", r"\[GT-\d\]"),
            ("README.md", r"\(điền"),
            ("CONTRIBUTIONS.md", r"\(dien\)")]


def kiem_o_khuyet(repo: Path) -> None:
    for ten, pat in O_KHUYET:
        f = repo / ten
        if not f.exists():
            continue
        n = len(re.findall(pat, f.read_text(encoding="utf-8")))
        if n:
            bao(HONG, ten, f"còn {n} ô chưa điền (khớp {pat})")
        else:
            bao(DAT, ten, "không còn ô trống")

    c = repo / "CONTRIBUTIONS.md"
    if c.exists():
        pcts = [int(x) for x in re.findall(r"\|\s*(\d{1,3})%\s*\|", c.read_text(encoding="utf-8"))]
        if pcts and sum(pcts) != 100:
            bao(HONG, "CONTRIBUTIONS %",
                f"cột tỷ lệ đóng góp cộng lại = {sum(pcts)}%, phải bằng 100%")
        elif pcts:
            bao(DAT, "CONTRIBUTIONS %", "cột tỷ lệ cộng lại đúng 100%")


# ---------------------------------------------------------------------------
# 7. Bằng chứng tiến trình: tag tuần & CHECKPOINTS
# ---------------------------------------------------------------------------
def kiem_tien_trinh(repo: Path) -> None:
    rc, out = chay(["git", "tag", "-l"], repo, timeout=60)
    if rc != 0:
        bao(CANH, "Git", "không đọc được tag (không phải repo git?)")
        return
    tags = set(out.split())
    tuan = sorted(t for t in tags if t.startswith("week-"))

    # Mỗi tag tuần THIẾU = −1% điểm môn, không hồi lại được. Phải liệt kê đúng
    # những tuần ĐÃ TRÔI QUA mà không có tag, chứ không chỉ đếm xem có tag nào.
    import datetime
    bat_dau = datetime.date(2026, 9, 7)          # thứ Hai của week-01
    hom_nay = datetime.date.today()
    thieu, dang_dien_ra = [], None
    for n in range(1, 15):
        d1 = bat_dau + datetime.timedelta(days=7 * (n - 1))
        d2 = d1 + datetime.timedelta(days=6)
        if d1 > hom_nay:
            break
        ten = f"week-{n:02d}"
        if ten in tags:
            continue
        if d1 <= hom_nay <= d2:
            dang_dien_ra = (ten, d2)
        else:
            thieu.append(ten)
    if thieu:
        bao(HONG, "Tag tuần THIẾU",
            f"{', '.join(thieu)} — mỗi tag thiếu là −1% điểm môn, KHÔNG tạo tag "
            f"lùi ngày để bù (đã có: {', '.join(tuan) or 'không có'})")
    else:
        bao(DAT, "Tag tuần", ", ".join(tuan) if tuan else "chưa có tag week-* nào")
    if dang_dien_ra:
        ten, han = dang_dien_ra
        bao(CANH, "Tag tuần này", f"{ten} chưa có — hạn Chủ nhật {han}")

    for t in tuan:
        rc, kind = chay(["git", "cat-file", "-t", t], repo, timeout=60)
        if rc == 0 and kind.strip() != "tag":
            bao(CANH, f"Tag {t}", "là tag nhẹ — nên dùng `git tag -a` để tag "
                                  "mang mốc thời gian của chính nó")

    cp = repo / "CHECKPOINTS.md"
    if cp.exists():
        noi_dung = cp.read_text(encoding="utf-8")
        ngay = re.findall(r"^20\d\d-\d\d-\d\d\s+—", noi_dung, re.M)
        bao(DAT if ngay else HONG, "CHECKPOINTS.md",
            f"{len(ngay)} dòng có ngày" if ngay else "chưa có dòng nào ghi ngày")


# ---------------------------------------------------------------------------
def clone_sach(url_repo: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="check_m2_"))
    dich = tmp / "clone"
    rc, out = chay(["git", "clone", "--quiet", str(url_repo), str(dich)], tmp, timeout=300)
    if rc != 0:
        print(f"[check_m2] không clone được: {out}", file=sys.stderr)
        sys.exit(2)
    return dich


def main() -> int:
    ap = argparse.ArgumentParser(description="Tự kiểm Module 2 theo rubric")
    ap.add_argument("--clean", action="store_true",
                    help="clone sạch rồi kiểm, để chắc không dựa vào file chưa commit")
    ap.add_argument("--repo", default=None, help="đường dẫn repo (mặc định: repo chứa file này)")
    a = ap.parse_args()

    goc = Path(a.repo).resolve() if a.repo else Path(__file__).resolve().parent.parent
    repo = clone_sach(goc) if a.clean else goc
    print(f"[check_m2] kiểm: {repo}{'  (clone sạch)' if a.clean else ''}\n")

    kiem_file(repo)
    kiem_mot_chu_so_huu_prefer(repo)
    kiem_run_all_noi_m2(repo)
    truoc = kiem_chay_va_schema(repo)
    if truoc:
        kiem_tai_lap(repo, truoc)
    kiem_trong_so(repo)
    kiem_tri_tuyet_doi(repo)
    kiem_mot_nguon_q(repo)
    kiem_khong_mo_coi(repo)
    kiem_nghiem_m2(repo)
    kiem_thang_baseline(repo)
    kiem_requirements(repo)
    kiem_o_khuyet(repo)
    kiem_tien_trinh(repo)

    uu_tien = {HONG: 0, CANH: 1, DAT: 2}
    for muc, ten, ct in sorted(_ket_qua, key=lambda r: uu_tien[r[0]]):
        dong = ct.splitlines()
        print(f"  {muc:<9} {ten:<22} {dong[0] if dong else ''}")
        for d in dong[1:]:
            print(f"  {'':<9} {'':<22} {d}")

    n_hong = sum(1 for m, _, _ in _ket_qua if m == HONG)
    n_canh = sum(1 for m, _, _ in _ket_qua if m == CANH)
    n_dat = sum(1 for m, _, _ in _ket_qua if m == DAT)
    print(f"\n{n_hong} {HONG} · {n_canh} {CANH} · {n_dat} {DAT}")
    if n_hong:
        print("CHƯA SẠCH — sửa các mục HỎNG rồi mới (dời) tag m2.")
        return 1
    print("SẠCH — đủ điều kiện tag m2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
