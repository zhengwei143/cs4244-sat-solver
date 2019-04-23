from structures import *

COMMENT = 'c'
INFO = 'p'

def parse_cnf(filename):
    file = open(filename, 'r')
    clauses = []
    for line in file.readlines():
        # Skip comments or info lines
        if COMMENT == line[0] or INFO == line[0]:
            continue
        
        literals = tuple(map(Literal, line.split()))
        clauses.append(Clause(literals, 0))

    assignment_list = AssignmentList(clauses)
    return (assignment_list, clauses)

def cdcl(assignment_list, clauses):
    did_succeed, result = unit_propagation(assignment_list.decision_level, clauses)
    if not did_succeed:
        return False
    
    while not assignment_list.all_values_assigned():
        next_variable, value = assignment_list.assign_next()
        if next_variable is None or value is None:
            print("This probably shouldn't happen: either next_variable or value is None")
            return False

        did_succeed, result = unit_propagation(assignment_list.decision_level, clauses)
        if not did_succeed: # Conflict
            learnt_clause, min_decision_level = result.learn_new_clause(assignment_list)
            # Check if we can backtrack to min_decision_level
            backtrack_decision_level = assignment_list.get_backtrack_decision_level(min_decision_level)
            if backtrack_decision_level == -1:
                print("Unable to backtrack any further...")
                return False

            backtracked_clauses = list(map(lambda x: x.backtrack(backtrack_decision_level), clauses))
            backtracked_clauses.append(learnt_clause)
            clauses = backtracked_clauses
        else:
            # Unit propagation successful, replace old clauses with newly propagated clauses
            clauses = result

    return True


def unit_propagation(decision_level, clauses):
    """ Carries out unit propagation on the list of clauses

    returns: If succeeeded, (True, new list of clauses)
        If contradiction, (False, clause that reached a contradiction)
    """
    unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)
    while unpropagated_unit_clause is not None:
        # Set flag to True (so that it will not be propagated again)
        unpropagated_unit_clause.unit_clause_propagated = True

        new_clauses = []
        # Propagate with other clauses
        for clause in clauses:
            if unpropagated_unit_clause is clause:
                new_clauses.append(unpropagated_unit_clause)
                continue
            new_clause = clause.propagate_with(unpropagated_unit_clause, decision_level)

            # Contradiction reached
            if new_clause.is_empty_clause():
                return (False, new_clause)

            new_clauses.append(new_clause)

        clauses = new_clauses
        unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)

    return (True, clauses)


def find_unpropagated_unit_clause(clauses):
    """ Finds an unpropagated unit clause """
    for clause in clauses:
        if clause.is_unit_clause() and not clause.unit_clause_propagated:
            return clause
    return None



def run(filename):
    assignment_list, clauses = parse_cnf(filename)
    return cdcl(assignment_list, clauses)