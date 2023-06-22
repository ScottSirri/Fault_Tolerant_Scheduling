import random
import math

def distribute(m, x):
    bins = [[]]*m
    for num in x:
        which = random.sample(range(m), num)
        for each in which:
            bins[each].append(num)
    return bins

def count_collisions(bins):
    ctr = 0
    for slot in bins:
        if len(slot) > 1:
            ctr += 1
    return ctr

def count_distinct_cfs(bins):
    ctr = 0
    cfs = []
    for slot in bins:
        if len(slot) == 1 and slot[0] not in cfs:
            ctr += 1
            cfs.append(slot[0])
    return ctr

def expected_collisions(m, x, num_trials):
    sum_collisions = 0
    for i in range(num_trials):
        bins = distribute(m,x)
        sum_collisions += count_collisions(bins)
    avg_collisions = float(sum_collisions) / num_trials
    return avg_collisions

def expected_distinct_cfs(m, x, num_trials):
    sum_cfs = 0
    for i in range(num_trials):
        bins = distribute(m,x)
        sum_cfs += count_distinct_cfs(bins)
    avg_distinct_cfs = float(sum_cfs) / num_trials
    return avg_distinct_cfs
