import unittest
from lib_bonds import *

graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

node_SF = FlyNodeSF("SF")
node_C  = FlyNodeC("C")
node_R = FlyNodeR("R")
node_I = FlyNodeI("I")
node_0 = FlyNodeZERO("0")
node_1 = FlyNodeONE("1")


# make list of edges
es = [
    FlyEdge(1, node_SF.get_name(), node_0.get_name() , pwr_to_dest=1),
    FlyEdge(2, node_C.get_name(), node_0.get_name() , pwr_to_dest=0),
    FlyEdge(3, node_0.get_name(), node_1.get_name() , pwr_to_dest=1),
    FlyEdge(4, node_1.get_name(), node_R.get_name() , pwr_to_dest=1),
    FlyEdge(5, node_1.get_name(), node_I.get_name() , pwr_to_dest=1),
]

# assign causality
assign_se_causality(es)
assign_sf_causality(es)
assign_I_causality(es)


class Test_5p4(unittest.TestCase):

    def test_SF(self):

        # get edges with SF node as a source
        edges_w_sf_src = [e for e in es if "SF" in e.src]

        # SRC [SF] ----- DEST [*]
        # Flow must come from source
        for e in edges_w_sf_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)


if __name__ == '__main__':
    unittest.main()
