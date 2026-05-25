import random
import sqlite3
from datetime import date, timedelta

import config


def generate_players(
    conn: sqlite3.Connection,
    rng: random.Random,
    player_count: int = config.PLAYER_COUNT,
) -> None:
    sim_days = (config.SIMULATION_END - config.SIMULATION_START).days + 1

    segments = list(config.SEGMENT_WEIGHTS.keys())
    seg_weights = list(config.SEGMENT_WEIGHTS.values())

    markets = list(config.MARKET_WEIGHTS.keys())
    mkt_weights = list(config.MARKET_WEIGHTS.values())

    platforms = list(config.PLATFORM_WEIGHTS.keys())
    plt_weights = list(config.PLATFORM_WEIGHTS.values())

    # Generate all player attributes without experiment group assignment
    rows = []
    for player_id in range(1, player_count + 1):
        install_date = config.SIMULATION_START + timedelta(days=rng.randrange(sim_days))
        segment = rng.choices(segments, weights=seg_weights)[0]
        market = rng.choices(markets, weights=mkt_weights)[0]
        platform = rng.choices(platforms, weights=plt_weights)[0]
        rows.append((player_id, install_date.isoformat(), segment, market, platform))

    # Stratified randomization: guarantee 50/50 Control/Treatment split within
    # each segment so group imbalances don't confound experiment results.
    experiment_by_segment: dict[str, list[int]] = {seg: [] for seg in segments}
    for player_id, install_date, segment, _, _ in rows:
        if date.fromisoformat(install_date) >= config.EXPERIMENT_START:
            experiment_by_segment[segment].append(player_id)

    group_assignment: dict[int, str] = {}
    for seg_players in experiment_by_segment.values():
        shuffled = seg_players[:]
        rng.shuffle(shuffled)
        mid = len(shuffled) // 2
        for pid in shuffled[:mid]:
            group_assignment[pid] = "Control"
        for pid in shuffled[mid:]:
            group_assignment[pid] = "Treatment"

    final_rows = [
        (player_id, install_date, segment, market, platform,
         group_assignment.get(player_id))
        for player_id, install_date, segment, market, platform in rows
    ]

    conn.executemany(
        """INSERT INTO players
               (player_id, install_date, spend_segment, market, platform, experiment_group)
               VALUES (?, ?, ?, ?, ?, ?)""",
        final_rows,
    )
    conn.commit()
