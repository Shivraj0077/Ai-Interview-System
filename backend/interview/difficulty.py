LEVELS = ["L1", "L2", "L3"]


def update_difficulty(current_level: str, score: float) -> str:
    """Step up a level on a score >= 8, step down on a score <= 4, otherwise stay."""
    idx = LEVELS.index(current_level) if current_level in LEVELS else 0

    if score >= 8 and idx < len(LEVELS) - 1:
        idx += 1
    elif score <= 4 and idx > 0:
        idx -= 1

    return LEVELS[idx]
