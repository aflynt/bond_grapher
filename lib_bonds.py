import pydot
from enum import Enum
import sympy as sym
import json

class FLOWSIDE(Enum):
    SRC =  1 
    IDK =  0
    DEST = -1



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





class SymbolManager:
    def __init__(self):
        self.symbols = {}

    def get_symbol(self, name: str) -> sym.Symbol:
        """
        Get a symbol by name, creating it if it doesn't exist.
        """
        if name not in self.symbols:
            self.symbols[name] = sym.Symbol(name, real=True)
        return self.symbols[name]
    
    def add_symbol(self, name: str) -> sym.Symbol:
        """
        Add a new symbol by name, creating it if it doesn't exist.
        """
        if name not in self.symbols:
            self.symbols[name] = sym.Symbol(name, real=True)
        return self.symbols[name]

def load_json_graph(fname) -> tuple[list[str], list[FlyEdge]]:

    with open(fname, 'r') as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    ns = []
    for node in nodes:
        label = node.get("label", "")
        ns.append(label)

    ns = list(set(ns))  # Remove duplicates

    # create edge list
    es = []

    for edge in edges:
        num = int(edge.get("label", 0))
        start_node_id = 0
        end_node_id = 0

        start_node_id = edge["startNodeId"] if "startNodeId" in edge else 0
        end_node_id = edge["endNodeId"] if "endNodeId" in edge else 0

        start_node_name = "IDK"
        for node in nodes:
            if node.get("id", 0) == start_node_id:
                start_node_name = node.get("label", "")

        end_node_name = "IDK"
        for node in nodes:
            if node.get("id", 0) == end_node_id:
                end_node_name = node.get("label", "")

        es.append(FlyEdge(label_num=num, src=start_node_name, dest=end_node_name, pwr_to_dest=1, flow_side=FLOWSIDE.IDK))

    return ns, es

    


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
        case "GY":
            assign_causality_to_nodetype_gy(node_name, es)
        case _:
            pass

def assign_causality_to_nodetype_tf(node_name: str, es: list[FlyEdge] ):
    '''
    Assign causality to connected nodes of type "TF"
    '''
    NODE_ID = "TF"

    # TF nodes are special, they only have two edges connected to them
    # if one edge brings in the flow, the other edge must take it out

    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    if len(connected_edges) != 2:
        raise ValueError(f"Node {node_name} has {len(connected_edges)} edges connected, but must have exactly 2.")

    # check if the node is a TF type
    if NODE_ID in node_name.split("_")[0]:
        # extend causality to connected nodes

        # check if only one edge has e.flow_side set to FLOWSIDE.SRC or FLOWSIDE.DEST
        known_edges = [e for e in connected_edges if e.flow_side != FLOWSIDE.IDK]
        if len(known_edges) == 1:
            known_edge = known_edges[0] # the known edge is the one that has flow_side set to SRC or DEST
            idk_edge = [e for e in connected_edges if e.num != known_edge.num][0] # the other edge is the one that has flow_side set to IDK

            # get the other node name from the idk_edge
            idk_node_name = idk_edge.dest if node_name in idk_edge.src else idk_edge.src

            is_flow_side_src = known_edge.flow_side == FLOWSIDE.SRC
            is_node_name_in_src = node_name in known_edge.src

            if (    is_flow_side_src and     is_node_name_in_src) or \
               (not is_flow_side_src and not is_node_name_in_src):
                # this edge brings in the effort, the other edge must take out the effort
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.DEST
                else:
                    idk_edge.flow_side = FLOWSIDE.SRC

            elif (not is_flow_side_src and     is_node_name_in_src) or \
                 (    is_flow_side_src and not is_node_name_in_src):
                # this edge brings in the flow, the other edge must take out the flow
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST

            else:
                raise ValueError(f"Node {node_name} has an unknown flow_side configuration: {known_edge.flow_side} and {idk_edge.flow_side}")
            
            extend_causality_to_node(idk_node_name, es)

def assign_causality_to_nodetype_gy(node_name: str, es: list[FlyEdge] ):
    '''
    Assign causality to connected nodes of type "GY"
    '''
    NODE_ID = "GY"

    # GY nodes are special, they only have two edges connected to them
    # if one edge brings in the flow, the other edge must take it out

    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

    if len(connected_edges) != 2:
        raise ValueError(f"Node {node_name} has {len(connected_edges)} edges connected, but must have exactly 2.")

    # check if the node is a GY type
    if NODE_ID in node_name.split("_")[0]:
        # extend causality to connected nodes
        # type "GY" nodes are special, they have only two edges connected to them
        # so one port can bring in the flow and the other port can take it out

        # check if ony one edge has e.flow_side set to FLOWSIDE.SRC or FLOWSIDE.DEST
        known_edges = [e for e in connected_edges if e.flow_side != FLOWSIDE.IDK]
        if len(known_edges) == 1:
            known_edge = known_edges[0] # the known edge is the one that has flow_side set to SRC or DEST
            idk_edge = [e for e in connected_edges if e.num != known_edge.num][0] # the other edge is the one that has flow_side set to IDK

            # get the other node name from the idk_edge
            idk_node_name = idk_edge.dest if node_name in idk_edge.src else idk_edge.src

            is_flow_side_src = known_edge.flow_side == FLOWSIDE.SRC
            is_node_name_in_src = node_name in known_edge.src

            if  (    is_flow_side_src and     is_node_name_in_src) or \
                (not is_flow_side_src and not is_node_name_in_src):
                # MODE A) known_edge brings in the effort, other edge must take out the flow
                # MODE D) known_edge brings in the effort, other edge must take out the flow
                if node_name in idk_edge.src:
                    idk_edge.flow_side = FLOWSIDE.SRC
                else:
                    idk_edge.flow_side = FLOWSIDE.DEST

            elif (not is_flow_side_src and     is_node_name_in_src) or \
                 (    is_flow_side_src and not is_node_name_in_src):
                # MODE B) the known edge brings in flow, other edge must take out effort
                # MODE C) the known edge brings in flow, other edge must take out effort
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

    NODE_ID = "0"

    def extend_to_connections(node_name: str, strong_bond: FlyEdge, es: list[FlyEdge], extension_list: list[str] = []):
        
        connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

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

    # check if the node is a 0 type
    if NODE_ID in node_name.split("_")[0]:

        # extend causality to connected nodes

        # type "0" nodes are special, they have only one strong bond
        # so only one port can bring in the effort

        # check if the node has a strong bond
        zero_strong_bond = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC  and node_name in e.src
                                         or e.flow_side == FLOWSIDE.DEST and node_name in e.dest]
        if len(zero_strong_bond) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(zero_strong_bond) == 1:
            strong_bond = zero_strong_bond[0]

            extend_to_connections(node_name, strong_bond, es, extension_list=[])

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

                extension_list = [strong_bond.dest if node_name in strong_bond.src else strong_bond.src]
                extend_to_connections(node_name, strong_bond, es, extension_list=extension_list)


    else:
        return

def assign_causality_to_nodetype_one(node_name: str, es: list[FlyEdge] ):
    """
    Assign causality to connected nodes of type "1"
    """
    # collect edges connected to the node
    connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]
    NODE_ID = "1"

    def extend_to_connections(node_name: str, strong_bond: FlyEdge, es: list[FlyEdge], extension_list: list[str] = []):

        connected_edges = [e for e in es if node_name in e.src or node_name in e.dest]

        for e in connected_edges:
            if e.num != strong_bond.num and e.flow_side == FLOWSIDE.IDK:
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

    # check if the node is a 1 type
    if NODE_ID in node_name.split("_")[0]:

        # extend causality to connected nodes

        # type "1" nodes are special, they have only one strong bond
        # so only one port can bring in the flow
        # check if the node has a strong bond
        one_strong_bond = [e for e in connected_edges if e.flow_side == FLOWSIDE.SRC  and node_name in e.dest
                                 or e.flow_side == FLOWSIDE.DEST and node_name in e.src]
        if len(one_strong_bond) > 1:
            raise ValueError(f"Node {node_name} has more than one strong bond, which is not allowed.")

        elif len(one_strong_bond) == 1:
            # non-strong bonds push flow out of node with node_name
            strong_bond = one_strong_bond[0]

            extend_to_connections(node_name, strong_bond, es, extension_list=[])

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

                extension_list = [strong_bond.dest if node_name in strong_bond.src else strong_bond.src]
                extend_to_connections(node_name, strong_bond, es, extension_list=extension_list)

    else:
        return

def assign_se_causality(es: list[FlyEdge] ):

    NODE_ID = "SE"

    # collect SE sources
    se_srcs = [e for e in es if NODE_ID in e.src.split("_")[0]]

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
    se_dests = [e for e in es if NODE_ID in e.dest.split("_")[0]]
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

    NODE_ID = "SF"

    # collect SF sources
    sf_srcs = [e for e in es if NODE_ID in e.src.split("_")[0]]

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
    sf_dests = [e for e in es if NODE_ID in e.dest.split("_")[0]]
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

    NODE_ID = "I"


    # collect I sources
    I_source_edges = [e for e in es if NODE_ID in e.src.split("_")[0]]

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
    I_dest_edges = [e for e in es if NODE_ID in e.dest.split("_")[0]]
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

    NODE_ID = "C"

    # collect C sources
    C_source_edges = [e for e in es if NODE_ID in e.src.split("_")[0]]

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
    C_dest_edges = [e for e in es if NODE_ID in e.dest.split("_")[0]]
    # assign preferred (non-flow side) causality to C destinations
    for C_edge in C_dest_edges:
        C_edge.flow_side = FLOWSIDE.SRC

        src_name = C_edge.src.split("_")[0]

        CHK_TYPES = ["0", "1", "TF"]

        # Extend causality to connected nodes of type "0", "1", "TF"
        for CT in CHK_TYPES:
            if CT in src_name:
                extend_causality_to_node(C_edge.src, es)

def assign_R_causality(es: list[FlyEdge]):

    NODE_ID = "R"

    # collect R source nodes on edges
    R_src_edges = [e for e in es if NODE_ID in e.src.split("_")[0] ]

    # assign arbitrary causality to R elements
    for R_edge in R_src_edges:
        if R_edge.flow_side == FLOWSIDE.IDK:
            R_edge.flow_side = FLOWSIDE.SRC

            dest_name = R_edge.dest.split("_")[0]

            CHK_TYPES = ["0", "1", "TF"]

            # Extend causality to connected nodes of type "0", "1", "TF"
            for CT in CHK_TYPES:
                if CT in dest_name:
                    extend_causality_to_node(R_edge.dest, es)

    # collect R destination nodes on edges
    R_dest_edges = [e for e in es if NODE_ID in e.dest.split("_")[0]]

    for R_edge in R_dest_edges:
        if R_edge.flow_side == FLOWSIDE.IDK:
            R_edge.flow_side = FLOWSIDE.DEST

            src_name = R_edge.src.split("_")[0]

            CHK_TYPES = ["0", "1", "TF"]

            # Extend causality to connected nodes of type "0", "1", "TF"
            for CT in CHK_TYPES:
                if CT in src_name:
                    extend_causality_to_node(R_edge.src, es)

def assign_arbitrary_causality(es: list[FlyEdge]):
    """
    Assign causality to edges that still have flow_side set to IDK.
    This is a last resort to ensure all edges have a flow_side set.
    """
    for e in es:
        if e.flow_side == FLOWSIDE.IDK:
            # assign arbitrary causality
            e.flow_side = FLOWSIDE.SRC


            CHK_TYPES = ["0", "1", "TF"]

            # Extend causality to connected nodes of type "0", "1", "TF"
            for CT in CHK_TYPES:
                if CT == e.src.split("_")[0]:
                    extend_causality_to_node(e.src, es)
                if CT == e.dest.split("_")[0]:
                    extend_causality_to_node(e.dest, es)


def assign_causality_to_all_nodes(es: list[FlyEdge], report: bool = True):

    assign_se_causality(es)
    assign_sf_causality(es)
    assign_I_causality(es)
    assign_C_causality(es)

    any_step_1 = any(e.flow_side == FLOWSIDE.IDK for e in es)

    if any_step_1:
        assign_R_causality(es)

    any_step_2 = any(e.flow_side == FLOWSIDE.IDK for e in es)

    if any_step_2:
        assign_arbitrary_causality(es)

    # all edges should now have their flow_side set
    if report:
        if any_step_1:
            print("AFTER SIC: Some edges still have flow_side set to IDK, which is not great.")
            if any_step_2:
                print("AFTER R: Some edges still have flow_side set to IDK, which is not great.")
            else:
                print("AFTER R: All edges have their flow_side set.")
        else:
            print("AFTER SIC: All edges have their flow_side set.")

def generate_symbols_for_SF(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for SF elements 
    This function will create symbols like SF_01, SF_02, ..., SF_99
    """
    NODE_ID = "SF"
    equations = []

    # get list of source of flow symbols
    sf_nums = [e.num for e in es if 
            NODE_ID in e.src.split("_")[0] or
            NODE_ID in e.dest.split("_")[0]]

    # equate the generic names to the unique names
    for sf_num in sf_nums:

        # create symbol SF_nn, then equate f_nn = SF_nn
        sf_f_sym = sm.add_symbol(f"SF_{sf_num:02d}")
        ff_f_sym = sm.add_symbol(f"f_{sf_num:02d}")

        eq = sym.Eq(ff_f_sym, sf_f_sym)
        equations.append(eq)

    return equations

def generate_symbols_for_SE(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for SE elements
    This function will create symbols like SE_01, SE_02, ..., SE_99
    """
    # equation list
    NODE_ID = "SE"
    equations = []

    # get list of source of effort symbols
    se_nums = [e.num for e in es if 
            NODE_ID in e.src.split("_")[0] or
            NODE_ID in e.dest.split("_")[0]]

    # equate the generic names to the unique names
    for se_num in se_nums:

        # create symbol SE_nn, then equate e_nn = SE_nn
        se_e_sym = sm.add_symbol(f"SE_{se_num:02d}")
        ee_e_sym = sm.add_symbol(f"e_{se_num:02d}")

        eq = sym.Eq(ee_e_sym, se_e_sym)
        equations.append(eq)

    return equations

def generate_symbols_for_I(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for I elements
    This function will create symbols like I_01, I_02, ..., I_99
    """
    # equation list
    NODE_ID = "I"
    equations = []

    # get list of I symbols
    I_nums = [e.num for e in es if 
            NODE_ID in e.src.split("_")[0] or
            NODE_ID in e.dest.split("_")[0]]

    # create symbol [I,p]_nn, then generate equation
    for i_num in I_nums:

        I_nn = sm.add_symbol(f"I_{i_num:02d}")
        p_nn = sm.add_symbol(f"p_{i_num:02d}")
        f_nn = sm.add_symbol(f"f_{i_num:02d}")

        # equation is always f_nn = p_nn / I_nn
        eq = sym.Eq(f_nn, p_nn / I_nn) # type: ignore
        equations.append(eq)

    return equations

def generate_symbols_for_C(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for C elements
    This function will create symbols like C_01, C_02, ..., C_99
    """
    # equation list
    NODE_ID = "C"
    equations = []

    # get list of C symbols
    C_nums = [e.num for e in es if 
            NODE_ID in e.src.split("_")[0] or
            NODE_ID in e.dest.split("_")[0]]

    # create symbol [C,q]_nn, then generate equation
    for c_num in C_nums:

        C_nn = sm.add_symbol(f"C_{c_num:02d}")
        q_nn = sm.add_symbol(f"q_{c_num:02d}")
        e_nn = sm.add_symbol(f"e_{c_num:02d}")

        # equation is always e_nn = q_nn / C_nn
        eq = sym.Eq(e_nn, q_nn / C_nn) # type: ignore
        equations.append(eq)

    return equations

def generate_symbols_for_R(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for R elements
    This function will create symbols like R_01, R_02, ..., R_99
    """
    # equation list
    NODE_ID = "R"
    equations = []

    for e in es:

        is_R_element = NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]

        if is_R_element:
            # this edge has an R element

            is_R_on_src = NODE_ID in e.src.split("_")[0]

            R_nn = sm.add_symbol(f"R_{e.num:02d}")
            e_nn = sm.add_symbol(f"e_{e.num:02d}")
            f_nn = sm.add_symbol(f"f_{e.num:02d}")

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

    return equations

def generate_symbols_for_GY(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for GY elements
    This function will create symbols like GY_01, GY_02, ..., GY_99
    """
    NODE_ID = "GY"
    # equation list
    equations = []

    # create a map from GY_name nodes to tuple of (edge_1, edge_2) pairs
    gy_name_map = {}

    for e in es:
        is_GY_element = NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]

        if is_GY_element:
            # this edge has a GY element
            gy_name = e.src if NODE_ID in e.src.split("_")[0] else e.dest

            if gy_name not in gy_name_map:
                gy_name_map[gy_name] = []

            gy_name_map[gy_name].append(e)

    # create symbols for each GY element
    for gy_name, edges in gy_name_map.items():

        assert len(edges) == 2, f"{NODE_ID} element {gy_name} must have exactly 2 edges connected to it, found {len(edges)}."


        # deterine which edge has power flowing to the GY element
        edge_a = edges[0]
        edge_b = edges[1]

        # assume edge_b is the first edge
        edge_1 = edge_b
        edge_2 = edge_a

        if (edge_a.pwr_to_dest and gy_name in edge_a.dest) or (not edge_a.pwr_to_dest and gy_name in edge_a.src):
            # edge_a is the first edge
            edge_1 = edge_a
            edge_2 = edge_b

        gy_name_str = f"GY_{edge_1.num:02d}"
        gy_sym = sm.add_symbol(gy_name_str)

        e_1_nn = sm.get_symbol(f"e_{edge_1.num:02d}")
        e_2_nn = sm.get_symbol(f"e_{edge_2.num:02d}")
        f_1_nn = sm.get_symbol(f"f_{edge_1.num:02d}")
        f_2_nn = sm.get_symbol(f"f_{edge_2.num:02d}")

        # create equations for the GY element
        eq_1 = sym.Eq(e_1_nn, sym.Mul(gy_sym ,f_2_nn))  # e_1 = GY_name_sym * f_2
        eq_2 = sym.Eq(e_2_nn, sym.Mul(gy_sym ,f_1_nn))  # e_2 = GY_name_sym * f_1
        equations.extend([eq_1, eq_2])

    return equations 

def generate_symbols_for_TF(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for TF elements
    This function will create symbols like TF_01, TF_02, ..., TF_99
    """
    NODE_ID = "TF"
    # equation list
    equations = []

    # create a map from TF_name nodes to tuple of (edge_1, edge_2) pairs
    tf_name_map = {}

    for e in es:
        is_TF_element = NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]

        if is_TF_element:
            # this edge has a TF element
            tf_name = e.src if NODE_ID in e.src.split("_")[0] else e.dest

            if tf_name not in tf_name_map:
                tf_name_map[tf_name] = []

            tf_name_map[tf_name].append(e)

    # create symbols for each TF element
    for tf_name, edges in tf_name_map.items():

        assert len(edges) == 2, f"{NODE_ID} element {tf_name} must have exactly 2 edges connected to it, found {len(edges)}."


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

        tf_name_str = f"TF_{edge_1.num:02d}"
        tf_sym = sm.add_symbol(tf_name_str)

        e_1_nn = sm.get_symbol(f"e_{edge_1.num:02d}")
        e_2_nn = sm.get_symbol(f"e_{edge_2.num:02d}")
        f_1_nn = sm.get_symbol(f"f_{edge_1.num:02d}")
        f_2_nn = sm.get_symbol(f"f_{edge_2.num:02d}")

        # create equations for the TF element
        eq_1 = sym.Eq(e_1_nn, sym.Mul(tf_sym ,e_2_nn))  # e_1 = TF_name_sym * e_2
        eq_2 = sym.Eq(f_2_nn, sym.Mul(tf_sym ,f_1_nn))  # f_2 = TF_name_sym * f_1
        equations.extend([eq_1, eq_2])

    return equations 

def generate_symbols_for_zero_junctions(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for zero junctions
    This function will create symbols like e_01, e_02, ..., e_99
    0-junctions are special cases where the effort for all edges is equal to the effort of the strong edge
    and the flows are summed up to equal zero.
    """
    equations = []
    NODE_ID = "0"

    # get list of edges with one node as a zero-junction
    zero_junction_edges = [e for e in es if NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]]

    # create a map from J0_name node to list of edges, (edge_1, edge_2, ...)
    zero_junction_name_map = {}
    for e in zero_junction_edges:
        j_name = e.src if NODE_ID in e.src.split("_")[0] else e.dest
        if j_name not in zero_junction_name_map:
            zero_junction_name_map[j_name] = []
        zero_junction_name_map[j_name].append(e)

    # create symbols for each zero-junction
    for j_name, edges in zero_junction_name_map.items():

        assert len(edges) > 1, f"Zero-junction {j_name} must have at least 2 edges connected to it, found {len(edges)}."

        zero_strong_bond = [e for e in edges if e.flow_side == FLOWSIDE.SRC  and j_name in e.src
                                         or e.flow_side == FLOWSIDE.DEST and j_name in e.dest]

        if len(zero_strong_bond) > 1:
            raise ValueError(f"Node {j_name} has more than one strong bond, which is not allowed.")

        elif len(zero_strong_bond) == 1:
            # non-strong bonds push flow out of node with j_name
            strong_bond = zero_strong_bond[0]
            strong_bond_num = strong_bond.num

            # define the strong bond effort symbol
            e_strong = sm.add_symbol(f"e_{strong_bond_num:02d}")

            # deal with effort symbols
            for e in edges:
                if e.num == strong_bond_num:
                    continue  # skip the strong bond, we already have its effort symbol

                # create symbols for the effort
                e_nn = sm.add_symbol(f"e_{e.num:02d}")

                # create effort equations for the zero-junction
                eq_f = sym.Eq(e_strong, e_nn)  # e_strong = e_nn
                equations.append(eq_f)


            exprs = []
            # deal with flow symbols
            for e in edges:
                # create symbols for the flow
                f_nn = sm.add_symbol(f"f_{e.num:02d}")

                # determine if power is flowing into the zero-junction from this edge
                is_power_to_this_zero_junction = e.pwr_to_dest and e.dest == j_name or not e.pwr_to_dest and e.src == j_name
                if is_power_to_this_zero_junction:
                    # this edge is bringing power to the zero-junction
                    # so we add the flow to the list of flows
                    exprs.append(sym.Add(0, f_nn))
                else:
                    # this edge is taking power from the zero-junction
                    # so we subtract the flow from the list of flows
                    exprs.append(sym.Add(0, sym.Mul(sym.Integer(-1), f_nn)))

            if exprs:
                # create flow equations for the zero-junction
                eq_f = sym.Eq(sym.Add(*exprs), 0)
                equations.append(eq_f)

    return equations

def generate_symbols_for_one_junctions(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate unique symbols for one junctions
    This function will create symbols like e_01, e_02, ..., e_99
    1-junctions are special cases where the flow for all edges is equal to the flow of the strong edge
    and the efforts are summed up to equal zero.
    """
    equations = []
    NODE_ID = "1"

    # get list of edges with one node as a one-junction
    one_junction_edges = [e for e in es if NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]]

    # create a map from J1_name nodes to list of edges, (edge_1, edge_2, ...)
    one_junction_name_map = {}
    for e in one_junction_edges:
        j_name = e.src if NODE_ID in e.src.split("_")[0] else e.dest
        if j_name not in one_junction_name_map:
            one_junction_name_map[j_name] = []
        one_junction_name_map[j_name].append(e)

    # create symbols for each one-junction
    for j_name, edges in one_junction_name_map.items():

        assert len(edges) > 1, f"One-junction {j_name} must have at least 2 edges connected to it, found {len(edges)}."

        one_strong_bonds = [e for e in edges if e.flow_side == FLOWSIDE.SRC and j_name in e.dest
                        or e.flow_side == FLOWSIDE.DEST and j_name in e.src]

        if len(one_strong_bonds) > 1:
            raise ValueError(f"Node {j_name} has more than one strong bond, which is not allowed.")

        elif len(one_strong_bonds) == 1:
            # non-strong bonds push flow out of node with j_name
            strong_bond = one_strong_bonds[0]
            strong_bond_num = strong_bond.num

            # define the strong bond flow symbol
            f_strong = sm.add_symbol(f"f_{strong_bond_num:02d}")

            # deal with flow symbols
            for e in edges:
                if e.num == strong_bond_num:
                    continue  # skip the strong bond, we already have its flow symbol

                # create symbols for the flow
                f_nn = sm.add_symbol(f"f_{e.num:02d}")

                # create flow equations for the one-junction
                eq_f = sym.Eq(f_strong, f_nn)  # f_strong = f_nn
                equations.append(eq_f)

            exprs = []
            # deal with effort symbols
            for e in edges:
                # create symbols for the effort
                e_nn = sm.add_symbol(f"e_{e.num:02d}")

                # determine if power is flowing into the one-junction from this edge
                is_power_to_this_one_junction = e.pwr_to_dest and e.dest == j_name or not e.pwr_to_dest and e.src == j_name
                if is_power_to_this_one_junction:
                    # this edge is bringing power to the one-junction
                    # so we add the effort to the list of efforts
                    exprs.append(sym.Add(0, e_nn))
                else:
                    # this edge is taking power from the one-junction
                    # so we subtract the effort from the list of efforts
                    exprs.append(sym.Add(0, sym.Mul(sym.Integer(-1), e_nn)))

            if exprs:
                # create effort equations for the one-junction
                eq_e = sym.Eq(sym.Add(*exprs), 0)
                equations.append(eq_e)

    return equations

def generate_equations_for_I_storage_elements(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate equations for storage elements I
    """
    NODE_ID = "I"

    equations = []

    for e in es:
        is_I_storage_element = NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]

        if is_I_storage_element:
            # this edge has an I storage element
            pdot_nn = sm.add_symbol(f"pdot_{e.num:02d}")
            e_nn = sm.add_symbol(f"e_{e.num:02d}")

            # create equations for the storage element
            # pdot_nn = e_nn
            eq_1 = sym.Eq(pdot_nn , e_nn)
            equations.append(eq_1)

    return equations 

def generate_equations_for_C_storage_elements(es: list[FlyEdge], sm: SymbolManager) -> list[sym.Eq]:
    """
    Generate equations for storage elements C
    """

    NODE_ID = "C"

    equations = []

    for e in es:
        is_C_storage_element = NODE_ID in e.src.split("_")[0] or NODE_ID in e.dest.split("_")[0]

        if is_C_storage_element:
            # this edge has an C storage element
            qdot_nn = sm.add_symbol(f"qdot_{e.num:02d}")
            f_nn = sm.add_symbol(f"f_{e.num:02d}")


            # create equations for the storage element
            # qdot_nn = f_nn
            eq_1 = sym.Eq(qdot_nn , f_nn)
            equations.append(eq_1)

    return equations

def generate_symbols(es: list[FlyEdge]) -> tuple[list[sym.Eq], SymbolManager]:
    """
    Generate symbols for the bonds
    """

    equations = []
    sm = SymbolManager()

    # generate symbols for f and e
    # f_01, f_02, ..., f_99
    # e_01, e_02, ..., e_99
    for e in es:
        sm.add_symbol(f"f_{e.num:02d}")
        sm.add_symbol(f"e_{e.num:02d}")

    new_eqs = generate_symbols_for_SF(es, sm)
    equations.extend(new_eqs)

    new_eqs = generate_symbols_for_SE(es, sm)
    equations.extend(new_eqs)

    new_eqs = generate_symbols_for_I(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_C(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_R(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_TF(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_GY(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_equations_for_I_storage_elements(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_equations_for_C_storage_elements(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_one_junctions(es, sm)
    equations.extend(new_eqs)

    new_eqs= generate_symbols_for_zero_junctions(es, sm)
    equations.extend(new_eqs)

    return equations, sm


def report_equations(es: list[FlyEdge], report_all: bool, file_name: str | None= None) -> None:
    """
    Report the equations and symbols
    """
    sym.init_printing(use_unicode=True)

    equations, sm = generate_symbols(es)
    symbols = [s for s in sm.symbols.values() if s.name.startswith(('pdot_', 'qdot_', 'e_', 'f_' ))]
    dot_vars = [s for s in sm.symbols.values() if s.name.startswith(('pdot_', 'qdot_'))]

    solution_explicit = sym.solve(equations, symbols, dict=True)

    final_answers = []

    if solution_explicit:
        sol = solution_explicit[0]
        for k,v in sol.items():
            if k in dot_vars:
                pq_sol = sol.get(k)
                if pq_sol is not None:
                    ans_pretty = sym.pretty(sym.simplify(sym.Eq(k, pq_sol)))
                    ans_str = f"{k} = {pq_sol}"
                    final_answers.append((ans_str, ans_pretty))
    
    for basic_ans, _ in final_answers:
        print(basic_ans)

    for _, pretty_ans in final_answers:
        print(pretty_ans)


    if report_all:
        print("\nFormal Equations:")
        for eq in equations:
            sym.pprint(sym.simplify(eq))

        print("\nFormal Symbols:")
        for symb in sm.symbols.values():
            sym.pprint(symb)

        print("\nBasic Form Equations:")
        for eq in equations:
            print(sym.simplify(eq))

        print("\nBasic Form Symbols:")
        for symb in sm.symbols.values():
            print(symb)

    # write basic form of equations and symbols to a file
    if file_name is not None:
        with open(file_name, "w", encoding="utf-8") as f:

            f.write("Final Answers:\n\n")
            for _, pretty_ans in final_answers:
                f.write(pretty_ans)
                f.write("\n")
            
            f.write("\n")
            for basic_ans, _ in final_answers:
                f.write(basic_ans)
                f.write("\n")

            if report_all:
                f.write("\nSymbols:\n\n")
                for symb in sm.symbols.values():
                    f.write(f"{sym.simplify(symb)}\n")

                f.write("\nEquations:\n\n")
                for eq in equations:
                    f.write(f"{sym.simplify(eq)}\n")


def plot_graph(edges: list[FlyEdge], node_names: list[str], ofname: str) -> None:
    """
    Plot the graph of edges and nodes
    """
    graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

    for n in node_names:
        graph.add_node(pydot.Node(n, shape="none", label=n))

    for e in edges:
        graph.add_edge(e.mk_edge())

    graph.write_png(ofname) # type: ignore
