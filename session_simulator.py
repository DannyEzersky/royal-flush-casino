import random
import sqlite3
from datetime import date, timedelta

import config
from spin_engine import REGULAR_MULTS, REGULAR_PROBS, ROYAL_MULTS, ROYAL_PROBS

# --- Behavioral parameters (all exposed for test inspection) ---

DAILY_PLAY_PROB = {
    "Minnow":  0.22,
    "Dolphin": 0.50,
    "Whale":   0.80,
}

# (choices, weights) pairs for rng.choices()
SESSION_COUNT_OPTIONS = {
    "Minnow":  ([1],       [1.0]),
    "Dolphin": ([1, 2],    [0.70, 0.30]),
    "Whale":   ([1, 2, 3], [0.20, 0.50, 0.30]),
}

SPIN_RANGE = {
    "Minnow":  (10,  30),
    "Dolphin": (30,  80),
    "Whale":   (80, 200),
}

PURCHASE_PROB_BASE = {
    "Minnow":  0.02,
    "Dolphin": 0.08,
    "Whale":   0.25,
}
IOS_PURCHASE_UPLIFT = 1.5

# Treatment Group only; fraction of spins that are Royal when session participates
ROYAL_SPIN_PARTICIPATION = {
    "Minnow":  0.10,
    "Dolphin": 0.35,
    "Whale":   0.70,
}
ROYAL_SPIN_FRACTION = 0.20

REGULAR_COIN_COST  = 100   # coins wagered per regular Spin
ROYAL_TOKEN_COST   = 1     # Royal Tokens wagered per Royal Spin
ROYAL_COIN_BASE    = 500   # coin base for Royal Spin payout (multiplied by payout_multiplier)

CHURN_DAYS       = 14
SECONDS_PER_SPIN = 5
BATCH_SIZE       = 20_000  # rows per executemany flush

# Pre-built weight lists for batch outcome generation
_OUTCOMES        = list(REGULAR_PROBS.keys())
_REGULAR_WEIGHTS = [REGULAR_PROBS[o] for o in _OUTCOMES]
_ROYAL_WEIGHTS   = [ROYAL_PROBS[o]   for o in _OUTCOMES]


def generate_sessions(conn: sqlite3.Connection, rng: random.Random) -> None:
    players = conn.execute(
        "SELECT player_id, install_date, spend_segment, platform, experiment_group "
        "FROM players"
    ).fetchall()

    sim_days = [
        config.SIMULATION_START + timedelta(days=i)
        for i in range((config.SIMULATION_END - config.SIMULATION_START).days + 1)
    ]

    session_id  = 1
    spin_id     = 1
    session_buf: list = []
    spin_buf:    list = []

    total = len(players)
    print(f"  0%", end="", flush=True)

    for idx, (player_id, install_date_str, segment, platform, experiment_group) in enumerate(players):
        if idx % max(1, total // 10) == 0 and idx > 0:
            print(f" {idx * 100 // total}%", end="", flush=True)

        install_date  = date.fromisoformat(install_date_str)
        last_spin_date = install_date   # churn clock starts on install date
        is_treatment  = experiment_group == "Treatment"

        purchase_prob = min(
            PURCHASE_PROB_BASE[segment] * (IOS_PURCHASE_UPLIFT if platform == "iOS" else 1.0),
            1.0,
        )
        royal_participation = ROYAL_SPIN_PARTICIPATION[segment] if is_treatment else 0.0
        session_choices, session_weights = SESSION_COUNT_OPTIONS[segment]
        spin_lo, spin_hi = SPIN_RANGE[segment]

        for day in sim_days:
            if day < install_date:
                continue

            # Churn check: 7 consecutive days without a Spin
            if (day - last_spin_date).days >= CHURN_DAYS:
                break

            # Daily play decision
            if rng.random() >= DAILY_PLAY_PROB[segment]:
                continue

            last_spin_date = day
            day_str = day.isoformat()
            num_sessions = rng.choices(session_choices, weights=session_weights)[0]

            for _ in range(num_sessions):
                spin_count  = rng.randint(spin_lo, spin_hi)
                is_royal_session = royal_participation > 0 and rng.random() < royal_participation

                # Determine royal vs regular split using binomialvariate (Python 3.12+)
                num_royal   = rng.binomialvariate(spin_count, ROYAL_SPIN_FRACTION) if is_royal_session else 0
                num_regular = spin_count - num_royal

                # Batch-generate all outcomes in two calls
                regular_outcomes = rng.choices(_OUTCOMES, weights=_REGULAR_WEIGHTS, k=num_regular) if num_regular else []
                royal_outcomes   = rng.choices(_OUTCOMES, weights=_ROYAL_WEIGHTS,   k=num_royal)   if num_royal   else []

                # Session-level aggregates derived from outcomes
                coins_spent        = num_regular * REGULAR_COIN_COST
                royal_tokens_spent = num_royal   * ROYAL_TOKEN_COST
                coins_earned = (
                    sum(round(REGULAR_MULTS[o] * REGULAR_COIN_COST) for o in regular_outcomes) +
                    sum(round(ROYAL_MULTS[o]   * ROYAL_COIN_BASE)   for o in royal_outcomes)
                )

                purchase_made = 1 if rng.random() < purchase_prob else 0
                duration      = max(10, spin_count * SECONDS_PER_SPIN + rng.randint(-30, 30))
                start_time    = f"{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}"

                session_buf.append((
                    session_id, player_id, day_str, start_time, duration,
                    spin_count, coins_earned, coins_spent, royal_tokens_spent, purchase_made,
                ))

                # Individual spin rows
                base = spin_id
                for i, outcome in enumerate(regular_outcomes):
                    spin_buf.append((
                        base + i, session_id, player_id, day_str,
                        "regular", outcome,
                        REGULAR_COIN_COST, round(REGULAR_MULTS[outcome] * REGULAR_COIN_COST),
                        0, REGULAR_MULTS[outcome],
                    ))
                for i, outcome in enumerate(royal_outcomes):
                    spin_buf.append((
                        base + num_regular + i, session_id, player_id, day_str,
                        "royal", outcome,
                        0, round(ROYAL_MULTS[outcome] * ROYAL_COIN_BASE),
                        ROYAL_TOKEN_COST, ROYAL_MULTS[outcome],
                    ))

                session_id += 1
                spin_id    += spin_count

                if len(session_buf) >= BATCH_SIZE:
                    _flush(conn, session_buf, spin_buf)
                    session_buf, spin_buf = [], []

    _flush(conn, session_buf, spin_buf)
    print(" 100%")


def _flush(conn: sqlite3.Connection, sessions: list, spins: list) -> None:
    if sessions:
        conn.executemany("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?)", sessions)
    if spins:
        conn.executemany("INSERT INTO spins VALUES (?,?,?,?,?,?,?,?,?,?)", spins)
    conn.commit()
