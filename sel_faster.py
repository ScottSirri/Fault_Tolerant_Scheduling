from ortools.sat.python import cp_model
#https://developers.google.com/optimization/cp/cp_solver 
import math, random
import sys, time

VALID = 0
INVALID = -1

BINARY = 1 # Inclusive upper bound on values of integer variables

# Arbitrary default values, later overwritten
n = 4
k = 2
r = 2

# Parameters for ball-bin method
c = 2
d = 3

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

class InputError(Exception):
    pass

class Selector:
    family = []

    def __init__(self, in_n, in_k, in_r, in_c, in_d):
        self.n = in_n
        self.k = in_k
        self.r = in_r
        self.c = in_c
        self.d = in_d

    # Populates the sets of the selector
    def populate(self):
        num_collections = math.ceil(self.d * math.log(self.n))
        collection_size = math.ceil(self.c * self.k)
        sel_family_size = num_collections * collection_size

        self.family = []
        for i in range(num_collections):
            collection = [] # List of lists, each of which is a selector set
            for j in range(collection_size):
                collection.append([])
            for element in range(n):
                index = math.floor(random.uniform(0, collection_size))
                collection[index].append(element)
            for sel_set in collection:
                # I'm guessing this is necessary? I see no reason to include
                # empty selector sets
                if len(sel_set) > 0: 
                    self.family.append(sel_set)

    # Validates that selector parameters are sensical
    def validate(self):
        if (self.n <= 0 or self.k <= 0 or self.r <= 0 or self.k > self.n
                or self.r > self.k or self.c <= 0 or self.d <= 0):
            return INVALID
        for set in self.family:
            if type(set) is not list:
                return INVALID
            for i in set:
                if i < 0 or i >= self.n:  # Elements are in [0,n)
                    return INVALID
        return VALID

    # Prints the selector with stars denoting the "bottleneck" sets in which
    # the minimal set of selected elements are selected
    def print_sel(self, selected_list):
        if selected_list == None:
            selected_list = []
        print(f"Candidate selector({self.n}, {self.k}, {self.r}):")
        for sel_set in self.family:
            print("\t", end='')
            marker = "    " 
            if len(intersection(sel_set, selected_list)) == 1:
                   marker = "*** "
            print(marker, end = '')
            print(sel_set)
        print()

    def print_sel_temp(self):
        print(f"Candidate selector({self.n}, {self.k}, {self.r}):")
        for sel_set in self.family:
            print("\t", sel_set)
        print()

# Prints usage message for the program
def usage():
    print("Usage: sel.py [ilp/lp] [n] [k] [r]\n"
          "       sel.py [ilp/lp] [n]\t\t(assumes k=sqrt(n), r=k/2)\n")


# ===============  Command-line Input Processing ===============

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

# =================== Creating the selector ===================

# Creating and populating the selector
sel = Selector(n, k, r, c, d)
sel.populate()

# Validate the selector
if sel.validate() != VALID:
    print("======================== Invalid selector ========================")
    raise InputError("Invalid selector")

start_time = time.perf_counter()

# ==================== Creating the (I)LP ====================

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
model = cp_model.CpModel()

# model.NewIntVar(0, num_vals - 1, 'x')

# ==================== Variable generation ====================
for v in range(sel.n):
    z_vars.append(model.NewIntVar(0, BINARY, f"z{v:03}"))
    x_vars.append(model.NewIntVar(0, BINARY, f"x{v:03}"))
    D_vars.append(model.NewIntVar(0, BINARY, f"D{v:03}"))
    c_vars.append(model.NewIntVar(0, BINARY, f"c{v:03}"))

for i in range(len(sel.family)):
    di = []
    for v in range(sel.n):
        di.append(model.NewIntVar(0, BINARY, f"d{i},{v}"))
    div_vars.append(di)

# ==================== Constraint generation ====================

# Constraint: \sum x_{v} = k
model.Add(sum(x_vars) == sel.k)

# Constraint: D_{v} = 1
for v in range(sel.n):
    model.Add(D_vars[v] == 1)

# Constraint: 0 <= D_{v} - ... <= 2/3
for v in range(sel.n):
    Dv, zv, xv, cv = D_vars[v], z_vars[v], x_vars[v], c_vars[v]
    #print("--------- " + str(zv))
    D_constraint_lower = (0 <= 3*Dv - (zv + 1 - xv + cv))
    D_constraint_upper = (     3*Dv - (zv + 1 - xv + cv) <= 2)
    #print("Constraint " + str(D_constraint_lower))
    #print("Constraint " + str(D_constraint_upper))
    model.Add(D_constraint_lower)
    model.Add(D_constraint_upper)

# Constraint: -1 + 1/F <= c_{v} - ... <= 0
F = len(sel.family)
print("c = " + str(c) + ", d = " + str(d))
print("Selector size = " + str(F))
for v in range(sel.n):
    Dv, cv = D_vars[v], c_vars[v]
    dv = []
    for i in range(len(sel.family)):
        dv.append(div_vars[i][v])
    cv_constraint_lower = (-1*F + 1 <= F * cv - sum(dv))
    cv_constraint_upper = (            F * cv - sum(dv) <= 0)
    model.Add(cv_constraint_lower)
    model.Add(cv_constraint_upper)

# Constraint: 0 <= d_{i,v} - ... <= 1 - 1/S_{i}
for v in range(sel.n):
    for i in range(len(sel.family)):
        div = div_vars[i][v]
        yiv = yiv_consts[i][v]
        Si = len(sel.family[i])
        x_i_not_v = []
        for var in sel.family[i]:
            if var != v:
                x_i_not_v.append(x_vars[var])
        div_constraint_lower = (0 <= Si * div - (1 - yiv + sum(x_i_not_v)))
        div_constraint_upper = (     Si * div - (1 - yiv + sum(x_i_not_v)) <= Si - 1)
        model.Add(div_constraint_lower)
        model.Add(div_constraint_upper)

# Objective function ******************************************************
model.Add(sum(z_vars) < sel.r) # This way, the only feasible solutions are 
                               # those disqualifying the candidate selector 

print(f"Testing for ({sel.n}, {sel.k}, {sel.r})-selector")

print("======================== solver.solve() ========================")
solver = cp_model.CpSolver()
status = solver.Solve(model)

end_time = time.perf_counter()


selected_x = []

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    # This only executes if fewer than r elements are selected in some subset
    print("Found solution")
    ctr = 0
    for x in x_vars:
        val = solver.Value(x)
        if val == 1:
            selected_x.append(ctr)
            print(f'x{ctr:02} = {val} ***')
        else:
            print(f'x{ctr:02} = {val}')
        ctr += 1
else:
    sel.print_sel(selected_x)
    print("No solution found, i.e., there's no subset of vars such that "
          "fewer than " + str(r) + " are selected")
    print("Time to solve: " + str(end_time - start_time) + " s")
    print("Success")
    quit()

sel.print_sel(selected_x)

print("Time to solve: " + str(end_time - start_time) + " s")
num_sel = 0
for z in z_vars:
    print(str(z))
    num_sel += solver.Value(z)
    if solver.Value(z) > 0:
        print(str(z))

for v in range(sel.n):
    var = x_vars[v]
    if solver.Value(var) != 1:
        continue
    print(str(var) + "  " + str(solver.Value(var)))
    var = z_vars[v]
    print(str(var) + "  " + str(solver.Value(var)))
    var = D_vars[v]
    print(str(var) + "  " + str(solver.Value(var)))
    var = c_vars[v]
    print(str(var) + "  " + str(solver.Value(var)))
    for i in range(len(sel.family)):
        var = div_vars[i][v]
        print(str(var) + "  " + str(solver.Value(var)))
        
    print()

print("Number of elements selected: " + str(num_sel))

#print("Obj val: " + str(solver.ObjectiveValue()))

print("Success")
