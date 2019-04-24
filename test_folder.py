from cdcl import *
import os

# testFolder = 'test-data'
# testFolder = 'test-small' # Taking forever
testFolder = 'uf50' # Seems to be correct
total = 0
success = 0
numSat = 0
for file in os.listdir(testFolder):
    if '.cnf' not in file:
        continue

    if '100' in file or '200' in file:
        continue

    # Benchmark
    # isSatisfiable = 'yes' in file
    print(file)
    isSatisfiable = True
    
    filepath = os.path.join(testFolder, file)
    result, assignment_list = run(filepath)
    
    total += 1
    if isSatisfiable == result:
        print("success! " + filepath + ", Answer is: ", isSatisfiable, "and got: ", result)
        success += 1
    else:
        print("Supposed to be: ", isSatisfiable, "but got: ", result)
    
print("numSat: ", numSat)
print("Success Rate: ", success, "/", total)
