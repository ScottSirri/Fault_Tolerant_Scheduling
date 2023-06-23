from random import random, sample
from math import ceil, floor, log
from heapq import *
from functools import total_ordering
from itertools import combinations
from scratch import expected_collisions, expected_distinct_cfs
#import numpy as np
#from sklearn.neighbors import NearestNeighbors

ERR = -1

@total_ordering
class Wrapper:
    def __init__(self, val):
        self.val = val
  
    def __lt__(self, other):
        return self.val > other.val
  
    def __eq__(self, other):
        return self.val == other.val

def sort_first(val):
    return val[0]

class Matrix:
    def __init__(self, matrix, num_moves):
        self.matrix = matrix
        self.width = len(matrix[0])
        self.height = len(matrix)
        self.m = ceil(self.height / 2)
        self.num_moves = num_moves
        self.invalid_rows = None

    def __init__(self):
        self.matrix = None
        self.width = -1
        self.height = -1
        self.m = -1
        self.num_moves = -1
        self.invalid_rows = None

    def sort_rows(self):
        arr = []
        for row in self.matrix:
            num = 0
            for i in range(len(row)):
                if row[i] == 1:
                    num += 2**(len(row) - i - 1)
            #print(f"row has val {num}")
            arr.append([num, row]) # TODO: can make this faster, don't need to store whole row

        arr.sort(key=sort_first, reverse=True)

        if invalid_rows != None:
            for i in range(len(self.invalid_rows)): # TODO
                for j in range(len(arr)):
                    if self.matrix[self.invalid_rows[i]-1] == arr[j][1]:
                        print(f"invalid row {self.invalid_rows[i]} -> {j+1}")
                        print(f"\tself.matrix[self.invalid_rows[i]-1]")
                        self.invalid_rows[i] = j + 1
                        break

        for i in range(len(arr)):
            self.matrix[i] = arr[i][1]

    def num_cfs(self, subset):
        cfs = [0] * self.width
        for node in subset:
            for j in range(self.width):
                cfs[j] += self.matrix[node.vector_index][j]
        num_cfs = 0
        for i in cfs:
            if i == 1:
                num_cfs += 1
        return num_cfs


    def to_matrix(self, sel, subset=None):
        if subset != None:
            self.invalid_rows = subset
        family = sel.family
        self.matrix = []
        for i in range(sel.n):
            self.matrix.append([])

        for i in range(len(family)):
            slot = family[i]
            for j in range(sel.n):
                if (j+1) in slot:
                    self.matrix[j].append(1)
                else:
                    self.matrix[j].append(0)
        self.width = len(family)
        self.height = sel.n
        self.num_moves = 200000
        self.ones_per_row = sel.n*ceil(sel.d*log(sel.n))

    def swap_rows(self, inds):
        ind1 = inds[0]
        ind2 = inds[1]
        if ind1 < 0 or ind2 < 0 or ind1 >= self.height or ind2 >= self.height:
            return ERR
        if ind1 == ind2:
            return
        temp = self.matrix[ind1]
        self.matrix[ind1] = self.matrix[ind2]
        self.matrix[ind2] = temp

    def swap_cols(self, inds):
        ind1 = inds[0]
        ind2 = inds[1]
        if ind1 < 0 or ind2 < 0 or ind1 >= self.width or ind2 >= self.width:
            return ERR
        if ind1 == ind2:
            return
        for i in range(self.height):
            temp = self.matrix[i][ind1]
            self.matrix[i][ind1] = self.matrix[i][ind2]
            self.matrix[i][ind2] = temp

    def print_matrix(self, matrix):
        for i in range(len(matrix)):
            row = matrix[i]
            print(row,end='')
            if self.invalid_rows != None and i+1 in self.invalid_rows: 
                print(" !!!!",end='')
            print()
        print()

    def print(self):
        self.print_matrix(self.matrix)

    def dist(self, v1, v2):
        d = 0
        for i in range(len(v1)):
            if v1[i] != v2[i]:
                d += 1
        return d

    def update(self, neighbors, query_row, new_vec_row):
        farthest = None
        farthest_d = -1

        for i in range(len(neighbors)):
            d = self.dist(self.matrix[neighbors[i]], self.matrix[query_row]) 
            if d > farthest_d:
                farthest = neighbors[i]
                farthest_d = d

        new_d = self.dist(self.matrix[new_vec_row], self.matrix[query_row]) 
        if new_d < farthest_d:
            neighbors.remove(farthest)
            neighbors.append(new_vec_row)

        return farthest

    # TODO : This is somehow bugged, but it's not important
    def k_nn_brute_force(self, query_row, k):

        neighbors = []

        for i in range(len(self.matrix)):

            if query_row == i:
                continue

            if len(neighbors) < k:
                neighbors.append(i)
                continue

            self.update(neighbors, query_row, i)

        return neighbors

            


    def find_subsets(self, n, k):
        s = range(1, n+1, 1)
        return list(combinations(s, k))

    def subdivide_matrix(self):
        
        num_matrices = ceil(log(self.width, 2))
        matrices = []

        for i in range(num_matrices):
            matrices.append([])
            for j in range(self.height):
                matrices[len(matrices) - 1].append([])
        
        for i in range(num_matrices):
            num_divs = 2**(i+1)
            div_len = ceil(self.width / num_divs)
            print(f"i={i}, num_divs = {num_divs}, div_len = {div_len}, length = {self.width}")
            
            for row_ind in range(self.height):    
                row = self.matrix[row_ind]
                div_sum = 0

                for col_ind in range(self.width):
                    # TODO : There exists the possibility for the last bucket to be very small, depending on the width and 
                    # div_len. Adjust so that each bucket has size off by at most 1 from each other at that matrix level
                    if (col_ind > 0 and col_ind % div_len == 0) or col_ind == len(row) - 1:
                        matrices[i][row_ind].append(div_sum)
                        div_sum = 0
                    div_sum += row[col_ind]

            self.print_matrix(matrices[i])

        return matrices

    def heuristic(self, row_set, matrix_level):

        mat = self.matrices[matrix_level]
        div_len = ceil(self.width / (2**(matrix_level+1)))

        if div_len == 1:

            #print(f"\tChecking {row_set}: ",end='')
            cfs = [] # Which messages have already gotten a collision-free slot
            assert matrix_level == len(self.matrices) - 1

            for col in range(len(mat[0])):
                msgs_in_slot = []
                for i in range(len(row_set)):
                    row = row_set[i] - 1 # Not stored as zero-indexed
                    if mat[row][col] == 1:
                        msgs_in_slot.append(row)
                if len(msgs_in_slot) == 1 and msgs_in_slot[0] not in cfs:
                    #print(f"col{col} ",end='')
                    cfs.append(msgs_in_slot[0])
            #print()
            return len(cfs)
        else:
            assert matrix_level < len(self.matrices) - 1

        exp_cfs = 0
        for col in range(len(mat[0])):
            ball_sets_sizes = []
            for i in range(len(row_set)):
                ball_sets_sizes.append(mat[row_set[i]-1][col])
            exp_cfs += expected_distinct_cfs(div_len, ball_sets_sizes, 50)
        return exp_cfs

    def check(self):
        
        self.matrices = self.subdivide_matrix()
        row_set_size = self.m
        heap = []
        #max_heap_wrapper = list(map(lambda item: Wrapper(item), heap))

        row_sets_to_check = self.find_subsets(self.height, row_set_size)

        print(" ==================== init heuristics =========================")
        pruned_ctr = 0
        for row_set in row_sets_to_check:
            # The 0 argument indicates it is being checked at the coarsest matrix level (big buckets)
            init_heuristic = self.heuristic(row_set, 0)
            actual = self.heuristic(row_set, len(self.matrices) - 1) # TODO : ERASE, FOR DEBUGGING
            #print(f"{row_set} gets {init_heuristic} when actual is {actual}")
            #heappush(max_heap_wrapper, (init_heuristic, row_set, 0, [init_heuristic]))
            heappush(heap, (init_heuristic, row_set, 0, [init_heuristic]))

        print(" ==================== loop heuristics =========================")
        #print(f"min = {len(heap)}, max = {len(max_heap_wrapper)}")
        #print(f"heap size = {len(heap)}")
        #while len(max_heap_wrapper) > 0:
        while len(heap) > 0:
            #old_heuristic, row_set, matrix_level, heurs = heappop(max_heap_wrapper)
            old_heuristic, row_set, matrix_level, heurs = heappop(heap)
            matrix_level += 1
            new_heuristic = self.heuristic(row_set, matrix_level)
            heurs.append(new_heuristic)
            actual = self.heuristic(row_set, len(self.matrices) - 1) # TODO : ERASE, FOR DEBUGGING
            #print(f"{row_set} went from {old_heuristic} -> {new_heuristic} when actual is {actual}")

            if matrix_level == len(self.matrices) - 1:
                if new_heuristic < ceil(self.m/2):
                    print(f"\n\nFound a winner. Greatest heuristic at finest level is {new_heuristic}: rows {row_set}, heurs {heurs}")
                    for row in row_set:
                        for mat in self.matrices:
                            print(f"{mat[row-1]} -> ", end='')
                        print()
                    return
            else:   
                #heappush(max_heap_wrapper, (new_heuristic, row_set, matrix_level, heurs))
                heappush(heap, (new_heuristic, row_set, matrix_level, heurs))


    """
    def k_nn(self):
        neigh = NearestNeighbors(n_neighbors=8, metric=hamming)
        print(neigh.fit(self.matrix))
        print(neigh.kneighbors([self.matrix[0]], 8, return_distance=True))
    """

    def shuffle_and_print(self):
        for ctr in range(self.num_moves):
            if random() < .5: # Swap cols
                inds = sample(range(self.width), 2)
                self.swap_cols(inds)
            else: # Swap rows
                inds = sample(range(self.height), 2)
                self.swap_rows(inds)
            if self.check():
                self.print()
                return
        print("Did a lot of shuffling, nothing...")
    """
    def to_selector(self):
        family = []
        for c in range(self.width):
            col = []
            for r in range(self.height):
                col.append(self.matrix[r][c])
            family.append(col)
        return family
    """
