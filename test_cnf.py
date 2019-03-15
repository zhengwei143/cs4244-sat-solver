from cdcl import *
import os

testFolder = 'test-data'
total = 0
success = 0
numSat = 0
for file in os.listdir(testFolder):
    # Benchmark
    isSatisfiable = 'yes' in file
    #if not isSatisfiable:
    #    continue
    
    filepath = os.path.join(testFolder, file)
    result = run(filepath)
    total += 1
    if isSatisfiable == result:
        print("success!")
        success += 1
    else:
        print("Supposed to be: ", isSatisfiable, "but got: ", result)
    
print("numSat: ", numSat)
print("Success Rate: ", success, "/", total)
