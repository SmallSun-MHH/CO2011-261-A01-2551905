import random

def generate_weights(seed_int: int):
    """Sinh 3 trọng số ngẫu nhiên từ 0.5 đến 2.0 dựa trên seed_int"""
    rng = random.Random(seed_int)
    w1 = rng.uniform(0.5, 2.0)
    w2 = rng.uniform(0.5, 2.0)
    w3 = rng.uniform(0.5, 2.0)
    return w1, w2, w3

def build_soft_penalty_terms(model, x, m2_data: dict, seed_int: int, max_load: int = 3):
    """
    Tạo danh sách các biểu thức phạt cho ràng buộc mềm (CP-SAT).
    Đầu vào:
      - model: cp_model.CpModel()
      - x: dict chứa biến nhị phân x[i, j]
      - m2_data: Dữ liệu từ preprocess.py của Long
    """
    I = m2_data.get("I", [])
    J = m2_data.get("J", [])
    campus = m2_data.get("campus", {})
    preferences = m2_data.get("preferences", {})

    w_loc_float, w_load_float, _ = generate_weights(seed_int)
    
    # Scale trọng số float thành int cho CP-SAT
    SCALE = 1000
    w_loc = int(round(w_loc_float * SCALE))
    w_load = int(round(w_load_float * SCALE))
    
    penalty_terms = []

    # S1: Ưu tiên cơ sở (Location Preference)
    for i in I:
        pref_campus = preferences.get(i, {}).get("prefer_campus")
        if pref_campus: 
            for j in J:
                shift_campus = campus.get(j)
                if shift_campus and shift_campus != pref_campus:
                    # Vi phạm: cơ sở ca thi khác nguyện vọng -> Phạt w_loc
                    penalty_terms.append(w_loc * x[i, j])

    # S2: Giới hạn tải làm việc (Fatigue Limit)
    for i in I:
        viol_load = model.NewIntVar(0, len(J), f"viol_load_S2_{i}")
        total_shifts = sum(x[i, j] for j in J)
        
        # viol_load >= Tổng ca gán - Max Load (nếu < 0 thì tự ép về 0)
        model.Add(viol_load >= total_shifts - max_load)
        penalty_terms.append(w_load * viol_load)

    return penalty_terms
