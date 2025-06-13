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

my_equations, symbols = generate_symbols(es)



# report_equations(equations, symbols, write=False)

# collect all symbols that are not parameters (like R_03, I_02, C_05, SE_01)

def is_variable(symbol):
    fixed_vars = ["f_", "e_" ]
    return any(symbol.name.startswith(s) for s in fixed_vars)

# unknowns = [ s for s in symbols if is_variable(s) ]

# # find pdot_* and qdot_* symbols
# dot_vars = [s for s in symbols if s.name.startswith(('pdot_', 'qdot_'))]
# print(f"dot_vars = {dot_vars}")
# print(f"unknowns = {unknowns}")
# xs = dot_vars + unknowns
# print(f"xs = {xs}")

# Define all symbols
SE_01, e_01, f_02, p_02, I_02, e_05, q_05, C_05, e_03, R_03, f_03, f_06, e_06, R_06, e_02, pdot_02, f_05, qdot_05, f_01, f_04, e_04 = sym.symbols(
    'SE_01, e_01, f_02, p_02, I_02, e_05, q_05, C_05, e_03, R_03, f_03, f_06, e_06, R_06, e_02, pdot_02, f_05, qdot_05, f_01, f_04, e_04', real=True
)

# Define the equations
eq1 = sym.Eq(SE_01, e_01)
eq2 = sym.Eq(f_02, p_02 / I_02)
eq3 = sym.Eq(e_05, q_05 / C_05)
eq4 = sym.Eq(e_03, R_03 * f_03)
eq5 = sym.Eq(f_06, e_06 / R_06)
eq6 = sym.Eq(e_02, pdot_02)
eq7 = sym.Eq(f_05, qdot_05)
eq8 = sym.Eq(f_01, f_02)
eq9 = sym.Eq(f_02, f_03)
eq10 = sym.Eq(f_02, f_04)
eq11 = sym.Eq(e_01, e_02 + e_03 + e_04)
eq12 = sym.Eq(e_04, e_05)
eq13 = sym.Eq(e_05, e_06)
eq14 = sym.Eq(f_04, f_05 + f_06)

new_equations = [eq1, eq2, eq3, eq4, eq5, eq6, eq7, eq8, eq9, eq10, eq11, eq12, eq13, eq14]

for my_eq, new_eq in zip(my_equations, new_equations):
    print(f"{my_eq} <=> {new_eq}")

solution_explicit = sym.solve(new_equations, [pdot_02, qdot_05, e_01, e_02, e_03, e_04, e_05, e_06, f_01, f_02, f_03, f_04, f_05, f_06], dict=True)

print("\nExplicit solution for pdot_02 and qdot_05:")
if solution_explicit:
    sol = solution_explicit[0]
    pdot_02_sol = sol.get(pdot_02)
    qdot_05_sol = sol.get(qdot_05)

    if pdot_02_sol is not None:
        sym.pprint(sym.simplify(sym.Eq(pdot_02, pdot_02_sol)))
    else:
        print("pdot_02 not found in this solution set.")

    if qdot_05_sol is not None:
        sym.pprint(sym.simplify(sym.Eq(qdot_05, qdot_05_sol)))
    else:
        print("qdot_05 not found in this solution set.")

else:
    print("Could not find an explicit solution for all variables.")

# solution_explicit = sym.solve(equations, xs, dict=True)

# if solution_explicit:
#     sol = solution_explicit[0]
#     for k,v in sol.items():
#         if k in dot_vars:
#             pq_sol = sol.get(k)
#             if pq_sol is not None:
#                 print(f"{k} = {pq_sol}")
#                 sym.pprint(sym.simplify(sym.Eq(k, pq_sol)))