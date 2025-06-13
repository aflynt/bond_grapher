
from lib_bonds import *

CASE = "EX_03"

n_SE1 = "SE_1"
n_SE2 = "SE_2"


n_C3  = "C_3"
n_C4  = "C_4"

n_I5  = "I_5"

n_R6  = "R_6"
n_R7  = "R_7"
n_R8  = "R_8"

n_0a  = "0_a"
n_1a  = "1_a"
n_1b  = "1_b"

n_TF  = "TF"

# make list of nodes
ns = [ n_SE1, n_SE2, n_C3, n_C4, n_R6, n_R7, n_R8, n_I5, n_0a, n_1a, n_1b, n_TF ]

# number, power_from, power_to
edge_specs = [
    (1, n_SE1, n_1a),
    (2, n_SE2, n_1b),
    (3, n_0a, n_C3),
    (4, n_1b, n_C4),
    (5, n_1b, n_I5),
    (6, n_1b, n_R6),
    (7, n_1b, n_R7),
    (8, n_1a, n_R8),
    (9, n_1a, n_0a),
    (10, n_0a, n_TF),
    (11, n_TF, n_1b),
]


# make list of edges
es = [ FlyEdge(num, pwr_fm_node, pwr_to_node, pwr_to_dest=1) 
       for num, pwr_fm_node, pwr_to_node in edge_specs ]


assign_causality_to_all_nodes(es)

plot_graph(es, ns, f"graph_{CASE}.png")

report_equations(es, report_all=False, write=True)