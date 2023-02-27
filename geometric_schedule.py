from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random

class Schedule:
    def __init__(self, n_in, f_in, c_in, d_in):
        self.n = n_in
        self.f = f_in
        self.c = c_in
        self.d = d_in
        self.schedule = []

    def generate_schedule(self):

        # Identity mapping
        for i in range(n):
            schedule.append([i+1])

        # Phase i
        for i in range(ceil(math.log(self.f, 2) + 1)):
            
            num_mappings = ceil(2 * (1 + 2**(i+1)))
            valid = false

            while not valid:
                mapping = self.generate_mapping(self.f / (2**i))
                if self.is_valid(mapping):
                    valid = True

            self.concatenate(mapping, num_mappings)

    def generate_mapping(self, m):
        num_collections = ceil(self.d * math.log(self.n))
        collection_size = ceil(self.c * m)

        mapping_length = num_collections * collection_size
        mapping = []

        for i in range(num_collections):

            collection = [] # List of lists, each of which is a time slot      
            for j in range(collection_size):
                collection.append([])

            for node in range(n):
                index = math.floor(random.uniform(0, collection_size))
                collection[index].append(node + 1)

            for slot in collection:
                if len(slot) > 0: 
                    mapping.append(slot)

        return mapping


    def selection_constraints(mapping, solver, formula):

        for v in range(1, n+1):
            zv,xv = get_var_num(["z", v]), get_var_num(["x", v])

            for i in range(len(mapping)):
                v_in_slot_i = False

                clause_v_i = [zv, NOT * xv] # Left out the NOT * v_in_slot_i
                for x_num_raw in mapping[i]:
                    if x_num_raw != v:
                        x_not_v = get_var_num(["x", x_num_raw])
                        clause_v_i.append(x_not_v)
                    else:
                        v_in_slot_i = True

                if v_in_slot_i == True: # If v isn't in Si, the clause is trivially true
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


    def is_valid(self, mapping):

        k_vals = []
        k_ind = 1
        EPS = .001

        while (new_k_val := math.ceil(k/2 + k/(2*k_ind) - EPS)) > math.ceil(k/2) + 1:
            if len(k_vals) == 0 or (len(k_vals) > 0 and new_k_val != k_vals[len(k_vals) - 1]):
                k_vals.append(new_k_val)
            k_ind += 1
        
        # Logarithmically iterate over SAME selector to check reducibility
        for k in k_vals:                 
            gen_timer = My_Timer()
            solve_timer = My_Timer()

            # Parameter for this iteration of reducibility check
            r = math.ceil(k / 2)

            # Initialize model
            model = Cadical(use_timer = True)
            formula = [] # Not integral to calculation, just for display

            # Add constraints to model
            gen_timer.start_timer()
            selection_constraints(sel, k, r, model, formula)
            card_constraints(sel, k, r, model, formula)
            gen_timer.stop_timer()
            iter_gen_time += gen_timer.get_time()

            #Solve model
            solve_timer.start_timer()
            try:
                sat = model.solve()
            except Exception as err:
                print("\n\n\nException occurred during the pysat solver's operation")
                print(f"Unexpected {err=}, {type(err)=}")
