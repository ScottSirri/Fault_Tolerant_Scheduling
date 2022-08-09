from scipy.optimize import linprog

VALID = 0
INVALID = -1

class Selector:
   n = -1
   family = []

   def validate():
       if n <= 0:
           return INVALID
       for set in family:
           if type(set) is not list:
               return INVALID
           for i in set:
               if i > n:
                   return INVALID
        return VALID

obj = [-1, -2]

lhs_ineq = [[ 2,  1],
            [-4,  5],
            [ 1, -2]]
rhs_ineq = [20,
            10,
             2]

lhs_eq = [[-1, 5]]
rhs_eq = [15]

bnd = [(0, float("inf")),
       (0, float("inf"))]

opt = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq,
              A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd,
              method="highs")

opt
print(opt)

print("Success")
