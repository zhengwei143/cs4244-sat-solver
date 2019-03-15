from cnf_parser import parse_cnf, toVariable, negate
from functools import reduce


def cdcl(matrix):
    # decisionLevel -> variable assignment
    previousAssignments = {}

    result, resultantClauses = propagateUnitClauses(matrix)
    if not result: # Conflict
        return False
    # print(matrix.literalPositions)
    while not allVariablesAssigned(matrix):
        variable, value, anyRemainingAssignments = pickBranching(matrix, previousAssignments)
        # print("assignments: ", previousAssignments)
        if variable is None:
            # This occurs when both assignments for the variable have been tried
            # print("UNSAT!")
            return False
        # print("Assigning: ", (variable, value))
        success, variableAssignments = matrix.assign(variable, value)
        if not success:
            backtrackAndLearn(matrix, matrix.decisionLevel, variableAssignments, previousAssignments)
            continue
        # print("After assignment: ", matrix.display())
        result, resultantClauses = propagateUnitClauses(matrix)
        # print("Result: ", (result, resultantClauses))
        if not result:
            (highestDl, variableAssignments) = matrix.variableAssignmentsInvolved(resultantClauses)
            backtrackAndLearn(matrix, highestDl, variableAssignments, previousAssignments)

    return True

def propagateUnitClauses(matrix):
    # For each clause, whenever a unit clause successfully propagates that clause
    # Add all clauses that resulted in that unit clause
    clauseAffectedBy = {}
    for clause in matrix.validClauses():
        clauseAffectedBy[clause] = set([clause])

    propagated = set()
    unitClauses = set(matrix.unitClauses())
    while len(unitClauses) > len(propagated):
        unpropagated = unitClauses.difference(propagated)
        unitClause = unpropagated.pop()
        # print("propagating unit clause: ", unitClause)
        for targetClause in matrix.validClauses():
            if targetClause == unitClause:
                continue
            # print("target: ", targetClause)
            valid, affectedByClause = matrix.propagate(targetClause, unitClause)
            # print("After propagate: ", matrix.display())
            # print("Propagate Result: ", (valid, affectedByClause))
            if affectedByClause is not None:
                clauseAffectedBy[targetClause].update(clauseAffectedBy[affectedByClause])
            if not valid: # Conflict
                # Return clauses that lead to conflict at target clause
                return (False, clauseAffectedBy[targetClause])

        propagated.add(unitClause)
        unitClauses = set(matrix.unitClauses())
    return (True, None)

def allVariablesAssigned(matrix):
    return len(matrix.dlVariableMapping) == len(matrix.variables())

def pickBranching(matrix, previousAssignments):
    dl = matrix.decisionLevel + 1
    
    # Picking a new assignment for a previously assigned
    if dl in previousAssignments:
        # Search for variable assignment that still has remaining assignments
        while dl >= 1 and not previousAssignments[dl][2]:
            dl -= 1
        if dl <= 0:
            return (None, None, None)
        variable, parity, anyRemainingAssignments = previousAssignments[dl]
        previousAssignments[dl] = (variable, not parity, not anyRemainingAssignments)
        return (variable, not parity, not anyRemainingAssignments)

    # TODO: Use some heuristic for pickbranching here, currently just randomly picking and setting to True.
    variablesAssigned = list(map(lambda x: toVariable(x[0]), previousAssignments.values()))
    diff = set(matrix.variables()).difference(set(variablesAssigned))
    variable = list(diff)[0]
    
    STARTING_ASSIGNMENT = False
    previousAssignments[dl] = (variable, STARTING_ASSIGNMENT, True)
    return previousAssignments[dl]

def backtrackAndLearn(matrix, highestDecisionLevel, variableAssignments, previousAssignments):
    matrix.backtrack(highestDecisionLevel - 1)
    # print("backtracing to: ", highestDecisionLevel - 1)
    keys = list(previousAssignments.keys())
    for key in keys:
        if highestDecisionLevel < key:
            del previousAssignments[key]
    literals = list(map(lambda x: negate(x), variableAssignments))
    matrix.addClause(literals, 0)

def run(filename):
    # Reset assignments
    matrix = parse_cnf(filename)
    return cdcl(matrix)
