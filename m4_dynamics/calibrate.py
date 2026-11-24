#!/usr/bin/env python3
"""
m4_dynamics/calibrate.py — Module 4, Yêu cầu M4-A (Task 16)

Nhiệm vụ:
  Chọn bộ tham số (a, b, r) cho hệ động lực mệt mỏi và ghi ra
  data/processed/m4_params.json cho recurrence/rolling_horizon/simulate.

Phạm vi của bước này (ghi rõ để báo cáo không nói quá — xem identify.py):
  * l_bar, rho_bar lấy từ instance_slice (tải/nghỉ trung bình của MỘT ngày).
  * a = tỷ lệ ngày nghỉ trong m3_real_strings — đây là một QUY ƯỚC chọn a,
    không phải ước lượng: profile likelihood trong identify.py cho thấy dữ liệu
    ưu tiên a nhỏ và a = tỷ lệ ngày nghỉ nằm NGOÀI vùng tin cậy 95%.
  * r chọn theo công thức quy ước; b được GIẢI RA từ ràng buộc chuẩn hoá
        F* = (b * l_bar - r * rho_bar) / (1 - a) = l_bar.
    Vì b được chọn để thoả ràng buộc này, "F* khớp l_bar" là ĐẲNG THỨC đúng với
    MỌI (a, r) — nó không kiểm chứng mô hình với dữ liệu, chỉ đặt thang đo của F
    bằng đơn vị "ca/kỳ".
"""
import json
import math
from pathlib import Path

# Đường dẫn tĩnh tới thư mục gốc
REPO = Path(__file__).resolve().parent.parent

def run(quiet=False):
    """
    Hàm thực thi chính: đọc dữ liệu, tính toán tham số và lưu file JSON.
    Trả về dictionary tham số để các module khác (như recurrence.py) gọi trực tiếp.
    """
    slice_path = REPO / "data" / "instance_slice.json"
    m3_path = REPO / "data" / "processed" / "m3_real_strings.json"
    out_path = REPO / "data" / "processed" / "m4_params.json"
    
    # 1. Trích xuất tải trung bình (l_bar) và nghỉ trung bình (rho_bar) từ instance_slice
    with open(slice_path, 'r', encoding='utf-8') as f:
        inst = json.load(f)
        
    n_inv = len(inst["invigilators"])
    # Tính tổng số ca thi (cộng tổng capacity)
    total_cap = sum(int(v) for k, v in inst["capacity"].items() if k in inst.get("campus_of", {}))
    max_load_ref = 2 # Ngưỡng mệt mỏi theo đề bài
    
    l_bar = total_cap / n_inv
    rho_bar = max_load_ref - l_bar
    
    # 2. Tính hệ số suy giảm mệt mỏi (a) từ m3_real_strings
    with open(m3_path, 'r', encoding='utf-8') as f:
        m3_data = json.load(f)
        
    strings = m3_data.get("strings", {})
    total_days = sum(len(s) for s in strings.values())
    work_days = sum(sum(1 for ch in s if ch != "-") for s in strings.values())
    rest_days = total_days - work_days
    
    # Quy ước: a = tỷ lệ ngày nghỉ (không phải ước lượng hợp lý cực đại — xem identify.py)
    a = rest_days / total_days
    
    # 3. Chọn r theo quy ước, rồi GIẢI b từ ràng buộc chuẩn hoá F* = l_bar.
    #    (Đây không phải phép fit: với b như dưới, F* = l_bar đúng cho mọi a, r.)
    r = (1.0 - a) * (l_bar / max_load_ref)
    b = (1.0 - a) + r * (rho_bar / l_bar)
    
    f_star = (b * l_bar - r * rho_bar) / (1.0 - a)
    
    cycle_weeks = n_inv // math.gcd(n_inv, total_cap)
    
    params = {
        "source": "empirical_fit_from_real_data",
        "calibrated_by": "m4_dynamics/calibrate.py",
        "a": round(a, 6),
        "b": round(b, 8),
        "r": round(r, 6),
        "l_bar": round(l_bar, 8),
        "rho_bar": round(rho_bar, 8),
        "max_load_ref": max_load_ref,
        "F_star": round(f_star, 8),
        "observed_mean_load": round(l_bar, 8),
        "calibration_error": abs(f_star - l_bar),
        "calibration_note": (
            "F* = l_bar là ràng buộc chuẩn hoá dùng để giải b (đúng với mọi a, r), "
            "không phải bằng chứng khớp dữ liệu. a là quy ước (tỷ lệ ngày nghỉ); "
            "b, r không được ước lượng từ dữ liệu. Xem m4_dynamics/identify.py."
        ),
        "a_is_convention": True,
        "n_invigilators_slice": n_inv,
        "total_capacity_slice": total_cap,
        "rotation_cycle_periods": cycle_weeks,
        "full_dataset_stats": {
            "total_person_days": total_days,
            "work_person_days": work_days,
            "rest_person_days": rest_days,
            "empirical_rest_ratio_a": round(a, 6)
        }
    }
    
    # Lưu file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
        
    if not quiet:
        print("=== THAM SỐ M4 (Task 16) — a theo quy ước, b giải từ chuẩn hoá F* = l_bar ===")
        print(f"Tổng giám thị    : {n_inv}")
        print(f"Tổng số ca thi   : {total_cap}")
        print(f"Tải TB (l_bar)   : {l_bar:.6f} ca/kỳ")
        print(f"Nghỉ TB (rho_bar): {rho_bar:.6f} ca/kỳ")
        print(f"Hệ số a          : {params['a']:.6f}")
        print(f"Hệ số b          : {params['b']:.8f}")
        print(f"Hệ số r          : {params['r']:.6f}")
        print(f"Điểm bất động F* : {params['F_star']:.8f} (= l_bar theo cách chọn b; "
              f"sai số làm tròn {params['calibration_error']:.1e} — không phải phép kiểm chứng)")
        print("Lưu ý: a là quy ước, không được dữ liệu ủng hộ (xem identify.py).")
        print(f"Đã lưu kết quả tại {out_path}")
        
    return params

if __name__ == "__main__":
    run()