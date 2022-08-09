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
print(sel.n)
print(sel.family)

z_vars = []
x_vars = []
D_vars = []
c_vars = []
d_vars = []

# Initializing the instance (y variables)
y_vars = []
for sel_set in sel.family:
    set_i_list = []
    for i in range(sel.n):
        if i in sel_set:
            set_i_list.append(1)
        else:
            set_i_list.append(0)
    y_vars.append(set_i_list)

# LP model
model = LpProblem(name="small-problem", sense=LpMaximize)

for v in range(sel.n):
    z_vars.append(LpVariable(name = f"{v}", lowBound = 0))
    x_vars.append(LpVariable(name = f"{v}", lowBound = 0))
    D_vars.append(LpVariable(name = f"{v}", lowBound = 0))
    c_vars.append(LpVariable(name = f"{v}", lowBound = 0))

for i in range(len(sel.family)):
    d_i = []
    for v in range(sel.n):
        d_i.append(LpVariable(name = f"d{i},{v}", lowBound = 0))
    d_vars.append(d_i)
    

# = LpVariable(name="", lowBound=0)



# Constraint: D_{v} = 1

# Constraint: 0 <= D_{v} - ... <= 2/3

#Constraint: -1 + 1/F <= c_{v} - ... <= 0

#Constraint: 0 <= d_{i,v} - ... <= 1 - 1/S_{i}


model += (2 * x + y <= 20, "red_constraint")

# Objective function
model += lpSum([])

print(model)
status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")

print(f"objective: {model.objective.value()}")

for var in model.variables():
    print(f"{var.name}: {var.value()}")

print("Success")
