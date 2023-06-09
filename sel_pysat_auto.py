from pysat.solvers import Cadical153
from pysat.card import *
import math, random
from math import ceil
import sys, os, time
import csv, signal
import itertools
from datetime import datetime

VALID   = True
INVALID = False

WEAK_REDUC   = 0
STRONG_REDUC = 1

SAT_METHOD   = 0
NAIVE_METHOD = 1

EPS = .001

NOT = -1

DEBUG_INVALID = False

program_start_time = time.time()

# Utility class for timing code execution
class My_Timer:
    def __init__(self):
        self.start_time = -1
        self.end_time = -1

    # Start the timer
    def start_timer(self):
        if self.start_time <= 0:
            self.start_time = time.process_time()
        else:
            print("start_timer error")

    # Stop the timer
    def stop_timer(self):
        if self.end_time <= 0 and self.start_time > 0:
            self.end_time = time.process_time()
        else:
            print("stop_timer error: self.end_time = %f and self.start_time = %f" % (self.end_time, self.start_time))

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

    def reset(self):
        self.start_time = -1
        self.end_time = -1

    # Get the timer duration
    def get_time_no_reset(self):
        if self.start_time <= 0 or self.end_time <= self.start_time:
            print("get_time error")
            return
        elapsed = self.end_time - self.start_time
        return elapsed

logging_data = False

if len(sys.argv) > 1:
    if sys.argv[1] == 'log':
        logging_data = True

if logging_data:
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
    filename = './data/' + date_time_str

    file_obj = open(filename, 'w')
    writer = csv.writer(file_obj)
    header =   ['c', 'd', 'n', 'time', 'valid', 'method', 'reducibility', 'mapping length']
    writer.writerow(header)

def clean_up():
    if logging_data:
        f.close()
        print('closed file')
    else:
        print('not logging data, no file to close')
    print('elapsed real time: ' + str(time.time() - program_start_time))

def signal_handler(sig, frame):
    print('\n\n\nYou pressed Ctrl+C')
    clean_up()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(math.sqrt(num)) + 1):
        if num % i == 0:
            return False
    return True

# Generate the first num_primes prime numbers >= lower
def generate_primes(lower, num_primes):
    primes = []
    i = lower
    if i % 2 == 0:
        i += 1
    while len(primes) < num_primes:
        if is_prime(i):
            primes.append(i)
        i += 2
    return primes

class InputError(Exception):
    pass


class Selector:
    family = []

    def __init__(self, in_n, in_k, in_c, in_d):
        self.n = in_n
        self.k = in_k
        self.r = ceil(self.k/2)
        self.c = in_c
        self.d = in_d

    # Populates the sets of the selector
    def populate(self):
        num_collections = ceil(self.d * math.log(self.n))
        collection_size = ceil(self.c * self.k)
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
        num_collections = ceil(self.d * math.log(self.n))
        collection_size = ceil(self.c * self.k)
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
        for sel_set in self.family:
            if type(sel_set) is not list:
                return INVALID
            for i in sel_set:
                if i < 1 or i > self.n:  # Elements are in [1,n]
                    return INVALID
        return VALID

    # Prints the selector with stars denoting the "bottleneck" sets in which
    # the minimal set of selected elements are selected
    def print_sel(self, selected_list=None):
        if selected_list == None:
            selected_list = []
        print("Candidate selector(%d, %d, %d):" % (self.n, self.k, self.r))
        for sel_set in self.family:
            print("\t", end='')
            marker = "    " 
            if len(intersection(sel_set, selected_list)) == 1:
                   marker = "*** "
            print(marker, end = '')
            #print(sel_set)
            for elem in sel_set:
                print(" .%d. " % (elem), end="")
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
            print("%s   " % (num_str),end='')
        print()

def prep_sel(n, k, c, d):
    sel = Selector(n, k, c, d)
    sel.populate()
    if sel.validate() != VALID:
        print("====================== Invalid selector ======================")
        raise InputError("Invalid selector")
    return sel

def selection_constraints(sel_in, k, r, solver, formula):
    num_sel_consts = 0
    # Had to do a little distributing to get this into CNF
    for v in range(1, n+1):
        zv,xv = get_var_num(["z",v]), get_var_num(["x",v])
        for i in range(1, len(sel_in.family)+1):
            v_in_Si = False

            clause_v_i = [zv, NOT * xv] # Left out the NOT * v_in_Si
            for x_num_raw in sel_in.family[i-1]:
                if x_num_raw != v:
                    x_not_v = get_var_num(["x", x_num_raw])
                    clause_v_i.append(x_not_v)
                else:
                    v_in_Si = True
            if v_in_Si == True: # If v isn't in Si, the clause is trivially true
                num_sel_consts += 2
                solver.add_clause(clause_v_i)
                formula.append(clause_v_i)

def card_constraints(sel_in, k, r, solver, formula):
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

def findsubsets(n, k):
    s = range(1, n+1, 1)
    return list(itertools.combinations(s, k))

# Count the number of True elements in a passed list of booleans
def num_selected(sel_arr):
    num = 0
    for elem in sel_arr:
        if elem == True:
            num += 1
    return num

# Naively check whether the selector is 1/2-good for the subset sizes in k_vals
def naive_verify(sel, k_vals):
    timer = My_Timer()
    timer.start_timer()
    n = sel.n

    for k in k_vals:
        print("next k = %d" % (k))
        r = ceil(k/2)
        subsets = findsubsets(n, k)

        for subset in subsets:
            selected = [False] * n

            for slot in sel.family:
                num_subset_elems = 0
                selected_elem = -1

                for elem in slot:
                    if elem in subset:
                        num_subset_elems += 1
                        selected_elem = elem

                if num_subset_elems == 1: # If elem is selected in this slot
                    selected[selected_elem - 1] = True 

            if num_selected(selected) < r:
                return [INVALID, -1]

    timer.stop_timer()
    return [VALID, timer.get_time()]

# Use SAT solver to check whether the selector is 1/2-good for the subset sizes in k_vals
def sat_verify(sel, k_vals):
    timer = My_Timer()
    timer.start_timer()

    for k in k_vals:                 

        r = ceil(k/2 - EPS)

        # Initialize model
        model = Cadical153(use_timer = True)
        formula = [] # Not integral to calculation, just for display

        # Add constraints to model
        selection_constraints(sel, k, r, model, formula)
        card_constraints(sel, k, r, model, formula)

        #Solve model using SAT method
        try:
            sat = model.solve()
        except Exception as err:
            print("\n\n\nException occurred during the pysat solver's operation")
            print("Unexpected {err=}, {type(err)=}")
            clean_up()
            sys.exit(0)

        if sat: # Only when not 1/2-good for this subset size
            if DEBUG_INVALID == True: # Dump details of the invalid selector
                model = model.get_model()
                k_subset = []
                print("Model:")
                print(model[:2*n])
                for xv in range(n+1, 2*n+1):
                    if model[xv - 1] > 0:
                        k_subset.append(xv - n)
                print("k_subset: " + str(k_subset))
                sel.print_sel(k_subset)
                input()
            return [INVALID, -1]
        else: # Valid selector
            model.delete()

    timer.stop_timer()
    return [VALID, timer.get_time()]

# Print the results of that iteration and, if logging data, write it to file
def log_data(sel, data, method, reduc):
    output_str = ''

    if method == SAT_METHOD:
        output_str += "  SAT"
    else:
        output_str += "NAIVE"

    if reduc == WEAK_REDUC:
        output_str += "   WEAK"
    else:
        output_str += " STRONG"

    output_str += f" n={sel.n:>3} c={sel.c} d={sel.d} "

    if data[0] == VALID:
        output_str += " VALID "
        output_str += f"{data[1]:3.4f}"
    else:
        output_str += " INVALID"

    print(output_str, flush=True)

    if logging_data:
        valid_str = 'Y' if data[0] == VALID else 'N'
        method_str = 'sat' if method == SAT_METHOD else 'naive'
        reduc_str = 'weak' if reduc == WEAK_REDUC else 'strong'
        time = data[1]

        data_row = [sel.c, sel.d, sel.n, time, valid_str, method_str, reduc_str, len(sel.family)]
        writer.writerow(data_row)
        file_obj.flush()

def is_empty(list_in):
    return len(list_in) == 0

def generate_weak_k_vals(n, k):
    k_vals_weak = []
    k_ind = 1
    new_k_val = ceil(k/2 + k/(2*k_ind) - EPS)
    lowest = ceil(k/2 - EPS) + 1
    assert new_k_val == k, "First weak k val isn't k"

    while new_k_val > lowest:

        if is_empty(k_vals_weak) or new_k_val != k_vals_weak[len(k_vals_weak) - 1]:
            k_vals_weak.append(new_k_val)

        k_ind += 1
        new_k_val = ceil(k/2 + k/(2*k_ind) - EPS)

    k_vals_weak.append(lowest)
    #k_vals_weak.append(lowest - 1)  NOT SURE THIS SHOULD BE COMMENTED OUT
    return k_vals_weak

#cd_vals = [[12,12], [12,8], [12,4], [8,8], [8,4], [4,4], [3,2], [2,3], [2,2], [2,1], [1,2], [1,1]]
#n_vals = range(100, 1001, 100)
n_vals = range(1000, 99, -100)

num_iters = 10
c, d = 3, 3

for i in range(num_iters):
    for n in n_vals: # Cycling through n values

        k = 4

        print("")
        if not logging_data:
            print("[NOT LOGGING DATA]", end='')
        print("====== n=%d, k=%d ========\n" % (n,k))

        # The set of subset sizes that must be checked for 1/2-goodness in a weakly reducible selector
        k_vals_weak = generate_weak_k_vals(n, k)

        # The set of subset sizes that must be checked for 1/2-goodness in a strongly reducible selector
        """k_vals_strong = range(1, k+1, 1) # The list [1, 2, ..., k]"""

        print("weak: ", k_vals_weak)
        """print("strong: ", k_vals_strong)"""

        sel = prep_sel(n, k, c, d)

        sat_weak_data = sat_verify(sel, k_vals_weak)
        log_data(sel, sat_weak_data, SAT_METHOD, WEAK_REDUC)

        """sat_strong_data = sat_verify(sel, k_vals_strong)
        log_data(sel, sat_strong_data, SAT_METHOD, STRONG_REDUC)

        naive_weak_data = naive_verify(sel, k_vals_weak)
        log_data(sel, naive_weak_data, NAIVE_METHOD, WEAK_REDUC)

        naive_strong_data = naive_verify(sel, k_vals_strong)
        log_data(sel, naive_strong_data, NAIVE_METHOD, STRONG_REDUC)"""

clean_up()
print("Successfully terminated")
