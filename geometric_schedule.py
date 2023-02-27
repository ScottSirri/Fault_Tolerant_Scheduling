from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random, time
from math import ceil, log
import sys, os
import csv, signal
from datetime import datetime

VALID = 0
INVALID = -1

NOT = -1

PHASE_DELIMITERS = False
DEBUG_PRINT = True

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

# Start logging data if indicated on command line
logging_data = False

param_n = int(sys.argv[1])
param_f = int(sys.argv[2])

if len(sys.argv) == 4:
    if sys.argv[3] == 'log':
        logging_data = True

if logging_data:
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
    filename = './sched_data/' + date_time_str

    f = open(filename, 'w')
    writer = csv.writer(f)
    header = ['n', 'f', 'c', 'd', 'time', 'sched_len']
    writer.writerow(header)

# Closes data file and prints time elapsed
def clean_up():
    if logging_data:
        f.close()
        print('closed file')
    else:
        print('not logging data, no file to close')
    print('elapsed real time: ' + str(time.time() - program_start_time))

# Handles CTRL + C terminating execution
def signal_handler(sig, frame):
    print('\n\n\nYou pressed Ctrl+C')
    clean_up()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

class Schedule:
    def __init__(self, n_in, f_in, c_in, d_in):
        self.n = n_in
        self.f = f_in
        self.c = c_in
        self.d = d_in
        self.schedule = []
        self.length = 0

    # Generates the entire reducible 1/2-good schedule
    def generate_schedule(self):

        self.schedule.clear()
        self.length = 0

        mapping_timer = My_Timer()

        sched_timer = My_Timer()
        sched_timer.start_timer()

        # Identity mapping
        for i in range(self.n):
            self.schedule.append([i+1])

        if PHASE_DELIMITERS:
            self.schedule.append(["=" for i in range(20)])

        # Phase i
        for i in range(ceil(log(self.f, 2) + 1)):
            
            num_mappings = ceil(2 * (1 + 2**(i+1))) # \alpha = 1/2
            valid = False

            mapping_timer.start_timer()

            num_attempts = 0
            while not valid: # Generate until valid mapping obtained

                m = self.f / (2**i)

                if DEBUG_PRINT:
                    print(f"{num_attempts} failed")

                mapping = self.generate_mapping(m)
                valid = self.is_valid(mapping, m)

                if valid:
                    mapping_timer.stop_timer()
                    if DEBUG_PRINT:
                        print(f"phase {i}, m = {m}, valid mapping (time {mapping_timer.get_time()})")
                num_attempts += 1

            self.concatenate(mapping, num_mappings)

            if PHASE_DELIMITERS:
                self.schedule.append(["=" for i in range(25)])

        # Full schedule has now been generated
        self.length = len(self.schedule)

        sched_timer.stop_timer()
        duration = sched_timer.get_time()

        if DEBUG_PRINT:
            print(f"n={self.n} f={self.f} c={self.c} d={self.d} time={duration} schedule_length={self.length}")
        
        if logging_data: # Write data to file
            data_row = [self.n, self.f, self.c, self.d, duration, self.length]
            writer.writerow(data_row)


    # Generates the smaller 1/2-good mappings
    def generate_mapping(self, m):
        num_collections = ceil(self.d * log(self.n))
        collection_size = ceil(self.c * m)

        mapping_length = num_collections * collection_size
        mapping = []

        for i in range(num_collections):

            collection = [] # List of lists, each of which is a time slot      
            for j in range(collection_size):
                collection.append([])

            for node in range(self.n):
                index = math.floor(random.uniform(0, collection_size))
                collection[index].append(node + 1)

            for slot in collection:
                if len(slot) > 0: 
                    mapping.append(slot)

        return mapping

    def concatenate(self, mapping, num_copies):
        for i in range(num_copies):
            self.schedule.extend(mapping)
            if PHASE_DELIMITERS:
                self.schedule.append(["*" for i in range(20)])

    """
                [1,n]: z_{v}
             [n+1,2n]: x_{v}
             [2n+1,\infty): AUX

    var_data is a tuple with first entry one of 'z', 'x'.
    The next entry is the node it corresponds to.
    Returns the integer mapped to that.
    """
    def get_var_num(self, var_data):
        if var_data[0] == "z":
            return var_data[1]
        elif var_data[0] == "x":
            return self.n + var_data[1]
        else:
            return "INVALID"
    def get_var_name(self, var_num):
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

    def selection_constraints(self, mapping, solver, formula):

        for v in range(1, self.n+1):
            zv,xv = self.get_var_num(("z",v)), self.get_var_num(("x",v))

            for i in range(len(mapping)):
                v_in_slot_i = False

                clause_v_i = [zv, NOT * xv] # Left out the NOT * v_in_slot_i
                for x_num_raw in mapping[i]:
                    if x_num_raw != v:
                        x_not_v = self.get_var_num(["x", x_num_raw])
                        clause_v_i.append(x_not_v)
                    else:
                        v_in_slot_i = True

                if v_in_slot_i == True: # If v isn't in Si, the clause is trivially true
                    solver.add_clause(clause_v_i)
                    formula.append(clause_v_i)

    def card_constraints(self, mapping, m, solver, formula):
        # \sum x_{v} = m
        xv_m = CardEnc.equals(lits=list(range(self.n+1, 2*self.n+1)), 
                  bound=m, top_id = 2*self.n + 1, encoding=EncType.mtotalizer)
        greatest_id = -1
        for clause in xv_m:
            solver.add_clause(clause)
            formula.append(clause)
            for num in clause:
                if abs(num) > greatest_id:
                    greatest_id = abs(num)

        # \sum z_{v} < ceil(m/2)
        zv_m2 = CardEnc.atmost(lits=list(range(1, self.n+1)), 
                  bound=ceil(m/2)-1, top_id = greatest_id + 1, encoding=EncType.mtotalizer)
        for clause in zv_m2:
            solver.add_clause(clause)
            formula.append(clause)

    # Returns whether the passed mapping is 1/2-good for subset size m
    def is_valid(self, mapping, m):

        good_vals = []
        ind = 1
        EPS = .0001

        new_good_val = ceil( m/2 + m/(2*ind) - EPS )
        while new_good_val > ceil(m/2) + 1:
            if len(good_vals) == 0 or new_good_val != good_vals[len(good_vals) - 1]:
                good_vals.append(new_good_val)
            ind += 1
            new_good_val = ceil(m/2 + m/(2*ind) - EPS)
        good_vals.append(ceil(m/2) + 1)

        if DEBUG_PRINT:
            print("Mapping 1/2-good for ", good_vals, end = ' ', flush = True)
        
        # Logarithmically iterate over same mapping checking *reducible* 1/2-goodness
        for good_val in good_vals:                 

            # Initialize model
            model = Cadical(use_timer = True)
            formula = [] # Not integral to calculation, just for display

            # Add constraints to model
            self.selection_constraints(mapping, model, formula)
            self.card_constraints(mapping, good_val, model, formula)

            # Solve model (determine is this mapping 1/2-good for subset size good_val)
            try:
                sat = model.solve()
            except Exception as err:
                print("\n\n\nException occurred during the pysat solver's operation")
                print(f"Unexpected {err=}, {type(err)=}")

            if sat: # Invalid mapping

                if DEBUG_PRINT:
                    print('\r', end = '')
                    print(' '*100, end = '')
                    print('\033[F', end = '', flush = True)

                return False
            else:   # Valid mapping
                model.delete()

            if DEBUG_PRINT:
                print(".", end = '', flush = True)

        if DEBUG_PRINT:
            print()

        return True

    def print(self):
        for slot in self.schedule:
            print(slot)



mapping = Schedule(param_n, param_f, 2, 2)
mapping.generate_schedule()
print(mapping.length)
mapping.print()
