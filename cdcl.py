from structures import *
import time
import logging
import os
import errno

logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
COMMENT = 'c'
INFO = 'p'

OUTPUT_RESULTS_TO_FILE = True
OUTPUT_DIRECTORY = "results\\"

def parse_cnf(filename):
    file = open(filename, 'r')
    clauses = []
    for line in file.readlines():
        line = line.strip()
        # Skip comments or info lines
        if not line or COMMENT == line[0] or INFO == line[0]:
            continue
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
    returns: (SAT/UNSAT boolean, AssignmentList, contradiction_clauses)
    """
    contradiction_clauses = []

    did_succeed, new_clauses, contradiction_clause = unit_propagation(assignment_list.decision_level, clauses)
    if not did_succeed:
        contradiction_clauses.append(contradiction_clause)
        # logging.debug("did not succeed after first propagation")
        return (False, assignment_list, contradiction_clauses)
    
    did_backtrack = False
    while not assignment_list.all_values_assigned() or did_backtrack:
        next_variable, value = assignment_list.assign_next(did_backtrack)

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
            contradiction_clauses.append(contradiction_clause)
            learnt_clause, max_decision_level, max_variable = contradiction_clause.learn_new_clause(assignment_list)
            # Check if we can backtrack to max_decision_level
            backtrack_decision_level = assignment_list.get_backtrack_decision_level(max_decision_level)
            logging.info("Contradiction clause: " + contradiction_clause.hidden_str() + ", with var: " + str(max_variable) \
                + ", to dl: " + str(backtrack_decision_level))
            if backtrack_decision_level == -1:
                logging.debug("Unable to backtrack any further...")
                return (False, assignment_list, contradiction_clauses)
            
            assignment_list.backtrack(backtrack_decision_level)
            # Need to backtrack one step further for clauses (as it will be reassigned without incrementing decision level in the next iteration)
            backtracked_clauses = list(map(lambda x: x.backtrack(backtrack_decision_level-1), clauses))
            backtracked_clauses.append(learnt_clause)
            assignment_list.update_vsids_with(learnt_clause)
            did_backtrack = True
            clauses = backtracked_clauses
        else:
            # Unit propagation successful, replace old clauses with newly propagated clauses
            did_backtrack = False
            clauses = new_clauses

    # Sanity check to make sure that clauses here are not contradictions
    for clause in clauses:
        if clause.is_empty_clause():
            logging.debug("CONTRADICTION FOUND WHERE IT RETURNS BE SAT")

    return (True, assignment_list, [])


def unit_propagation(decision_level, clauses):
    """ Carries out unit propagation on the list of clauses

    returns: If succeeeded, (True, new list of clauses, None)
        If contradiction, (False, new list of clauses, clause that reached a contradiction)
    """
    # Check for any empty clauses first.
    for clause in clauses:
        if clause.is_empty_clause():
            return (False, clauses, clause)

    unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)
    while unpropagated_unit_clause is not None:
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
        unpropagated_unit_clause = find_unpropagated_unit_clause(clauses)

    return (True, clauses, None)

def find_unpropagated_unit_clause(clauses):
    """ Finds an unpropagated unit clause """
    for clause in clauses:
        if clause.is_unit_clause() and not clause.unit_clause_propagated:
            return clause
    return None

def run(filename):
    assignment_list, clauses = parse_cnf(filename)
    start = time.time()
    result, assignment_list, contradiction_clauses = cdcl(assignment_list, clauses.copy())
    
    end = time.time()
    time_elapsed = end - start
    logging.info("Time Elapsed: " + str(time_elapsed))
    variable_assignment = None
    if result:
        variable_assignment = assignment_list.get_variable_assignment()
        verified_result = verify(variable_assignment, clauses)
        if verified_result == result:
            logging.info("Successfuly Verified to be: " + str(verified_result))
        else:
            logging.info("ERROR Verified to be: " + str(verified_result) + " but result was: " + str(result))
    else: # Contradiction
        all_proofs = []
        all_clauses_involved = []
        # Goes in order of created contradiction clauses
        for contradiction_clause in contradiction_clauses:
            proofs, clauses_involved = contradiction_clause.generate_contradiction_proof()
            all_proofs.extend(proofs)
            all_clauses_involved.extend(clauses_involved)

        filename = filename.split('\\')[-1]
        output_filename = OUTPUT_DIRECTORY + "results-" + filename.replace(".cnf", "") + ".txt"
        output_contradiction_proof(all_proofs, all_clauses_involved, output_filename)
        
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

def output_contradiction_proof(proofs, clauses, output_filename):
    """ Logs the contradiction proof in the required format to a file """
    # Sorts the clauses by order of increasing decision level
    ordered_clauses = sorted(list(clauses), key=lambda x: x.decision_level)
    if OUTPUT_RESULTS_TO_FILE:
        if not os.path.exists(os.path.dirname(output_filename)):
            try:
                os.makedirs(os.path.dirname(output_filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        output_file = open(output_filename, 'w')

    # First segment - number of clauses used in proof
    initial_line = "v " + str(len(ordered_clauses))
    # logging.info(initial_line)
    if OUTPUT_RESULTS_TO_FILE:
        output_file.write(initial_line + "\n")

    # Second segment - clauses and their unique ids
    for i, clause in enumerate(ordered_clauses):
        clause_identifier_line = str(i) + ": " + clause.output_format()
        # logging.info(clause_identifier_line)
        if OUTPUT_RESULTS_TO_FILE:
            output_file.write(clause_identifier_line + "\n")

    # Used to prevent duplicate proofs
    proven_clauses = set()

    # Third segment - proofs:
    for previous_clause, propagated_by_clause, resultant_clause in proofs:
        if resultant_clause in proven_clauses:
            continue
        proven_clauses.add(resultant_clause)
        previous_id = ordered_clauses.index(previous_clause)
        propagated_by_id = ordered_clauses.index(propagated_by_clause)
        resultant_id = ordered_clauses.index(resultant_clause)
        resolution_line = " ".join(map(str, [previous_id, propagated_by_id, resultant_id]))
        # logging.info(resolution_line)
        # logging.info(previous_clause.hidden_str() + ", " + propagated_by_clause.hidden_str() + " -> " + resultant_clause.hidden_str())
        if OUTPUT_RESULTS_TO_FILE:
            output_file.write(resolution_line + "\n")

        if resultant_clause.is_empty_clause():
            logging.info("Learnt Clause generated: " + resultant_clause.hidden_str())

