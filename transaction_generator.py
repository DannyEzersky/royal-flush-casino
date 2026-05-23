import random
import sqlite3

import config

# Coin Bundle tier weights by segment
COIN_BUNDLE_WEIGHTS = {
    "Minnow":  {"small": 0.70, "medium": 0.25, "large": 0.05},
    "Dolphin": {"small": 0.30, "medium": 0.50, "large": 0.20},
    "Whale":   {"small": 0.05, "medium": 0.15, "large": 0.80},
}

# Royal Token Bundle tier weights by segment
ROYAL_TOKEN_BUNDLE_WEIGHTS = {
    "Minnow":  {"starter": 0.70, "standard": 0.25, "value": 0.05},
    "Dolphin": {"starter": 0.30, "standard": 0.50, "value": 0.20},
    "Whale":   {"starter": 0.05, "standard": 0.20, "value": 0.75},
}

# Probability a Treatment Group session also generates a Royal Token Bundle.
# For ADDITIVE_SEGMENTS (Whale): Royal Tokens are purchased ON TOP of a Coin Bundle —
# no budget constraint, so Royal Spin is purely incremental spend.
# For all other Treatment segments: Royal Tokens REPLACE the Coin Bundle —
# Minnows and Dolphins have a fixed session budget and substitute rather than add.
ROYAL_TOKEN_PURCHASE_PROB = {
    "Minnow":  0.20,
    "Dolphin": 0.40,
    "Whale":   0.60,
}

# Segments where Royal Token purchases are additive with (not substitutive for) Coin purchases
ADDITIVE_SEGMENTS = {"Whale"}

BATCH_SIZE = 20_000

# Pre-computed (tiers, weights) tuples keyed by segment to avoid per-row list construction
_COIN_CHOICES = {
    seg: (
        list(config.COIN_BUNDLES.keys()),
        [COIN_BUNDLE_WEIGHTS[seg][t] for t in config.COIN_BUNDLES],
    )
    for seg in COIN_BUNDLE_WEIGHTS
}
_ROYAL_CHOICES = {
    seg: (
        list(config.ROYAL_TOKEN_BUNDLES.keys()),
        [ROYAL_TOKEN_BUNDLE_WEIGHTS[seg][t] for t in config.ROYAL_TOKEN_BUNDLES],
    )
    for seg in ROYAL_TOKEN_BUNDLE_WEIGHTS
}


def generate_transactions(conn: sqlite3.Connection, rng: random.Random) -> None:
    purchasing_sessions = conn.execute("""
        SELECT s.session_id, s.player_id, s.session_date,
               p.spend_segment, p.experiment_group
        FROM sessions s
        JOIN players p ON s.player_id = p.player_id
        WHERE s.purchase_made = 1
        ORDER BY s.session_date, s.session_id
    """).fetchall()

    transaction_id = 1
    batch: list = []

    for _session_id, player_id, session_date, segment, experiment_group in purchasing_sessions:
        is_treatment = experiment_group == "Treatment"
        is_additive  = is_treatment and segment in ADDITIVE_SEGMENTS

        if is_additive:
            # Whale Treatment: always buy a Coin Bundle, then independently
            # decide whether to also buy a Royal Token Bundle on top.
            for currency_type, bundle_map, choices_map in (
                ("coin",         config.COIN_BUNDLES,         _COIN_CHOICES),
                ("royal_token",  config.ROYAL_TOKEN_BUNDLES,  _ROYAL_CHOICES),
            ):
                if currency_type == "royal_token" and rng.random() >= ROYAL_TOKEN_PURCHASE_PROB[segment]:
                    continue
                tiers, weights = choices_map[segment]
                tier = rng.choices(tiers, weights=weights)[0]
                amount_usd, quantity = bundle_map[tier]
                batch.append((transaction_id, player_id, session_date,
                               currency_type, tier, amount_usd, quantity))
                transaction_id += 1
        elif is_treatment and rng.random() < ROYAL_TOKEN_PURCHASE_PROB[segment]:
            # Minnow/Dolphin Treatment: Royal Token replaces Coin (budget-constrained)
            tiers, weights = _ROYAL_CHOICES[segment]
            tier = rng.choices(tiers, weights=weights)[0]
            amount_usd, quantity = config.ROYAL_TOKEN_BUNDLES[tier]
            batch.append((transaction_id, player_id, session_date,
                           "royal_token", tier, amount_usd, quantity))
            transaction_id += 1
        else:
            # Control / non-experiment / substitution fallback: Coin Bundle only
            tiers, weights = _COIN_CHOICES[segment]
            tier = rng.choices(tiers, weights=weights)[0]
            amount_usd, quantity = config.COIN_BUNDLES[tier]
            batch.append((transaction_id, player_id, session_date,
                           "coin", tier, amount_usd, quantity))
            transaction_id += 1

        if len(batch) >= BATCH_SIZE:
            _flush(conn, batch)
            batch = []

    _flush(conn, batch)


def _flush(conn: sqlite3.Connection, rows: list) -> None:
    if rows:
        conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?)", rows)
        conn.commit()
