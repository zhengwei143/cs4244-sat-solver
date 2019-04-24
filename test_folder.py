from cdcl import *
import os

# testFolder = 'test-data'
# testFolder = 'test-small' # Taking forever
testFolder = 'uf50-218' # Seems to be correct
total = 0
total_branches = 0
success = 0
total_time = 0
for file in os.listdir(testFolder):
    if '.cnf' not in file:
        continue

# if '100' in file or '200' in file:
#        continue

    # Benchmark
    # isSatisfiable = 'yes' in file
    print(file)
    isSatisfiable = 'uuf' not in file
    
    filepath = os.path.join(testFolder, file)
    result, assignment_list, branching_count, time_elapsed = run(filepath)

    if branching_count:
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
