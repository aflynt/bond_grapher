from lib_bonds import *
graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

n_SE_a = "SE_a"
n_SE_b = "SE_b"
n_I_a = "I_a"
n_R_a = "R_a"
n_R_b = "R_b"
n_R_c = "R_c"
n_1_a = "1_a"
n_1_b = "1_b"
n_0_a = "0_a"
n_C_a = "C_a"
n_C_b = "C_b"
n_TF_a = "TF_a"

ns = [
    pydot.Node(n_SE_a, shape="none", label=n_SE_a),
    pydot.Node(n_SE_b, shape="none", label=n_SE_b),
    pydot.Node(n_I_a, shape="none", label=n_I_a),
    pydot.Node(n_R_a, shape="none", label=n_R_a),
    pydot.Node(n_R_b, shape="none", label=n_R_b),
    pydot.Node(n_R_c, shape="none", label=n_R_c),
    pydot.Node(n_1_a, shape="none", label=n_1_a),
    pydot.Node(n_1_b, shape="none", label=n_1_b),
    pydot.Node(n_0_a, shape="none", label=n_0_a),
    pydot.Node(n_C_a, shape="none", label=n_C_a),
    pydot.Node(n_C_b, shape="none", label=n_C_b),
    pydot.Node(n_TF_a, shape="none", label=n_TF_a),
]

edge_list = [
    (1, n_SE_a, n_1_a, 1),
    (8, n_1_a, n_R_a, 1),
    (9, n_1_a, n_0_a, 1),
    (3, n_0_a, n_C_a, 1),
    (10, n_0_a, n_TF_a, 1),
    (11, n_TF_a, n_1_b, 1),
    (5, n_1_b, n_I_a, 1),
    (6, n_1_b, n_R_c, 1),
    (7, n_1_b, n_R_b, 1),
    (2, n_SE_b, n_1_b, 1),
    (4, n_1_b, n_C_b, 1),
]

es = []

for edge in edge_list:
    edge_id, src, dest, pwr_to_dest = edge
    es.append(FlyEdge(edge_id, src, dest, pwr_to_dest=pwr_to_dest))


assign_causality_to_all_nodes(es)

graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")
for n in ns:
    graph.add_node(n)
for e in es:
    graph.add_edge(e.mk_edge())

graph.write_png("my_graph.png") # type: ignore