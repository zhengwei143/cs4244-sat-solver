from math import *

AND = "AND"
OR = "OR"
NOT = "~"
OPEN = "("
CLOSE = ")"

def toVariable(literal):
    if NOT in literal:
        idx = literal.index(NOT)
        return literal[idx+1:]
    return literal

def negate(literal):
    if NOT in literal:
        idx = literal.index(NOT)
        return literal[idx+1:]
    return NOT + literal

def setBitAt(binary, position, value):
    mask = 1 << position
    if value == 1:
        return binary | mask
    return binary & ~mask

class Matrix:
    def __init__(self, clauses, literalPositions):
        self.decisionLevel = 0
        # Each value in matrix is a list of decisionValue (decisionLevel, value) tuples.
        # The list is bounded by the size of the clause (as new decisionValues are added when value changes)
        # This ensures that the size of our data structure is bounded by O(3n) => O(n) for 3-CNF
        self.matrix = {}
        self.dlVariableMapping = {}
        self.literalPositions = literalPositions
        # Convert the clauses to bit-values
        for i, clause in enumerate(clauses):
            self.matrix[i] = [(self.decisionLevel, self.toBinary(clause))]

    def variables(self):
        literals = list(self.literalPositions.keys())
        return list(filter(lambda x: NOT not in x, literals))
        
    # Checks if the clause has a literal
    def hasLiteral(self, clauseNum, literal):
        position = self.literalPositions[literal]
        return self.hasBit(clauseNum, position)

    # Checks if the bit at the position for the clause is 1
    def hasBit(self, clauseNum, position):
        binary = self.getBinary(clauseNum)
        return binary & (1 << position) != 0

    # Each literal corresponds to a particular bit - in literalPositions
    # e.g. 01001010 represents a clause with 3 literals
    def toBinary(self, literals):
        val = 0
        for literal in literals:
            position = self.literalPositions[literal]
            val = setBitAt(val, position, 1)
        return val

    def addClause(self, literals, decisionLevel):
        print("Learning clause: ", literals)
        nextClauseNum = max(self.matrix.keys()) + 1
        self.matrix[nextClauseNum] = [(decisionLevel, self.toBinary(literals))]

    def clauseLength(self, clauseNum):
        binary = self.getBinary(clauseNum)
        return bin(binary).count("1")

    def getBinary(self, clauseNum):
        return self.matrix[clauseNum][-1][1]

    def addDecisionValue(self, clauseNum, dv):
        if self.matrix[clauseNum][-1][0] == dv[0]:
            self.matrix[clauseNum][-1] = dv
            return    
        self.matrix[clauseNum].append(dv)

    def isUnitClause(self, clauseNum):
        return self.clauseLength(clauseNum) == 1

    def clauses(self):
        return list(self.matrix.keys())

    def unitClauses(self):
        return list(filter(lambda x: self.isUnitClause(x), self.clauses()))

    # Unit clause contains a single literal (e.g. (y))
    # If the target clause contains the literal, remove it and return True
    # If the target clause contains the negation of the literal, remove the negation and return True
    # Returns False if a contradiction - e.g. resolving (~y), (y)
    def propagate(self, targetClauseNum, unitClauseNum):
        targetClauseBinary = self.getBinary(targetClauseNum)
        unitClauseBinary = self.getBinary(unitClauseNum)
        position = int(log(unitClauseBinary, 2))
    
        # If the target clause has the unit literal, remove it
        if self.hasBit(targetClauseNum, position):
            # Keep track of which decision level it was removed at
            self.addDecisionValue(targetClauseNum, (self.decisionLevel, 0))
            return (True, False)

        # Get the mask of the negated literal (~y) - e.g. 11110111
        negatedPosition = self.negatePosition(position)
        mask = ~(1 << negatedPosition)

        # If masking this clause does not affect it, skip
        if not self.hasBit(targetClauseNum, negatedPosition):
            return (True, False)

        # Apply mask to target clause - to remove any literals (~y)
        result = targetClauseBinary & mask
        
        # Contradiction reached
        if result == 0:
            return (False, False)
        
        self.addDecisionValue(targetClauseNum, (self.decisionLevel, result))
        return (True, True)

    def negatePosition(self, position):
        if position % 2 == 0:
            return position + 1
        else:
            return position - 1

    # Returns True if variables assigned successfully
    # Returns False if assignment results in a False clause
    def assign(self, variable, value):
        self.decisionLevel += 1
        position = self.literalPositions[variable]
        negatedPosition = self.negatePosition(position)
        if value:
            # Set decision level -> variable mapping
            self.dlVariableMapping[self.decisionLevel] = variable

            # Remove all clauses with variable
            for clause in self.clauses():
                if self.hasBit(clause, position):
                    self.addDecisionValue(clause, (self.decisionLevel, 0))
                
            # Remove ~variable from all clauses
            negatedVariableMask = ~(1 << negatedPosition)
            for clause in self.clauses():
                # If masking this clause does not affect it, skip
                if not self.hasBit(clause, negatedPosition):
                    continue
                result = self.getBinary(clause) & negatedVariableMask
                if result == 0:
                    self.addDecisionValue(clause, (self.decisionLevel, 0))
                    return False
                self.addDecisionValue(clause, (self.decisionLevel, result))
        else:
            # Set decision level -> variable mapping
            self.dlVariableMapping[self.decisionLevel] = negate(variable)

            # Remove all clauses with ~variable
            for clause in self.clauses():
                if self.hasBit(clause, negatedPosition):
                    self.addDecisionValue(clause, (self.decisionLevel, 0))

            # Remove variable from all clauses
            variableMask = ~(1 << position)
            for clause in self.clauses():
                # If masking this clause does not affect it, skip
                if not self.hasBit(clause, position):
                    continue
                result = self.getBinary(clause) & variableMask
                if result == 0:
                    self.addDecisionValue(clause, (self.decisionLevel, 0))
                    return False
                self.addDecisionValue(clause, (self.decisionLevel, result))
        return True

    def backtrack(self, toLevel):
        self.decisionLevel = toLevel
        for clause in self.clauses():
            originalDecisionValues = self.matrix[clause]
            self.matrix[clause] = list(filter(lambda x: x[0] <= self.decisionLevel, originalDecisionValues))

    def variableAssignmentsInvolved(self, clauses):
        levelsInvolved = set()
        for clause in clauses:
            dls = list(map(lambda x: x[0], self.matrix[clause]))
            levelsInvolved.update(set(dls))
        levelsInvolved = levelsInvolved.difference(set([0]))
        print(self.dlVariableMapping)
        return (min(levelsInvolved), list(map(lambda x: self.dlVariableMapping[x], levelsInvolved)))
