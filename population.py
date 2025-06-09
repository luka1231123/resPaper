import numpy as np
import pandas as pd
from typing import List

import config as C
from shape import Shape

class Population:

    def __init__(self, size: int):
        self.shapes: List[Shape] = [Shape() for _ in range(size)]
        self.generation = 1

    def evaluate(self) -> None:
        """Compute t_spin for every Shape."""
        for s in self.shapes:
            s.calc_spin_time()

    def normalise(self) -> None:
        self.apply_human_decay()

        t_vec = np.array([s.t_spin for s in self.shapes])
        t_min, t_max = t_vec.min(), t_vec.max()

        for s in self.shapes:
            s.normalize(t_min, t_max)      # updates t_norm & h_norm
            s.calc_fitness()               # combines with physics + human

    def rank(self) -> np.ndarray:
        fit = np.array([s.fitness for s in self.shapes])
        return np.argsort(fit)[::-1]

    def best(self, n: int = 1) -> List[Shape]:
        idx = self.rank()[:n]
        return [self.shapes[i].clone() for i in idx]

    def diversity(self) -> float:
        R = np.stack([s.radii for s in self.shapes])
        dists = np.sqrt(((R[:, None, :] - R[None, :, :]) ** 2).sum(-1))
        return dists[np.triu_indices_from(dists, k=1)].mean()

    def to_dataframe(self, gen: int) -> pd.DataFrame:
        records = []
        for i, s in enumerate(self.shapes):
            rec = {'gen': gen, 'id': i}
            rec.update(s.to_dict())
            records.append(rec)
        return pd.DataFrame(records)

    def _mean_anchor(self, fallback: float = 5.0) -> float:
        """Mean of all non-None anchor scores (raw 1-10)."""
        vals = [s.h_anchor for s in self.shapes if s.h_anchor is not None]
        return float(np.mean(vals)) if vals else fallback

    def apply_human_decay(self) -> None:
        """Decay stored human anchor ratings so old opinions fade out."""
        for s in self.shapes:
            if s.h_anchor is not None:
                s.h_anchor *= C.H_DECAY
                if s.h_anchor < 1.0:
                    s.h_anchor = None
        self._fill_missing_anchors()

    def _fill_missing_anchors(self) -> None:
        """Ensure every shape has at least the population mean anchor."""
        mean = self._mean_anchor()
        for s in self.shapes:
            if s.h_anchor is None:
                s.h_anchor = mean
                s.anchor_r = s.radii.copy()
                s.update_guard()

    def next_generation(self, elite_idx: np.ndarray) -> None:
        new_shapes: List[Shape] = []

        # 1) Exact elites
        for i in elite_idx[:C.N_EK]:
            new_shapes.append(self.shapes[i].clone())

        # 2) Immigrants seeded with population mean anchor
        mean_anchor = self._mean_anchor()
        for _ in range(C.N_IMMIGRANTS):
            sh = Shape()
            sh.h_anchor = mean_anchor
            sh.anchor_r = sh.radii.copy()
            sh.update_guard()
            new_shapes.append(sh)

        # 3) Offspring via crossover+mutation, always inheriting anchor
        while len(new_shapes) < C.N:
            p1_id, p2_id = np.random.choice(elite_idx[:C.N_E], 2, replace=True)
            p1, p2 = self.shapes[p1_id], self.shapes[p2_id]

            sigma_now = max(C.SIGMA_MIN, C.SIGMA * (C.SIGMA_DECAY ** self.generation))
            child = Shape.crossover(p1, p2)
            child.mutate(sigma_now)

            # inherit decayed anchor from the higher-rated parent
            pa = p1 if (p1.h_anchor or 0) >= (p2.h_anchor or 0) else p2
            inherited = (pa.h_anchor or mean_anchor)
            child.h_anchor = inherited * C.H_DECAY
            child.anchor_r = pa.anchor_r.copy() if pa.anchor_r is not None else pa.radii.copy()
            child.update_guard()

            new_shapes.append(child)

        self.shapes = new_shapes[:C.N]
