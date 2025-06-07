import numpy as np
import pandas as pd
from typing import List

import config as C
from shape import Shape


class Population:
    """Container around a list[Shape] with convenience helpers."""

    # ──────────────────────────────
    # Construction
    # ──────────────────────────────
    def __init__(self, size: int):
        self.shapes: List[Shape] = [Shape() for _ in range(size)]
        self.generation = 1 

    # ──────────────────────────────
    # Core GA helpers
    # ──────────────────────────────
    def evaluate(self) -> None:
        """Compute t_spin for every Shape."""
        for s in self.shapes:
            s.calc_spin_time()

    def normalise(self) -> None:
        """Normalise aerodynamic + human metrics to [0,1]."""
        t_vec = np.array([s.t_spin for s in self.shapes])
        t_min, t_max = t_vec.min(), t_vec.max()

        # normalise each shape in-place then recompute fitness
        for s in self.shapes:
            s.normalize(t_min, t_max)
            s.calc_fitness()

    def rank(self) -> np.ndarray:
        """Return indices sorted by descending fitness."""
        fit = np.array([s.fitness for s in self.shapes])
        return np.argsort(fit)[::-1]

    # ──────────────────────────────
    # Stats & convenience
    # ──────────────────────────────
    def best(self, n: int = 1) -> List[Shape]:
        """Return the top-n shapes (deep copies)."""
        idx = self.rank()[:n]
        return [self.shapes[i].clone() for i in idx]

    def diversity(self) -> float:
        """Mean pairwise Euclidean distance between radii vectors."""
        R = np.stack([s.radii for s in self.shapes])
        dists = np.sqrt(((R[:, None, :] - R[None, :, :]) ** 2).sum(-1))
        # exclude diagonal zeros
        return dists[np.triu_indices_from(dists, k=1)].mean()

    def to_dataframe(self, gen: int) -> pd.DataFrame:
        """Dump current population to a DataFrame for logging."""
        records = []
        for i, s in enumerate(self.shapes):
            rec = {'gen': gen, 'id': i}
            rec.update(s.to_dict())
            records.append(rec)
        return pd.DataFrame(records)

    # ──────────────────────────────
    # GA transitions
    # ──────────────────────────────
    def next_generation(self, elite_idx: np.ndarray) -> None:
        """
        Build the next generation in-place:
        • Keep N_EK elites unchanged
        • Fill the remainder by mutating random parents from elite set
        """
        # 1. Copy spared elites
        new_shapes: List[Shape] = [
            self.shapes[i].clone() for i in elite_idx[:C.N_EK]
        ]

        # 2. Produce children until population is full
        while len(new_shapes) < C.N:
            parent = self.shapes[np.random.choice(elite_idx)]
            child = parent.clone()
            child.mutate()
            # reset any human score carried over
            child.h_score = None
            new_shapes.append(child)

        self.shapes = new_shapes