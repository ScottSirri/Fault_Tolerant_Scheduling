from ortools.sat.python import cp_model

model = cp_model.CpModel()

num_vals = 999
x = model.NewIntVar(0, num_vals - 1, 'x')
y = model.NewIntVar(0, num_vals - 1, 'y')
z = model.NewIntVar(0, num_vals - 1, 'z')

model.Add(.2*x + y - z <= 20)
model.Add(4 * x - 5 * y >= -10)
model.Add(10*x + y > 0)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('x = %i' % solver.Value(x))
    print('y = %i' % solver.Value(y))
    print('z = %i' % solver.Value(z))
else:
    print('No solution found.')

print("Success")
