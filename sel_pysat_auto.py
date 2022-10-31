from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random
import sys, time

VALID = 0
INVALID = -1

NOT = -1

# Ball-bin generation method parameters
c = 2
d = 2

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

class InputError(Exception):
    pass

# Utility class for timing code execution
class My_Timer:
    def __init__(self):
        self.start_time = -1
        self.end_time = -1

    # Start the timer
    def start_timer(self):
        if self.start_time <= 0:
            self.start_time = time.time()
        else:
            print("start_timer error")

    # Stop the timer
    def stop_timer(self):
        if self.end_time <= 0 and self.start_time > 0:
            self.end_time = time.time()
        else:
            print("stop_timer error")

    # Print the timer duration and reset it
    def print_timer(self):
        if self.start_time <= 0 or self.end_time <= self.start_time:
            print("print_timer error")
            return
        elapsed = self.end_time - self.start_time
        print("Time elapsed: %.3f" % elapsed)
        self.start_time = -1
        self.end_time = -1
        return elapsed
    
    # Get the timer duration and reset it
    def get_time(self):
        if self.start_time <= 0 or self.end_time <= self.start_time:
            print("get_time error")
            return
        elapsed = self.end_time - self.start_time
        self.start_time = -1
        self.end_time = -1
        return elapsed

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
        #print(f"num_collections={num_collections}, collection_size={collection_size}")

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
            #print(sel_set)
            for elem in sel_set:
                print(f" .{elem}. ", end="")
            print()
        print()


"""
            [1,n]: z_{v}
         [n+1,2n]: x_{v}

var_data is a tuple with first entry one of 'z', 'x', 'y'
The next one or two entries are the var numbers
Returns the integer mapped to that.
"""
def get_var_num(var_data):
    if var_data[0] == "z":
        return var_data[1]
    elif var_data[0] == "x":
        return n + var_data[1]
    else:
        return "INVALID"
def get_var_name(var_num):
    # Negation
    if var_num < 0:
        var_num *= -1

    if 1 <= var_num and var_num <= n:
        return ["z", var_num]
    elif n+1 <= var_num and var_num <= 2*n:
        return ["x", var_num - n]
    elif 2*n+1 <= var_num:
        return ["AUX", var_num]
    else:
        return "INVALID"
def print_clauses(formula):
    print("Clauses: ")
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
    num_sel_consts = 0
    # Had to do a little distributing to get this into CNF
    for v in range(1, n+1):
        zv,xv = get_var_num(["z",v]), get_var_num(["x",v])
        for i in range(1, len(sel.family)+1):
            v_in_Si = False

            clause_v_i = [zv, NOT * xv] # Technically, there'd also be a NOT * v_in_Si
            for x_num_raw in sel.family[i-1]:
                if x_num_raw != v:
                    x_not_v = get_var_num(["x", x_num_raw])
                    clause_v_i.append(x_not_v)
                else:
                    v_in_Si = True
            if v_in_Si == True: # If v isn't in Si, the clause is trivially true
                num_sel_consts += 2
                solver.add_clause(clause_v_i)
                formula.append(clause_v_i)

def card_constraints(solver, formula):
    # \sum x_{v} = k
    xv_k = CardEnc.equals(lits=list(range(n+1, 2*n+1)), 
                    bound=k, top_id = 2*n + 1, encoding=EncType.mtotalizer)
    greatest_id = -1
    for clause in xv_k:
        solver.add_clause(clause)
        formula.append(clause)
        for num in clause:
            if abs(num) > greatest_id:
                greatest_id = abs(num)

    # \sum z_{v} < r
    zv_r = CardEnc.atmost(lits=list(range(1, n+1)), 
                          bound=r-1, top_id = greatest_id + 1, encoding=EncType.mtotalizer)
    for clause in zv_r:
        solver.add_clause(clause)
        formula.append(clause)

"""
# main
for c in range(14,1,-3):
    for n in range(10, 501, 10):
        k = math.ceil(math.sqrt(n))
        #r = math.ceil(k / 2.0)
        r = k

        avg_time = 0
        num_iters = 10
        print(f"GENERATING ({n}, {k}, {r})-SELECTORS for (c,d)=({c},{d}):")
        for i in range(num_iters):
            
            sel = prep_sel(n, k, r, c, d)

            model = Cadical(use_timer = True) # Arbitrary, choose a more suitable solver later
            formula = [] # Not integral to calculation, just for display

            selection_constraints(model, formula)
            card_constraints(model, formula)

            #print_clauses(formula)
            if i == 0:
                print("   # vars: " + str(model.nof_vars()) + f" ({2*n} non-auxiliary)")
                print("# clauses: " + str(model.nof_clauses()))

            sat = model.solve()
            #print("/",end='',flush=True)

            #print("Valid selector: " + str(not sat))
            avg_time += model.time()
            print(f"({i+1}/{num_iters}) Time spent: " + str(model.time()))

            if sat: # Only when invalid selector
                model = model.get_model()
                k_subset = []
                print("Model:")
                print(model[:2*n+1])
                for xv in range(n+1, 2*n+1):
                    if model[xv - 1] > 0:
                        k_subset.append(xv - n)
                print("k_subset: " + str(k_subset))
                sel.print_sel(k_subset)
            model.delete()
        avg_time /= num_iters
        print("AVG_TIME = " + str(avg_time))
        print("=============================================================\n")
"""

def my_trunc(num):
    num *= 100
    num = math.trunc(num)
    num /= 100
    return num

data = {}
for sum_vals in range(8,40,4):
    c = math.floor(sum_vals / 2)
    d = math.floor(sum_vals / 2)
    if sum_vals % 2 == 1:
        c += 1
    for n in range(100, 501, 100):
        k = math.ceil(math.sqrt(n))
        r = k

        avg_solve_time = 0
        avg_gen_time = 0
        num_correct = 0
        num_iters = 10
        print(f"GENERATING ({n}, {k}, {r})-SELECTORS for (c,d)=({c},{d}): ")
        for i in range(num_iters):
            
            sel = prep_sel(n, k, r, c, d)

            model = Cadical(use_timer = True) # Arbitrary, choose a more suitable solver later
            formula = [] # Not integral to calculation, just for display

            model_timer = My_Timer()
            model_timer.start_timer()

            selection_constraints(model, formula)
            card_constraints(model, formula)

            model_timer.stop_timer()
            avg_gen_time += model_timer.get_time()

            #print_clauses(formula)
            if i == 0:
                print("   # vars: " + str(model.nof_vars()) + f" ({2*n} non-auxiliary)")
                print("# clauses: " + str(model.nof_clauses()))

            sat = model.solve()
            avg_solve_time += model.time()

            if sat: # Only when invalid selector
                """
                model = model.get_model()
                k_subset = []
                print("Model:")
                print(model[:2*n])
                for xv in range(n+1, 2*n+1):
                    if model[xv - 1] > 0:
                        k_subset.append(xv - n)
                print("k_subset: " + str(k_subset))
                sel.print_sel(k_subset)
                """
                print("|",end="",flush=True)
            else:
                print(".",end="",flush=True)
                num_correct += 1
                model.delete()
        avg_solve_time /= num_iters
        avg_gen_time /= num_iters

        print(f"  [{n},{c},{d}]: [{my_trunc(avg_gen_time)}, {my_trunc(avg_solve_time)}, {num_correct}]")
        if num_correct == 0:
            break
    print()
print("Successfully terminated")
