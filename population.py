import numpy as np
import pandas as pd
from typing import List

import config as C
from shape import Shape

class Population:
    """Container around a list[Shape] with convenience helpers."""

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
            s.calc_fitness()               # combines with (possibly-decayed) h_score

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

    def apply_human_decay(self) -> None:
        """Decay stored human ratings so old opinions fade out."""
        for s in self.shapes:
            if s.h_score is not None:
                s.h_score *= C.H_DECAY
                # clamp into [1,10] if you want an explicit floor
                if s.h_score < 1:
                    s.h_score = None  # treat as unrated after fading out

 


    def next_generation(self, elite_idx: np.ndarray) -> None:
        """
        Elites kept, random immigrants added, rest via crossover+mutation.
        Human score handling:
          – mutation-only child: copies *decayed* parent score
          – crossover child   : average of decayed parent scores (or None)
        """
        new_shapes: List[Shape] = []

        # 1) Exact elites
        for i in elite_idx[:C.N_EK]:
            new_shapes.append(self.shapes[i].clone())

        # 2) Immigrants (no human score)
        for _ in range(C.N_IMMIGRANTS):
            new_shapes.append(Shape())

        # 3) Offspring
        while len(new_shapes) < C.N:
            p1_id, p2_id = np.random.choice(elite_idx[:C.N_E], 2, replace=False)
            p1, p2 = self.shapes[p1_id], self.shapes[p2_id]

            child = Shape.crossover(p1, p2)
            child.mutate()
            # propagate already-decayed scores
            if p1_id == p2_id:
                child.h_score = p1.h_score
            else:
                scores = [sc for sc in (p1.h_score, p2.h_score) if sc is not None]
                child.h_score = None if not scores else sum(scores)/len(scores)

            new_shapes.append(child)

        self.shapes = new_shapes[:C.N]
