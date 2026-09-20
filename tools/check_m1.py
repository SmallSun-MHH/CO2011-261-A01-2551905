#!/usr/bin/env python3
"""
Kiểm tra lần cuối trước khi tag m1 — chạy ở THƯ MỤC GỐC của repo.

    python tools/check_m1.py
    python tools/check_m1.py --clean     # thêm bước clone sạch rồi chạy lại (chậm hơn)

Đối chiếu với: Definition of Done (§3), quy tắc repo & git (§4),
rubric Module 1 và Process (Appendix B) của đề bài.

Kết quả: HỎNG = phải sửa trước khi tag · CẢNH BÁO = nên sửa · ĐẠT.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

TEAM_ID_RE = re.compile(r"^CO2011-261-(L|CC|A01|TN01)-\d{7}$")
NAME_RE = re.compile(r"^\d{7} \S.+$")
MAIL_RE = re.compile(r"^\d{7}@hcmut\.edu\.vn$")
MSG_RE = re.compile(r"^(m[1-5]|week-\d\d|docs|chore|fix)\b.*", re.I)

ket_qua = []   # (muc, trang_thai, noi_dung)


def ghi(muc, tt, nd):
    ket_qua.append((muc, tt, nd))


def git(*a):
    r = subprocess.run(["git", *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def chay(cmd, cwd=None, timeout=300):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)


# ------------------------------------------------------------------ 1. file
def kiem_file():
    bat_buoc = ["README.md", "requirements.txt", "run_all.py", "CHECKPOINTS.md",
                "CONTRIBUTIONS.md", "DECISIONS.md", "MEETINGS.md", "data/seed.txt",
                "m1_logic/spec.md", "m1_logic/slice_builder.py",
                "m1_logic/cnf_encoder.py", "m1_logic/unsat_core.py",
                "m1_logic/bang_logic_to_lp.py", "m1_logic/unsat_core.py"]
    thieu = [f for f in bat_buoc if not Path(f).exists()]
    if thieu:
        ghi("File bắt buộc", "HỎNG", "thiếu: " + ", ".join(thieu))
    else:
        ghi("File bắt buộc", "ĐẠT", f"đủ {len(bat_buoc)} file")


# ------------------------------------------------------------------ 2. seed
def kiem_seed():
    p = Path("data/seed.txt")
    if not p.exists():
        return
    seed = p.read_text(encoding="utf-8").strip()
    if not seed:
        ghi("Seed", "HỎNG", "data/seed.txt rỗng")
        return
    team = None
    try:   # nguồn đáng tin nhất: meta của instance do slice_builder sinh
        team = json.loads(Path("data/instance_slice.json").read_text(encoding="utf-8"))["meta"]["team_id"]
    except Exception:
        pass
    for f in ([] if team else ["m1_logic/slice_builder.py", "README.md"]):
        if Path(f).exists():
            m = next((x for x in re.findall(r"CO2011-261-(?:L|CC|A01|TN01)-\d{7}", Path(f).read_text(encoding="utf-8")) if not x.endswith("2252107")), None)
            if m:
                team = m
                break
    if not team:
        ghi("Team ID", "CẢNH BÁO", "không thấy Team ID trong README.md")
    else:
        ghi("Team ID", "ĐẠT" if TEAM_ID_RE.match(team) else "HỎNG", team)
        repo = Path.cwd().name
        if repo != team:
            ghi("Tên repo", "CẢNH BÁO", f"thư mục '{repo}' khác Team ID '{team}' — tên repo trên GitHub phải trùng từng byte")
    if Path("tools/make_seed.py").exists() and team:
        rc, out = chay([sys.executable, "tools/make_seed.py", team])
        if rc == 0:
            if out.strip() == seed:
                ghi("Seed", "ĐẠT", "data/seed.txt khớp tools/make_seed.py")
            else:
                ghi("Seed", "HỎNG", "data/seed.txt KHÁC kết quả tools/make_seed.py — sinh lại")
    else:
        ghi("Seed", "CẢNH BÁO", "không có tools/make_seed.py để đối chiếu")


# ------------------------------------------------------------------ 3. requirements
def kiem_requirements():
    p = Path("requirements.txt")
    if not p.exists():
        return
    dong = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]
    chua_ghim = [l for l in dong if "==" not in l]
    if chua_ghim:
        ghi("requirements.txt", "HỎNG", "chưa ghim phiên bản: " + ", ".join(chua_ghim))
    else:
        ghi("requirements.txt", "ĐẠT", f"{len(dong)} gói, đều ghim ==")
    if not any("python-sat" in l.lower() for l in dong):
        ghi("requirements.txt", "HỎNG", "thiếu python-sat")


# ------------------------------------------------------------------ 4. placeholder
def kiem_placeholder():
    mau = [("DECISIONS.md", [r"\[GT-\d\]", r"TODO"]),
           ("README.md", [r"\(điền", r"\(dien", r"TODO"]),
           ("m1_logic/README.md", [r"\(điền", r"\(dien"]),
           ("CONTRIBUTIONS.md", [r"\(điền", r"\(dien", r"TODO"])]
    for f, pats in mau:
        if not Path(f).exists():
            continue
        s = Path(f).read_text(encoding="utf-8")
        con = [p for p in pats if re.search(p, s)]
        if len(s.strip()) < 80:
            ghi(f, "HỎNG", "gần như rỗng")
        elif con:
            ghi(f, "HỎNG", "còn ô chưa điền: " + ", ".join(con))
        else:
            ghi(f, "ĐẠT", "không còn ô trống")
    if Path("README.md").exists() and "AI" not in Path("README.md").read_text(encoding="utf-8"):
        ghi("Khai báo AI", "HỎNG", "README.md chưa có mục khai báo dùng AI (§4 bắt buộc)")


# ------------------------------------------------------------------ 5. git
def kiem_git():
    if git("rev-parse", "--is-inside-work-tree") != "true":
        ghi("Git", "HỎNG", "không phải repo git")
        return
    log = git("log", "--use-mailmap", "--format=%H%x1f%aN%x1f%aE%x1f%s") or ""
    commits = [l.split("\x1f") for l in log.splitlines() if l]
    sai_ten = sorted({(a, e) for _, a, e, _ in commits
                      if not NAME_RE.match(a) or not MAIL_RE.match(e)})
    if sai_ten:
        ghi("Danh tính git", "HỎNG",
            "commit sai định dạng '<MSSV> <Họ tên>' / '<MSSV>@hcmut.edu.vn': "
            + "; ".join(f"{a} <{e}>" for a, e in sai_ten))
    else:
        ghi("Danh tính git", "ĐẠT", f"{len(commits)} commit, danh tính đúng định dạng")

    sai_msg = [s for _, _, _, s in commits if not MSG_RE.match(s)]
    if sai_msg:
        ghi("Commit message", "CẢNH BÁO",
            f"{len(sai_msg)} commit không mở đầu bằng 'm1:' / 'm2:'... ví dụ: '{sai_msg[0][:50]}'")

    # mỗi tác giả phải có commit chạm m1_logic/
    tac_gia = sorted({a for _, a, _, _ in commits})
    m1 = git("log", "--use-mailmap", "--format=%aN", "--", "m1_logic/") or ""
    co_m1 = set(m1.splitlines())
    thieu = [a for a in tac_gia if a not in co_m1]
    if thieu:
        ghi("Đóng góp M1", "HỎNG", "chưa có commit trong m1_logic/: " + ", ".join(thieu))
    else:
        ghi("Đóng góp M1", "ĐẠT", f"cả {len(tac_gia)} tác giả có commit ở m1_logic/")
    if len(tac_gia) < 4:
        ghi("Số tác giả", "CẢNH BÁO", f"mới thấy {len(tac_gia)} tác giả trong lịch sử — nhóm 4–5 người")

    tags = set((git("tag") or "").split())
    for t in ["week-01"]:
        ghi(f"Tag {t}", "ĐẠT" if t in tags else "CẢNH BÁO",
            "có" if t in tags else "đã lỡ, mất 1% — không sửa được, KHÔNG tạo tag lùi ngày")
    for t in ["week-02", "m1"]:
        ghi(f"Tag {t}", "ĐẠT" if t in tags else "CẢNH BÁO",
            "có" if t in tags else "chưa có — push trước 23:59 CN 20/09")

    ban = git("status", "--porcelain")
    if ban:
        ghi("Cây làm việc", "CẢNH BÁO", f"{len(ban.splitlines())} file chưa commit")

    nhanh = git("rev-parse", "--abbrev-ref", "HEAD")
    if nhanh and nhanh != "main":
        ghi("Nhánh", "CẢNH BÁO", f"đang ở '{nhanh}', tag phải đặt trên main")


# ------------------------------------------------------------------ 6. checkpoints
def kiem_checkpoints():
    p = Path("CHECKPOINTS.md")
    if not p.exists():
        return
    s = p.read_text(encoding="utf-8")
    ngay = re.findall(r"2026-(\d\d)-(\d\d)", s)
    tuan2 = [d for d in ngay if d[0] == "09" and 14 <= int(d[1]) <= 20]
    ghi("CHECKPOINTS.md", "ĐẠT" if tuan2 else "HỎNG",
        "có dòng tuần 14–20/09" if tuan2 else "chưa có dòng nào ghi ngày 14–20/09")
    if "m1" not in s.lower():
        ghi("CHECKPOINTS.md", "CẢNH BÁO", "chưa nhắc tới m1")


# ------------------------------------------------------------------ 7. chạy thật
def kiem_pipeline(goc="."):
    g = Path(goc)
    if not (g / "m1_logic/slice_builder.py").exists():
        return
    rc, out = chay([sys.executable, "m1_logic/slice_builder.py", "--quiet"], cwd=goc)
    raw = (g / "data/seed.txt").read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in raw or not raw.strip().isdigit():
        ghi("seed.txt", "HỎNG", "không phải ASCII chỉ chứa số — `$(cat data/seed.txt)` của người chấm sẽ vỡ")
    if rc != 0:
        ghi("slice_builder.py", "HỎNG", out.strip().splitlines()[-1][:120] if out.strip() else "lỗi")
        return
    inst = json.loads((g / "data/instance_slice.json").read_text(encoding="utf-8"))
    ghi("slice_builder.py", "ĐẠT",
        f"ngày {inst['meta']['date']} · {len(inst['invigilators'])} giám thị · {len(inst['shifts'])} ca")
    if not inst.get("busy"):
        ghi("Busy", "HỎNG", "busy vẫn rỗng — chưa áp bản vá, H2 biến mất")
    else:
        ghi("Busy", "ĐẠT", f"{len(inst['busy'])} cặp")

    rc, out = chay([sys.executable, "m1_logic/cnf_encoder.py"], cwd=goc)
    ghi("cnf_encoder.py", "ĐẠT" if rc == 0 and "SAT" in out else "HỎNG",
        "chạy xong" if rc == 0 else out.strip().splitlines()[-1][:120])

    rc, out = chay([sys.executable, "m1_logic/unsat_core.py", "data/instance_slice.json"], cwd=goc)
    p = g / "m1_logic/out/unsat_core.json"
    if rc != 0 or not p.exists():
        ghi("unsat_core.py", "HỎNG", (out.strip().splitlines() or ["lỗi"])[-1][:120])
        return
    r = json.loads(p.read_text(encoding="utf-8"))
    ok = all(x["dat"] for x in r["kiem_chung_toi_thieu"])
    ho = sorted(set(r["ho_rang_buoc"].values()))
    ghi("unsat_core.py", "ĐẠT" if ok else "HỎNG",
        f"MUS {len(r['unsat_core'])} nhóm · họ: {', '.join(ho)} · tối thiểu: {'đã chứng minh' if ok else 'CHƯA'}")
    if "availability" not in ho:
        ghi("Dạng lõi", "CẢNH BÁO", "lõi không chứa availability — lệch dạng mô tả ở Appendix A M1/Q2")
    if "contracts/fake" in json.dumps(r) or "mock" in json.dumps(r).lower():
        ghi("Nguồn dữ liệu", "HỎNG", "kết quả đang chạy trên dữ liệu GIẢ, không được đưa vào report")


def kiem_clone_sach():
    d = tempfile.mkdtemp(prefix="m1check_")
    try:
        rc, out = chay(["git", "clone", "-q", ".", d])
        if rc != 0:
            ghi("Clone sạch", "HỎNG", "không clone được")
            return
        for f in ["data/dataset.csv"]:          # dataset có thể không commit
            if Path(f).exists() and not (Path(d) / f).exists():
                ghi("Clone sạch", "CẢNH BÁO", f"{f} không nằm trong git — người chấm clone về sẽ thiếu")
        rc, out = chay([sys.executable, "run_all.py", "--seed", Path("data/seed.txt").read_text().strip()],
                       cwd=d, timeout=900)
        ghi("Clone sạch + run_all.py", "ĐẠT" if rc == 0 else "HỎNG",
            "chạy thông từ bản clone" if rc == 0 else (out.strip().splitlines() or ["lỗi"])[-1][:120])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    if not Path("m1_logic").exists() and not Path(".git").exists():
        sys.exit("Chạy lệnh này ở thư mục GỐC của repo.")
    kiem_file(); kiem_seed(); kiem_requirements(); kiem_placeholder()
    kiem_git(); kiem_checkpoints(); kiem_pipeline()
    if "--clean" in sys.argv:
        kiem_clone_sach()

    w = max(len(m) for m, _, _ in ket_qua)
    for tt_loc in ["HỎNG", "CẢNH BÁO", "ĐẠT"]:
        for m, tt, nd in ket_qua:
            if tt == tt_loc:
                print(f"  {tt:<9} {m:<{w}}  {nd}")
    hong = sum(1 for _, t, _ in ket_qua if t == "HỎNG")
    canh = sum(1 for _, t, _ in ket_qua if t == "CẢNH BÁO")
    print(f"\n{hong} HỎNG · {canh} CẢNH BÁO · {len(ket_qua)-hong-canh} ĐẠT")
    print("CHƯA SẠCH — sửa các mục HỎNG rồi mới (dời) tag m1." if hong else "Sạch — tag m1 được.")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
