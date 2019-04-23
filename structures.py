import random
from functools import reduce

NOT = '-'

class Literal:
    """ Representation of a literal """

    def __init__(self, literal_string):
        self.value = literal_string

    def negation(self):
        """ Returns a negated copy of the Literal """
        if NOT == self.value[0]:
            return Literal(self.value[1:])
        return Literal(NOT + self.value)

    def is_negation_of(self, other):
        """ Checks it the other Literal is the negation of the current Literal """
        return other == self.negation()

    def get_variable(self):
        """ Returns the variable string of the Literal """
        if NOT == self.value[0]:
            return self.value[1:]
        return self.value

    @staticmethod
    def init_from_variable(variable_string, value):
        """ Creates a Literal from the a variable string (not negated) and its boolean value """
        if value:
            return Literal(variable_string)
        return Literal(NOT + variable_string)

    def __eq__(self, other):
        return self.value == other.value
    
    def __str__(self):
        return self.value

class AssignmentList:
    """ Variables assignments are stored in the assignment list
    
    :attribute decision_level: The decision level of the current assignments
    :attribute variables: Dictionary containing the variables and the past assignments assigned to them
        - { variable string -> assignment history [True / False] (empty if not assigned a variable before) }
    :attribute assignments: Dictionary containing the variable and the decision level it was assigned
        - { variable string -> decision level }
    """

    def __init__(self, clauses):
        self.decision_level = 0
        self.assignments = {}
        for clause in clauses:
            for literal in clause.literals:
                variable = literal.get_variable()
                self.assignments[variable] = []
        self.decision_levels = {}

    def assign_next(self):
        """ Assigns the next variable with a boolean value """
        next_variable = self.pickbranching_variable()
        if next_variable is None:
            return (None, None)
        value = self.value_to_assign(next_variable)
        if value is None:
            return (None, None)
        self.decision_level += 1
        self.assignments[next_variable].append(value)
        self.decision_levels[next_variable] = self.decision_level
        return (next_variable, value)

    def pickbranching_variable(self):
        """ Pickbranching to decide which variable to pick for assignment next
        TODO: Implement pickbranching heuristic
            - Temporarily finds the first unassigned variable
        """
        for variable, assignment in self.assignments.items():
            if assignment is None:
                return variable
        return None

    def value_to_assign(self, variable):
        """ Decides what value to assign the next variable
        TODO: Implement heuristic to decide value to assign
            - Temporarily randomly picks first value to assign it
        """
        if len(self.assignments[variable] == 2):
            return None
        if len(self.assignments[variable]) == 0:
            values = [True, False]
            random.shuffle(values)
            return values[0]
        return not self.assignments[variable][-1]

    def get_dl_variable_assignment(self, of_variable):
        """ Gets the value assigned to a given variable and the decision level it was assigned """
        if of_variable not in self.assignments or len(self.assignments[of_variable]) == 0:
            return (None, None)
        # Return the last assignment
        value_assigned = self.assignments[of_variable][-1]
        at_decision_level = self.decision_levels[of_variable]
        return (value_assigned, at_decision_level)

    def get_backtrack_decision_level(self, min_decision_level):
        """ Gets the decision level that we can backtrack to:
        min_decision_level might already have two previous assignments, so we might need to backtrack further by one.

        :param min_decision_level: Minimum decision level that lead to a contradiction (from conflict analysis)
        """
        variable_at_min_dl = list(filter(lambda x: x[1] == min_decision_level, self.decision_levels.items))[0]
        if len(self.assignments[variable_at_min_dl]) == 2:
            return min_decision_level - 1
        return min_decision_level

    def backtrack(self, to_decision_level):
        """ Backtracks to the decision level """
        for variable, decision_level in self.decision_levels.items():
            if decision_level > to_decision_level:
                del self.decision_levels[variable]
                self.assignments[variable] = []

    def all_values_assigned(self):
        """ Checks if all values are assigned """
        values_assigned = tuple(map(lambda x: len(x) != 0, self.assignments.values()))
        return reduce(lambda x, y: x and y, values_assigned)

    


class Clause:
    """ Representation of a clause - contains multiple literals
    
    :attribute literals: a tuple of literals it contains
    :attribute decision_level: the decision level it was created at
    :attribute evaluation: when a clause is evaluated to be True through variable assignment
        - This is set to True, else False
    :attribute previous_clause: a link to the previous clause it was created from (for backtracking)
    :attribute propagated_by: a link to the unit clause it was propagated with
    :attribute unit_clause_propagated: Only used for unit clauses as a flag to indicate if it has been propagated before
    """

    def __init__(self, literals, decision_level = -1, evaluation = False, previous_clause = None, propagated_by = None):
        self.literals = literals
        self.decision_level = decision_level
        self.evaluation = evaluation
        self.previous_clause = previous_clause
        self.propagated_by = propagated_by
        self.unit_clause_propagated = False

    def is_unit_clause(self):
        return self.literals

    def propagate_with(self, unit_clause, at_decision_level):
        """ Resolves the current Clause with another Clause, generating a new Clause
    
        :param unit_clause: the unit clause being resolved with the current clause
        :param at_decision_level: the decision level at which the new clause is being created
        returns: a newly clause if propagated, else itself
        """
        literal = unit_clause.literals[0]
        if literal.negation() not in self.literals:
            return self
        new_literals = tuple(filter(lambda x: x != literal.negation(), self.literals))
        new_clause = Clause(new_literals, at_decision_level, False, self, unit_clause)
        return new_clause

    def assign(self, variable, with_value, at_decision_level):
        """ Assigns a value to a variable in the clause

        :param variable: the variable that is being assigned (class is a literal, but always non-negated)
        :param with_value: the boolean value assigned to the variable
        :param at_decision_level: the decision level at which the variable assignment is happening
        """
        # Situation 1: When the clause becomes True by variable assignment:
        #   Assigning True to a variable that exists in the clause or
        #   Assigning False to a variable has its negation in the clause 
        if (with_value and variable in self.literals) or (not with_value and variable.negation() in self.literals):
            return Clause(self.literals, at_decision_level, True, self, None)
        
        # Situation 2: When a literal in the clause no longer needs to be considered because it is False
        #   Remove any instance of the literal in the clause and return a new clause
        if with_value and variable.negation() in self.literals:
            new_literals = tuple(filter(lambda x: x != variable.negation(), self.literals))
            return Clause(new_literals, at_decision_level, False, self, None)
        elif not with_value and variable in self.literals:
            new_literals = tuple(filter(lambda x: x != variable, self.literals))
            return Clause(new_literals, at_decision_level, False, self, None)

        # A new clause is NOT created
        return self


    def backtrack(self, to_decision_level):
        """ Backtracks to a given decision level by traversing previous_clause(s) until the 
        current decision_level <= to_decision_level
        """
        to_clause = self
        while to_clause.decision_level > to_decision_level and to_clause.previous_clause is not None:
            to_clause = to_clause.previous_clause
        return to_clause

    def is_empty_clause(self):
        """ A contradiction is found by checking if any newly generated clause is empty """
        return len(self.literals) == 0

    def learn_new_clause(self, assignment_list):
        """ Used when the clause is empty and hence a contradiction
        Recursively searches the previous_clause(s) and propagated_by unit clauses to their base clauses with DFS
        and creates a set of variables that lead to the contradiction. From there, generates a new clause to be learnt.
        
        :param assignment_list: The current variable AssignmentList that leads to the contradiction
        returns: a newly learned clause (negation of the conjunction of resultant variable assignments)
            and the minimum decision level that started the contradiction
        """
        variable_set = set()
        visited_clauses = set() # To short-cuircuit the dfs

        def dfs(clause):
            """ Helper recursive function """
            if clause is None or clause in visited_clauses:
                return
            # Mark current clause as visited
            visited_clauses.add(clause)
            # Recurse through parent clauses
            dfs(clause.previous_clause)
            dfs(clause.propagated_by)

            # Check if base clause has been reached
            if clause.previous_clause is None and clause.propagated_by is None:
                variables = list(map(lambda x: x.get_variable(), clause.literals))
                variable_set.update(variables)

        dfs(self)
        new_literals = []
        min_decision_level = int('inf')
        for variable in variable_set:
            value_assigned, at_decision_level = assignment_list.get_dl_variable_assignment(variable)
            # Variables that were not assigned a value should not be added to the learnt clause
            if value_assigned is None:
                continue
            min_decision_level = min(min_decision_level, at_decision_level)
            literal = Literal.init_from_variable(variable, not value_assigned)
            new_literals.append(literal)
        
        assert(len(new_literals) != 0, "Newly learned clause should have non-empty literal list")
        
        # Newly learnt clause should start at decision level 0
        return (Clause(new_literals, 0), min_decision_level)

    def __str__(self):
        return ' '.join(self.literals)

