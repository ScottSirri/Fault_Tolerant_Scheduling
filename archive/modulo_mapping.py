import math, random, time
from math import ceil, log, sqrt
import sys, os
import csv, signal
from datetime import datetime

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
    i = ceil(lower + .0001)
    if i % 2 == 0:
        i += 1
    while len(primes) < num_primes:
        if is_prime(i):
            primes.append(i)
        i += 2
    return primes

# Start logging data if indicated on command line
logging_data = False

if len(sys.argv) == 2:
    if sys.argv[1] == 'log':
        logging_data = True

if logging_data:
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
    filename = './sched_data/mod_' + date_time_str

    f = open(filename, 'w')
    writer = csv.writer(f)
    header = ['n', 'f', 'time', 'sched_len']
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
    def __init__(self, n_in, f_in):
        self.n = n_in
        self.f = f_in
        self.schedule = []
        self.length = 0

    # Generates the entire reducible 1/2-good schedule
    def generate_schedule(self):

        self.schedule.clear()
        self.length = 0

        sched_timer = My_Timer()
        sched_timer.start_timer()

        # Identity mapping
        for i in range(self.n):
            self.schedule.append([i+1])

        n = self.n
        f = self.f
        C = f * ceil(log(n,2) / log(f * log(n,2),2))
        #print(f"C={C}, f*log(n,2)={ceil(f*log(n,2)+.0001)}")

        # The first C prime numbers greater than f*log(n)
        primes = generate_primes(f * log(n,2), C)
        #print("primes: ", end='')
        #print(primes)

        # Phase i
        for i in range(C):

            for j in range(primes[i]):
                slot = []
                x = j
                # Add all ints in msg_ind (mod primes[i])
                while x < n:
                    slot.append(x)
                    x += primes[i]
                self.schedule.append(slot)

        # Full schedule has now been generated
        self.length = len(self.schedule)
        #print("modulo length ", int(self.length))
        #self.print_sched()

        sched_timer.stop_timer()
        duration = sched_timer.get_time()

        if DEBUG_PRINT:
            print("n=" + str(self.n), end='')
            print(" f=" + str(self.f), end='')
            print(" schedule_length=" + str(self.length), end='')
            print(" time=" + str(duration))
            print("\n")
        
        if logging_data: # Write data to file
            data_row = [self.n, self.f, duration, self.length]
            writer.writerow(data_row)

    def concatenate(self, mapping, num_copies=1):
        for i in range(num_copies):
            self.schedule.extend(mapping)

    def print_sched(self):
        print(f"Schedule (length {len(self.schedule)}):")
        for slot in self.schedule:
            print(slot)

n_vals = [10,20,30,40,50,60,70,80,90,100,200,300,400,500]
f_funcs = ['sqrt',2,4,8,16,32]

num_iters = 10

for i in range(num_iters):
    for f in f_funcs:
        for n_val in n_vals:
            if f == 'sqrt':
                f_in = ceil(math.sqrt(n_val))
            else:
                f_in = f

            mapping = Schedule(n_val, f_in)
            mapping.generate_schedule()
