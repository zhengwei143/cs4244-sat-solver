import random
from functools import reduce
from collections import defaultdict
import logging

NOT = '-'
NUM_BACKTRACKS = 5
DIVISION_CONSTANT = 2

class Literal:
    """ Representation of a literal """

    def __init__(self, literal_string):
        self.value = literal_string

    def negation(self):
        """ Returns a negated copy of the Literal """
        if self.is_negation():
            return Literal(self.value[1:])
        return Literal(NOT + self.value)

    def is_negation(self):
        return NOT == self.value[0]

    def is_negation_of(self, other):
        """ Checks it the other Literal is the negation of the current Literal """
        return other == self.negation()

    def get_variable(self):
        """ Returns the variable string of the Literal """
        if self.is_negation():
            return self.value[1:]
        return self.value

    def evaluate(self, variable_assignment):
        """ Given a variable assignment evaluate the boolean value of the literal """
        variable_value = variable_assignment[self.get_variable()]
        return (not self.is_negation() and variable_value) or (self.is_negation() and not variable_value)

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
    
    def __lt__(self, other):
        return self.value < other.value

    def __hash__(self):
        return hash(self.value)

class AssignmentList:
    """ Variables assignments are stored in the assignment list
    
    :attribute decision_level: The decision level of the current assignments
    :attribute variables: Dictionary containing the variables and the past assignments assigned to them
        - { variable string -> assignment history [True / False] (empty if not assigned a variable before) }
    :attribute assignments: Dictionary containing the variable and the decision level it was assigned
        - { variable string -> decision level }
    :attribute vsids: Dictionary containing the literal and its count. Used in the pickbranching heuristic
    :attribute branching_count: Int counter that indicates the number of times a variable is re-assigned due to a backtrack
    """

    def __init__(self, clauses):
        self.decision_level = 0
        self.assignments = {}
        self.vsids = defaultdict(float)
        for clause in clauses:
            for literal in clause.literals:
                self.vsids[literal] += 1
                variable = literal.get_variable()
                self.assignments[variable] = []
        self.decision_levels = {}
        self.branching_count = 0
        self.backtrack_count = 0

    def assign_next(self, did_backtrack):
        """ Assigns the next variable with a boolean value,
        If the algorithm did backtrack, look to replace the variable at the current decision level
        """
        next_variable, value = self.pickbranching_variable(did_backtrack)
        if next_variable is None or value is None:
            return (None, None)
        if not did_backtrack:
            self.decision_level += 1
        self.assignments[next_variable].append(value)
        self.decision_levels[next_variable] = self.decision_level
        return (Literal(next_variable), value)

    def pickbranching_variable(self, did_backtrack):
        # Choose pickbranching implementation here.
        self.branching_count += 1
        return self.pickbranching_variable_vsids(did_backtrack)
        # return self.pickbranching_variable_random(did_backtrack)

    def pickbranching_variable_vsids(self, did_backtrack):
        """ Pickbranching heuristic to decide which variable assignment to choose
        Currently implementing VSIDS:
        """
        if did_backtrack: # Select the variable at the current decision_level
            self.did_backtrack_divide_vsids()
            variable = list(filter(lambda x: x[1] == self.decision_level, self.decision_levels.items()))[0][0]
            value = not self.assignments[variable][-1]
            
            return (variable, value)
        else:
            # Predicate: variable must be unassigned at the current decision level
            predicate = lambda x: x[0].get_variable() not in self.decision_levels
            literal = max(filter(predicate, self.vsids.items()), key=lambda x: x[1])[0]
            variable = literal.get_variable()
            value = not literal.is_negation()
            return (variable, value)

    def pickbranching_variable_random(self, did_backtrack):
        """ Pickbranching to decide which variable to pick for assignment next
            - Temporarily finds the first unassigned variable and assigns a random value
        """
        variable = None
        if did_backtrack: # Select the variable at the current decision_level
            self.did_backtrack_divide_vsids()
            variable = list(filter(lambda x: x[1] == self.decision_level, self.decision_levels.items()))[0][0]
        else:
            for var, assignment in self.assignments.items():
                if len(assignment) == 2 or var in self.decision_levels:
                    continue
                variable = var
                break
        if variable is None or len(self.assignments[variable]) == 2:
            return (None, None)
        if len(self.assignments[variable]) == 0:
            values = [True, False]
            random.shuffle(values)
            value = values[0]
        else:
            value = not self.assignments[variable][-1]
        return (variable, value)

    def update_vsids_with(self, clause):
        """ When a clause is learnt,
        update vsids by incrementing all the new literal counters by 1
        """
        for literal in clause.literals:
            self.vsids[literal] += 1

    def did_backtrack_divide_vsids(self):
        """ Called everytime it backtracks, keeps counter and divides when it reaches the threshold """
        self.backtrack_count += 1
        if self.backtrack_count < NUM_BACKTRACKS:
            return
        self.backtrack_count = 0
        for variable in self.vsids:
            self.vsids[variable] /= DIVISION_CONSTANT


    def get_dl_variable_assignment(self, of_variable):
        """ Gets the value assigned to a given variable and the decision level it was assigned """
        if of_variable not in self.assignments or len(self.assignments[of_variable]) == 0:
            return (None, None)
        # Return the last assignment
        value_assigned = self.assignments[of_variable][-1]
        at_decision_level = self.decision_levels[of_variable]
        return (value_assigned, at_decision_level)

    def get_backtrack_decision_level(self, max_decision_level):
        """ Gets the decision level that we can backtrack to:
        max_decision_level might already have two previous assignments, so we might need to backtrack further by one.
        Find the maximum decision_level <= max_decision_level that does already have two assignments

        :param max_decision_level: Minimum decision level that lead to a contradiction (from conflict analysis)
        """
        predicate = lambda x: len(self.assignments[x[0]]) < 2 and x[1] <= max_decision_level
        valid_items = list(filter(predicate, self.decision_levels.items()))
        if len(valid_items) == 0:
            return -1 
        return max(valid_items, key=lambda x: x[1])[1]

    def backtrack(self, to_decision_level):
        """ Backtracks to the decision level """
        self.decision_level = to_decision_level
        items = list(self.decision_levels.items())
        for variable, decision_level in items:
            if decision_level > to_decision_level:
                del self.decision_levels[variable]
                self.assignments[variable] = []

    def all_values_assigned(self):
        """ Checks if all values are assigned """
        values_assigned = tuple(map(lambda x: len(x) != 0, self.assignments.values()))
        return reduce(lambda x, y: x and y, values_assigned)

    def get_variable_assignment(self):
        """ Returns a dictionary of the final variable assignment """
        final = {}
        for variable, assignments in self.assignments.items():
            if len(assignments) == 0:
                continue
            final[variable] = assignments[-1]
        return final

    def __str__(self):
        assignments = list(filter(lambda x: len(x[1]) > 0, self.assignments.items()))
        assignments = list(map(lambda x: str(x[0]) + ":" + str(x[1][-1]), assignments))
        return '(' + ', '.join(assignments) + ')'

class Clause:
    """ Representation of a clause - contains multiple literals
    
    :attribute literals: a tuple of literals it contains
    :attribute decision_level: the decision level it was created at
    :attribute evaluated_true: when a clause is evaluated to be True through variable assignment
        - This is set to True, else False
    :attribute previous_clause: a link to the previous clause it was created from (for backtracking)
    :attribute propagated_by: a link to the unit clause it was propagated with
    :attribute unit_clause_propagated: Only used for unit clauses as a flag to indicate if it has been propagated before
    :attribute learnt: Boolean flag to indicate whether or not this is a learnt clause (from a refutation)
    """

    def __init__(self, literals, decision_level = -1, evaluated_true = False,
        previous_clause = None, propagated_by = None, hidden_literals = set()):
        self.literals = literals
        self.hidden_literals = hidden_literals
        self.decision_level = decision_level
        self.evaluated_true = evaluated_true
        self.previous_clause = previous_clause
        self.propagated_by = propagated_by
        self.unit_clause_propagated = False
        self.learnt = None

    def is_unit_clause(self):
        return len(self.literals) == 1

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
        
        # If at the same level, modifies itself
        # if self.decision_level == at_decision_level:
        #     self.literals = new_literals
        #     return self
        hidden_literals = self.hidden_literals.union(unit_clause.hidden_literals)
        new_clause = Clause(new_literals, at_decision_level, False, self, unit_clause, hidden_literals)
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
        if with_value and variable in self.literals:
            hidden_literals = self.hidden_literals.union([variable])
            return Clause(self.literals, at_decision_level, True, self, None, hidden_literals)
        elif not with_value and variable.negation() in self.literals:
            hidden_literals = self.hidden_literals.union([variable.negation()])
            return Clause(self.literals, at_decision_level, True, self, None, hidden_literals)
        
        # Situation 2: When a literal in the clause no longer needs to be considered because it is False
        #   Remove any instance of the literal in the clause and return a new clause
        if with_value and variable.negation() in self.literals:
            new_literals = tuple(filter(lambda x: x != variable.negation(), self.literals))
            hidden_literals = self.hidden_literals.union([variable.negation()])
            return Clause(new_literals, at_decision_level, False, self, None, hidden_literals)
        elif not with_value and variable in self.literals:
            new_literals = tuple(filter(lambda x: x != variable, self.literals))
            hidden_literals = self.hidden_literals.union([variable])
            return Clause(new_literals, at_decision_level, False, self, None, hidden_literals)

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
        max_decision_level = 0
        max_variable = None
        for variable in variable_set:
            value_assigned, at_decision_level = assignment_list.get_dl_variable_assignment(variable)
            # Variables that were not assigned a value should not be added to the learnt clause
            if value_assigned is None:
                continue
            if max_decision_level < at_decision_level:
                max_decision_level = at_decision_level
                max_variable = variable
            literal = Literal.init_from_variable(variable, not value_assigned)
            new_literals.append(literal)
        
        assert(len(new_literals) != 0, "Newly learned clause should have non-empty literal list")
        
        # Newly learnt clause should start at decision level 0
        learnt_clause = Clause(tuple(new_literals), 0, False, self, None, set())
        learnt_clause.learnt = max_variable
        return (learnt_clause, max_decision_level)

    def evaluate(self, variable_assignment):
        """ Given a variable assignment, evaluates the boolean value of the clause by:
        Evaluating the disjuction of the evaluation of each literal
        """
        result = False
        for literal in self.literals:
            result = result or literal.evaluate(variable_assignment)
        return result

    def __str__(self):
        if self.evaluated_true:
            return '(TRUE)'
        return '(' + ', '.join(map(str, self.literals)) + ')'

    def format_string(self):
        if self.evaluated_true:
            return '(TRUE)'
        sorted_hidden_literals = sorted(list(self.hidden_literals))
        return ' '.join(map(str, sorted_hidden_literals)) 

    #####################################################
    # Methods to used in generating contradiction proof #
    #####################################################

    def generate_contradiction_proof(self):
        """ Generates the proof of contradiction """
        assert(self.is_empty_clause(), "Should only be generating a proof for contradictions (empty clauses)")
        proofs = []
        visited_clauses = set()

        def dfs(clause):
            if clause is None or clause in visited_clauses:
                return None
            if not clause.previous_clause and not clause.propagated_by:
                visited_clauses.add(clause)
                return clause
            if clause.previous_clause and not clause.propagated_by:
                dfs(clause.previous_clause)
                return

            clause = clause.get_preceeding_clause()
            visited_clauses.add(clause)
            # Recursively search previous clauses first to add any preceeding resolutions
            previous_clause = clause.previous_clause.get_preceeding_clause()
            propagated_by_clause = clause.propagated_by.get_preceeding_clause()
            prev = dfs(previous_clause)
            prop = dfs(propagated_by_clause)

            # Current clause is a result of resolution between two clauses
            if clause.previous_clause and clause.propagated_by:
                resolution = (previous_clause, propagated_by_clause, clause)
                proofs.append(resolution)
            # if prev and prop:
            #     resolution = (prev, prop, clause)
            #     proofs.append(resolution)

            return clause

        dfs(self)
        return proofs, visited_clauses

    def get_preceeding_clause(self):
        """ A clause could be generated as a result of a variable assignment """
        clause = self
        while clause.previous_clause and not clause.propagated_by:
            clause = clause.previous_clause
        return clause

    def resolution_with(self, other, on_variable):
        """ Resolution between two clauses using a given variable """
        assert(on_variable in map(lambda x: x.get_variable(), self.literals),
            "Clause should contain the variable")
        assert(on_variable in map(lambda x: x.get_variable(), other.literals),
            "Clause should contain the variable")
        all_literals = list(set(self.literals + other.literals))
        filtered_literals = tuple(filter(lambda x: x.get_variable() != on_variable, all_literals))
        variables = set(map(lambda x: x.get_variable(), filtered_literals))
        is_true = len(variables) < len(filtered_literals)
        new_clause = Clause(filtered_literals)
        return (new_clause, is_true)

