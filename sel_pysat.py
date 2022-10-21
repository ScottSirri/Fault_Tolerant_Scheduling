from pysat.solvers import Glucose3
from pysat.card import *
import math, random
import sys, time

VALID = 0
INVALID = -1

NOT = -1

# Ball-bin generation method parameters
c = 2
d = 3

# Arbitrary default values, later overwritten
n = 4
k = 2
r = 2

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

# Prints usage message for the program
def usage():
    print("Usage: sel_pysat.py [n] [k] [r]\n"
          "       sel_pysat.py [n]\t\t(assumes k=sqrt(n), r=k/2)\n")


# ===============  Command-line Input Processing ===============
if len(sys.argv) == 4:
    n = int(sys.argv[1])
    k = int(sys.argv[2])
    r = int(sys.argv[3])
elif len(sys.argv) == 2:
    n = int(sys.argv[1])
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


# ================= Generate formula =====================

"""
            [1,n]: z_{v}
         [n+1,2n]: x_{v}
        [2n+1,3n]: y_{1,v}
[(i+1)n+1,(i+2)n]: y_{i,v}

var_data is a tuple with first entry one of 'z', 'x', 'y'
The next one or two entries are the var numbers
Returns the integer mapped to that.
"""
def get_var_num(var_data):
    if var_data[0] == "z":
        return var_data[1]
    elif var_data[0] == "x":
        return n + var_data[1]
    elif var_data[0] == "y":
        i,v = var_data[1],var_data[2]
        return (i+1)*n + v
    else:
        return "INVALID"
def get_var_name(var_num):
    if 1 <= var_num and var_num <= n:
        return ["z", var_num]
    elif n+1 <= var_num and var_num <= 2*n:
        return ["x", var_num - n]
    elif 2*n+1 <= var_num:
        i = (var_num - 2*n) / n + 1
        v = (var_num - 2*n) % n
        return ["y", i, v]
    else:
        return "INVALID"


# Had to do a little distributing to get this into CNF

g = Glucose3(use_timer = True) # Arbitrary, choose a more suitable solver later
for v in range(1,n+1):
    zv,xv = get_var_num(["z",v]), get_var_num(["x",v])
    for i in range(1,len(sel.family)+1):
        yiv = get_var_num(["y",i,v])
        v_in_Si = False

        clause_v_i = [zv, NOT * xv, NOT * yiv]
        for x_num_raw in sel.family[i-1]:
            if x_num_raw != v:
                x_not_v = get_var_num(["x", x_num_raw])
                clause_v_i.append(x_not_v)
            else:
                # Not strictly in the original formula, but this makes it 
                # necessary to set yiv=1 constant for each v in each Si
                v_in_Si = True
        if v_in_Si:
            g.add_clause([yiv])
        else:
            g.add_clause([NOT * yiv])
        #print(f"clause_{v}_{i}:", end=" ")
        #print(clause_v_i)
        g.add_clause(clause_v_i)


# \sum x_{v} >= k
xv_k = CardEnc.atleast(lits=list(range(n+1, 2*n+1)), 
                       bound=k, encoding=EncType.seqcounter)
for clause in xv_k:
    g.add_clause(clause)

# \sum z_{v} < r
zv_r = CardEnc.atmost(lits=list(range(1, n+1)), 
                      bound=r-1, encoding=EncType.seqcounter)
for clause in zv_r:
    g.add_clause(clause)

#print("Clauses:")
#print(g.clauses)

print("   # vars: " + str(g.nof_vars()))
print("# clauses: " + str(g.nof_clauses()))

print("Solve: ", end='')
#start_time = time.perf_counter()
sat = g.solve()
print(sat)

print("Time spent: " + str(g.time()))

if not sat:
    print("Core:", end='')
    print(g.get_core())
else:
    print("Model:")
    print(g.get_model())

print("Success")
