from cdcl import *
import sys

filename = sys.argv[1]
result = run(filename)
print("Result of: ", filename)
if result:
    print("SAT")
else:
    print("UNSAT")

