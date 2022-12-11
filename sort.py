
# Merge two sorted lists of integers into a larger sorted list
def merge(arr1, arr2):
    
    list_out = []
    ind1, ind2 = 0, 0
    
    while ind1 < len(arr1) or ind2 < len(arr2):
        # Reached the end of one of the lists
        if ind1 == len(arr1):
            while ind2 < len(arr2):
                list_out.append(arr2[ind2])
                ind2 += 1
            return list_out
        elif ind2 == len(arr2):
            while ind1 < len(arr1):
                list_out.append(arr1[ind1])
                ind1 += 1
            return list_out
        
        # Not at the end of either list
        if arr1[ind1] < arr2[ind2]:
            list_out.append(arr1[ind1])
            ind1 += 1
        else:
            list_out.append(arr2[ind2])
            ind2 += 1
            
    return list_out

# Perform merge sort on the passed list of integers
def merge_sort(arr):
    # Base case
    if len(arr) == 0 or len(arr) == 1:
        return arr

    mid   = int(len(arr)/2)
    left  = arr[:mid]
    right = arr[mid:]
    
    # Recurse
    left  = merge_sort(left)
    right = merge_sort(right)
    
    # Combine
    return merge(left, right)

# Return the value in one of these sorted arrays of integers
# that's not in the other.
def compare(arr1, arr2):
    
    shorter_arr = -1
    end = -1
    
    if len(arr1) < len(arr2):
        end = len(arr1)
        shorter_arr = 1
    else:
        end = len(arr2)
        shorter_arr = 2
    
    ind = 0
    while ind < end:
        if arr1[ind] != arr2[ind]:
            # The longer array has the extra value
            if shorter_arr == 1:
                return arr2[ind]
            else:
                return arr1[ind]
        ind += 1
    
    # The extra value is the last one
    if shorter_arr == 1:
        return arr2[len(arr2) - 1]
    else:
        return arr1[len(arr1) - 1]

def solution(x, y):

    print(x)
    print(y)

    x = merge_sort(x)
    y = merge_sort(y)

    print(x)
    print(y)

    return compare(x,y)

x = [4, 8, 3, 6, 0]
y = [3, 4, 0, 5, 6, 8]

print(solution(x, y))
