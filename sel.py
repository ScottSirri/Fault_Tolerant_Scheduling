from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable

VALID = 0
INVALID = -1

class Selector:
    n = -1
    family = []

    def __init__(self, in_n):
        self.n = in_n

    def validate():
        if n <= 0:
            return INVALID
        for set in family:
            if type(set) is not list:
                return INVALID
            for i in set:
                if i < 0 or i >= n:
                    return INVALID
        return VALID

sel = Selector(4)

# Test input
sel.family.append([1,2])
sel.family.append([2])
sel.family.append([1,3])
sel.family.append([0,2])
print(f"Selector({sel.n}):")
print(sel.family)
print()

z_vars = []
x_vars = []
D_vars = []
c_vars = []
div_vars = []

# Initializing the instance (y variables)
yiv_vars = []
for sel_set in sel.family:
    set_i_list = []
    for i in range(sel.n):
        if i in sel_set:
            set_i_list.append(1)
        else:
            set_i_list.append(0)
    yiv_vars.append(set_i_list)

# LP model
model = LpProblem(name="small-problem", sense=LpMaximize)

# ==================== LP Variable generation ====================
for v in range(sel.n):
    z_vars.append(LpVariable(name = f"z{v}", lowBound = 0))
    x_vars.append(LpVariable(name = f"x{v}", lowBound = 0))
    D_vars.append(LpVariable(name = f"D{v}", lowBound = 0))
    c_vars.append(LpVariable(name = f"c{v}", lowBound = 0))

for i in range(len(sel.family)):
    di = []
    for v in range(sel.n):
        di.append(LpVariable(name = f"d{i},{v}", lowBound = 0))
    div_vars.append(di)

# ==================== Constraint generation ====================
    
# Constraint: D_{v} = 1
for v in range(sel.n):
    Dv = D_vars[v]
    D_constraint = (Dv == 1)
    model += D_constraint

# Constraint: 0 <= D_{v} - ... <= 2/3
for v in range(sel.n):
    Dv, zv, xv, cv = D_vars[v], z_vars[v], x_vars[v], c_vars[v]
    D_constraint_lower = (0 <= Dv - (zv + 1 - xv + cv)/3.0)
    D_constraint_upper = (     Dv - (zv + 1 - xv + cv)/3.0 <= 2.0/3.0)
    model += D_constraint_lower
    model += D_constraint_upper

# Constraint: -1 + 1/F <= c_{v} - ... <= 0
F = len(sel.family)
for v in range(sel.n):
    Dv, cv = D_vars[v], c_vars[v]
    dv = []
    for i in range(len(sel.family)):
        dv.append(div_vars[i][v])
    cv_constraint_lower = (-1 + 1.0/F <= cv - (1.0/F)*lpSum(dv))
    cv_constraint_upper = (              cv - (1.0/F)*lpSum(dv) <= 0)
    model += cv_constraint_lower
    model += cv_constraint_upper

# Constraint: 0 <= d_{i,v} - ... <= 1 - 1/S_{i}
for v in range(sel.n):
    for i in range(len(sel.family)):
        div = div_vars[i][v]
        yiv = yiv_vars[i][v]
        Si = len(sel.family[i])
        x_i_not_v = []
        for var in sel.family[i]:
            if var is not v:
                x_i_not_v.append(x_vars[var])
        div_constraint_lower = (0 <= div - (1.0/Si)*(1 - yiv + lpSum(x_i_not_v)))
        div_constraint_upper = (     div - (1.0/Si)*(1 - yiv + lpSum(x_i_not_v)) <= 1 - (1.0/Si))
        model += div_constraint_lower
        model += div_constraint_upper


"""
model += (2 * x + y <= 20, "red_constraint")

# Objective function
model += lpSum([])

print(model)
status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")

print(f"objective: {model.objective.value()}")

for var in model.variables():
    print(f"{var.name}: {var.value()}")
"""
print("Success")
