import math, time, random, itertools, scipy, sys

left = []
left_subsets = []

n = 20
m = 10
d = int(math.log(n))
sample_number = 5
num_valid = 0

#test = ['a', 'b', 'c', 'd', 'e', 'f']
#print(list(itertools.combinations(test, 3)))

if len(sys.argv) == 4:
    n = int(sys.argv[1])
    m = int(sys.argv[2])
    sample_number = int(sys.argv[3])
elif len(sys.argv) != 1:
    print("Usage:")
    print("\tdisperser.py n m sample_number")
    quit()

print("n = " + str(n))
print("m = " + str(m))
print("d = " + str(d))

print("Forewarning: Number left-hand subsets is " + str(scipy.special.binom(n, math.ceil(m/2))) + " for EACH")
print("Approximate average time per iteration is " + str(scipy.special.binom(n, math.ceil(m/2)) / 523000))

def generate_new_graph():
    global left
    global left_subsets

    left = []
    for i in range(n):
        vert = random.sample(range(1,m), d)
        left.append(vert)
    left_subsets = list(itertools.combinations(range(1, n), math.ceil(m/2)))

def print_graph():
    for i in range(n):
        print(str(i + 1) + ":\t", end = "")
        for j in range(m):
            if j in left[i]:
                print("1", end = " ")
            else:
                print("0", end = " ")
        print()


def evaluate_left_subsets():
    global left
    global left_subsets
    global num_valid
    assert len(left_subsets) > 0

    invalid = False

    for left_subset in left_subsets:
        assert len(left_subsets) > 0

        neighborhood = set()
        for left_vert in left_subset:
            neighborhood.update(left[left_vert - 1])
        if len(neighborhood) < math.ceil(m/4):
            print("Not a disperser, left-subset w neighborhood of size " + str(len(neighborhood)))
            print("Left subset vertex numbers: ", end = "")
            for left_vert in left_subset:
                print(left_vert, end = ", ")
            print()
            print("Neighborhood: ", end = "")
            print(neighborhood)
            print_graph()
            invalid = True
            break
    if invalid == False:
        print("Yes, it's a disperser!")
        num_valid += 1

# ================ MAIN =================

for i in range(sample_number):
    start_time = time.perf_counter()
    print(" ========================= iteration " + str(i) + " ========================= ")
    generate_new_graph()
    #print_graph()
    evaluate_left_subsets()
    end_time = time.perf_counter()
    print("Iteration time: %02fs" % (end_time - start_time))

print("Num valid: %d/%d = %d%%" % (num_valid, sample_number, math.floor(100.0 * num_valid / sample_number)))

    
