from lib_bonds import *
graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

n_SF = "SF"
n_C  = "C"
n_R  = "R"
n_I  = "I"
n_0  = "0"
n_1  = "1"


# make list of nodes
ns = [ n_SF, n_C, n_R, n_I, n_0, n_1, ]

# make list of edges
es = [
    FlyEdge(1, n_SF, n_0, pwr_to_dest=1),
    FlyEdge(2, n_C, n_0, pwr_to_dest=0),
    FlyEdge(3, n_0, n_1, pwr_to_dest=1),
    FlyEdge(4, n_1, n_R, pwr_to_dest=1),
    FlyEdge(5, n_1, n_I, pwr_to_dest=1),
]

assign_causality_to_all_nodes(es)

generate_symbols(es)


'''
for n in ns:
    graph.add_node(pydot.Node(n, shape="none", label=n))

for e in es:
    graph.add_edge(e.mk_edge())

graph.write_png("graph_5p4.png") # type: ignore
# graph.write_pdf("o.pdf") # type: ignore

'''