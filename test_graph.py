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

        assign_se_causality(self.es)
        assign_sf_causality(self.es)
        assign_I_causality(self.es)


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


if __name__ == '__main__':
    unittest.main()
