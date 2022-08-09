from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable

model = LpProblem(name="small-problem", sense=LpMinimize)

x = LpVariable(name="x", lowBound=0)
y = LpVariable(name="y", lowBound=0)

expression = 2 * x + 4 * y
type(expression)

print("Success")
