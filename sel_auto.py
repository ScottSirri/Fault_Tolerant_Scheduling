from ortools.sat.python import cp_model
#https://developers.google.com/optimization/cp/cp_solver 
import math, random
from math import log
import sys, time
import itertools, re

VALID = 0
INVALID = -1

BINARY = 1 # Inclusive upper bound on values of ILP integer variables

# Helper function for output purposes
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

# Helper function for parsing string, extracting integers
def extract_vars_constraints(string):
    ints = re.findall(r'\d+', string)
    return [int(ints[0]), int(ints[5])+int(ints[7])+int(ints[9])+int(ints[10])]

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
    def __init__(self, in_n, in_k, in_r, in_c, in_d):
        self.family = []
        self.n = in_n
        self.k = in_k
        self.r = in_r
        self.c = in_c
        self.d = in_d

    # Populates the sets of the selector
    def populate(self):
        num_collections = math.ceil(self.d * log(self.n))
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

    # For the purposes of sanity check on verifying ILP correctness... except
    # it doesn't produce a selector that's disqualified by my ILP as often as
    # I think it should...
    def populate_incorrectly(self):
        num_collections = math.ceil(self.d * log(self.n))
        collection_size = math.ceil(self.c * self.k)
        sel_family_size = num_collections * collection_size
        # Achieve the same approximate proportion of element membership
        p = num_collections/sel_family_size

        self.family = []
        for i in range(sel_family_size):
            sel_set = [] # List of lists, each of which is a selector set
            while len(sel_set) <= 0:
                for j in range(n):
                    if random.random() < p:
                        sel_set.append(j)
                if len(sel_set) > 0: 
                    self.family.append(sel_set)
    
    # Returns the number of sets that would be in a selector of these
    # parameters produced by the modulo mapping method in Dr. Agrawal's paper.
    def modulo_num_slots(self):
        n = self.n
        k = self.k
        num_collections = k * math.ceil(log(n) / log(k * log(n)))
        primes = generate_primes(num_collections, math.floor(k * log(n)) + 1)
        num_slots = 0
        for prime in primes:
            num_slots += prime
        return num_slots

    # Validates that selector parameters and values are sensical
    def validate(self):
        if (self.n <= 0 or self.k <= 0 or self.r <= 0 or self.k > self.n
                or self.r > self.k or self.c <= 0 or self.d <= 0):
            return INVALID
        for set in self.family:
            if type(set) is not list:
                return INVALID
            for i in set:
                if i < 0 or i >= self.n:  # Elements are in [0,n)
                    print("================ Invalid selector ================")
                    raise InputError("Invalid selector")
                    return INVALID
        return VALID

    # Prints the selector with stars denoting the "bottleneck" sets in which
    # the minimal set of selected elements are selected
    def print_sel(self, selected_list = None):
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


class ILP:
    def __init__(self, selector):
        self.z_vars = []
        self.x_vars = []
        self.D_vars = []
        self.c_vars = []
        self.div_vars = []
        self.yiv_consts = []
        self.selector = selector
        self.model = cp_model.CpModel()

    # Initialize the y_{i,v} constants defining the selector (problem instance)
    def init_instance(self):
        # Initializing the instance (y variables)
        for sel_set in self.selector.family:
            set_i_list = []
            for i in range(self.selector.n):
                if i in sel_set:
                    set_i_list.append(1)
                else:
                    set_i_list.append(0)
            self.yiv_consts.append(set_i_list)

    # Initialize the ILP variables being optimized
    def init_vars(self):
        for v in range(self.selector.n):
            self.z_vars.append(self.model.NewIntVar(0, BINARY, f"z{v:03}"))
            self.x_vars.append(self.model.NewIntVar(0, BINARY, f"x{v:03}"))
            self.D_vars.append(self.model.NewIntVar(0, BINARY, f"D{v:03}"))
            self.c_vars.append(self.model.NewIntVar(0, BINARY, f"c{v:03}"))
        for i in range(len(self.selector.family)):
            di = []
            for v in range(self.selector.n):
                di.append(self.model.NewIntVar(0, BINARY, f"d{i},{v}"))
            self.div_vars.append(di)

    # Add to the ILP model the constraint for number of elements per subset
    def constraint_num_chosen(self):
        # Constraint: \sum x_{v} = k
        self.model.Add(sum(self.x_vars) == self.selector.k)

    # Add to the ILP model the keystone constraint for the conjunction to work
    def constraint_keystone(self):
        # Constraint: D_{v} = 1
        for v in range(self.selector.n):
            self.model.Add(self.D_vars[v] == 1)

    # Add to the ILP model the overall conjunction constraint
    def constraint_Dv(self):
        # Constraint: 0 <= 3*D_{v} - ... <= 2
        for v in range(self.selector.n):
            Dv, zv, xv, cv = self.D_vars[v], self.z_vars[v], self.x_vars[v], self.c_vars[v]
            D_constraint_lower = (0 <= 3*Dv - (zv + 1 - xv + cv))
            D_constraint_upper = (     3*Dv - (zv + 1 - xv + cv) <= 2)
            self.model.Add(D_constraint_lower)
            self.model.Add(D_constraint_upper)

    # Add to the ILP model the constraint that cv = 1 iff all div = 1
    def constraint_cv(self):
        # Constraint: -F + 1 <= F*c_{v} - ... <= 0
        F = len(self.selector.family)
        for v in range(self.selector.n):
            Dv, cv = self.D_vars[v], self.c_vars[v]
            dv = []
            for i in range(len(self.selector.family)):
                dv.append(self.div_vars[i][v])
            cv_constraint_lower = (-1*F + 1 <= F * cv - sum(dv))
            cv_constraint_upper = (            F * cv - sum(dv) <= 0)
            self.model.Add(cv_constraint_lower)
            self.model.Add(cv_constraint_upper)

    # Add to the ILP model the constraint that div = 1 iff v not selected by Si
    def constraint_div(self):
        # Constraint: 0 <= Si*d_{i,v} - ... <= Si - 1
        for v in range(self.selector.n):
            for i in range(len(self.selector.family)):
                div = self.div_vars[i][v]
                yiv = self.yiv_consts[i][v]
                Si = len(self.selector.family[i])
                x_i_not_v = []
                for var in self.selector.family[i]:
                    if var != v:
                        x_i_not_v.append(self.x_vars[var])
                div_constraint_lower = (0 <= Si * div - (1 - yiv + sum(x_i_not_v)))
                div_constraint_upper = (     Si * div - (1 - yiv + sum(x_i_not_v)) <= Si - 1)
                self.model.Add(div_constraint_lower)
                self.model.Add(div_constraint_upper)

    # Add to the ILP model the constraint that fewer than r elements of any
    # subset be selected, i.e., the candidate selector must be disqualified
    def constraint_r_selected(self):
        # "Objective function"
        self.model.Add(sum(self.z_vars) < self.selector.r) 

    # Runs the ILP once its been totally configured
    def run_ilp(self):
        print(f"Testing... ", end = '')
        self.solver = cp_model.CpSolver()
        self.status = self.solver.Solve(self.model)
    
    # Displays the results of the ILP once its been run
    def display_results(self):
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            # Only executes if <r elements are selected in some subset
            print(f"====== DISQUALIFIED CANDIDATE ({self.selector.n}, "
                  f"{self.selector.k}, {self.selector.r})-SELECTOR ======")
            selected_x = []
            ctr = 0
            for x in self.x_vars:
                val = self.solver.Value(x)
                if val == 1:
                    selected_x.append(ctr)
                    print(f'x{ctr:02} = {val} ***')
                else:
                    print(f'x{ctr:02} = {val}')
                ctr += 1
            self.selector.print_sel(selected_x)
            return INVALID
        else:
            print(f"    Confirmed ({self.selector.n}, {self.selector.k}, "
                  f"{self.selector.r})-selector")
            return VALID

    # Dumps the relevant variables for debugging purposes
    def dump_vars(self):
        if self.solver == None:
            print("Cannot var dump")
            return
        print("===== Var dumping ====")
        num_sel = 0
        for z in self.z_vars:
            print(str(z))
            num_sel += self.solver.Value(z)
            if self.solver.Value(z) > 0:
                print(str(z))
        for v in range(self.selector.n):
            var = self.x_vars[v]
            if self.solver.Value(var) != 1:
                continue
            print(str(var) + "  " + str(self.solver.Value(var)))
            var = self.z_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            var = self.D_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            var = self.c_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            for i in range(len(self.selector.family)):
                var = self.div_vars[i][v]
                print(str(var) + "  " + str(self.solver.Value(var)))
            print()
        print("Number of elements selected: " + str(num_sel))

    # Perform an iteration of the ILP, including instantiation, initialization,
    # running, and reporting of results
    def ilp_iter(self):
        local_timer = My_Timer()
        local_timer.start_timer()

        # Initialization, variables
        self.init_instance()
        self.init_vars()
        # Constraints
        self.constraint_num_chosen()
        self.constraint_keystone()
        self.constraint_Dv()
        self.constraint_cv()
        self.constraint_div()
        self.constraint_r_selected()
        local_timer.stop_timer()
        gen_time = local_timer.get_time()

        #print(self.model.ModelStats())
        stats = self.model.ModelStats()
        nums_tuple = extract_vars_constraints(stats)
        num_vars = nums_tuple[0]
        num_constraints = nums_tuple[1]

        # Run
        local_timer.start_timer()
        self.run_ilp()
        local_timer.stop_timer()
        run_time = local_timer.get_time()
        
        print("Selector size: %03d, # ILP vars: %05d, # ILP constraints: %05d"
              % (len(self.selector.family), num_vars, num_constraints))
        print("    Time to generate vs run ILP: %.3f vs %.3f\t" % 
              (gen_time, run_time))
        results = self.display_results()
        if results == INVALID:
            self.dump_vars()
            print("Awaiting user input, press enter when ready...")
            input()
        #else:   # Delete this else-statement later, it's for testing purposes
        #    self.selector.print_sel()
        return [gen_time, run_time]

# Perform the naive verification, exhaustively checking {n \choose k} subsets
def naive_verify(selector):
    my_timer = My_Timer()
    my_timer.start_timer()
    subsets = itertools.combinations(range(selector.n), selector.k)
    for subset in subsets:
        selected = []
        for sel_set in selector.family:
            inter_set = intersection(subset, sel_set)
            if len(inter_set) == 1:
                if inter_set[0] not in selected:
                    selected.append(inter_set[0])
        if len(selected) < selector.r:
            print("=== DISQUALIFIED (%d, %d, %d)-SELECTOR ===" % 
                  (selector.n, selector.k, selector.r))
            my_timer.stop_timer()
            return [INVALID, my_timer.get_time()]
    print("    Confirmed (%d, %d, %d)-selector" % 
          (selector.n, selector.k, selector.r))
    my_timer.stop_timer()
    return [VALID, my_timer.get_time()]

# The main code that's run

c, d = 2, 3
NAIVE = False
if NAIVE:
    lower, upper, step = 21, 100, 2
else:
    lower, upper, step = 105, 200, 10
    

for n_ind in range(lower, upper + step, step):
    n = n_ind
    k = math.ceil(math.sqrt(n))
    r = math.ceil(k/2)
    sel = Selector(n, k, r, c, d)

    print(f"=== ({n}, {k}, {r}) ===")
    #print("MODULO size: %d" % sel.modulo_num_slots())
    avg_gen_time, avg_run_time = 0, 0
    iters = 4
    for i in range(iters):
        print("%02d)." % (i+1), end = '')
        sel = Selector(n, k, r, c, d)
        #sel.populate_incorrectly(c, d)
        sel.populate()
        sel.validate()
        if not NAIVE:
            #sel.print_sel()
            ilp = ILP(sel)
            times = ilp.ilp_iter()
            avg_gen_time += times[0]
            avg_run_time += times[1]
        else:
            output = naive_verify(sel)
            print("Time elapsed: %.3f" % output[1])
            avg_run_time += output[1]
    avg_run_time /= iters
    if not NAIVE:
        avg_gen_time /= iters
        print("\tAverage time: %.3f (%.3f vs %.3f)" % 
              ((avg_gen_time + avg_run_time), avg_gen_time, avg_run_time))
    else:
        print("\tAverage time: %.3f" % avg_run_time)
    print()

print("Success")
