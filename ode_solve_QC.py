import numpy as np
import math as m
from scipy.integrate import solve_ivp
from matplotlib import pyplot as plt

# DEFINE SYMBOLS

# *_s == sprung mass system
# *_us == unsprung mass system
# *_t  == tire system


t = 0.0   # seconds, initial time for simulation
t_final = 2.5 # seconds, final time for simulation
dt = 1.0e-5 # time step for simulation
g = 9.81  # m/s^2, acceleration due to gravity

m_s = 320
m_us = m_s / 6

f_s = 1 # Hz suspension frequency
omega_s = 2 * m.pi * f_s

# spring stiffnesses
k_s1 = m_s * omega_s**2 # spring stiffness for the first suspension spring segment
k_s2 = 10 * k_s1 # spring stiffness for the second suspension spring segment
k_t = 10*k_s1  # tire spring stiffness

# damper parameters
B = 1500.0 # N/(m/s)^3
# damper force is Fd = B * v_d^3, where v_d is the relative velocity between sprung and unsprung mass
# e_8 = B * f_8**3

# input bump geometry
h = 0.25 # bump height (m)
d = 1.00 # bump diameter (m)

# forward velocity
# U = 2.0 * 0.44704  # convert mph to m/s
U = 30.0 * 0.44704  # convert mph to m/s

# INITIAL CONDITIONS
q_09_ini  = m_s * g / k_s1  # initial sprung mass position
q_02_ini  = (m_s + m_us) * g / k_t # initial unsprung mass position
q_s0 = 1.3 * q_09_ini  # breakpoint for suspension spring position

# initial momenta
p_05  = 0.0
p_12  = 0.0
# initial positions
q_09 = q_09_ini
q_02 = q_02_ini

def v_i_profile(t):
    """Input bump velocity profile as a function of time."""
    if t <= 1:
        return (h / d) * m.pi * U * m.cos(m.pi * U / d * t)
    else:
        return 0

def F_s(q_s):
    # e_9 given q_9
    """Suspension spring force."""
    F_s = 0
    if q_s <= q_s0:
        F_s = k_s1 * q_s
    else:
        F_s = k_s1*q_s0 + k_s2 * (q_s - q_s0)

    return F_s

def F_d(v_d):
    # e_8 given f_8
    """Damper force."""
    return B * v_d**3

def F_t(q_t):
    # e_2 given q_2
    """Tire spring force."""
    Ft = 0
    if q_t >= 0:
        Ft = k_t * q_t

    return Ft

I_05  = m_us
I_12  = m_s
SE_04 = m_us*g
SE_11 = m_s*g 


# initial state vector
y0 = [q_02, q_09, p_05, p_12]
t_span = (0, t_final)
t_eval = np.arange(0, t_final, dt)

def ode_system(t, y):
    q_02, q_09, p_05, p_12 = y

    # Define the system of ODEs

    # get tire spring force
    e_02 = F_t(q_02)

    # get suspension spring force
    e_09 = F_s(q_09)

    # get damper force
    f_08 =  p_05/I_05 - p_12/I_12
    e_08 = F_d(f_08)

    # get input bump velocity
    v_i = v_i_profile(t)
    SF_01 = v_i

    e_03 = e_02
    e_04 = SE_04
    e_07 = e_08 + e_09
    e_06 = e_07
    e_11 = SE_11
    e_10 = e_07
    e_12 = e_10 - e_11
    e_05 = e_03 - e_04 - e_06

    f_01 = SF_01
    f_05 = p_05/I_05
    f_03 = f_05
    f_02 = f_01 - f_03

    f_06 = f_05
    f_12 = p_12/I_12
    f_10 = f_12
    f_07 = f_06 - f_10
    f_09 = f_07

    # Calculate derivatives
    pdot_05 = e_05
    pdot_12 = e_12
    qdot_02 = f_02
    qdot_09 = f_09

    return [qdot_02, qdot_09, pdot_05, pdot_12]

sol = solve_ivp(ode_system, t_span, y0, t_eval=t_eval)

ts = sol.t
q_02s = sol.y[0]
q_09s = sol.y[1]
p_05s = sol.y[2]
p_12s = sol.y[3]

# plot the displacements of the sprung and unsprung masses
plt.plot(ts, q_09s, label="Sprung Mass Displacement")
plt.plot(ts, q_02s, label="Unsprung Mass Displacement")
plt.title("Suspension System Displacements vs Time")
plt.xlabel("Time (s)")
plt.ylabel("Displacement (m)")
plt.xlim(0, 2.0)
plt.grid()
plt.legend()
plt.show()

# calculate forces for plotting
F_tires = [F_t(q) for q in q_02s]
F_susps = [F_s(q) for q in q_09s]

f_08s = [p_05/I_05 - p_12/I_12 for p_05, p_12 in zip(p_05s, p_12s)]
F_damps = [F_d(f) for f in f_08s]

# plot the forces in the tire, suspension, and damper
plt.plot(ts, F_tires, label="Tire Force")
plt.plot(ts, F_susps, label="Suspension Force")
plt.plot(ts, F_damps, label="Damper Force")
plt.title("Suspension System Forces vs Time")
plt.xlabel("Time (s)")
plt.ylabel("Force (N)")
plt.xlim(0, 2.0)
# plt.ylim(-2000, 8000)
plt.grid()
plt.legend()
plt.show()