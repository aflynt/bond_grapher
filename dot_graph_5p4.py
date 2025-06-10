from lib_bonds import *
graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

node_SE = FlyNodeSF("SF")
node_C  = FlyNodeC("C")
node_R = FlyNodeR("R")
node_I = FlyNodeI("I")
node_0 = FlyNodeZERO("0")
node_1 = FlyNodeONE("1")



# make list of nodes
ns = [
  node_SE,
  node_C,
  node_R,
  node_I,
  node_0,
  node_1,
]

for n in ns:
    graph.add_node(n.node)


# make list of edges
es = [
    FlyEdge(1, node_SE.get_name(), node_1.get_name() , pwr_to_dest=1),
    FlyEdge(2, node_C.get_name(), node_1.get_name() , pwr_to_dest=0),
    FlyEdge(3, node_1.get_name(), node_0.get_name() , pwr_to_dest=1),
    FlyEdge(4, node_0.get_name(), node_R.get_name() , pwr_to_dest=1),
    FlyEdge(5, node_0.get_name(), node_I.get_name() , pwr_to_dest=1),
]

# add bond numbers to node ports
for e in es:
    src = e.src
    dest = e.dest
    bond_num = e.num
    for n in ns:
        if n.name == src or n.name == dest:
            n.add_port(bond_num)


# make a flygraph
fg = FlyGraph(ns, es)




# assign causality
assign_se_causality(fg)
assign_sf_causality(fg)

# report edge flow_side
for e in fg.es:
    print(f"Edge {e.num} from {e.src} to {e.dest} has flow side: {e.flow_side}")

for e in es:
    graph.add_edge(e.mk_edge())

graph.write_png("graph_5p4.png") # type: ignore
# #graph.write_pdf("o.pdf")

# constrained_etypes = [
#     "n_0",
#     "n_1",
#     "n_TF",
# ]