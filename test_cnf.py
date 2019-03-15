from cdcl import *
import os

testFolder = 'test-data'
total = 0
success = 0
for file in os.listdir(testFolder):
    total += 1
    # Benchmark
    isSatisfiable = 'yes' in file
    
    filepath = os.path.join(testFolder, file)
    result = run(filepath)
    if isSatisfiable == result:
        success += 1
    
print("Success Rate: ", success / total * 100, "%")
