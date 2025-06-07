
import shutil
from typing import Dict, List

import config as C
from shape import Shape


def _radius_to_cols(r: float, col_max: int) -> int:
    """
    Map radius r ∈ [B_MIN, B_MAX] to a number of columns for the bar.
    """
    span = C.B_MAX - C.B_MIN
    return max(1, int(((r - C.B_MIN) / span) * col_max))


def ascii_grid(shape: Shape, col_max: int = 50) -> str:
    lines: List[str] = []
    for idx, r in reversed(list(enumerate(shape.radii))):  # show highest slice on top
        bar_cols = _radius_to_cols(r, col_max)
        bar = "█" * bar_cols
        lines.append(f"{idx:2d} | {bar}")
    return "\n".join(lines)


def ask_scores(candidate_ids: List[int], population) -> Dict[int, int]:
    """
    CLI loop: display each candidate as ASCII + first three radii,
    then ask user for an integer score 1-10.
    Returns: {shape_index_in_population: score}
    """
    # Try to size bar length to half the terminal width
    term_cols = shutil.get_terminal_size((80, 20)).columns
    col_max = max(10, int(0.5 * term_cols))
    scores: Dict[int, int] = {}
    print("\n─── HUMAN RATING ROUND ──────────────────────────────")
    print(f"Generation: {getattr(population, 'generation', 'N/A')}")
    print("Enter an integer 1-10 (10 = best). Press <Enter> after each.")

    for idx in candidate_ids:
        shape = population.shapes[idx]
        print("\n" + "=" * term_cols)
        print(f"Candidate ID: {idx}")
        print(f"Generation: {getattr(population, 'generation', 'N/A')}")
        print(ascii_grid(shape, col_max))
        while True:
            try:
                score_str = input("Score 1-10 → ").strip()
                score = int(score_str)
                if 1 <= score <= 10:
                    break
            except ValueError:
                pass
            print("Invalid. Enter an integer between 1 and 10.")
        scores[idx] = score

    print("── rating round complete ──\n")
    return scores