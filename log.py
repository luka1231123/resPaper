# log.py
from pathlib import Path
from typing import List, Dict

import pandas as pd
import numpy as np
import config as C

# ──────────────────────────────────────────────────────────────────────
class ExperimentLogger:
    """
    Collect per-generation records and emit:
      • <exp_id>_<seed>_full.csv   – every individual
      • <exp_id>_<seed>_summary.csv – per-generation averages
    """

    def __init__(self, *, exp_id: str, seed: int, k_eval: int) -> None:
        self.records: List[Dict] = []
        self.exp_id = exp_id
        self.seed   = seed
        self.k_eval = k_eval

    # ------------------------------------------------------------------ #
    def add_population(self, gen: int, population) -> None:
        diversity_val = population.diversity()
        for idx, shp in enumerate(population.shapes):
            rec = {
                "exp_id":   self.exp_id,
                "seed":     self.seed,
                "k_eval":   self.k_eval,
                "gen":      gen,
                "id":       idx,
                "t_spin":   shp.t_spin,
                "h_score":  shp.h_score,
                "t_norm":   shp.t_norm,
                "h_norm":   shp.h_norm,
                "diversity": diversity_val,
            }
            rec.update({f"r_{i}": r for i, r in enumerate(shp.radii)})
            self.records.append(rec)

    # ------------------------------------------------------------------ #
    def to_csv(self, out_dir: Path) -> None:
        if not self.records:
            raise RuntimeError("No records logged; nothing to write.")

        df = pd.DataFrame(self.records)

        # Full log -------------------------------------------------------
        fixed = ["exp_id","seed","k_eval","gen","id",
                 "t_spin","h_score","t_norm","h_norm","diversity"]
        radii_cols = [f"r_{i}" for i in range(C.K)]
        full = df[fixed + radii_cols]

        out_dir.mkdir(exist_ok=True)
        full_path = out_dir / f"{self.exp_id}_{self.seed}_full.csv"
        full.to_csv(full_path, index=False, float_format="%.6g")

        # Summary log ----------------------------------------------------
        summary = (
            df.groupby("gen")[["t_spin","h_score","diversity"]]
              .mean()
              .reset_index()
              .assign(exp_id=self.exp_id, seed=self.seed, k_eval=self.k_eval)
              [["exp_id","seed","k_eval","gen",
                "t_spin","h_score","diversity"]]
        )
        summ_path = out_dir / f"{self.exp_id}_{self.seed}_summary.csv"
        summary.to_csv(summ_path, index=False, float_format="%.6g")

        print(f"[logger] saved {len(full)} rows → {full_path}")
        print(f"[logger] saved {len(summary)} rows → {summ_path}")
