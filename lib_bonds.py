import pydot
from enum import Enum
import sympy as sym

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
            assign_causality_to_nodetype_zero(node_name, es)
        case "1":
            assign_causality_to_nodetype_one(node_name, es)
        case "TF":
            assign_causality_to_nodetype_tf(node_name, es)
        case _:
            pass

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
    if "TF" in node_name.split("_")[0]:
        # extend causality to connected nodes
        # type "TF" nodes are special, they have only two edges connected to them
        # so one port can bring in the flow and the other port can take it out

        # check if ony one edge has e.flow_side set to FLOWSIDE.SRC or FLOWSIDE.DEST
        known_edges = [e for e in connected_edges if e.flow_side != FLOWSIDE.IDK]
        if len(known_edges) == 1:
            known_edge = known_edges[0] # the known edge is the one that has flow_side set to SRC or DEST
            known_edge_num = known_edge.num
            idk_edge_num = [e.num for e in connected_edges if e.num != known_edge_num][0]
            idk_edge = [e for e in connected_edges if e.num != known_edge_num][0] # the other edge is the one that has flow_side set to IDK

            # get the other node name from the idk_edge
            idk_node_name = idk_edge.dest if node_name in idk_edge.src else idk_edge.src

            is_flow_side_src = known_edge.flow_side == FLOWSIDE.SRC
            is_node_name_in_src = node_name in known_edge.src

            if is_flow_side_src and is_node_name_in_src:
                # MODE A) the known edge is the source side, so the other edge must be the destination side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.DEST
                else:
                    idk_edge.flow_side = FLOWSIDE.SRC

            elif not is_flow_side_src and is_node_name_in_src:
                # MODE B) the known edge is the destination side, but the node_name is in the source side
                # this means that the node_name is in the source side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST

            elif is_flow_side_src and not is_node_name_in_src:
                # MODE C) the known edge is the source side, but the node_name is not in the source side
                # this means that the node_name is in the destination side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST

            elif not is_flow_side_src and not is_node_name_in_src:
                # MODE D) the known edge is the destination side, so the other edge must be the source side
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.DEST
                else:
                    idk_edge.flow_side = FLOWSIDE.SRC
            else:
                raise ValueError(f"Node {node_name} has an unknown flow_side configuration: {known_edge.flow_side} and {idk_edge.flow_side}")
            
            extend_causality_to_node(idk_node_name, es)




def assign_causality_to_nodetype_zero(node_name: str, es: list[FlyEdge] ):
    """
    Assign causality to connected nodes of type "0"
    """
    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    # check if the node is a 0 type
    if "0" in node_name.split("_")[0]:

        # extend causality to connected nodes

        # type "0" nodes are special, they have only one strong bond
        # so only one port can bring in the effort

        # check if the node has a strong bond
        strong_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC and "0" in e.src.split("_")[0]
                        or e.flow_side == FLOWSIDE.DEST and "0" in e.dest.split("_")[0]]
        if len(strong_bonds) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(strong_bonds) == 1:
            strong_bond = strong_bonds[0]

            extension_list = []
            # extend causality to other edges connected to the node
            for e in connected_edges:
                if e.num != strong_bond.num and e.flow_side == FLOWSIDE.IDK:
                    if node_name in e.src:
                        e.flow_side = FLOWSIDE.DEST
                        extension_list.append(e.dest)
                    else:
                        e.flow_side = FLOWSIDE.SRC
                        extension_list.append(e.src)

            for ext_node in extension_list:
                node_type = ext_node.split("_")[0]
                if node_type in ["0", "1", "TF"]:
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


    else:
        return

def assign_causality_to_nodetype_one(node_name: str, es: list[FlyEdge] ):
    """
    Assign causality to connected nodes of type "1"
    """
    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    # check if the node is a 1 type
    if "1" in node_name.split("_")[0]:

        # extend causality to connected nodes

        # type "1" nodes are special, they have only one strong bond
        # so only one port can bring in the flow
        # check if the node has a strong bond
        strong_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC and "1" in e.dest.split("_")[0]
                        or e.flow_side == FLOWSIDE.DEST and "1" in e.src.split("_")[0]]
        if len(strong_bonds) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(strong_bonds) == 1:
            # non-strong bonds push flow out of node with node_name
            strong_bond = strong_bonds[0]

            extension_list = []
            # extend causality to other edges connected to the node
            for e in connected_edges:
                if e.num != strong_bond.num and (e.flow_side == FLOWSIDE.IDK):
                    if node_name in e.src:
                        e.flow_side = FLOWSIDE.SRC
                        extension_list.append(e.dest)
                    else:
                        e.flow_side = FLOWSIDE.DEST
                        extension_list.append(e.src)

            for ext_node in extension_list:
                node_type = ext_node.split("_")[0]
                if node_type in ["0", "1", "TF"]:
                    extend_causality_to_node(ext_node, es)
        else:
            # No strong bond found; check for a single IDK bond
            idk_bonds = [e for e in connected_edges if e.flow_side == FLOWSIDE.IDK]
            if len(idk_bonds) == 1:
                strong_bond = idk_bonds[0]
                # Assign causality: decide direction based on node_name's position
                if node_name in strong_bond.src:
                    strong_bond.flow_side = FLOWSIDE.DEST
                else:
                    strong_bond.flow_side = FLOWSIDE.SRC

    else:
        return

def assign_se_causality(es: list[FlyEdge] ):

    # collect SE sources
    se_srcs = [e for e in es if "SE" in e.src.split("_")[0]]

    # assign required causality to SE sources
    # we are working with SE elements that are the source side of an edge
    # SE   src -> dest
    # so flow side = DEST
    for e in se_srcs:
        e.flow_side = FLOWSIDE.DEST

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
        

    # collect SE destinations
    se_dests = [e for e in es if "SE" in e.dest.split("_")[0]]
    # assign required causality to SE destinations

    for e in se_dests:
        e.flow_side = FLOWSIDE.SRC

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)


def assign_sf_causality(es: list[FlyEdge] ):


    # collect SF sources
    sf_srcs = [e for e in es if "SF" in e.src.split("_")[0]]

    # assign required causality to SF sources
    # we are working with SF elements that are the source side of an edge
    # SF   src -> dest
    # so flow side = SRC
    for e in sf_srcs:
        e.flow_side = FLOWSIDE.SRC

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
        

    # collect SF destinations
    sf_dests = [e for e in es if "SF" in e.dest.split("_")[0]]
    # assign required causality to SF destinations

    for e in sf_dests:
        e.flow_side = FLOWSIDE.DEST

        dest_name = e.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(e.dest, es)
    
def assign_I_causality(es: list[FlyEdge] ):


    # collect I sources
    I_source_edges = [e for e in es if "I" in e.src.split("_")[0]]

    # assign preferred (flow side) causality to I sources
    for I_edge in I_source_edges:
        I_edge.flow_side = FLOWSIDE.SRC

        dest_name = I_edge.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(I_edge.dest, es)
    
    # collect I destinations
    I_dest_edges = [e for e in es if "I" in e.dest.split("_")[0]]
    # assign preferred (flow side) causality to I destinations
    for I_edge in I_dest_edges:
        I_edge.flow_side = FLOWSIDE.DEST

        src_name = I_edge.src.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in src_name:
                extend_causality_to_node(I_edge.src, es)

def assign_C_causality(es: list[FlyEdge] ):

    # collect C sources
    C_source_edges = [e for e in es if "C" in e.src.split("_")[0]]

    # assign preferred (non-flow side) causality to C sources
    for C_edge in C_source_edges:
        C_edge.flow_side = FLOWSIDE.DEST

        dest_name = C_edge.dest.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in dest_name:
                extend_causality_to_node(C_edge.dest, es)
    
    # collect C destinations
    C_dest_edges = [e for e in es if "C" in e.dest.split("_")[0]]
    # assign preferred (non-flow side) causality to C destinations
    for C_edge in C_dest_edges:
        C_edge.flow_side = FLOWSIDE.SRC

        src_name = C_edge.src.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in src_name:
                extend_causality_to_node(C_edge.src, es)

def assign_causality_to_all_nodes(es: list[FlyEdge], report: bool = True):

    assign_se_causality(es)
    assign_sf_causality(es)
    assign_I_causality(es)
    assign_C_causality(es)

    # all edges should now have their flow_side set
    if report:
        any_flow_side_idk = any(e.flow_side == FLOWSIDE.IDK for e in es)
        if any_flow_side_idk:
            print("Some edges still have flow_side set to IDK, which is not great.")
        else:
            print("All edges have their flow_side set correctly.")


def generate_symbols_for_SF(es: list[FlyEdge] ) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for SF elements 
    This function will create symbols like SF_01, SF_02, ..., SF_99
    """
    equations = []
    new_symbols = []

    # get list of source of flow symbols
    sf_nums = [e.num for e in es if 
            "SF" in e.src.split("_")[0] or
            "SF" in e.dest.split("_")[0]]

    # equate the generic names to the unique names
    for sf_num in sf_nums:

        # create symbol SF_nn, then equate f_nn = SF_nn
        unique_f_sym = sym.Symbol(f"SF_{sf_num:02d}", real=True)
        generic_f_sym = sym.Symbol(f"f_{sf_num:02d}", real=True)
        new_symbols.append(unique_f_sym)

        eq = sym.Eq(generic_f_sym, unique_f_sym)
        equations.append(eq)

    return equations, new_symbols

def generate_symbols_for_SE(es: list[FlyEdge]) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for SE elements
    This function will create symbols like SE_01, SE_02, ..., SE_99
    """
    # equation list
    equations = []
    new_symbols = []

    # get list of source of effort symbols
    se_nums = [e.num for e in es if 
            "SE" in e.src.split("_")[0] or
            "SE" in e.dest.split("_")[0]]

    # equate the generic names to the unique names
    for se_num in se_nums:

        # create symbol SE_nn, then equate e_nn = SE_nn
        unique_e_sym = sym.Symbol(f"SE_{se_num:02d}", real=True)
        generic_e_sym = sym.Symbol(f"e_{se_num:02d}", real=True)
        new_symbols.append(unique_e_sym)

        eq = sym.Eq(generic_e_sym, unique_e_sym)
        equations.append(eq)

    return equations, new_symbols

def generate_symbols_for_I(es: list[FlyEdge] ) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for I elements
    This function will create symbols like I_01, I_02, ..., I_99
    """
    # equation list
    equations = []
    new_symbols = []

    # get list of I symbols
    I_nums = [e.num for e in es if 
            "I" in e.src.split("_")[0] or
            "I" in e.dest.split("_")[0]]

    # create symbol [I,p]_nn, then generate equation
    for i_num in I_nums:

        I_nn = sym.Symbol(f"I_{i_num:02d}", real=True)
        p_nn = sym.Symbol(f"p_{i_num:02d}", real=True)
        f_nn = sym.Symbol(f"f_{i_num:02d}", real=True)

        new_symbols.append(I_nn)
        new_symbols.append(p_nn)
        new_symbols.append(f_nn)

        # equation is always f_nn = p_nn / I_nn
        eq = sym.Eq(f_nn, p_nn / I_nn) # type: ignore
        equations.append(eq)

    return equations, new_symbols

def generate_symbols_for_C(es: list[FlyEdge] ) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for C elements
    This function will create symbols like C_01, C_02, ..., C_99
    """
    # equation list
    equations = []
    new_symbols = []

    # get list of C symbols
    C_nums = [e.num for e in es if 
            "C" in e.src.split("_")[0] or
            "C" in e.dest.split("_")[0]]

    # create symbol [C,q]_nn, then generate equation
    for c_num in C_nums:

        C_nn = sym.Symbol(f"C_{c_num:02d}", real=True)
        q_nn = sym.Symbol(f"q_{c_num:02d}", real=True)
        e_nn = sym.Symbol(f"e_{c_num:02d}", real=True)

        new_symbols.append(C_nn)
        new_symbols.append(q_nn)
        new_symbols.append(e_nn)

        # equation is always e_nn = q_nn / C_nn
        eq = sym.Eq(e_nn, q_nn / C_nn) # type: ignore
        equations.append(eq)

    return equations, new_symbols

def generate_symbols_for_R(es: list[FlyEdge]) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for R elements
    This function will create symbols like R_01, R_02, ..., R_99
    """
    # equation list
    equations = []
    new_symbols = []

    for e in es:

        is_R_element = "R" in e.src.split("_")[0] or "R" in e.dest.split("_")[0]

        if is_R_element:
            # this edge has an R element

            is_R_on_src = "R" in e.src.split("_")[0]

            r_num = e.num
            R_nn = sym.Symbol(f"R_{r_num:02d}", real=True)
            e_nn = sym.Symbol(f"e_{r_num:02d}", real=True)
            f_nn = sym.Symbol(f"f_{r_num:02d}", real=True)

            new_symbols.append(R_nn)
            new_symbols.append(e_nn)
            new_symbols.append(f_nn)

            if is_R_on_src:
                if e.flow_side == FLOWSIDE.SRC:
                    # this element provides the flow
                    # f_nn = e_nn / R_nn
                    eq = sym.Eq(f_nn, e_nn / R_nn) # type: ignore
                    equations.append(eq)
                else:
                    # this element consumes the flow
                    # e_nn = f_nn * R_nn
                    eq = sym.Eq(e_nn, f_nn * R_nn) # type: ignore
                    equations.append(eq)
            else: 
                # R is on the destination side
                if e.flow_side == FLOWSIDE.SRC:
                    # this element consumes the flow
                    # e_nn = f_nn * R_nn
                    eq = sym.Eq(e_nn, f_nn * R_nn) # type: ignore
                    equations.append(eq)
                else:
                    # this element provides the flow
                    # f_nn = e_nn / R_nn
                    eq = sym.Eq(f_nn, e_nn / R_nn) # type: ignore
                    equations.append(eq)

    return equations, new_symbols

def generate_symbols_for_TF(es: list[FlyEdge]) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for TF elements
    This function will create symbols like TF_01, TF_02, ..., TF_99
    """
    # equation list
    equations = []
    new_symbols = []

    # create a map from TF_name nodes to tuple of (edge_1, edge_2) pairs
    tf_name_map = {}

    for e in es:
        is_TF_element = "TF" in e.src.split("_")[0] or "TF" in e.dest.split("_")[0]

        if is_TF_element:
            # this edge has a TF element
            tf_name = e.src if "TF" in e.src.split("_")[0] else e.dest

            if tf_name not in tf_name_map:
                tf_name_map[tf_name] = []

            tf_name_map[tf_name].append(e)

    # create symbols for each TF element
    for tf_name, edges in tf_name_map.items():

        assert len(edges) == 2, f"TF element {tf_name} must have exactly 2 edges connected to it, found {len(edges)}."

        new_symbols.append(tf_name)

        # deterine which edge has power flowing to the TF element
        edge_a = edges[0]
        edge_b = edges[1]

        # assume edge_b is the first edge
        edge_1 = edge_b
        edge_2 = edge_a

        if (edge_a.pwr_to_dest and tf_name in edge_a.dest) or (not edge_a.pwr_to_dest and tf_name in edge_a.src):
            # edge_a is the first edge
            edge_1 = edge_a
            edge_2 = edge_b

        e_1_nn = sym.Symbol(f"e_{edge_1.num:02d}", real=True)
        e_2_nn = sym.Symbol(f"e_{edge_2.num:02d}", real=True)
        f_1_nn = sym.Symbol(f"f_{edge_1.num:02d}", real=True)
        f_2_nn = sym.Symbol(f"f_{edge_2.num:02d}", real=True)
        new_symbols.extend([e_1_nn, e_2_nn, f_1_nn, f_2_nn])

        # create equations for the TF element
        eq_1 = sym.Eq(e_1_nn, tf_name * e_2_nn)  # e_1 = TF_name * e_2
        eq_2 = sym.Eq(f_2_nn, tf_name * f_1_nn)  # f_2 = TF_name * f_1
        equations.extend([eq_1, eq_2])

    return equations, new_symbols

def generate_symbols_for_one_junctions(es: list[FlyEdge]) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate unique symbols for one junctions
    This function will create symbols like e_01, e_02, ..., e_99
    1-junctions are special cases where the flow for all edges is equal to the flow of the strong edge
    and the efforts are summed up to equal zero.
    """
    equations = []
    new_symbols = []
    KEY_NODE = "1"

    # get list of edges with one node as a one-junction
    one_junction_edges = [e for e in es if KEY_NODE in e.src.split("_")[0] or KEY_NODE in e.dest.split("_")[0]]

    # create a map from J1_name nodes to list of edges, (edge_1, edge_2, ...)
    one_junction_name_map = {}
    for e in one_junction_edges:
        j_name = e.src if KEY_NODE in e.src.split("_")[0] else e.dest
        if j_name not in one_junction_name_map:
            one_junction_name_map[j_name] = []
        one_junction_name_map[j_name].append(e)

    # create symbols for each one-junction
    for j_name, edges in one_junction_name_map.items():

        assert len(edges) > 1, f"One-junction {j_name} must have at least 2 edges connected to it, found {len(edges)}."

        strong_bonds = [e for e in edges if e.flow_side == FLOWSIDE.SRC and KEY_NODE in e.dest.split("_")[0]
                        or e.flow_side == FLOWSIDE.DEST and KEY_NODE in e.src.split("_")[0]]

        if len(strong_bonds) > 1:
            raise ValueError(f"Node {j_name} has more than one strong bond, which is not allowed.")

        elif len(strong_bonds) == 1:
            # non-strong bonds push flow out of node with j_name
            strong_bond = strong_bonds[0]
            strong_bond_num = strong_bond.num

            # define the strong bond flow and effort symbols
            f_strong = sym.Symbol(f"f_{strong_bond_num:02d}", real=True)
            e_strong = sym.Symbol(f"e_{strong_bond_num:02d}", real=True)

            # deal with flow symbols
            for e in edges:

                # create symbols for the flow
                f_nn = sym.Symbol(f"f_{e.num:02d}", real=True)
                new_symbols.append(f_nn)

                # create flow equations for the one-junction
                eq_f = sym.Eq(f_strong, f_nn)  # f_strong = f_nn
                equations.append(eq_f)

            effort_strs = []

            # deal with effort symbols
            for e in edges:
                # create symbols for the effort
                e_nn = sym.Symbol(f"e_{e.num:02d}", real=True)
                new_symbols.append(e_nn)

                # determine if power is flowing into the one-junction from this edge
                is_power_to_this_one_junction = e.pwr_to_dest and e.dest == j_name or not e.pwr_to_dest and e.src == j_name
                if is_power_to_this_one_junction:
                    # this edge is bringing power to the one-junction
                    # so we add the effort to the list of efforts
                    effort_strs.append(f"+{e_nn}")
                else:
                    # this edge is taking power from the one-junction
                    # so we subtract the effort from the list of efforts
                    effort_strs.append(f"-{e_nn}")
            
            effort_str = "".join(effort_strs)
            if effort_str:
                # create effort equations for the one-junction
                eq_e = sym.Eq(sym.sympify(effort_str), 0)
                equations.append(eq_e)

    return equations, new_symbols

def generate_equations_for_I_storage_elements(es: list[FlyEdge] ) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate equations for storage elements I
    """

    equations = []
    new_symbols = []

    for e in es:
        is_I_storage_element = "I" in e.src.split("_")[0] or "I" in e.dest.split("_")[0]

        if is_I_storage_element:
            # this edge has an I storage element
            i_num = e.num
            pdot_nn = sym.Symbol(f"pdot_{i_num:02d}", real=True)
            e_nn = sym.Symbol(f"e_{i_num:02d}", real=True)

            new_symbols.extend([pdot_nn, e_nn])

            # create equations for the storage element
            # pdot_nn = e_nn
            eq_1 = sym.Eq(pdot_nn , e_nn) # type: ignore 
            equations.append(eq_1)

    return equations, new_symbols

def generate_equations_for_C_storage_elements(es: list[FlyEdge] ) -> tuple[list[sym.Eq], list[sym.Symbol]]:
    """
    Generate equations for storage elements C
    """

    equations = []
    new_symbols = []

    for e in es:
        is_C_storage_element = "C" in e.src.split("_")[0] or "C" in e.dest.split("_")[0]

        if is_C_storage_element:
            # this edge has an C storage element
            i_num = e.num
            qdot_nn = sym.Symbol(f"qdot_{i_num:02d}", real=True)
            f_nn = sym.Symbol(f"f_{i_num:02d}", real=True)

            new_symbols.extend([qdot_nn, f_nn])

            # create equations for the storage element
            # qdot_nn = f_nn
            eq_1 = sym.Eq(qdot_nn , f_nn) # type: ignore 
            equations.append(eq_1)

    return equations, new_symbols

def generate_symbols(es: list[FlyEdge]) -> None:
    """
    Generate symbols for the bonds
    """
    sym.init_printing(use_unicode=True)

    equations = []
    symbols = []

    # pull out the numbers from the edges
    nums = [e.num for e in es]

    # generate symbols for f and e
    # f_01, f_02, ..., f_99
    # e_01, e_02, ..., e_99
    f_symbols = [sym.Symbol(f"f_{num:02d}", real=True) for num in nums]
    e_symbols = [sym.Symbol(f"e_{num:02d}", real=True) for num in nums]
    symbols.extend(f_symbols)
    symbols.extend(e_symbols)

    new_eqs, new_symbols = generate_symbols_for_SF(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_SE(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_I(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_C(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_R(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_TF(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_equations_for_I_storage_elements(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_equations_for_C_storage_elements(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    new_eqs, new_symbols = generate_symbols_for_one_junctions(es)
    equations.extend(new_eqs)
    symbols.extend(new_symbols)

    # print all equations
    print("\nEquations:")
    for eq in equations:
        sym.pprint(eq)
        print(eq)