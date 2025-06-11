import pydot
from enum import Enum

class FLOWSIDE(Enum):
    SRC =  1 
    IDK =  0
    DEST = -1

class YNI(Enum):
    YES =  1
    IDK =  0
    NO  = -1

class NODETYPE(Enum):
    SE   = 0
    SF   = 1
    R    = 2
    I    = 3
    C    = 4
    TF   = 5
    ZERO = 6
    ONE  = 7


class FlyEdge:
    def __init__(self, label_num=0, src="", dest="", pwr_to_dest=1, flow_side=FLOWSIDE.IDK):
        self.src = src
        self.dest = dest
        self.num = label_num
        self.pwr_to_dest = pwr_to_dest
        self.flow_side = flow_side
    def mk_edge(self):
        a_h = "none"
        a_t = "none"
        if self.pwr_to_dest:
            a_h = "lnormal"
        else:
            a_t = "lnormal"
        if self.flow_side == FLOWSIDE.SRC:
            a_t = "tee" + a_t
        elif self.flow_side == FLOWSIDE.DEST:
            a_h = "tee" + a_h
        e = pydot.Edge(self.src, self.dest, label=self.num, dir="both", arrowhead=a_h, arrowtail=a_t)
        return e
    def __str__(self):
        sfstr = self.flow_side.name
        estr = f"{self.num:2d}: {self.src:10s} -> {self.dest:10s} [{self.pwr_to_dest:3d}] [{sfstr}]"
        return estr



class FlyNode:
    def __init__(self, name:str, type:NODETYPE):
        self.name = name
        self.type = type
        self.node = pydot.Node(self.name, shape="none", label=self.name)

    def get_name(self):
        return self.name

class FlyNodeSE(FlyNode):
    def __init__(self, name  ):
        super().__init__(name, NODETYPE.SE)

class FlyNodeSF(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.SF)

class FlyNodeR(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.R)

class FlyNodeI(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.I)

class FlyNodeC(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.C)

class FlyNodeTF(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.TF)

class FlyNodeZERO(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.ZERO)

class FlyNodeONE(FlyNode):
    def __init__(self, name ):
        super().__init__(name, NODETYPE.ONE)


    


def extend_causality_to_node(node_name: str, es: list[FlyEdge]):

    """
    Extend causality to connected nodes of type "0", "1", "TF"
    """

    # check if the node is a 0, 1, or TF type
    node_type = node_name.split("_")[0]

    CHK_TYPES = ["0", "1", "TF"]
    match node_type:
        case "0":
            print(f"Node {node_name} is of type 0")
            assign_causality_to_nodetype_zero(node_name, es)
        case "1":
            print(f"Node {node_name} is of type 1")
            assign_causality_to_nodetype_one(node_name, es)
        case "TF":
            print(f"Node {node_name} is of type TF")
            assign_causality_to_nodetype_tf(node_name, es)
        case _:
            print(f"Node {node_name} is of type: {node_type}, passing")

def assign_causality_to_nodetype_tf(node_name: str, es: list[FlyEdge] ):
    '''
    Assign causality to connected nodes of type "TF"
    '''

    # TF nodes are special, they only have two edges connected to them
    # if one edge brings in the flow, the other edge must take it out

    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    if len(connected_edges) != 2:
        raise ValueError(f"Node {node_name} has {len(connected_edges)} edges connected, but must have exactly 2.")

    # check if the node is a TF type
    if "TF" in node_name:
        print(f"Node {node_name} is of type TF")
        # extend causality to connected nodes
        # type "TF" nodes are special, they have only two edges connected to them
        # so one port can bring in the flow and the other port can take it out

        # check if ony one edge has e.flow_side set to FLOWSIDE.SRC or FLOWSIDE.DEST
        known_edges = [e for e in connected_edges if e.flow_side != FLOWSIDE.IDK]
        if len(known_edges) == 1:
            known_edge = known_edges[0 ] # the known edge is the one that has flow_side set to SRC or DEST
            idk_edge   = known_edges[-1] # the other edge is the one that has flow_side set to IDK
            print(f"Node {node_name} has an edge with flow_side known: {known_edge}")

            is_flow_side_src = known_edge.flow_side == FLOWSIDE.SRC
            is_node_name_in_src = node_name in known_edge.src

            if is_flow_side_src and is_node_name_in_src:
                # MODE A) the known edge is the source side, so the other edge must be the destination side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.DEST
                    print(f"Setting flow_side of edge {idk_edge.num} to DEST")
                else:
                    idk_edge.flow_side = FLOWSIDE.SRC
                    print(f"Setting flow_side of edge {idk_edge.num} to SRC")

            elif not is_flow_side_src and is_node_name_in_src:
                # MODE B) the known edge is the destination side, but the node_name is in the source side
                # this means that the node_name is in the source side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                    print(f"Setting flow_side of edge {idk_edge.num} to SRC")
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST
                    print(f"Setting flow_side of edge {idk_edge.num} to DEST")

            elif is_flow_side_src and not is_node_name_in_src:
                # MODE C) the known edge is the source side, but the node_name is not in the source side
                # this means that the node_name is in the destination side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                    print(f"Setting flow_side of edge {idk_edge.num} to SRC")
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST
                    print(f"Setting flow_side of edge {idk_edge.num} to DEST")

            elif not is_flow_side_src and not is_node_name_in_src:
                # MODE D) the known edge is the destination side, so the other edge must be the source side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.DEST
                    print(f"Setting flow_side of edge {idk_edge.num} to DEST")
                else:
                    idk_edge.flow_side = FLOWSIDE.SRC
                    print(f"Setting flow_side of edge {idk_edge.num} to SRC")
            else:
                raise ValueError(f"Node {node_name} has an unknown flow_side configuration: {known_edge.flow_side} and {idk_edge.flow_side}")




def assign_causality_to_nodetype_zero(node_name: str, es: list[FlyEdge] ):
    """
    Assign causality to connected nodes of type "0"
    """
    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    # check if the node is a 0 type
    if "0" in node_name:
        print(f"Node {node_name} is of type 0")

        # extend causality to connected nodes

        # type "0" nodes are special, they have only one strong bond
        # so only one port can bring in the effort

        # check if the node has a strong bond
        strong_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC and "0" in e.src
                        or e.flow_side == FLOWSIDE.DEST and "0" in e.dest]
        if len(strong_bonds) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(strong_bonds) == 1:
            strong_bond = strong_bonds[0]
            print(f"Node {node_name} has a strong bond: {strong_bond}")

            extension_list = []
            # extend causality to other edges connected to the node
            for e in connected_edges:
                if e.num != strong_bond.num:
                    if node_name in e.src:
                        e.flow_side = FLOWSIDE.DEST
                        extension_list.append(e.dest)
                    else:
                        e.flow_side = FLOWSIDE.SRC
                        extension_list.append(e.src)
                    print(f"Extended causality to edge: {e}")

            for ext_node in extension_list:
                extend_causality_to_node(ext_node, es)
        else:
            # No strong bond found; check for a single IDK bond
            idk_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.IDK]
            if len(idk_bonds) == 1:
                strong_bond = idk_bonds[0]
                # Assign causality: decide direction based on node_name's position
                if node_name in strong_bond.src:
                    strong_bond.flow_side = FLOWSIDE.SRC
                else:
                    strong_bond.flow_side = FLOWSIDE.DEST
                print(f"Assigned causality: Node {node_name} now has a strong bond: {strong_bond}")

                # extension_list = []
                # # extend causality to other edges connected to the node
                # for e in connected_edges:
                #     if e.num != strong_bond.num:
                #         if node_name in e.src:
                #             extension_list.append(e.dest)
                #         else:
                #             extension_list.append(e.src)
                #         print(f"Extended causality to edge: {e}")

                # for ext_node in extension_list:
                #     extend_causality_to_node(ext_node, fg)
            # else: No strong bond and not exactly one IDK bond; do nothing or log as needed.

    else:
        print(f"Node {node_name} is not of type 0, no causality assignment needed.")
        return

def assign_causality_to_nodetype_one(node_name: str, es: list[FlyEdge] ):
    """
    Assign causality to connected nodes of type "1"
    """
    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    # check if the node is a 1 type
    if "1" in node_name:
        print(f"extending causality to Node {node_name} of type 1")

        # extend causality to connected nodes

        # type "1" nodes are special, they have only one strong bond
        # so only one port can bring in the flow
        # check if the node has a strong bond
        strong_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC and "1" in e.dest
                        or e.flow_side == FLOWSIDE.DEST and "1" in e.src]
        if len(strong_bonds) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(strong_bonds) == 1:
            # non-strong bonds push flow out of node with node_name
            strong_bond = strong_bonds[0]
            print(f"Node {node_name} has a strong bond: {strong_bond}")

            extension_list = []
            # extend causality to other edges connected to the node
            for e in connected_edges:
                if e.num != strong_bond.num:
                    if node_name in e.src:
                        e.flow_side = FLOWSIDE.SRC
                        extension_list.append(e.dest)
                    else:
                        e.flow_side = FLOWSIDE.DEST
                        extension_list.append(e.src)
                    print(f"Extended causality to edge: {e}")

            for ext_node in extension_list:
                extend_causality_to_node(ext_node, es)
    else:
        print(f"Node {node_name} is not of type 0, no causality assignment needed.")
        return

def assign_se_causality(es: list[FlyEdge] ):

    # collect SE sources
    se_srcs = [e for e in es if "SE" in e.src]

    # assign required causality to SE sources
    # we are working with SE elements that are the source side of an edge
    # SE   src -> dest
    # so flow side = DEST
    for e in se_srcs:
        e.flow_side = FLOWSIDE.DEST

        print(f" [e]: {e}")

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
        

    # collect SE destinations
    se_dests = [e for e in es if "SE" in e.dest]
    # assign required causality to SE destinations

    for e in se_dests:
        e.flow_side = FLOWSIDE.SRC

        print(f" [e]: {e}")

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)


def assign_sf_causality(es: list[FlyEdge] ):


    # collect SF sources
    se_srcs = [e for e in es if "SF" in e.src]

    # assign required causality to SF sources
    # we are working with SF elements that are the source side of an edge
    # SF   src -> dest
    # so flow side = SRC
    for e in se_srcs:
        e.flow_side = FLOWSIDE.SRC

        print(f" [e]: {e}")

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
        

    # collect SF destinations
    sf_dests = [e for e in es if "SF" in e.dest]
    # assign required causality to SF destinations

    for e in sf_dests:
        e.flow_side = FLOWSIDE.DEST

        print(f" [e]: {e}")

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
    
def assign_I_causality(es: list[FlyEdge] ):


    # collect I sources
    I_source_edges = [e for e in es if "I" in e.src]

    # assign preferred (flow side) causality to I sources
    for I_edge in I_source_edges:
        I_edge.flow_side = FLOWSIDE.SRC
        print(f" [I_node]: {I_edge}")

        dest_name = I_edge.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(I_edge.dest, es)
    
    # collect I destinations
    I_dest_edges = [e for e in es if "I" in e.dest]
    # assign preferred (flow side) causality to I destinations
    for I_edge in I_dest_edges:
        I_edge.flow_side = FLOWSIDE.DEST
        print(f" [I_node]: {I_edge}")

        src_name = I_edge.src.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in src_name:
                extend_causality_to_node(I_edge.src, es)
