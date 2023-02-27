from pysat.solvers import Glucose3, Cadical
from pysat.card import *
import math, random, time
import sys, os
import csv, signal
from datetime import datetime

VALID = 0
INVALID = -1

NOT = -1

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

if len(sys.argv) > 1:
    if sys.argv[1] == 'log':
        logging_data = True

if logging_data:
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
    filename = './data/sched_' + date_time_str

    f = open(filename, 'w')
    writer = csv.writer(f)
    header = ['c', 'd', 'n', 'f', 'time', 'sched_len']
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

        # Identity mapping
        for i in range(n):
            schedule.append([i+1])

        # Phase i
        for i in range(ceil(math.log(self.f, 2) + 1)):
            
            num_mappings = ceil(2 * (1 + 2**(i+1))) # \alpha = 1/2
            valid = False

            while not valid: # Generate until valid mapping obtained
                m = self.f / (2**i)
                mapping = self.generate_mapping(m)
                if self.is_valid(mapping, m)[0]:
                    valid = True

            self.concatenate(mapping, num_mappings)
        self.length = len(self.schedule)

    # Generates the smaller 1/2-good mappings
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

    """
                [1,n]: z_{v}
             [n+1,2n]: x_{v}
             [2n+1,\infty): AUX

    var_data is a tuple with first entry one of 'z', 'x'.
    The next entry is the node it corresponds to.
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

    def selection_constraints(mapping, solver, formula):

        for v in range(1, n+1):
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

    def card_constraints(mapping, m, solver, formula):
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

        timer = My_Timer()
        timer.start_timer()

        good_vals = []
        ind = 1
        EPS = .0001

        new_good_val = math.ceil( m/2 + m/(2*ind) - EPS )
        while new_good_val > math.ceil(m/2) + 1:
            if len(good_vals) == 0 or new_good_val != good_vals[len(good_vals) - 1]:
                good_vals.append(new_k_val)
            ind += 1
            new_good_val = math.ceil(m/2 + m/(2*ind) - EPS)
        good_vals.append(ceil(m/2) + 1)
        
        # Logarithmically iterate over same mapping checking *reducible* 1/2-goodness
        for good_val in good_vals:                 

            # Initialize model
            model = Cadical(use_timer = True)
            formula = [] # Not integral to calculation, just for display

            # Add constraints to model
            selection_constraints(mapping, model, formula)
            card_constraints(mapping, good_val, model, formula)

            # Solve model (determine is this mapping 1/2-good for subset size good_val)
            try:
                sat = model.solve()
            except Exception as err:
                print("\n\n\nException occurred during the pysat solver's operation")
                print(f"Unexpected {err=}, {type(err)=}")

            if sat: # Invalid mapping
                timer.stop_timer()
                return (False, timer.get_time())
            else:   # Valid mapping
                model.delete()

        timer.stop_timer()
        return (True, timer.get_time())


mapping = Schedule(100, 10, 4, 4)
mapping.generate_schedule()
print(mapping.length)
print(mapping.schedule)
