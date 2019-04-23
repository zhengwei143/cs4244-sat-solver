from helpers import *

SPACE = ' '
COMMENT = 'c'
INFO = 'p'

def parse_cnf(filename):
    clauses = []
    variables = set()
    literalPositions = {}
    file = open(filename, 'r')

    for line in file.readlines():
        values = line.split(SPACE)
        if values[0] == COMMENT or values[0] == INFO:
            continue
        
        # Ignore the last value 0
        literals = list(map(lambda x: x.strip(), values[:-1]))
        if not literals:
            continue
        clauses.append(literals)
        for literal in literals:
            var = toVariable(literal)
            variables.add(var)

    # Assign each variable a bit position
    position = 0
    for variable in sorted(variables):
        literalPositions[variable] = position
        position += 1
        # Negations are kept one bit after its variable
        negatedVariable = negate(variable)
        literalPositions[negatedVariable] = position
        position += 1

    matrix = Matrix(clauses, literalPositions)

    return matrix

