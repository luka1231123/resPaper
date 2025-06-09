import numpy as np, config as C

class Shape:
    def __init__(self, radii=None):
        self.radii   = radii if radii is not None else self.random_radii()
        self.t_spin  = None
        self.h_score = None
        self.t_norm  = None
        self.h_norm  = None
        self.fitness = None
    
    @staticmethod
    def random_radii():
        return np.random.uniform(C.B_MIN, C.B_MAX, C.K)

    def calc_spin_time(self):
        """
        Analytic proxy for ‘pressure + form’ drag vs. inertia.
        • Inertia  ~ Σ r⁴
        • Drag     ~  A_front / slopeBoost · smoothPenalty
            A_front        = π·R²        (frontal area)
            slopeBoost     = ⟨|Δr|⟩ + δ  (reward gradual taper; cylinder → 0)
            smoothPenalty  = 1 + κ·⟨|Δ²r|⟩  (punish wavy / spiky shapes)
        The score grows when the body is *large enough to carry
        inertia*, *tapers smoothly*, and *avoids abrupt steps*.
        """
        r = self.radii
        R = r.max()
        inertia = (r**4).sum()                    # Σ r⁴

        slope     = np.abs(np.diff(r)).mean()       # first derivative
        curvature = np.abs(np.diff(r, n=2)).mean()  # second derivative

        κ = 50.0      # how hard to punish wiggles – tune if needed

        slope_boost   = slope + C.EPS                # ↑ with taper
        smooth_penalty = 1.0 + κ*curvature        # ↓ if wavy

        drag_proxy = (R**2) / slope_boost * smooth_penalty
        self.t_spin = inertia / (drag_proxy + C.EPS)
    def normalize(self, t_min, t_max):
        """
        Normalize t_spin → t_norm in [0,1] using given min/max,
        and human score → h_norm in [0,1].
        """

        self.t_norm = (self.t_spin - t_min) / (t_max - t_min + C.EPS)
        if self.h_score is None:
            self.h_norm = 0.0
        else:
            # maps 1–10 → 0–1
            self.h_norm = (self.h_score - 1) / 9.0

    def calc_fitness(self):
        """Combine normalized metrics into final fitness value."""
        self.fitness = C.W_A * self.t_norm + C.W_H * self.h_norm
    def mutate(self):
        """
        Mutate each radius by adding N(0, σ·(B_MAX–B_MIN)),
        then clip back to [B_MIN, B_MAX].
        """
        noise       = np.random.normal(0, C.SIGMA * (C.B_MAX - C.B_MIN), C.K)
        self.radii  = np.clip(self.radii + noise, C.B_MIN, C.B_MAX)
    def clone(self):
        """Return a deep copy of this Shape, including all metrics."""
        copy = Shape(self.radii.copy())
        copy.t_spin  = self.t_spin
        copy.h_score = self.h_score
        copy.t_norm  = self.t_norm
        copy.h_norm  = self.h_norm
        copy.fitness = self.fitness
        return copy
    
    @staticmethod
    def crossover(p1: "Shape", p2: "Shape") -> "Shape":
        """
        BLX-α crossover: mix two parent shapes into a new child.
        """
        alpha = C.BLX_ALPHA
        child_r = np.empty_like(p1.radii)
        for i, (r1, r2) in enumerate(zip(p1.radii, p2.radii)):
            lo, hi = min(r1, r2), max(r1, r2)
            I = hi - lo
            child_r[i] = np.clip(
                np.random.uniform(lo - alpha * I, hi + alpha * I),
                C.B_MIN, C.B_MAX
            )
        return Shape(child_r)
    
    
    def to_dict(self):
        """
        Pack metrics and radii into a flat dict for logging:
        { 't_spin':…, 'h_score':…, 'fitness':…, 'r_0':…, … 'r_K-1':… }
        """
        data = {
            't_spin':  self.t_spin,
            'h_score': self.h_score,
            't_norm':  self.t_norm,
            'h_norm':  self.h_norm,
            'fitness': self.fitness
        }
        for i, r in enumerate(self.radii):
            data[f'r_{i}'] = r
        return data

    def __repr__(self):
        fit = "NA" if self.fitness is None else f"{self.fitness:.3f}"
        return f"<Shape fit={fit} t={self.t_spin:.3f}>"





