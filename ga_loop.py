
import time
from pathlib import Path
import numpy as np

from gen_stl import radii_to_stl
import config as C
from population import Population
from log import ExperimentLogger
import hitl_pygame as hitl   # swap to ascii hitl if needed


# ────────────────────────────────────────────────────────────────────
def run_experiment(exp_id: str, k_eval: int, seed: int) -> None:
    np.random.seed(seed)

    pop = Population(C.N)
    logger = ExperimentLogger(exp_id=exp_id, seed=seed, k_eval=k_eval)

    for gen in range(1, C.G + 1):
        pop.generation = gen

        # 1) physics evaluation
        pop.evaluate()

        # 2) first normalisation → every shape gets fitness
        pop.normalise()

        # 3) optional HITL every k_eval generations
        if k_eval and (gen == 4 or gen % k_eval == 0):
            elite_ids = pop.rank()[: C.N_E // 2]

            # sample same number of random non-elite candidates
            pool = np.setdiff1d(np.arange(C.N), elite_ids, assume_unique=True)
            rand_ids = np.random.choice(pool, size=len(elite_ids), replace=False)
            candidate_ids = np.concatenate([elite_ids, rand_ids])

            new_scores = hitl.ask_scores_pygame(candidate_ids, pop)
            for idx, sc in new_scores.items():
                shp = pop.shapes[idx]
                shp.h_score = sc
                # update only that individual's norms & fitness
                shp.h_norm = (sc - 1) / 9.0
                shp.calc_fitness()

        # 4) log current generation
        logger.add_population(gen, pop)

        # 5) build next generation
        ranked = pop.rank()
        if gen < C.G:                      # ← guard for last gen
            pop.next_generation(ranked[:C.N_E])


    # ─── after evolution ───────────────────────────────────────────
    best_shape = pop.best(1)[0]
    stl_path, _ = radii_to_stl(best_shape.radii, dz=C.H, res=6, stl_path='best_shape.stl')
    logger.to_csv(Path("logs"))
    print(f"[{exp_id}] done – log saved.")
    


