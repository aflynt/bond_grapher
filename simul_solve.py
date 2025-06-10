import sympy as sym

#x,y = sym.symbols('x,y')
#eq1 = sym.Eq(x+y, 5)
#eq2 = sym.Eq(x**2+y**2, 17)

q_19 = sym.Symbol("q_19", real=True)
K_sp = sym.Symbol("K_sp", real=True)
e_8 = sym.Symbol("e_8", real=True)
e_19 = sym.Symbol("e_19", real=True)
p_2 = sym.Symbol("p_2", real=True)
m_tfe = sym.Symbol("m_tfe", real=True)
f_2 = p_2/m_tfe # type: ignore
f_23 = sym.Symbol("f_23", real=True)
f_26 = sym.Symbol("f_26", real=True)
f_29 = sym.Symbol("f_29", real=True)
R_TP30_PA = sym.Symbol("R_TP30_PA", real=True)
R_TP30_AT = sym.Symbol("R_TP30_AT", real=True)
R_TP30_PB = sym.Symbol("R_TP30_PB", real=True)
R_TP20    = sym.Symbol("R_TP20", real=True)
A_bore    = sym.Symbol("A_bore", real=True)
A_ann     = sym.Symbol("A_ann", real=True)

e_22 = R_TP30_PA*f_23 # type: ignore
e_25 = R_TP30_AT*f_26 # type: ignore
e_25 = R_TP30_AT*f_26 # type: ignore

#e_7 = R_TP20*(f_23 + f_26 + A_ann*f_2)
#print(f"e_7 = ")
#sym.pprint(e_7)
#
#pdot_2 = A_bore*e_8 + K_sp*q_19 - A_ann*(e_7 + e_8)
#print(f"pdot_2 = ")
#sym.pprint(pdot_2)
#print(pdot_2)

f_5 = f_2
f_6 = A_ann * f_5
f_21 = f_23
f_24 = f_26

f_20 = f_21 + f_24 + f_6 # type: ignore
f_9 = f_20
f_7 = f_20

f_3 = f_2
f_4 = A_bore*f_3

f_8 = f_4 - f_29 - f_9
print(f"f_8:")
sym.pprint(f_8)




#rs = sym.solve([eq1, eq2], (x,y))
#
#for r in rs:
#    print(r) 