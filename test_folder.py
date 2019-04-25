from cdcl import *
import os

# testFolder = 'uf20' # SAT
# testFolder = 'uf50' # SAT
testFolder = 'uuf50' # UNSAT
# testFolder = 'uf75' # SAT
# testFolder = 'uuf75' # UNSAT

total = 0
total_branches = 0
success = 0
total_time = 0
for file in os.listdir(testFolder):
    if '.cnf' not in file:
        continue

    print(file)
    # Benchmark
    isSatisfiable = 'uuf' not in file
    
    filepath = os.path.join(testFolder, file)
    result, assignment_list, branching_count, time_elapsed = run(filepath)

    total_branches += branching_count
    total += 1
    total_time += time_elapsed
    if isSatisfiable == result:
        print("success! " + filepath + ", Answer is: ", isSatisfiable, "and got: ", result)
        success += 1
    else:
        print("Supposed to be: ", isSatisfiable, "but got: ", result)
    
print("Success Rate: ", success, "/", total)
print("Average Branching Count: ", (total_branches / total))
print("Total time elapsed: ", total_time)
