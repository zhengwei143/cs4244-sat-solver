from cnf_parser import parse_formula, toVariable, negate

# decisionLevel -> variable assignment
previousAssignments = {}

def cdcl(matrix):
    result, resultantClauses = propagateUnitClauses(matrix)
    if not result: # Conflict
        return False

    while not allVariablesAssigned(matrix):
        variable, value = pickBranching(matrix)
        if variable is None:
            # This occurs when both assignments for the variable have been tried
            return False
        print((variable, value))
        matrix.assign(variable, value)

        result, resultantClauses = propagateUnitClauses(matrix)
        print((result, resultantClauses))
        if not result:
            (lowestDl, variableAssignments) = matrix.variableAssignmentsInvolved(resultantClauses)
            backtrackAndLearn(matrix, lowestDl, variableAssignments)

def propagateUnitClauses(matrix):
    # For each clause, whenever a unit clause successfully propagates that clause
    # Add all clauses that resulted in that unit clause
    clauseAffectedBy = {}
    for clause in matrix.clauses():
        clauseAffectedBy[clause] = set([clause])

    propagated = set()
    unitClauses = set(matrix.unitClauses())
    while len(unitClauses) > len(propagated):
        unpropagated = unitClauses.difference(propagated)
        unitClause = unpropagated.pop()
        for targetClause in matrix.clauses():
            if targetClause == unitClause:
                continue
            result, affectedByUnitClause = matrix.propagate(targetClause, unitClause)
            if not result: # Conflict
                # Clauses that lead to conflict
                resultantClauses = clauseAffectedBy[targetClause].union(clauseAffectedBy[unitClause])
                return (False, resultantClauses)
            if affectedByUnitClause:
                clauseAffectedBy[targetClause].update(clauseAffectedBy[unitClause])

        propagated.add(unitClause)
        unitClauses = set(matrix.unitClauses())
    return (True, None)

def allVariablesAssigned(matrix):
    return len(matrix.variables()) == len(matrix.dlVariableMapping)

def pickBranching(matrix):
    dl = matrix.decisionLevel + 1
    if dl in previousAssignments:
        if not previousAssignments[dl]:
            return (None, None)
        variable, parity = previousAssignments[dl]
        previousAssignments[dl] = False
        return (variable, not parity)

    # TODO: Use some heuristic for pickbranching here, currently just randomly picking and setting to True.
    variablesAssigned = list(map(lambda x: toVariable(x), matrix.dlVariableMapping.values()))
    diff = set(matrix.variables()).difference(set(variablesAssigned))
    variable = list(diff)[0]
    previousAssignments[dl] = (variable, True)
    return previousAssignments[dl]

def backtrackAndLearn(matrix, lowestDecisionLevel, variableAssignments):
    matrix.backtrack(lowestDecisionLevel - 1)
    for key in previousAssignments.keys():
        if key > lowestDecisionLevel:
            del previousAssignments[key]
    literals = list(map(lambda x: negate(x), variableAssignments))
    matrix.addClause(literals, 0)

formula = "(a) AND (~a OR b OR c) AND (~b) AND (~c)"
matrix = parse_formula(formula)

cdcl(matrix)
