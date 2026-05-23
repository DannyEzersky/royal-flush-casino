import random
from collections import Counter

import pytest

from spin_engine import (
    OUTCOMES,
    REGULAR_MULTS,
    REGULAR_PROBS,
    ROYAL_MULTS,
    ROYAL_PROBS,
    SpinResult,
    spin,
)

N = 100_000
TOP_OUTCOMES = ("Royal Flush", "Straight Flush", "Full House")
WINNING_OUTCOMES = ("Royal Flush", "Straight Flush", "Full House", "Pair")


def _rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


def _frequencies(spin_type: str, n: int = N, seed: int = 42) -> Counter:
    rng = _rng(seed)
    return Counter(spin(spin_type, "Minnow", rng).outcome for _ in range(n))


# --- Valid return values ---

def test_regular_spin_returns_spin_result():
    result = spin("regular", "Whale", _rng())
    assert isinstance(result, SpinResult)
    assert result.outcome in OUTCOMES
    assert result.payout_multiplier >= 0.0


def test_royal_spin_returns_spin_result():
    result = spin("royal", "Whale", _rng())
    assert isinstance(result, SpinResult)
    assert result.outcome in OUTCOMES
    assert result.payout_multiplier >= 0.0


def test_unknown_spin_type_raises():
    with pytest.raises(ValueError, match="spin_type"):
        spin("turbo", "Minnow", _rng())


def test_segment_parameter_accepted_for_all_segments():
    rng = _rng()
    for segment in ("Minnow", "Dolphin", "Whale"):
        result = spin("regular", segment, rng)
        assert result.outcome in OUTCOMES


# --- Regular Spin frequencies within ±1% of configured probabilities ---

def test_regular_spin_frequencies():
    counts = _frequencies("regular")
    for outcome, expected in REGULAR_PROBS.items():
        actual = counts[outcome] / N
        assert abs(actual - expected) <= 0.01, (
            f"Regular Spin / {outcome}: expected {expected:.3f}, got {actual:.3f}"
        )


# --- Royal Spin: top-3 combined probability measurably higher than regular ---

def test_royal_top_outcomes_higher_than_regular():
    regular_counts = _frequencies("regular", seed=1)
    royal_counts   = _frequencies("royal",   seed=2)

    regular_top = sum(regular_counts[o] for o in TOP_OUTCOMES) / N
    royal_top   = sum(royal_counts[o]   for o in TOP_OUTCOMES) / N

    assert royal_top > regular_top, (
        f"Royal top-3 ({royal_top:.3f}) not higher than regular ({regular_top:.3f})"
    )

def test_royal_top_outcomes_reflect_configured_gap():
    # Configured Royal top-3 rate is ~13.5% vs Regular ~6.1% — verify the gap is real
    expected_regular = sum(REGULAR_PROBS[o] for o in TOP_OUTCOMES)
    expected_royal   = sum(ROYAL_PROBS[o]   for o in TOP_OUTCOMES)
    assert expected_royal > expected_regular * 1.5, (
        f"Royal top-3 ({expected_royal:.3f}) not >1.5× regular ({expected_regular:.3f})"
    )


# --- Loss is most frequent for both spin types ---

def test_loss_most_frequent_regular():
    counts = _frequencies("regular")
    assert counts["Loss"] == max(counts.values()), (
        f"Loss is not most frequent: {counts.most_common()}"
    )


def test_loss_most_frequent_royal():
    counts = _frequencies("royal")
    assert counts["Loss"] == max(counts.values()), (
        f"Loss is not most frequent: {counts.most_common()}"
    )


# --- Royal multipliers strictly greater than regular for all winning outcomes ---

def test_royal_multipliers_strictly_greater_than_regular():
    for outcome in WINNING_OUTCOMES:
        assert ROYAL_MULTS[outcome] > REGULAR_MULTS[outcome], (
            f"{outcome}: Royal {ROYAL_MULTS[outcome]}× not > Regular {REGULAR_MULTS[outcome]}×"
        )


def test_loss_multiplier_is_zero_for_both():
    assert REGULAR_MULTS["Loss"] == 0.0
    assert ROYAL_MULTS["Loss"] == 0.0


# --- Purity: identical RNG state → identical result ---

def test_spin_is_pure_regular():
    result1 = spin("regular", "Dolphin", _rng(seed=99))
    result2 = spin("regular", "Dolphin", _rng(seed=99))
    assert result1 == result2


def test_spin_is_pure_royal():
    result1 = spin("royal", "Whale", _rng(seed=77))
    result2 = spin("royal", "Whale", _rng(seed=77))
    assert result1 == result2


def test_spin_result_carries_correct_multiplier():
    # Verify the returned multiplier matches the configured table for the outcome
    rng = _rng()
    for _ in range(1_000):
        result = spin("regular", "Minnow", rng)
        assert result.payout_multiplier == REGULAR_MULTS[result.outcome]

    rng = _rng()
    for _ in range(1_000):
        result = spin("royal", "Minnow", rng)
        assert result.payout_multiplier == ROYAL_MULTS[result.outcome]
