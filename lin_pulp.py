from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable

from ortools.sat.python import cp_model

model = LpProblem(name="small-problem", sense=LpMaximize)

x = LpVariable(name="x", lowBound=0, cat = "Integer")
y = LpVariable(name="y", lowBound=0)

model += (2 * x + y <= 20, "red_constraint")
model += (4 * x - 5 * y >= -10, "blue_constraint")
model += (-x + 2 * y >= -2, "yellow_constraint")
model += (-x + 5 * y == 15, "green_constraint")

# Objective function
model += lpSum([x, 2*y])

print(model)
status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")

print(f"objective: {model.objective.value()}")

for var in model.variables():
    print(f"{var.name}: {var.value()}")

print("Success")
