from cdcl import *
import sys

filename = sys.argv[1]
result = run(filename)
print("Result of: ", filename)
if result[0]:
    print("SAT")
else:
    print("UNSAT")

