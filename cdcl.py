from structures import *
import logging

logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
COMMENT = 'c'
INFO = 'p'

def parse_cnf(filename):
    file = open(filename, 'r')
    clauses = []
    for line in file.readlines():
        line = line.strip()
        # Skip comments or info lines
        if not line or COMMENT == line[0] or INFO == line[0]:
            continue
        # print(line.strip())
        # Ignore last value
        literal_strings = line.split()[:-1]
        if len(literal_strings) == 0:
            continue
        literals = tuple(map(Literal, literal_strings))
        clauses.append(Clause(literals, 0))

    assignment_list = AssignmentList(clauses)
    return (assignment_list, clauses)

def cdcl(assignment_list, clauses):
    did_succeed, result = unit_propagation(assignment_list.decision_level, clauses)
    # logging.debug("clauses: " + str(list(map(str, clauses))))
    if not did_succeed:
        # logging.debug("did not succeed after first propagation")
        return False
    
    did_backtrack = False
    while not assignment_list.all_values_assigned() or did_backtrack:
        next_variable, value = assignment_list.assign_next(did_backtrack)
        # print("decision_level: ", str(assignment_list.decision_level))
        # print(assignment_list)
        # logging.debug("assignments: " + str(assignment_list.assignments))
        # logging.debug("decision_levels: " + str(assignment_list.decision_levels))

        # Variable assignment to clauses
        assigned_clauses = []
        for clause in clauses:
            if clause.evaluated_true:
                assigned_clauses.append(clause)
                continue
            new_clause = clause.assign(next_variable, value, assignment_list.decision_level)
            assigned_clauses.append(new_clause)
        clauses = assigned_clauses

        # logging.debug(str(next_variable) + ", " + str(value))
        if next_variable is None or value is None:
            # logging.debug("This probably shouldn't happen: either next_variable or value is None")
            return (False, None)

        did_succeed, result = unit_propagation(assignment_list.decision_level, clauses)
        if not did_succeed: # Conflict
            learnt_clause, min_decision_level = result.learn_new_clause(assignment_list)
            # Check if we can backtrack to min_decision_level
            backtrack_decision_level = assignment_list.get_backtrack_decision_level(min_decision_level)
            if backtrack_decision_level == -1:
                logging.debug("Unable to backtrack any further...")
                return False
            # logging.debug("backtracking to: " + str(backtrack_decision_level))
            assignment_list.backtrack(backtrack_decision_level)
            backtracked_clauses = list(map(lambda x: x.backtrack(backtrack_decision_level-1), clauses))
            backtracked_clauses.append(learnt_clause)
            # logging.debug("Clause learnt: " + str(learnt_clause))
            did_backtrack = True
            clauses = backtracked_clauses
        else:
            # Unit propagation successful, replace old clauses with newly propagated clauses
            did_backtrack = False
            clauses = result

    # Sanity check to make sure that clauses here are not contradictions
    for clause in clauses:
        if clause.is_empty_clause():
            logging.debug("CONTRADICTION FOUND WHERE IT RETURNS BE SAT")

    return (True, assignment_list)


def unit_propagation(decision_level, clauses):
    """ Carries out unit propagation on the list of clauses

    returns: If succeeeded, (True, new list of clauses)
        If contradiction, (False, clause that reached a contradiction)
    """
    # logging.debug("initial clauses: " + str(list(map(str, clauses))))
    # Check for any empty clauses first.
    for clause in clauses:
        if clause.is_empty_clause():
            return (False, clause)

    unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)
    while unpropagated_unit_clause is not None:
        # logging.debug("propagating with: " + str(unpropagated_unit_clause))
        # Set flag to True (so that it will not be propagated again)
        unpropagated_unit_clause.unit_clause_propagated = True

        new_clauses = []
        # Propagate with other clauses
        for clause in clauses:
            # Ignore self or clauses that are already true by variable assignment
            if unpropagated_unit_clause is clause or clause.evaluated_true:
                new_clauses.append(clause)
                continue

            new_clause = clause.propagate_with(unpropagated_unit_clause, decision_level)

            # Contradiction reached
            if new_clause.is_empty_clause():
                return (False, new_clause)

            new_clauses.append(new_clause)

        clauses = new_clauses
        # logging.debug("clauses: " + str(list(map(str, clauses))))
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