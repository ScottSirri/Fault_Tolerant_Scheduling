from statistics import median
from random import sample
import heapq

class Node:

    def __init__(self, vector=None, vector_index=None, data_indices=None):
        self.vector = vector
        self.vector_index = vector_index
        self.radius = -1
        self.inside_child = None
        self.outside_child = None
        self.data_indices = data_indices

    def print_node(self, level=0):
        spaces = '\t'*level
        print(f"{spaces}{self} contains {self.data_indices}")

    def __str__(self):
        inside  = 'yes' if self.inside_child  != None else 'no'
        outside = 'yes' if self.outside_child != None else 'no'
        return f"[node row {self.vector_index} radius {self.radius} inside {inside} outside {outside}]" 

class VPTree:

    def __init__(self):
        self.root = None

    def __init__(self, matrix):
        self.nodes = []
        root_ind = sample(range(len(matrix)), 1)[0]
        data_indices = list(range(len(matrix)))
        data_indices.remove(root_ind)
        self.root = Node(matrix[root_ind], root_ind, data_indices)
        self.populate_node(matrix, self.root)

    # TODO : Beware returning the query itself in the results
    def k_nn(self, k, query): 
        print(f"k_nn received k={k}, query={query}")
        if type(query) == Node:
            ret = self.k_nn_helper(k, query, self.root)
            print(f"k_nn returning length {len(ret)}")
            return ret
        elif type(query) == int:
            for i in range(len(self.nodes)):
                node = self.nodes[i]
                if query == node.vector_index:
                    print(node)
                    
                    ret = self.k_nn_helper(k, node, self.root)
                    print(f"k_nn return length {len(ret)}")
                    return ret

    def k_nn_helper(self, k, query, current_node, results=[]):

        if current_node == None:
            return results

        self.update_results(query, k, results, current_node)

        if current_node.radius == 0: # Reached a leaf of the VP tree
            return results

        d = VPTree.hamming(current_node.vector, query.vector)
        
        if d <= current_node.radius: # Query inside current_node's radius

            results = self.k_nn_helper(k, query, current_node.inside_child, results)
            _,farthest_dist = self.farthest_node(query, results)

            # For when you don't find enough nodes or it might be missing closer nodes from the other subtree
            if len(results) < k or farthest_dist > current_node.radius - d:
                results = self.k_nn_helper(k, query, current_node.outside_child, results)

        elif d > current_node.radius: # Query outside current_node's radius

            results = self.k_nn_helper(k, query, current_node.outside_child, results)
            _,farthest_dist = self.farthest_node(query, results)

            # For when you don't find enough nodes or it might be missing closer nodes from the other subtree
            if len(results) < k or farthest_dist > current_node.radius - d:
                results = self.k_nn_helper(k, query, current_node.inside_child, results)

        return results

    def update_results(self, query, k, nodes_list, new_node):

        #print(f"Updating {nodes_list} with {new_node}")
        if query.vector_index == new_node.vector_index:
            return

        if len(nodes_list) < k:
            nodes_list.append(new_node)
            return
        
        new_dist = VPTree.hamming(query.vector, new_node.vector)
        far_node,far_dist = self.farthest_node(query, nodes_list)

        if new_dist < far_dist: # Replace farthest node if new_node is closer to query
            nodes_list.remove(far_node)
            nodes_list.append(new_node)
            return


    def farthest_node(self, query, nodes_list):

        if len(nodes_list) == 0:
            print("farthest_node got an empty nodes_list")
            return

        farthest = None
        farthest_dist = 999999999

        for node in nodes_list:
            dist = VPTree.hamming(query.vector, node.vector)
            if dist < farthest_dist:
                farthest = node
                farthest_dist = dist

        return [farthest, farthest_dist]


    # Recursive function to populate a node and its subtrees.
    # The passed node must have its vector, vector_index, and data_indices initialized already!
    def populate_node(self, matrix, node):

        self.nodes.append(node)

        if len(node.data_indices) == 0:
            node.radius = 0
            node.inside_child, node.outside_child = None, None
            return

        node.radius = self.calculate_median_dist(matrix, node.vector_index, node.data_indices)
        inside, outside = self.partition_data(matrix, node) # Lists of indices of nodes in each subtree

        #print(f"Node {node.vector_index}, data_indices {node.data_indices}")
        #print(f"inside: {inside}")
        #print(f"outside: {outside}\n")

        if len(inside) > 0:
            inside_child_ind = sample(inside, 1)[0]
            inside.remove(inside_child_ind)
            node.inside_child = Node(matrix[inside_child_ind], inside_child_ind, inside)
            self.populate_node(matrix, node.inside_child)
        else:
            node.inside_child = None

        if len(outside) > 0:
            outside_child_ind = sample(outside, 1)[0]
            outside.remove(outside_child_ind)
            node.outside_child = Node(matrix[outside_child_ind], outside_child_ind, outside)
            self.populate_node(matrix, node.outside_child)
        else:
            node.outside_child = None


    # Return the data_indices of vp partitioned according to its radius, i.e., inside vs outside its radius
    def partition_data(self, matrix, vp):

        inside, outside = [], []
        
        for i in range(len(vp.data_indices)):
            vector_index = vp.data_indices[i]
            if VPTree.hamming(vp.vector, matrix[vector_index]) <= vp.radius:
                inside.append(vector_index)
            else:
                outside.append(vector_index)

        return inside, outside

    # Returns the median Hamming distance from the vector at vp_index in matrix to each
    # of the vectors with their index in data_indices; doesn't include distance of 0 to self
    def calculate_median_dist(self, matrix, vp_index, data_indices):
        dists = []
        for i in range(len(data_indices)):
            row_index = data_indices[i]
            if row_index != vp_index:
                dist = VPTree.hamming(matrix[row_index], matrix[vp_index])
                dists.append(dist)
        return median(dists)

    def hamming(v1, v2):
        assert len(v1) == len(v2)
        dist = 0
        for i in range(len(v1)):
            if v1[i] != v2[i]:
                dist += 1
        return dist

    def print_vptree(self):
        self.print_vptree_helper(self.root, 0)

    def print_vptree_helper(self, node, level):
        spaces = '\t' * (level+1)
        node.print_node(level)
        if node.inside_child != None:
            print(f"{spaces}INSIDE OF {node.vector_index}:")
            self.print_vptree_helper(node.inside_child, level + 1)
        if node.outside_child != None:
            print(f"{spaces}OUTSIDE OF {node.vector_index}:")
            self.print_vptree_helper(node.outside_child, level + 1)
        
        



