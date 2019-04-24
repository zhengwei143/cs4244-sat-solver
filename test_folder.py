from cdcl import *
import os

# testFolder = 'test-data'
testFolder = 'test-small' # Taking forever
# testFolder = 'uf50' # Seems to be correct
total = 0
success = 0
numSat = 0
for file in os.listdir(testFolder):
    # Benchmark
    isSatisfiable = 'yes' in file
    print(file)
    # isSatisfiable = True
    
    filepath = os.path.join(testFolder, file)
    result, assignment_list = run(filepath)
    
    total += 1
    if isSatisfiable == result:
        # if len(assigned_values) != 50:
            # print("ERROR NOT ENOUGH ASSIGNED VALUES")

        print("success! " + filepath + ", Answer is: ", isSatisfiable, "and got: ", result)
        success += 1
    else:
        print("Supposed to be: ", isSatisfiable, "but got: ", result)
    
print("numSat: ", numSat)
print("Success Rate: ", success, "/", total)
