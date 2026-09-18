"""
Bang Logic_to_LP.py — Cầu nối Logic -> LP (1.3, Module 1)
Input: biến quyết định x[i, j] đã được định nghĩa ở Module 2. 
Output: (các) ràng buộc pulp có thể add thẳng vào mô hình ILP bằng `model += constraint`.

Người làm: Nguyễn Quang Phúc 2551920
"""

import pulp
def availability_constraint(x, i, j):
    """Busy(i,j) -> ~Assign(i,j)  =>  x[i,j] = 0"""
    return x[i, j] == 0


def clause_to_lp(x, clause):
    """
    Dịch một clause CNF (l1 OR l2 OR ... OR lk) sang bat dang thuc tuyen tinh >= 1.
    literal duong a -> x
    literal am ~a -> (1 - x)
    """
    terms = []
    for key, is_positive in clause:
        terms.append(x[key] if is_positive else (1 - x[key]))
    return pulp.lpSum(terms) >= 1


def no_double_booking(x, i, j, k):
    """Overlap(j,k) & Assign(i,j) -> ~Assign(i,k)  =>  x_ij + x_ik <= 1"""
    return x[i, j] + x[i, k] <= 1


def exact_capacity(x, invigilators, j, C_j):
    """Sum_i Assign(i,j) = C_j"""
    return pulp.lpSum(x[i, j] for i in invigilators) == C_j


def at_most_k(x, i, shifts, k):
    """Sum_j Assign(i,j) <= k"""
    return pulp.lpSum(x[i, j] for j in shifts) <= k


def at_least_k(x, invigilators, j, k):
    """Sum_i Assign(i,j) >= k"""
    return pulp.lpSum(x[i, j] for i in invigilators) >= k


def location_penalty(x, i, mismatched_shifts, penalty_var_name="p"):
    """
    Prefer(i, CS1) nhung AtCampus(j, CS2) voi j trong mismatched_shifts.
    Tra ve: (constraints, p_i) de cong w2 * p_i vao ham muc tieu.
    """
    p_i = pulp.LpVariable(f"{penalty_var_name}_{i}", lowBound=0, cat="Continuous")
    constraints = [p_i >= x[i, j] for j in mismatched_shifts]
    return constraints, p_i


def fatigue_indicator(load_i, threshold, f_i, M=1000):
    """
    Fatigue(i) <-> (load_i > threshold)
    Tra ve 2 rang buoc Big-M can add vao model.
    """
    c1 = load_i - threshold <= M * f_i
    c2 = threshold - load_i <= M * (1 - f_i)
    return c1, c2


if __name__ == "__main__":
    model = pulp.LpProblem("worked_example_check", pulp.LpMinimize)
    invigilators = ["CB1", "CB2"]
    shift = "s"

    x = pulp.LpVariable.dicts(
        "x", [(i, shift) for i in invigilators], cat="Binary"
    )

    model += availability_constraint(x, "CB1", shift)

    model += exact_capacity(x, invigilators, shift, 1)

    model += 0

    model.solve(pulp.PULP_CBC_CMD(msg=False))

    result = {i: int(x[i, shift].value()) for i in invigilators}
    print("LP result:", result)
    assert result == {"CB1": 0, "CB2": 1}, "Khong khop voi ket qua SAT trong brief!"
    print("OK - khop voi ket qua SAT (a1=0, a2=1) trong Worked Example cua brief.")
