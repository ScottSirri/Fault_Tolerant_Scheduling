from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random
import sys, time

VALID = 0
INVALID = -1

NOT = -1

# Ball-bin generation method parameters
c = 15
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
                collection[index].append(element+1)
            for sel_set in collection:
                if len(sel_set) > 0: 
                    self.family.append(sel_set)

    # Generates an invalid selector for testing purposes
    def bad_populate(self):
        num_collections = math.ceil(self.d * math.log(self.n))
        collection_size = math.ceil(self.c * self.k)
        sel_family_size = num_collections * collection_size
        print(" ====== BEWARE! BAD SELECTOR POPULATION! ======")

        self.family = []
        for i in range(self.k):
            sel_set = [] # List of lists, each of which is a selector set
            for element in range(n):
                if random.random() < .1:
                    sel_set.append(element+1)
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
                if i < 1 or i > self.n:  # Elements are in [1,n]
                    return INVALID
        return VALID

    # Prints the selector with stars denoting the "bottleneck" sets in which
    # the minimal set of selected elements are selected
    def print_sel(self, selected_list=None):
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
    if var_num < 0:
        var_num *= -1
    if 1 <= var_num and var_num <= n:
        return ["z", var_num]
    elif n+1 <= var_num and var_num <= 2*n:
        return ["x", var_num - n]
    elif 2*n+1 <= var_num and var_num <= (len(sel.family) + 2) * n:
        i = math.floor((var_num - 2*n) / n + 1)
        v = (var_num - 2*n) % n
        return ["y", i, v]
    elif (len(sel.family) + 2) * n < var_num:
        return ["AUX", var_num]
    else:
        return "INVALID"
def print_clauses(formula):
    print("Clauses: ", end='')
    for clause in formula:
        if type(clause) == str:
            continue
        for num in clause:
            var_name = get_var_name(num)
            num_str = ""
            if var_name[0] != "AUX":
                if num < 0:
                    num_str = "!"
                num_str = num_str + var_name[0]
                if var_name[0] == 'y':
                    num_str = num_str + str(var_name[1]) + "," + str(var_name[2])
                else:
                    num_str = num_str + str(var_name[1])
            else:
                num_str = var_name[0] + str(var_name[1])
            #print(f"{num}={num_str}   ",end='')
            print(f"{num_str}   ",end='')
        print()

def prep_sel(n, k, r, c, d):
    sel = Selector(n, k, r, c, d)
    sel.populate()
    if sel.validate() != VALID:
        print("======================== Invalid selector ========================")
        raise InputError("Invalid selector")
    return sel

def selection_constraints(solver, formula):
    # Had to do a little distributing to get this into CNF
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
                solver.add_clause([yiv])
                formula.append([yiv])
            else:
                solver.add_clause([NOT * yiv])
                formula.append([NOT * yiv])
            solver.add_clause(clause_v_i)
            formula.append(clause_v_i)

def card_constraints(solver, formula):
    # \sum x_{v} = k
    xv_k = CardEnc.equals(lits=list(range(n+1, 2*n+1)), 
                    bound=k, top_id = (len(sel.family) + 2)*n + 1, encoding=EncType.seqcounter)
    greatest_id = -1
    for clause in xv_k:
        solver.add_clause(clause)
        formula.append(clause)
        for num in clause:
            if abs(num) > greatest_id:
                greatest_id = abs(num)

    # \sum z_{v} < r
    zv_r = CardEnc.atmost(lits=list(range(1, n+1)), 
                          bound=r-1, top_id = greatest_id + 1, encoding=EncType.seqcounter)
    for clause in zv_r:
        solver.add_clause(clause)
        formula.append(clause)

for n in range (200, 350, 10):
    k = math.ceil(math.sqrt(n))
    r = math.ceil(k / 2.0)

    avg_time = 0
    num_iters = 10
    print(f"GENERATING ({n}, {k}, {r})-SELECTORS:")
    for i in range(num_iters):
        
        sel = prep_sel(n, k, r, c, d)

        g = Cadical(use_timer = True) # Arbitrary, choose a more suitable solver later
        formula = [] # Not integral to calculation, just for display

        selection_constraints(g, formula)
        card_constraints(g, formula)

        #print_clauses(formula)
        print("   # vars: " + str(g.nof_vars()) + f" ({(len(sel.family) + 2)*n} non-auxiliary)")
        print("# clauses: " + str(g.nof_clauses()) + "(vs formula " + str(len(formula)) + ")")

        sat = g.solve()

        print("Valid selector: " + str(not sat))
        avg_time += g.time()
        print("    Time spent: " + str(g.time()))

        if sat: # Only when invalid selector
            model = g.get_model()
            k_subset = []
            print("Model:")
            print(model[:2*n+1])
            for xv in range(n+1, 2*n+1):
                if model[xv - 1] > 0:
                    k_subset.append(xv)
            print("k_subset: " + str(k_subset))
            sel.print_sel(k_subset)
    avg_time /= num_iters
    print("AVG_TIME = " + str(avg_time))
    print("=============================================================\n")

print("Successfully terminated")
