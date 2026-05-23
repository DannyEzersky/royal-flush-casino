import random
from typing import NamedTuple

# Five Spin Outcomes in rarity order (rarest first)
OUTCOMES = ("Royal Flush", "Straight Flush", "Full House", "Pair", "Loss")

# Master table: (outcome, regular_prob, regular_mult, royal_prob, royal_mult)
# Royal Spins have better odds on Straight Flush and above, and higher multipliers
# on every winning outcome. segment is accepted by spin() but does not vary the odds —
# spend segment shapes behaviour via session frequency and purchase probability instead,
# keeping the A/B test effect attributable to Royal Spin access alone.
_TABLE = [
    #  outcome           reg_prob  reg_mult  roy_prob  roy_mult
    ("Royal Flush",       0.001,   100.0,    0.005,   200.0),
    ("Straight Flush",    0.010,    20.0,    0.030,    35.0),
    ("Full House",        0.050,     5.0,    0.100,    10.0),
    ("Pair",              0.150,     2.0,    0.150,     3.0),
    ("Loss",              0.789,     0.0,    0.715,     0.0),
]

# Exposed for tests and downstream consumers
REGULAR_PROBS: dict[str, float] = {row[0]: row[1] for row in _TABLE}
REGULAR_MULTS: dict[str, float] = {row[0]: row[2] for row in _TABLE}
ROYAL_PROBS:   dict[str, float] = {row[0]: row[3] for row in _TABLE}
ROYAL_MULTS:   dict[str, float] = {row[0]: row[4] for row in _TABLE}

_OUTCOME_NAMES = [row[0] for row in _TABLE]
_REG_WEIGHTS   = [row[1] for row in _TABLE]
_ROY_WEIGHTS   = [row[3] for row in _TABLE]


class SpinResult(NamedTuple):
    outcome: str
    payout_multiplier: float


def spin(spin_type: str, segment: str, rng: random.Random) -> SpinResult:
    """Return the outcome and payout multiplier for one Spin. Pure function."""
    if spin_type == "regular":
        outcome = rng.choices(_OUTCOME_NAMES, weights=_REG_WEIGHTS)[0]
        return SpinResult(outcome, REGULAR_MULTS[outcome])
    if spin_type == "royal":
        outcome = rng.choices(_OUTCOME_NAMES, weights=_ROY_WEIGHTS)[0]
        return SpinResult(outcome, ROYAL_MULTS[outcome])
    raise ValueError(f"Unknown spin_type: {spin_type!r}. Expected 'regular' or 'royal'.")
