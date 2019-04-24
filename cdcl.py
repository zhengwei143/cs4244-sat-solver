from structures import *
import time
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
    """ Conflict Driven Clause Learning Algorithm 
    returns: (SAT/UNSAT boolean, AssignmentList, learnt_clauses)
    """
    did_succeed, new_clauses, result = unit_propagation(assignment_list.decision_level, clauses)
    # logging.debug("clauses: " + str(list(map(str, clauses))))
    if not did_succeed:
        # logging.debug("did not succeed after first propagation")
        return (False, assignment_list, [])
    
    all_learnt_clauses = []

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

        did_succeed, new_clauses, contradiction_clause = unit_propagation(assignment_list.decision_level, clauses)
        if not did_succeed: # Conflict
            learnt_clause, max_decision_level = contradiction_clause.learn_new_clause(assignment_list)
            # Check if we can backtrack to max_decision_level
            backtrack_decision_level = assignment_list.get_backtrack_decision_level(max_decision_level)
            if backtrack_decision_level == -1:
                logging.debug("Unable to backtrack any further...")
                # learnt_clauses = list(filter(lambda x: x.learnt, clauses))
                # check_learnt_clauses(learnt_clauses)
                return (False, assignment_list, all_learnt_clauses)
            # logging.debug("backtracking to: " + str(backtrack_decision_level))
            assignment_list.backtrack(backtrack_decision_level)
            # Need to backtrack one step further for clauses (as it will be reassigned without incrementing decision level in the next iteration)
            backtracked_clauses = list(map(lambda x: x.backtrack(backtrack_decision_level-1), clauses))
            backtracked_clauses.append(learnt_clause)
            logging.debug("Learnt Clause: " + str(learnt_clause))
            assignment_list.update_vsids_with(learnt_clause)
            did_backtrack = True
            clauses = backtracked_clauses
            
            if not all_learnt_clauses or all_learnt_clauses[-1][1] > max_decision_level:
                all_learnt_clauses = []
            all_learnt_clauses.append((learnt_clause, max_decision_level))
            # learnt_clauses = list(filter(lambda x: x.learnt, clauses))
            # logging.info("Num learnt clauses: " + str(len(learnt_clauses)))
        else:
            # Unit propagation successful, replace old clauses with newly propagated clauses
            did_backtrack = False
            clauses = new_clauses

    # Sanity check to make sure that clauses here are not contradictions
    for clause in clauses:
        if clause.is_empty_clause():
            logging.debug("CONTRADICTION FOUND WHERE IT RETURNS BE SAT")

    return (True, assignment_list, all_learnt_clauses)


def unit_propagation(decision_level, clauses):
    """ Carries out unit propagation on the list of clauses

    returns: If succeeeded, (True, new list of clauses, None)
        If contradiction, (False, new list of clauses, clause that reached a contradiction)
    """
    # logging.debug("initial clauses: " + str(list(map(str, clauses))))
    # Check for any empty clauses first.
    for clause in clauses:
        if clause.is_empty_clause():
            return (False, clauses, clause)

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
                return (False, clauses, new_clause)

            new_clauses.append(new_clause)

        clauses = new_clauses
        # logging.debug("clauses: " + str(list(map(str, clauses))))
        unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)

    return (True, clauses, None)


def find_unpropagated_unit_clause(clauses):
    """ Finds an unpropagated unit clause """
    for clause in clauses:
        if clause.is_unit_clause() and not clause.unit_clause_propagated:
            return clause
    return None

def check_learnt_clauses(learnt_clauses):
    reduced_clause = None
    logging.info("Reduced Clause: " + str(reduced_clause))
    for clause in learnt_clauses:
        if reduced_clause is None:
            reduced_clause = clause
            continue
        variable = clause.learnt
        reduced_clause, is_true = reduced_clause.resolution_with(clause, variable)
        logging.info("Reduced Clause: " + str(reduced_clause))
        if is_true:
            reduced_clause = None


def run(filename):
    assignment_list, clauses = parse_cnf(filename)
    start = time.time()
    result, assignment_list, learnt_clauses_dl = cdcl(assignment_list, clauses.copy())
    learnt_clauses = list(map(lambda x: x[0], learnt_clauses_dl))
    
    end = time.time()
    time_elapsed = end - start
    logging.info("Time Elapsed: " + str(time_elapsed))
    variable_assignment = None
    if result:
        variable_assignment = assignment_list.get_variable_assignment()
        # print("Verifying with variable assignment: ", variable_assignment)
        verified_result = verify(variable_assignment, clauses)
        if verified_result == result:
            logging.info("Successfuly Verified to be: " + str(verified_result))
        else:
            logging.info("ERROR Verified to be: " + str(verified_result) + " but result was: " + str(result))
    else: # Contradiction
        logging.info("Number of learnt clauses: " + str(len(learnt_clauses)))
        all_proofs = []
        all_involved_clauses = []
        for learnt_clause in learnt_clauses:
            empty_clause = learnt_clause.previous_clause
            proofs, involved_clauses = empty_clause.generate_contradiction_proof()
            all_proofs.extend(proofs)
            all_involved_clauses.extend(involved_clauses)
        # output_contradiction_proof(all_proofs, all_involved_clauses)
        
        check_learnt_clauses(learnt_clauses)

    return result, variable_assignment, assignment_list.branching_count, time_elapsed

def verify(variable_assignment, clauses):
    """ Verifies a variable assignment against a list of clauses and outputs:
    Evaluates the conjunction of the evaluation of each clause
        - True if SAT and False if UNSAT
    """
    result = True
    for clause in clauses:
        result = result and clause.evaluate(variable_assignment)
    return result

def output_contradiction_proof(proofs, clauses):
    """ Logs the contradiction proof in the required format to a file """
    # Sorts the clauses by order of increasing decision level
    ordered_clauses = sorted(list(clauses), key=lambda x: x.decision_level)

    # First segment - number of clauses used in proof
    initial_line = "v " + str(len(ordered_clauses))
    logging.info(initial_line)

    # Second segment - clauses and their unique ids
    for i, clause in enumerate(ordered_clauses):
        clause_identifier_line = str(i) + ": " + clause.format_string()
        logging.info(clause_identifier_line)

    # Third segment - proofs:
    for previous_clause, propagated_by_clause, resultant_clause in proofs:
        # print(previous_clause)
        # print(previous_clause.previous_clause)
        # print(previous_clause.propagated_by)
        previous_id = ordered_clauses.index(previous_clause)
        # print(propagated_by_clause)
        propagated_by_id = ordered_clauses.index(propagated_by_clause)
        resultant_id = ordered_clauses.index(resultant_clause)
        resolution_line = " ".join(map(str, [previous_id, propagated_by_id, resultant_id]))
        logging.info(resolution_line)