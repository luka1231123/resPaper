# ===========================
# Physical Constants
# ===========================
RHO_MAT   = 7850      # kg/m³, density of material
RHO_AIR   = 1.20      # kg/m³, density of air
MU_AIR    = 1.81e-5   # Pa·s, dynamic viscosity
H         = 0.035      # m, thickness
C_D       = 1.1       # drag coefficient
OMEGA0    = 300       # rad/s, angular velocity
T_F       = 1e-6      # s, time factor
CF_MIN    = 4.0e-3    # numerical floor for C_f correlations
Pi       = 3.14159265358979323846  # pi constant
# ===========================
# Algorithm Parameters
# ===========================
K         = 15        # number of slices
B_MIN     = 0.15       # min radius (m)
B_MAX     = 0.3       # max radius (m)

N         = 100        # population size
G         = 200        # number of generations
N_E       = 10         # parents kept
N_EK      = 5          # elites copied intact
N_IMMIGRANTS = 10      # number of immigrants

SIGMA     = 0.05      # x% of range
SIGMA_DECAY = 0.975    # sigma decay factor
SIGMA_MIN = 0.005
BLX_ALPHA = 0.3       # BLX-alpha parameter
H_DECAY   = 0.95      # decay factor
CURV_PENALTY = 3.0    # curvature penalty factor
HUMP_PENALTY = 0.5    # e^β penalty per extra slope sign change
CD_FACE      = 0.40   # k-factor for rotating end-disk drag
SEED        = 2       # random seed for reproducibility

# ===========================
# Weights
# ===========================
W_A         = 0.15    # physics surrogate weight
W_H_ANCHOR  = 0.40    # decaying human anchor weight
W_H_GUARD   = 0.45    # proximity bonus weight
H_GUARD_K   = 8.0     # higher → guard dies off faster with distance

# ===========================
# Miscellaneous
# ===========================
EPS       = 1e-12     # small constant to avoid divide-by-zero
