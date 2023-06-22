from statistics import median
from random import sample

class Node:
    """
    def __init__(self):
        self.vector = None
        self.vector_index = None
        self.radius = None
        self.inside_subtree = None
        self.outside_subtree = None
        self.data_indices = None
    """

    def __init__(self, vector=None, vector_index=None, data_indices=None):
        self.vector = vector
        self.vector_index = vector_index
        self.radius = -1
        self.inside_child = None
        self.outside_child = None
        self.data_indices = data_indices

    def print_node(self, level=None):
        if level != None:
            spaces = '\t'*level
        else:
            spaces = ''
        print(f"{spaces}Row {self.vector_index}: radius {self.radius} contains {self.data_indices}")

class VpTree:

    def __init__(self):
        self.root = None

    def __init__(self, matrix):
        root_ind = sample(range(len(matrix)), 1)[0]
        data_indices = list(range(len(matrix)))
        data_indices.remove(root_ind)
        self.root = Node(matrix[root_ind], root_ind, data_indices)
        self.populate_node(matrix, self.root)

    # Recursive function to populate a node and its subtrees.
    # The passed node must have its vector, vector_index, and data_indices initialized already!
    def populate_node(self, matrix, node):

        if len(node.data_indices) == 0:
            node.radius = 0
            node.inside_child, node.outside_child = None, None
            return

        node.radius = self.calculate_median_dist(matrix, node.vector_index, node.data_indices)
        inside, outside = self.partition_data(matrix, node)

        #print(f"Node {node.vector_index}, data_indices {node.data_indices}")
        #print(f"inside: {inside}")
        #print(f"outside: {outside}\n")

        if len(inside) > 0:
            inside_child_ind = sample(inside, 1)[0]
            inside.remove(inside_child_ind)
            node.inside_child = Node(matrix[inside_child_ind],  inside_child_ind,  inside)
            #print("populating inside...")
            self.populate_node(matrix, node.inside_child)
        else:
            node.inside_child = None
        #print("done with inside")


        if len(outside) > 0:
            outside_child_ind = sample(outside, 1)[0]
            outside.remove(outside_child_ind)
            node.outside_child = Node(matrix[outside_child_ind],  outside_child_ind,  outside)
            #print("populating outside...")
            self.populate_node(matrix, node.outside_child)
        else:
            node.outside_child = None
        #print("done with outside")


    # Return the data_indices of vp partitioned according to its radius
    def partition_data(self, matrix, vp):

        inside, outside = [], []
        
        for i in range(len(vp.data_indices)):
            vector_index = vp.data_indices[i]
            if self.hamming(vp.vector, matrix[vector_index]) <= vp.radius:
                inside.append(vector_index)
            else:
                outside.append(vector_index)

        return inside, outside

    # Returns the median Hamming distance from the vector at vp_index in matrix to 
    # each of the vectors with index in data_indices. Doesn't include distance of 0 to self
    def calculate_median_dist(self, matrix, vp_index, data_indices):
        dists = []
        for i in range(len(data_indices)):
            row_index = data_indices[i]
            if row_index != vp_index:
                dists.append(self.hamming(matrix[row_index], matrix[vp_index]))
        return median(dists)

    def hamming(self, v1, v2):
        assert len(v1) == len(v2)
        dist = 0
        for i in range(len(v1)):
            if v1[i] != v2[i]:
                dist += 1
        return dist

    def print_vptree(self):
        self.print_vptree_helper(self.root, 0)

    def print_vptree_helper(self, node, level):
        spaces = '\t' * level
        node.print_node(level)
        if node.inside_child != None:
            print(f"{spaces}INSIDE OF {node.vector_index}:")
            self.print_vptree_helper(node.inside_child, level + 1)
        if node.outside_child != None:
            print(f"{spaces}OUTSIDE OF {node.vector_index}:")
            self.print_vptree_helper(node.outside_child, level + 1)
        
        



