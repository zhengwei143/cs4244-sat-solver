# CDCL SAT Solver

The algorithm for this CDCL SAT Solver follows the description of Algorithm 1 on page 6 of [https://www.cis.upenn.edu/~alur/CIS673/sat-cdcl.pdf] fairly closely. 

Several design and implementation choices were made in consideration of memory and time efficiencies. The rationales for each choice are detailed below.

## Formula encoding
Each clause is represented as a binary value. Each variable in the formula and its negation is assigned a bit-position (Every possible literal has a position). For each clause, if it has a literal, the corresponding bit-position of the literal is set to 1.
By bit shifting, we can check each clause for a literal in O(1) time and propagate in O(1) time as well.

## Unit Propagation
Unit propagation is done by masking the bit at the negated literal to propagate (e.g. to propagate (~y), bit mask the bit-position of (y)). If the value is equal to 0, this means that there are no literals in the clause (empty clause) and is hence a contradiction. If the value changes, we store the new value as a new state (explained in backtracking).

Our algorithm checks the clauses for any unit clauses, and carries out unit propagation for each unit clause. We keep doing this until all unit clauses have been propagated (including newly generated unit clauses).

## Backtracking 
To allow for backtracking, we keep the previous states of each clause in an array, so that we can revert the states to the appropriate decision level when we backtrack. Each state is tagged with a decision level. We do not store a state for every clause at every decision level as this would take up too much space. Instead, we store the new state everytime the original state changes (as a result of propagation or variable assignment) and tag on the decision level as well (so we know which state we should revert to - the state with decision level <= decision level to revert to).

To decide which level to backtrack to, when we run the propagation, we keep track of which clauses were affected by its unit clause as a result of the unit propagation. When we reach a contradiction at a clause, we get the clauses which affected that empty clause, and find the set of decision levels at which a variable was assigned to any of these clauses.

## Current Progress
We are currently stuck at fixing the correctness of our CDCL algorithm, and are testing it against the AIM dataset found on [https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html]. Later on, we will be using a random CNF generator, and using the cryptominisat [https://github.com/msoos/cryptominisat] SAT solver as a benchmark.
