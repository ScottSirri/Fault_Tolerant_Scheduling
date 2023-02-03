from pysat.solvers import Glucose3
from pysat.card import *
g = Glucose3()
"""
g.add_clause([-1, 2])
g.add_clause([-2, 3])
print(g.solve())
print(g.get_model())
print("Success")
"""

l, u = 4, 8

cnf = CardEnc.atmost(lits=list(range(1,5)), bound=2, encoding=EncType.seqcounter)
print("Clauses:")
print(cnf.clauses)
for clause in cnf:
    g.add_clause(clause)
print("Solve:")
print(g.solve())
print("Model:")
print(g.get_model())
print("Success")
