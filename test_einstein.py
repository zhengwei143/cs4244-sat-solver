from cdcl import run
import sys
import json

filepath = sys.argv[1]
output_path = sys.argv[2]
ref_path = "reference.txt"

result, assignment_list, branching_count, time_elapsed = run(filepath)

res_file = open(output_path, "w+")
true_vals = {}
if assignment_list:
    for key,value in assignment_list.items():
        if value:
            true_vals[key] = value

ref_file = open(ref_path, "r")
references = {}
for line in ref_file:
    entry = line.split()
    var = entry[0][:-1]
    ref = entry[1]
    references[var] = ref

true_vars_to_ref = {}
for key in true_vals:
    true_vars_to_ref[key] = references[key]

for key,value in true_vars_to_ref.items():
    res_file.write("{}: {}\n".format(key, value))

res_file.close()

print("Satisfiability: ", result)
print("Assignment List: ", true_vals)
print("Branching count: ", branching_count)
print("Time elapsed: ", time_elapsed)
