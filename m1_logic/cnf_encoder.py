import json
import os
from pysat.formula import CNF, IDPool
from pysat.solvers import Glucose3
from pysat.card import CardEnc, EncType

def solve_toy_instance():
    print("=== CHẠY TOY INSTANCE ===")
    cnf = CNF()
    cnf.append([-1])
    cnf.append([1, 2])
    cnf.append([-1, -2])
    
    with Glucose3(bootstrap_with=cnf) as solver:
        if solver.solve():
            print("Kết quả TOY: SAT")
            for val in solver.get_model():
                if val == 1: print("Giám thị CB1 -> Ca s")
                if val == 2: print("Giám thị CB2 -> Ca s")
        else:
            print("Kết quả TOY: UNSAT")
    print("=" * 40 + "\n")

def solve_data_slice(json_path):
    print("=== CHẠY DATA SLICE ===")
    
    if not os.path.exists(json_path):
        print(f"Lỗi: Không tìm thấy file {json_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    I_invigilators = data.get("invigilators", [])
    J_shifts = data.get("shifts", [])
    
    vpool = IDPool()
    cnf = CNF()

    def x(invig, shift):
        return vpool.id(f"{invig}_{shift}")

    for pair in data.get("overlap", []):
        if len(pair) == 2:
            s1, s2 = pair[0], pair[1]
            if s1 in J_shifts and s2 in J_shifts:
                for i in I_invigilators:
                    cnf.append([-x(i, s1), -x(i, s2)])

    for item in data.get("busy", []):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            i, j = item[0], item[1]
            if j in J_shifts:
                cnf.append([-x(i, j)])

    eligible_set = set(tuple(item) for item in data.get("eligible", []) if isinstance(item, list))
    for i in I_invigilators:
        for j in J_shifts:
            if (i, j) not in eligible_set:
                cnf.append([-x(i, j)])

    campus_of = data.get("campus_of", {})
    for j in J_shifts:
        if j not in campus_of or not campus_of[j]:
            for i in I_invigilators:
                cnf.append([-x(i, j)])

    capacities = data.get("capacity", {})
    for j in J_shifts:
        K = capacities.get(j, 1)
        shift_vars = [x(i, j) for i in I_invigilators]
        
        cnf_capacity = CardEnc.equals(lits=shift_vars, bound=K, encoding=EncType.seqcounter, vpool=vpool)
        cnf.extend(cnf_capacity)

    print(f"Tổng số biến (đã tối ưu): {vpool.top}")
    print(f"Tổng số mệnh đề CNF: {len(cnf.clauses)}\n")
    print("Đang chạy Glucose3 Solver...")
    
    with Glucose3(bootstrap_with=cnf) as solver:
        if solver.solve():
            print("Kết quả DATA SLICE: SAT (Lịch phân công hợp lệ!)\n")
            model = solver.get_model()
            
            print("-" * 30)
            count = 0
            for var_id in model:
                if var_id > 0:
                    var_name = vpool.obj(var_id)
                    if var_name and "_" in var_name:
                        i, j = var_name.split('_', 1)
                        print(f"Giám thị {i} -> Ca {j}")
                        count += 1
            print("-" * 30)
            print(f"Tổng số lượt gán: {count} lượt")
        else:
            print("Kết quả DATA SLICE: UNSAT (Không tìm được lịch)")

if __name__ == "__main__":
    solve_toy_instance()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'instance_slice.json') 
    solve_data_slice(json_path)
    #...