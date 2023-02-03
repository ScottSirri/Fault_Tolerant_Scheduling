import math

def not_cons(array):
    for i in range(len(array)):
        if i < len(array) - 1 and array[i] != array[i+1] - 1:
            print(i, arr[i])
            return True
    return False


m = 233

base = math.floor(m/2)
upper = math.ceil(math.log(1/m, 1/2))

half_factor = math.ceil(math.pow(.5, upper)*m)
next_half_factor = half_factor

arr = []

for i in range(upper, 0, -1):
    print(f"ceil(.5^{i}*{m}) = {half_factor}")

    half_factor = next_half_factor
    next_half_factor = math.ceil(math.pow(.5, i-1)*m)

    eps_upper = half_factor
    if next_half_factor % 2 == 1:
        eps_upper -= 1
    
    for eps in range(0, eps_upper):
        val = base + math.ceil(math.pow(.5, i)*m) + eps
        print(f"({i}, {eps}): {base} + .5^{i}*{m} + {eps} = {val}")
        arr.append(val)

if not_cons(arr):
    print("=================INVALID===================")
    print(arr)

"""
decrement_next_eps_upper = False

for i in range(1, math.ceil(math.log(1/m, 1/2)) + 1):

    half_factor = math.ceil(math.pow(.5,i)*m)
    eps_upper = half_factor
    if decrement_next_eps_upper == True:
        eps_upper -= 1

    print(f"ceil(.5^{i}*{m}) = {half_factor}")

    if half_factor % 2 == 1:
        decrement_next_eps_upper = True
    else:
        decrement_next_eps_upper = False

    for eps in range(0, eps_upper):
        print(f"({i}, {eps}): {base} + .5^{i}*{m} + {eps} = {base + math.ceil(math.pow(.5, i)*m) + eps}")
"""
