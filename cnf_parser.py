from helpers import *

def parse_formula(formula):
    clauses = formula.split(AND)
    clauses = []
    variables = set()
    literalPositions = {}

    # Splits the string into clauses and parses each literal
    while formula:
        openIdx = formula.index(OPEN)
        closeIdx = formula.index(CLOSE)
        clauseString = formula[openIdx+1:closeIdx]
        literals = list(map(lambda x: x.strip(), clauseString.split(OR)))
        clauses.append(literals)
        for literal in literals:
            var = toVariable(literal)
            variables.add(var)

        formula = formula[closeIdx+1:]

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

