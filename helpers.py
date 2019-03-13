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
        self.matrix = {}
        self.literalPositions = literalPositions
        # Convert the clauses to bit-values
        for i, clause in enumerate(clauses):
            self.matrix[i] = self.toBinary(clause)

    # Each literal corresponds to a particular bit - in literalPositions
    # e.g. 01001010 represents a clause with 3 literals
    def toBinary(self, literals):
        val = 0
        for literal in literals:
            position = self.literalPositions[literal]
            val = setBitAt(val, position, 1)
        return val
        
    # Checks if the clause has a literal
    def hasLiteral(self, clauseNum, literal):
        position = self.literalPositions[literal]
        return self.hasBit(clauseNum, position)

    # Checks if the bit at the position for the clause is 1
    def hasBit(self, clauseNum, position):
        binary = self.matrix[clauseNum]
        return binary & (1 << position) != 0

    def clauseLength(self, clauseNum):
        binary = self.matrix[clauseNum]
        return bin(binary).count("1")

    def isUnitClause(self, clauseNum):
        return self.clauseLength(clauseNum) == 1

    def clauses(self):
        return list(self.matrix.keys())

    # Unit clause contains a single literal (e.g. (y))
    # If the target clause contains the literal, remove it and return True
    # If the target clause contains the negation of the literal, remove the negation and return True
    # Returns False if a contradiction - e.g. resolving (~y), (y)
    def propagate(self, targetClauseNum, unitClauseNum):
        targetClauseBinary = self.matrix[targetClauseNum]
        unitClauseBinary = self.matrix[unitClauseNum]
        position = int(log(unitClauseBinary, 2))
    
        # If the target clause has the unit literal, remove it
        if self.hasBit(targetClauseNum, position):
            del self.matrix[targetClauseNum]
            return True

        # Get the mask of the negated literal (~y) - e.g. 11110111
        mask = None
        # Negations of variables are kept one bit after its non-negated form
        if position % 2 == 0:
            mask = ~(unitClauseBinary << 1)
        else:
            mask = ~(unitClauseBinary >> 1)
        # Apply mask to target clause - to remove any literals (~y)
        result = targetClauseBinary & mask
        
        # Contradiction reached
        if result == 0:
            return False
        
        self.matrix[targetClauseNum] = result
        return True