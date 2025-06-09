import numpy as np, math, config as C

class Shape:
    """Axis-symmetric radius profile → spin-time surrogate."""

    def __init__(self, radii=None):
        self.radii   = radii if radii is not None else self.random_radii()
        self.t_spin  = None
        self.t_norm  = None
        self.fitness = None
        self.h_anchor   = None          # raw human rating (decaying)
        self.anchor_r   = None          # radii at the moment of rating
        self.h_guard    = 0.0           # proximity bonus
        self.h_norm  = None




    @staticmethod
    def random_radii():
        return np.random.uniform(C.B_MIN, C.B_MAX, C.K)

    def update_guard(self):
        """Recompute the proximity bonus from current radii ↔ anchor."""
        if self.h_anchor is None or self.anchor_r is None:
            self.h_guard = 0.0
            return
        # normalised mean-square distance in [0,1]
        d = np.mean((self.radii - self.anchor_r)**2) / (C.B_MAX - C.B_MIN)**2
        self.h_guard = self.h_anchor * math.exp(-C.H_GUARD_K * d)

    def calc_spin_time(self):
        r   = self.radii
        K   = r.size
        dz  = C.H / (K - 1)

        # Moment of inertia
        I = (0.5 * C.RHO_MAT * math.pi * r**4 * dz).sum()

        # Oversampled profile
        n_sub   = 4
        z_coarse = np.linspace(0.0, C.H, K)
        z_fine   = np.linspace(0.0, C.H, (K - 1) * n_sub + 1)
        r_fine   = np.interp(z_fine, z_coarse, r)
        dz_fine  = dz / n_sub

        # Frustum integration
        r1, r2 = r_fine[:-1], r_fine[1:]
        r_avg  = 0.5 * (r1 + r2)
        dA     = math.pi * (r1 + r2) * np.sqrt((r2 - r1)**2 + dz_fine**2)

        v   = C.OMEGA0 * r_avg
        Re  = np.clip(C.RHO_AIR * v * r_avg / C.MU_AIR, 1.0, None)
        Cf  = np.where(Re <= 5e5, 1.328/np.sqrt(Re), 0.074*Re**-0.2)
        Cf  = np.maximum(Cf, C.CF_MIN)
        tau = 0.5 * C.RHO_AIR * v**2 * Cf

        T_drag_side = (tau * dA * r_avg).sum()

        # End-face drag
        k_face = C.CD_FACE
        T_drag_face = k_face * math.pi * C.RHO_AIR * C.OMEGA0**2 * (
            r[0]**5 + r[-1]**5)

        # Penalties
        curvature   = np.abs(np.diff(np.diff(r))).sum()
        norm_curv   = curvature / (K * (C.B_MAX - C.B_MIN))
        penalty_curv = 1.0 + C.CURV_PENALTY * norm_curv

        slope = np.diff(r)
        sign_changes = np.sum(np.diff(np.sign(slope)) != 0)
        penalty_hump = math.exp(C.HUMP_PENALTY * max(0, sign_changes - 1))

        T_drag = (T_drag_side + T_drag_face) * penalty_curv * penalty_hump

        # Spin-down time proxy
        self.t_spin = 0.5 * I * C.OMEGA0 / (T_drag + C.EPS)

    def normalize(self, t_min, t_max):
        self.t_norm = (self.t_spin - t_min) / (t_max - t_min + C.EPS)
        self.h_anchor = None if self.h_anchor is None else max(1, self.h_anchor)  # safety
        self.update_guard()                         # <-- NEW
        a = 0 if self.h_anchor is None else (self.h_anchor - 1) / 9
        g = self.h_guard / 10                       # already 0-10 scale
        self.h_norm = C.W_H_ANCHOR * a + C.W_H_GUARD * g

    def calc_fitness(self):
       self.fitness = C.W_A * self.t_norm + self.h_norm

    def mutate(self, sigma: float | None = None):
        if sigma is None:
            sigma = C.SIGMA
        noise      = np.random.normal(0, sigma * (C.B_MAX - C.B_MIN), C.K)
        #print(sigma)
        self.radii = np.clip(self.radii + noise, C.B_MIN, C.B_MAX)

    def clone(self):
        cp = Shape(self.radii.copy())
        cp.t_spin    = self.t_spin
        cp.h_anchor  = self.h_anchor
        cp.anchor_r  = self.anchor_r.copy() if self.anchor_r is not None else None
        cp.h_guard   = self.h_guard
        cp.t_norm    = self.t_norm
        cp.h_norm    = self.h_norm
        cp.fitness   = self.fitness
        return cp

    @staticmethod
    def crossover(p1: "Shape", p2: "Shape") -> "Shape":
        alpha = C.BLX_ALPHA
        child_r = np.empty_like(p1.radii)
        for i, (r1, r2) in enumerate(zip(p1.radii, p2.radii)):
            lo, hi = min(r1, r2), max(r1, r2)
            I = hi - lo
            child_r[i] = np.clip(np.random.uniform(lo - alpha*I, hi + alpha*I),
                                  C.B_MIN, C.B_MAX)
        return Shape(child_r)

    def to_dict(self):
        data = {"t_spin": self.t_spin,
                "h_score": self.h_score,
                "t_norm": self.t_norm,
                "h_norm": self.h_norm,
                "fitness": self.fitness}
        for i, rr in enumerate(self.radii):
            data[f"r_{i}"] = rr
        return data

    def __repr__(self):
        fit = "NA" if self.fitness is None else f"{self.fitness:.3f}"
        return f"<Shape fit={fit} t={self.t_spin:.3f}>"
