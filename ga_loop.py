import time
import numpy as np
import pandas as pd
from pathlib import Path
from log import ExperimentLogger

import config as C
from population import Population
import hitl


# ──────────────────────────────────────────────────────────────────
def run_experiment(exp_id: str, k_eval: int) -> None:
    np.random.seed(C.SEED)
    pop = Population(C.N)                # initial population
    rows = []                            # logging list
    logger = ExperimentLogger()

    for gen in range(1, C.G + 1):
        pop.generation = gen
        # 1) Evaluate physics metric
        pop.evaluate()

        # 2) Possibly collect human ratings
        if k_eval and gen % k_eval == 0:
            elite_idx = pop.rank()[: C.N_E]
            new_scores = hitl.ask_scores(elite_idx, pop)
            for idx, score in new_scores.items():
                pop.shapes[idx].h_score = score

        # 3) Normalise and calc fitness for everyone
        pop.normalise()

        # 4) Log population snapshot
        df_gen = pop.to_dataframe(gen)
        df_gen["diversity"] = pop.diversity()
        logger.add_dataframe(df_gen)


        # 5) Selection + reproduction
        ranked = pop.rank()
        pop.next_generation(ranked[: C.N_E])


        out_dir = Path("logs")
        fname   = f"{exp_id}_k{k_eval}_{int(time.time())}.csv"
        logger.to_csv(out_dir / fname)
    print("factum est")
