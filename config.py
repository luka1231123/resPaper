K          = 20                    # slices
B_MIN, B_MAX = 0.005, 0.03         # radii bounds (m)

# GA
N          = 40                    # pop size
G          = 100                   # generations
N_E        = 5                    # parents kept
N_EK       = 2                     # elites copied intact
SIGMA      = 0.10                  # 10 % of range
W_A, W_H   = 0.7, 0.3              # default weights

# physicsp
RHO_MAT    = 7850                 # kg/m³ density
H          = 0.002                # m
RHO_AIR    = 1.2
C_D        = 1.1
T_F        = 1e-6
OMEGA0     = 300                  # rad/s

SEED       = 123

EPS     = 1e-12 # small constant to avoid divide-by-zero