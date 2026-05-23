import random
import sqlite3
from datetime import timedelta

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

    rows = []
    for player_id in range(1, player_count + 1):
        install_date = config.SIMULATION_START + timedelta(days=rng.randrange(sim_days))
        segment = rng.choices(segments, weights=seg_weights)[0]
        market = rng.choices(markets, weights=mkt_weights)[0]
        platform = rng.choices(platforms, weights=plt_weights)[0]

        if install_date >= config.EXPERIMENT_START:
            experiment_group = rng.choice(["Control", "Treatment"])
        else:
            experiment_group = None

        rows.append((
            player_id,
            install_date.isoformat(),
            segment,
            market,
            platform,
            experiment_group,
        ))

    conn.executemany(
        """INSERT INTO players
               (player_id, install_date, spend_segment, market, platform, experiment_group)
               VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
