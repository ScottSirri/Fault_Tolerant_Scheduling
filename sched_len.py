from math import ceil, log, sqrt

c = 2
d = 2
n = 500
f = ceil(sqrt(n))
#f = 32
sched_len = 0

num_phases = ceil(log(f,2)) + 1
for i in range(num_phases):
    mapping_len = ceil(c*f/(2**i)) * ceil(d*log(n,2))
    num_mappings = 2 + 2**(i+2)
    sched_len += (num_mappings * mapping_len)

naive_len = (f+1)*n

print(f"num_phases={num_phases}")
print(f"n={n}, f={f}, c={c}, d={d}")
print(f"      Schedule length: {sched_len}")
print(f"Naive schedule length: {naive_len}")
