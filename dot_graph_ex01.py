from lib_bonds import *

CASE = "EX_01"

ns, es = load_json_graph(f"graph_{CASE}.json")

assign_causality_to_all_nodes(es)

plot_graph(es, ns, f"graph_{CASE}.png")

report_equations(es, report_all=False, file_name=f"bond_equations_{CASE}.txt")