from lib_bonds import *

CASE = "EX_01"

n_SF = "SF"
n_C  = "C"
n_R  = "R"
n_I  = "I"
n_0  = "0"
n_1  = "1"

ns = [ n_SF, n_C, n_R, n_I, n_0, n_1, ]

edge_specs = [
    (1, n_SF, n_0),
    (2, n_0 , n_C),
    (3, n_0 , n_1),
    (4, n_1 , n_R),
    (5, n_1 , n_I),
]
es = [ FlyEdge(num, pwr_fm_node, pwr_to_node, pwr_to_dest=1)
       for num, pwr_fm_node, pwr_to_node in edge_specs ]

assign_causality_to_all_nodes(es)

plot_graph(es, ns, f"graph_{CASE}.png")

report_equations(es, report_all=False, write=True)