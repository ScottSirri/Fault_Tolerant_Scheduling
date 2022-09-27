from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable, PULP_CBC_CMD, listSolvers, value
import math, random
import sys

VALID = 0
INVALID = -1

# Default values
n = 4
k = 2
r = 2


class InputError(Exception):
    pass

class Selector:
    family = []

    def __init__(self, in_n, in_k, in_r):
        self.n = in_n
        self.k = in_k
        self.r = in_r

    def validate(self):
        if self.n <= 0 or self.k <= 0 or self.r <= 0 or self.k > self.n or self.r > self.k:
            return INVALID
        for set in self.family:
            if type(set) is not list:
                return INVALID
            for i in set:
                if i < 0 or i >= self.n:  # Elements are in [0,n)
                    return INVALID
        return VALID

    def print_sel(self):
        print(f"Candidate selector({self.n}, {self.k}, {self.r}):")
        for sel_set in self.family:
            print("\t", end='')
            print(sel_set)
        print()

def usage():
    print("Usage: sel.py [ilp/lp] [n] [k] [r]\n       sel.py [ilp/lp] [n]\t\t(assumes k=sqrt(n), r=k/2)\n")


ilp_or_lp = ''
if len(sys.argv) > 1:
    if sys.argv[1] == "ilp":
        ilp_or_lp = "Integer"
    elif sys.argv[1] == "lp":
        ilp_or_lp = "Continuous"
    else:
        usage()
        raise InputError("Must specify 'ilp' or 'lp'")
else:
    usage()
    raise InputError("Must specify 'ilp' or 'lp'")

if len(sys.argv) == 5:
    n = int(sys.argv[2])
    k = int(sys.argv[3])
    r = int(sys.argv[4])
elif len(sys.argv) == 3:
    n = int(sys.argv[2])
    k = math.ceil(math.sqrt(n))
    r = math.ceil(k / 2.0)
else:
    usage()
    raise InputError()

sel = Selector(n,k,r)

c = 2   # Constant accompanying size of selector
sel_size = c * k * math.floor(math.log(n)) # Size of selector

p = 0.3 # Probability of each element being included (uniform distribution)

for i in range(sel_size):
    sel_set = []
    while len(sel_set) == 0:
        for j in range(n):
            if random.random() < p:
                sel_set.append(j)
    sel.family.append(sel_set)

# Test input
#sel.family.append([1,2])
#sel.family.append([2])
#sel.family.append([1,3])
#sel.family.append([0,2])
if sel.validate() != VALID:
    print("======================== Invalid selector ========================")
    raise InputError("Invalid selector")

z_vars = []
x_vars = []
D_vars = []
c_vars = []
div_vars = []

# Initializing the instance (y variables)
yiv_consts = []
for sel_set in sel.family:
    set_i_list = []
    for i in range(sel.n):
        if i in sel_set:
            set_i_list.append(1)
        else:
            set_i_list.append(0)
    yiv_consts.append(set_i_list)

# (I)LP model
model = LpProblem(name="small-problem", sense=LpMinimize)

# ==================== LP Variable generation ====================
for v in range(sel.n):
    z_vars.append(LpVariable(name = f"z{v}", lowBound = 0, upBound=1, cat=ilp_or_lp))
    x_vars.append(LpVariable(name = f"x{v}", lowBound = 0, upBound=1, cat=ilp_or_lp))
    D_vars.append(LpVariable(name = f"D{v}", lowBound = 0, upBound=1, cat=ilp_or_lp))
    c_vars.append(LpVariable(name = f"c{v}", lowBound = 0, upBound=1, cat=ilp_or_lp))

for i in range(len(sel.family)):
    di = []
    for v in range(sel.n):
        di.append(LpVariable(name = f"d{i},{v}", lowBound = 0, upBound=1, cat=ilp_or_lp))
    div_vars.append(di)

# ==================== Constraint generation ====================

# Constraint: \sum x_{v} = k
x_constraint = (lpSum(x_vars) == sel.k, "x_sum")
model += x_constraint

# Constraint: D_{v} = 1
for v in range(sel.n):
    Dv = D_vars[v]
    D_constraint = (Dv == 1, f"D{v}")
    model += D_constraint

# Constraint: 0 <= D_{v} - ... <= 2/3
for v in range(sel.n):
    Dv, zv, xv, cv = D_vars[v], z_vars[v], x_vars[v], c_vars[v]
    D_constraint_lower = (0 <= Dv - (1.0/3)*(zv + 1 - xv + cv), f"D{v}_lower")
    D_constraint_upper = (     Dv - (1.0/3)*(zv + 1 - xv + cv) <= 2.0/3.0, f"D{v}_upper")
    model += D_constraint_lower
    model += D_constraint_upper

# Constraint: -1 + 1/F <= c_{v} - ... <= 0
F = len(sel.family)
for v in range(sel.n):
    Dv, cv = D_vars[v], c_vars[v]
    dv = []
    for i in range(len(sel.family)):
        dv.append(div_vars[i][v])
    cv_constraint_lower = (-1 + (1.0/F) <= cv - (1.0/F)*lpSum(dv), f"c{v}_lower")
    cv_constraint_upper = (                cv - (1.0/F)*lpSum(dv) <= 0, f"c{v}_upper")
    model += cv_constraint_lower
    model += cv_constraint_upper

# Constraint: 0 <= d_{i,v} - ... <= 1 - 1/S_{i}
for v in range(sel.n):
    for i in range(len(sel.family)):
        div = div_vars[i][v]
        yiv = yiv_consts[i][v]
        Si = len(sel.family[i]) * 1.0
        x_i_not_v = []
        for var in sel.family[i]:
            if var != v:
                x_i_not_v.append(x_vars[var])
        div_constraint_lower = (0 <= div - (1.0/Si)*(1 - yiv + lpSum(x_i_not_v)), 
                f"d,i{i},v{v},lower")
        div_constraint_upper = (     div - (1.0/Si)*(1 - yiv + lpSum(x_i_not_v)) <= 1 - (1.0/Si), 
                f"d,i{i},v{v},upper")

        model += div_constraint_lower
        model += div_constraint_upper

# Objective function
model += lpSum(z_vars)

#print("======================== print(model) ========================")
#print(model)

print("======================== model.solve() ========================")
status = model.solve()
#status = model.solve(PULP_CBC_CMD(msg=False))

print("======================== Manually printing model info ========================")

print(f"status: {model.status}, {LpStatus[model.status]}")

print(f"objective: {model.objective.value()}")

print("\nVariables:")
selected = 0
for var in model.variables():
    if var.name[0] == "x":
        print(f"\t{var.name}: {var.value()}")
    if var.name[0] == "z":
        selected += value(var)

selected_str = str(selected)

only = ""
if selected < r:
    only = "only "
print("There exists a subset such that " + only + selected_str + " elements of it are selected.")
print()
sel.print_sel()
#print("\nConstraints:")
#for name, constraint in model.constraints.items():
#    print(f"\t{name}: {constraint.value()}")

print("Success")
