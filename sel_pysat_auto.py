from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random
import sys, os, time
import csv, signal
from datetime import datetime

VALID = 0
INVALID = -1

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

window_width = os.get_terminal_size().columns
resize_msg = "DO NOT RESIZE WINDOW DURING PROGRAM EXECUTION"
if window_width > 45:
    print(f"{' ' * (math.floor((window_width - len(resize_msg)) / 2))}", end='', flush=True)
print(resize_msg)

def resizeHandler(signum, frame):
    window_width = os.get_terminal_size().columns
    #print("resize-window signal caught")
signal.signal(signal.SIGWINCH, resizeHandler)

logging_data = False

if len(sys.argv) > 1:
    if sys.argv[1] == 'log':
        logging_data = True

if logging_data:
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
    filename = './data/' + date_time_str

    f = open(filename, 'w')
    writer = csv.writer(f)
    header = ['c', 'd', 'n', 'k', 'r', 'gen_time', 'solve_time', 'valid', 'sel_len']
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
        return [num_collections, collection_size]

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

    # Returns the number of sets that would be in a selector of these
    # parameters produced by the modulo mapping method in Dr. Agrawal's paper.
    def modulo_num_slots(self):
        n = self.n
        k = self.k
        num_collections = k * math.ceil(math.log(n) / math.log(k * math.log(n)))
        primes = generate_primes(num_collections, math.floor(k * math.log(n)) + 1)
        num_slots = 0
        for prime in primes:
            num_slots += prime
        return num_slots

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
            print(f"{num_str}   ",end='')
        print()

def prep_sel(n, k, r, c, d):
    sel = Selector(n, k, r, c, d)
    collection_data = sel.populate()
    if sel.validate() != VALID:
        print("====================== Invalid selector ======================")
        raise InputError("Invalid selector")
    return [sel, collection_data[0], collection_data[1]]

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

def my_trunc(num):
    num *= 1000
    num = math.trunc(num)
    num /= 1000
    return num

cd_vals = [[3,2], [2,3], [2,2], [2,1], [1,2], [1,1]]
n_vals = [10,20,30,40,50,60,70,80,90,100]
for pair in cd_vals:
    c, d = pair[0], pair[1]
    for n in n_vals: # Cycling through n values
        if pair == [3,2] and n == 100:
            continue
        k_0 = math.ceil(math.sqrt(n))
        r_0 = math.ceil(k_0/2)

        params_valid_time, params_invalid_time = 0, 0
        params_gen_time = 0
        num_correct = 0
        num_iters = 20
        logging_str = ''
        if not logging_data:
            logging_str = '[NOT LOGGING] '
        header_str = f"{logging_str}({n}, {k_0}, {r_0})-sels for (c,d)=({c},{d}): "
        lines_up = math.floor((len(header_str) - 1) / window_width) + 1
        print(header_str)
        progress_bar = []
        for iter_ind in range(num_iters): # Generating & testing num_iters different selectors

            sel_tuple = prep_sel(n, k_0, r_0, c, d)
            sel = sel_tuple[0]
            
            reduc_index = 0
            valid = True
            sub_index_invalid = False
            k = k_0

            iter_gen_time, iter_solve_time = 0, 0

            while k > 1: # Logarithmically iterate over the SAME selector to check reducibility

                gen_timer = My_Timer()
                solve_timer = My_Timer()

                # Parameters for this iteration of reducibility check
                k = k_0 if reduc_index == 0 else math.ceil(k / (2**reduc_index))
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
                    clean_up()
                    sys.exit(0)
                solve_timer.stop_timer()
                iter_solve_time += solve_timer.get_time()

                if sat: # Only when invalid selector
                    valid = False

                    if reduc_index > 1: # Unlikely for top selector to be valid and sub-selector to not be
                        sub_index_invalid = True

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
                    break
                else: # Valid selector
                    model.delete()

                reduc_index += 1 # Loop variable
            # === Outside the logarithmic while loop over k ===


            if logging_data: # Write data to file
                valid_char = 'Y' if valid else 'N'
                data_row = [c, d, n, k_0, r_0, iter_gen_time, iter_solve_time, valid_char, len(sel.family)]
                writer.writerow(data_row)

            # Update time + validity counts for this set of parameters
            params_gen_time += iter_gen_time
            if valid:
                params_valid_time   += iter_solve_time
                progress_bar.append('+')
                num_correct += 1
            else:
                params_invalid_time += iter_solve_time
                if sub_index_invalid:
                    progress_bar.append('!')
                else:
                    progress_bar.append('-')

            # (Temporary) normalized time variables for display purposes
            avg_params_gen_time = my_trunc(params_gen_time / (iter_ind+1))

            if num_correct != 0:
                avg_params_valid_time = my_trunc(params_valid_time / num_correct)
            else:
                avg_params_valid_time = -1.0

            if num_correct != iter_ind + 1:
                avg_params_invalid_time = my_trunc(params_invalid_time / (iter_ind + 1 - num_correct))
            else:
                avg_params_invalid_time = -1.0

            # Output stats
            stats_str = f" gen time={avg_params_gen_time}, avg valid={avg_params_valid_time}, avg invalid={avg_params_invalid_time}, {num_correct}/{iter_ind+1}"
            
            # Moves the cursor up and clears the lines above
            for i in range(lines_up):
                print(f"\033[A\r{' ' * window_width}\r", end='', flush=True)
            
            str_len = len(header_str) + len(stats_str)
            lines_up = math.floor((str_len - 1) / window_width) + 1

            print(header_str + stats_str)
            for char in progress_bar:
                print(char, end='')
            print('', end='', flush=True)
        print()
    print("==============================================================\n")

clean_up()
print("Successfully terminated")
