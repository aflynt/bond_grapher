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

plot_graph(es, ns, f"graph_{CASE}.png")

report_equations(es, report_all=False, write=True)