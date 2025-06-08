K          = 20                    # slices
B_MIN, B_MAX = 0.005, 0.03         # radii bounds (m)

N          = 40                    # pop size
G          = 40                   # generations
N_E        = 5                    # parents kept
N_EK       = 2                     # elites copied intact
SIGMA      = 0.10                  # 10 % of range
W_A, W_H   = 0.1, 0.9              # default weights

RHO_MAT    = 7850                 # kg/m³ density
H          = 0.002                # m
RHO_AIR    = 1.2
C_D        = 1.1
T_F        = 1e-6
OMEGA0     = 300                  # rad/s

EPS     = 1e-12 # small constant to avoid divide-by-zero

N_IMMIGRANTS = 4

BLX_ALPHA = 0.3

H_DECAY = 0.95
