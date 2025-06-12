from lib_bonds import *

CASE = "EX_02"

n_SE = "SE"
n_C  = "C"
n_R3  = "R_3"
n_R6  = "R_6"
n_I  = "I"
n_0  = "0"
n_1  = "1"

# make list of nodes
ns = [ n_SE, n_C, n_R3, n_R6, n_I, n_0, n_1, ]

# make list of edges
es = [
    FlyEdge(1, n_SE, n_1 , pwr_to_dest=1),
    FlyEdge(2, n_1 , n_I , pwr_to_dest=1),
    FlyEdge(3, n_1 , n_R3, pwr_to_dest=1),
    FlyEdge(4, n_1 , n_0 , pwr_to_dest=1),
    FlyEdge(5, n_0 , n_C , pwr_to_dest=1),
    FlyEdge(6, n_0 , n_R6, pwr_to_dest=1),
]

assign_causality_to_all_nodes(es)

# plot_graph(es, ns, f"graph_{CASE}.png")

equations, symbols = generate_symbols(es)

report_equations(equations, symbols, write=False)

'''
# collect all symbols that are not parameters (like R_03, I_02, C_05, SE_01)
key_symbols = [sym for sym in symbols if sym.name.startswith(('e_', 'f_', 'p_', 'q_', 'pdot_', 'qdot_'))]

key_symbols = list(set(key_symbols))  # Remove duplicates

state_var_symbols = [sym for sym in symbols if sym.name.startswith(('pdot_', 'qdot_'))]

solution_explicit = sym.solve(equations, key_symbols, dict=True)
print("\nExplicit solution for state variables:")
if not solution_explicit:
    print("Could not find an explicit solution for all variables.")
else:
    print(f"Found {len(solution_explicit)} explicit solutions.")
    print(solution_explicit)

if solution_explicit:
    sol = solution_explicit[0]

    for sv_sym in state_var_symbols:
        sol_value = sol.get(sv_sym)
        if sol_value is not None:
            sym.pprint(sym.simplify(sym.Eq(sv_sym, sol_value)))
        else:
            print(f"{sv_sym} not found in this solution set.")
'''