from ortools.sat.python import cp_model
#https://developers.google.com/optimization/cp/cp_solver 
import math, random
import sys, time

VALID = 0
INVALID = -1

BINARY = 1 # Inclusive upper bound on values of integer variables

# Helper function for output purposes
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
        self.start_time = -1
        self.end_time = -1

    def start_timer(self):
        if self.start_time <= 0:
            self.start_time = time.perf_counter()
        else:
            print("start_timer error")

    def stop_timer(self):
        if self.end_time <= 0 and self.start_time > 0:
            self.end_time = time.perf_counter()
        else:
            print("stop_timer error")

    def print_timer(self):
        if self.start_time <= 0 or self.end_time <= self.start_time:
            print("print_timer error")
            return
        print("Time elapsed: " + str(self.end_time - self.start_time))
        return self.end_time - self.start_time
        self.start_time = -1
        self.end_time = -1

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
        print(f"Testing for ({sel.n}, {sel.k}, {sel.r})-selector")
        self.start_timer()
        self.solver = cp_model.CpSolver()
        self.status = self.solver.Solve(self.model)
        self.stop_timer()
        return self.print_timer()
    
    # Displays the results of the ILP once its been run
    def display_results(self):
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            # Only executes if <r elements are selected in some subset
            print(f"====== DISQUALIFIED CANDIDATE ({self.selector.n}, "
                  f"{self.selector.k}, {self.selector.r})-SELECTOR ======")
            selected_x = []
            ctr = 0
            for x in x_vars:
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
            print(f"Confirmed ({self.selector.n}, {self.selector.k}, "
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
            var = z_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            var = D_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            var = c_vars[v]
            print(str(var) + "  " + str(self.solver.Value(var)))
            for i in range(len(self.selector.family)):
                var = self.div_vars[i][v]
                print(str(var) + "  " + str(self.solver.Value(var)))
            print()
        print("Number of elements selected: " + str(num_sel))

    def ilp_iter(self):
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
        # Run
        run_time = self.run_ilp()
        results = self.display_results()
        if results == INVALID:
            self.dump_vars()
        #else:   # Delete this else-statement later, it's for testing purposes
        #    self.selector.print_sel()
        return run_time


c, d = 2, 3

for k_ind in range(5, 8):
    n, k, r = k_ind**2, k_ind, math.ceil(k_ind/2)
    print("=== ({n}, {k}, {r}) ===")
    avg_time = 0
    iters = 5
    for i in range(iters):
        sel = Selector(n, k, r, c, d)
        sel.populate()
        sel.validate()
        ilp = ILP(sel)
        run_time = ilp.ilp_iter()
        avg_time += run_time
    avg_time /= iters
    print(f"Average time: {avg_time}")
    print()

print("Success")
