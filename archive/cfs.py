import math

for m in [20, 50, 80, 133, 279]:

    print("m = %d" % m)

    for gamma in range(math.floor(m/2) + 1, m+1):
        temp = gamma - m/2
        i_gamma = math.ceil(math.log(temp / m, 1/2))
        eps_gamma = temp - math.pow(1/2, i_gamma)*m
        cfs = m/4 + max(eps_gamma, math.pow(1/2, i_gamma+1)*m - eps_gamma)
        print("gamma_candidate: %d = %.1f + (1/2)^(%d)m + %.2f: %.2f cfs" % (gamma, m/2, i_gamma, eps_gamma, cfs))

    print("1/2-good vals: ", end='')
    for j in range(1, math.ceil(math.log(1/m, 1/2)) + 1):
        print(f"{(math.floor(m/2) + math.ceil(m * math.pow(1/2, j)))}, ", end="")
    print()

