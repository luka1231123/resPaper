
from pathlib import Path
from typing import List, Dict

import pandas as pd


class ExperimentLogger:
    def __init__(self) -> None:
        self._records: List[Dict] = []

    # --------------------------------------------------------------------- #
    # Collect data
    # --------------------------------------------------------------------- #
    def add(self, record: Dict) -> None:
        """Append a single row (dict)."""
        self._records.append(record)

    def add_dataframe(self, df: pd.DataFrame) -> None:
        """Append an entire DataFrame (faster than add() in a loop)."""
        self._records.extend(df.to_dict(orient="records"))

    # --------------------------------------------------------------------- #
    # Save
    # --------------------------------------------------------------------- #
    def to_csv(self, path: Path) -> None:
        if not self._records:
            raise RuntimeError("Nothing to log – no records added.")

        df = pd.DataFrame(self._records)

        # ── Nice column order for Excel ────────────────────────────────── #
        prefix = [
            "gen",
            "id",
            "fitness",
            "t_spin",
            "h_score",
            "t_norm",
            "h_norm",
            "diversity",
        ]
        # radii columns r_0 … r_19
        radii_cols = sorted([c for c in df.columns if c.startswith("r_")],
                            key=lambda x: int(x.split("_")[1]))
        other_cols = [c for c in df.columns if c not in prefix + radii_cols]

        df = df[prefix + radii_cols + other_cols]

        # Write with 6-dec float precision; index off
        path.parent.mkdir(exist_ok=True)
        df.to_csv(path, index=False, float_format="%.6f")
        print(f"[logger] CSV saved → {path}")