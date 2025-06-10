from lib_bonds import *

# TFE BOND GRAPH



#graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="grey")
graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

#n_SE_ACC = pydot.Node("n_SE_ACC", shape="none", label="SE:dP_acc")
#n_SE_SP = pydot.Node("n_SE_SP", shape="none", label="SE:F_spring")
#
#n_R_TP20 = pydot.Node("n_R_TP20", shape="none", label="R_TP20")
#
#n_TF_A = pydot.Node("n_TF_A", shape="none", label="TF:Aa")
#n_TF_B = pydot.Node("n_TF_B", shape="none", label="TF:Ab")
#
#n_I   = pydot.Node("n_I"  , shape="none", label="I")
#
#n_0_a = pydot.Node("n_0_a", shape="none", label="0_a")
#n_0_b = pydot.Node("n_0_b", shape="none", label="0_b")
#
#n_1_a = pydot.Node("n_1_a", shape="none", label="1_a")
#n_1_b = pydot.Node("n_1_b", shape="none", label="1_b")
#n_1_c = pydot.Node("n_1_c", shape="none", label="1_c")
#n_1_d = pydot.Node("n_1_d", shape="none", label="1_d")
#n_1_e = pydot.Node("n_1_e", shape="none", label="1_e")
#
#n_SF_QPA = pydot.Node("n_SF_QPA", shape="none", label="SF:Q_PA")
#n_SF_QPB = pydot.Node("n_SF_QPB", shape="none", label="SF:Q_PB")
#n_SF_QAT = pydot.Node("n_SF_QAT", shape="none", label="SF:Q_AT")
#
#n_R_TP30_PA = pydot.Node("n_R_TP30_PA", shape="none", label="R_TP30_PA")
#n_R_TP30_PB = pydot.Node("n_R_TP30_PB", shape="none", label="R_TP30_PB")
#n_R_TP30_AT = pydot.Node("n_R_TP30_AT", shape="none", label="R_TP30_AT")

fn_SE_ACC = FlyNodeSE("SE_ACC")
fn_SE_SP  = FlyNodeSE("SE_SP")
fn_R_TP20 = FlyNodeR("R_TP20")

fn_TF_A = FlyNodeTF("TF_A")
fn_TF_B = FlyNodeTF("TF_B")

fn_I   = FlyNodeI("I") 

fn_0_a = FlyNodeZERO("0_a")
fn_0_b = FlyNodeZERO("0_b")

fn_1_a = FlyNodeONE("1_a")
fn_1_b = FlyNodeONE("1_b")
fn_1_c = FlyNodeONE("1_c")
fn_1_d = FlyNodeONE("1_d")
fn_1_e = FlyNodeONE("1_e")

fn_SF_QPA = FlyNodeSF("SF_QPA")
fn_SF_QPB = FlyNodeSF("SF_QPB")
fn_SF_QAT = FlyNodeSF("SF_QAT")

fn_R_TP30_PA = FlyNodeR("R_TP30_PA")
fn_R_TP30_PB = FlyNodeR("R_TP30_PB")
fn_R_TP30_AT = FlyNodeR("R_TP30_AT")

# make list of nodes
ns = [
  fn_SE_ACC ,
  fn_R_TP20 ,
  fn_TF_A ,
  fn_TF_B ,
  fn_I   ,
  fn_SE_SP ,
  fn_0_a ,
  fn_0_b ,
  fn_1_a ,
  fn_1_b ,
  fn_1_c ,
  fn_1_d ,
  fn_1_e ,
  fn_SF_QPA,
  fn_R_TP30_AT,
  fn_SF_QPB,
  fn_R_TP30_PA,
  fn_SF_QAT,
  fn_R_TP30_PB,
]

for n in ns:
    graph.add_node(n.node)


# make list of edges
es = [
  FlyEdge(  19, fn_1_b.get_name(), fn_SE_SP.get_name() , pwr_to_dest=0),
  FlyEdge(  2, fn_1_b.get_name(), fn_I.get_name()   , pwr_to_dest=1),
  FlyEdge(  3, fn_TF_B.get_name(), fn_1_b.get_name() , pwr_to_dest=1),
  FlyEdge(  4, fn_0_a.get_name(), fn_TF_B.get_name() , pwr_to_dest=1),
  FlyEdge(  5, fn_TF_A.get_name(), fn_1_b.get_name() , pwr_to_dest=0),
  FlyEdge(  6, fn_0_b.get_name(), fn_TF_A.get_name() , pwr_to_dest=0),
  FlyEdge(  7, fn_1_a.get_name(), fn_R_TP20.get_name() , pwr_to_dest=1),
  FlyEdge(  8, fn_SE_ACC.get_name(), fn_0_a.get_name() , pwr_to_dest=1),
  FlyEdge(  9, fn_0_a.get_name(), fn_1_a.get_name() , pwr_to_dest=0),

  FlyEdge( 20, fn_0_b.get_name(), fn_1_a.get_name() , pwr_to_dest=1),
  FlyEdge( 21, fn_0_b.get_name(), fn_1_c.get_name() , pwr_to_dest=0),
  FlyEdge( 22, fn_1_c.get_name(), fn_R_TP30_PA.get_name() , pwr_to_dest=1),
  FlyEdge( 23, fn_1_c.get_name(), fn_SF_QPA.get_name() , pwr_to_dest=0),
  FlyEdge( 24, fn_0_b.get_name(), fn_1_d.get_name() , pwr_to_dest=0),
  FlyEdge( 25, fn_1_d.get_name(), fn_R_TP30_AT.get_name() , pwr_to_dest=0),
  FlyEdge( 26, fn_1_d.get_name(), fn_SF_QAT.get_name() , pwr_to_dest=0),

  FlyEdge( 27, fn_0_a.get_name(), fn_1_e.get_name() , pwr_to_dest=0),
  FlyEdge( 28, fn_1_e.get_name(), fn_R_TP30_PB.get_name() , pwr_to_dest=1),
  FlyEdge( 29, fn_1_e.get_name(), fn_SF_QPB.get_name() , pwr_to_dest=0),
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

for e in es:
    graph.add_edge(e.mk_edge())

graph.write_png("pretension_tfe.png") # type: ignore
#graph.write_pdf("o.pdf")

constrained_etypes = [
    "n_0",
    "n_1",
    "n_TF",
]