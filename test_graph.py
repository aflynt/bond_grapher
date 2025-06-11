import unittest
from lib_bonds import *






class Test_5p4(unittest.TestCase):

    def setUp(self) -> None:
        # This method is called before each test
        # It can be used to set up any state you want to share across tests

        self.es = [
            FlyEdge(1, "SF","0" , pwr_to_dest=1),
            FlyEdge(2, "C", "0" , pwr_to_dest=0),
            FlyEdge(3, "0", "1" , pwr_to_dest=1),
            FlyEdge(4, "1", "R" , pwr_to_dest=1),
            FlyEdge(5, "1", "I" , pwr_to_dest=1),
        ]

        assign_causality_to_all_nodes(self.es)


    def test_SF(self):

        # get edges with SF node as a source
        edges_w_sf_src = [e for e in self.es if "SF" in e.src]

        # SRC [SF] |--- DEST [*]
        # Flow must come from source
        for e in edges_w_sf_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

        # get edges with SF node as a destination
        edges_w_sf_dest = [e for e in self.es if "SF" in e.dest]

        # DEST [SF] |--- SRC [*]
        # Flow must come from destination
        for e in edges_w_sf_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

    def test_I(self):

        # get edges with I node as a source
        edges_w_I_src = [e for e in self.es if "I" in e.src]

        # SRC [I] |--- DEST [*]
        # Flow must (should) come from source
        for e in edges_w_I_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

        # get edges with I node as a destination
        edges_w_I_dest = [e for e in self.es if "I" in e.dest]

        # DEST [I] |--- SRC [*]
        # Flow must (should) come from destination
        for e in edges_w_I_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

    def test_C(self):

        # get edges with C node as a source
        edges_w_C_src = [e for e in self.es if "C" in e.src]

        # SRC [C] ---| DEST [*]
        # Flow must (should) come from destination
        for e in edges_w_C_src:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

        # get edges with C node as a destination
        edges_w_C_dest = [e for e in self.es if "C" in e.dest]

        # DEST [C] ---| SRC [*]
        # Flow must (should) come from source
        for e in edges_w_C_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

class Test_5p5(unittest.TestCase):

    def setUp(self) -> None:
        # This method is called before each test
        # It can be used to set up any state you want to share across tests

        n_SE_a = "SE_a"
        n_SE_b = "SE_b"
        n_SE_c = "SE_c"
        n_I_a = "I_a"
        n_I_b = "I_b"
        n_I_c = "I_c"
        n_R_a = "R_a"
        n_R_b = "R_b"
        n_R_c = "R_c"
        n_1_a = "1_a"
        n_1_b = "1_b"
        n_1_c = "1_c"
        n_0 = "0"
        n_C = "C"

        self.ns = [
           pydot.Node(n_SE_a, shape="none", label=n_SE_a),
           pydot.Node(n_SE_b, shape="none", label=n_SE_b),
           pydot.Node(n_SE_c, shape="none", label=n_SE_c),
           pydot.Node(n_I_a, shape="none", label=n_I_a),
           pydot.Node(n_I_b, shape="none", label=n_I_b),
           pydot.Node(n_I_c, shape="none", label=n_I_c),
           pydot.Node(n_R_a, shape="none", label=n_R_a),
           pydot.Node(n_R_b, shape="none", label=n_R_b),
           pydot.Node(n_R_c, shape="none", label=n_R_c),
           pydot.Node(n_1_a, shape="none", label=n_1_a),
           pydot.Node(n_1_b, shape="none", label=n_1_b),
           pydot.Node(n_1_c, shape="none", label=n_1_c),
           pydot.Node(n_0, shape="none", label=n_0),
           pydot.Node(n_C, shape="none", label=n_C),
        ]

        self.es = [
            FlyEdge(1, n_SE_a,n_1_a , pwr_to_dest=1),
            FlyEdge(2, n_SE_b, n_1_b , pwr_to_dest=0),
            FlyEdge(3, n_1_c, n_SE_c , pwr_to_dest=1),
            FlyEdge(4, n_I_a, n_1_a , pwr_to_dest=1),
            FlyEdge(5, n_1_b, n_I_b , pwr_to_dest=1),
            FlyEdge(6, n_1_c, n_I_c , pwr_to_dest=1),
            FlyEdge(7, n_1_a, n_R_a , pwr_to_dest=1),
            FlyEdge(8, n_1_b, n_R_b , pwr_to_dest=1),
            FlyEdge(9, n_1_c, n_R_c , pwr_to_dest=1),
            FlyEdge(10, n_0, n_C , pwr_to_dest=1),
            FlyEdge(11, n_1_a, n_0 , pwr_to_dest=1),
            FlyEdge(12, n_1_b, n_0 , pwr_to_dest=1),
            FlyEdge(13, n_0, n_1_c , pwr_to_dest=1),
        ]

        assign_causality_to_all_nodes(self.es)

        graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")
        for n in self.ns:
            graph.add_node(n)
        for e in self.es:
            graph.add_edge(e.mk_edge())

        graph.write_png("my_graph.png") # type: ignore

    def test_SF(self):

        # get edges with SF node as a source
        edges_w_sf_src = [e for e in self.es if "SF" in e.src]

        # SRC [SF] |--- DEST [*]
        # Flow must come from source
        for e in edges_w_sf_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

        # get edges with SF node as a destination
        edges_w_sf_dest = [e for e in self.es if "SF" in e.dest]

        # DEST [SF] |--- SRC [*]
        # Flow must come from destination
        for e in edges_w_sf_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

    def test_I(self):

        # get edges with I node as a source
        edges_w_I_src = [e for e in self.es if "I" in e.src]

        # SRC [I] |--- DEST [*]
        # Flow must (should) come from source
        for e in edges_w_I_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

        # get edges with I node as a destination
        edges_w_I_dest = [e for e in self.es if "I" in e.dest]

        # DEST [I] |--- SRC [*]
        # Flow must (should) come from destination
        for e in edges_w_I_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

    def test_C(self):

        # get edges with C node as a source
        edges_w_C_src = [e for e in self.es if "C" in e.src]

        # SRC [C] ---| DEST [*]
        # Flow must (should) come from destination
        for e in edges_w_C_src:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

        # get edges with C node as a destination
        edges_w_C_dest = [e for e in self.es if "C" in e.dest]

        # DEST [C] ---| SRC [*]
        # Flow must (should) come from source
        for e in edges_w_C_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

class Test_5p6(unittest.TestCase):

    def setUp(self) -> None:
        # This method is called before each test
        # It can be used to set up any state you want to share across tests

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

        self.ns = [
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

        self.edge_list = [
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

        self.es = []

        for edge in self.edge_list:
            edge_id, src, dest, pwr_to_dest = edge
            self.es.append(FlyEdge(edge_id, src, dest, pwr_to_dest=pwr_to_dest))


        assign_causality_to_all_nodes(self.es)

        graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")
        for n in self.ns:
            graph.add_node(n)
        for e in self.es:
            graph.add_edge(e.mk_edge())

        graph.write_png("my_graph.png") # type: ignore

    def test_SE(self):

        # get edges with SE node as a source
        edges_w_sf_src = [e for e in self.es if "SE" in e.src]

        # SRC [SE] ---| DEST [*]
        # Flow must come from DEST
        for e in edges_w_sf_src:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

        # get edges with SE node as a destination
        edges_w_sf_dest = [e for e in self.es if "SE" in e.dest]

        # DEST [SE] ---| SRC [*]
        # Flow must come from SRC
        for e in edges_w_sf_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

    def test_I(self):

        # get edges with I node as a source
        edges_w_I_src = [e for e in self.es if "I" in e.src]

        # SRC [I] |--- DEST [*]
        # Flow must (should) come from source
        for e in edges_w_I_src:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)

        # get edges with I node as a destination
        edges_w_I_dest = [e for e in self.es if "I" in e.dest]

        # DEST [I] |--- SRC [*]
        # Flow must (should) come from destination
        for e in edges_w_I_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

    def test_C(self):

        # get edges with C node as a source
        edges_w_C_src = [e for e in self.es if "C" in e.src]

        # SRC [C] ---| DEST [*]
        # Flow must (should) come from destination
        for e in edges_w_C_src:
            self.assertEqual(e.flow_side, FLOWSIDE.DEST)

        # get edges with C node as a destination
        edges_w_C_dest = [e for e in self.es if "C" in e.dest]

        # DEST [C] ---| SRC [*]
        # Flow must (should) come from source
        for e in edges_w_C_dest:
            self.assertEqual(e.flow_side, FLOWSIDE.SRC)
if __name__ == '__main__':
    unittest.main()
