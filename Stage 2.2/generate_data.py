import os
import pycosat

kFolder = '4'
output_path = 'data/' + kFolder + '/data_points.txt'
output_file = open(output_path, 'w+')

total = 0
num_SAT = 0

COMMENT = 'c'
INFO = 'p'

folder_paths = [f for f in os.listdir(kFolder) if not f.startswith('.')]
sorted_folder_paths = sorted(folder_paths, key=float)

for folder in sorted_folder_paths:
    for file in os.listdir(os.path.join(kFolder,folder)):
        filepath = os.path.join(kFolder, folder, file)
        if '.cnf' not in filepath:
            continue
        print(filepath)
        f = open(filepath, 'r')
        cnf = []
        for line in f.readlines():
            line = line.strip()
            if not line or COMMENT == line[0] or INFO == line[0]:
                continue
            literal_strings = line.split()[:-1]
            literal_strings = list(map(lambda x: int(x), literal_strings))
            if len(literal_strings) == 0:
                continue
            cnf.append(literal_strings)
        result = pycosat.solve(cnf)
        if type(result) is list:
            num_SAT += 1
        total += 1
    output_file.write(folder + "," + str(float(num_SAT/total)) + '\n')

output_file.close()
