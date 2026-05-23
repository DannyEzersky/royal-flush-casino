import random
import sqlite3

import pytest

import config
import db
from players import generate_players


@pytest.fixture
def mem_db():
    conn = sqlite3.connect(":memory:")
    db.create_schema(conn)
    yield conn
    conn.close()


def _rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


def _all_players(conn):
    return conn.execute(
        "SELECT player_id, install_date, spend_segment, market, platform, experiment_group "
        "FROM players ORDER BY player_id"
    ).fetchall()


# --- Distribution tests (N=10_000 for speed; ±2% tolerance) ---

def test_segment_distribution(mem_db):
    generate_players(mem_db, _rng(), player_count=10_000)
    rows = mem_db.execute(
        "SELECT spend_segment, COUNT(*) FROM players GROUP BY spend_segment"
    ).fetchall()
    counts = {seg: n for seg, n in rows}
    total = sum(counts.values())
    for segment, expected in config.SEGMENT_WEIGHTS.items():
        actual = counts.get(segment, 0) / total
        assert abs(actual - expected) <= 0.02, (
            f"{segment}: expected {expected:.1%}, got {actual:.1%}"
        )


def test_market_distribution(mem_db):
    generate_players(mem_db, _rng(), player_count=10_000)
    rows = mem_db.execute(
        "SELECT market, COUNT(*) FROM players GROUP BY market"
    ).fetchall()
    counts = {mkt: n for mkt, n in rows}
    total = sum(counts.values())
    for market, expected in config.MARKET_WEIGHTS.items():
        actual = counts.get(market, 0) / total
        assert abs(actual - expected) <= 0.02, (
            f"{market}: expected {expected:.1%}, got {actual:.1%}"
        )


def test_platform_distribution(mem_db):
    generate_players(mem_db, _rng(), player_count=10_000)
    rows = mem_db.execute(
        "SELECT platform, COUNT(*) FROM players GROUP BY platform"
    ).fetchall()
    counts = {plt: n for plt, n in rows}
    total = sum(counts.values())
    for platform, expected in config.PLATFORM_WEIGHTS.items():
        actual = counts.get(platform, 0) / total
        assert abs(actual - expected) <= 0.02, (
            f"{platform}: expected {expected:.1%}, got {actual:.1%}"
        )


# --- Experiment assignment rules ---

def test_all_experiment_window_players_have_group(mem_db):
    generate_players(mem_db, _rng())
    (missing,) = mem_db.execute(
        "SELECT COUNT(*) FROM players WHERE install_date >= ? AND experiment_group IS NULL",
        (config.EXPERIMENT_START.isoformat(),),
    ).fetchone()
    assert missing == 0, f"{missing} players in Experiment window have no group assigned"


def test_no_experiment_group_before_window(mem_db):
    generate_players(mem_db, _rng())
    (bad,) = mem_db.execute(
        "SELECT COUNT(*) FROM players WHERE install_date < ? AND experiment_group IS NOT NULL",
        (config.EXPERIMENT_START.isoformat(),),
    ).fetchone()
    assert bad == 0, f"{bad} pre-Experiment players have an experiment_group set"


def test_experiment_split_is_50_50(mem_db):
    generate_players(mem_db, _rng())
    rows = mem_db.execute(
        "SELECT experiment_group, COUNT(*) FROM players "
        "WHERE experiment_group IS NOT NULL GROUP BY experiment_group"
    ).fetchall()
    counts = {grp: n for grp, n in rows}
    total = sum(counts.values())
    assert total > 0, "No players assigned to Experiment groups"
    for group in ("Control", "Treatment"):
        actual = counts.get(group, 0) / total
        assert abs(actual - 0.5) <= 0.03, (
            f"{group}: expected 50%, got {actual:.1%}"
        )


# --- Install date bounds ---

def test_install_dates_within_simulation_period(mem_db):
    generate_players(mem_db, _rng())
    (out_of_range,) = mem_db.execute(
        "SELECT COUNT(*) FROM players WHERE install_date < ? OR install_date > ?",
        (config.SIMULATION_START.isoformat(), config.SIMULATION_END.isoformat()),
    ).fetchone()
    assert out_of_range == 0, f"{out_of_range} players have install_date outside Simulation Period"


# --- Reproducibility ---

def test_same_seed_produces_identical_players(mem_db):
    generate_players(mem_db, _rng(seed=7), player_count=1_000)
    run1 = _all_players(mem_db)

    mem_db.execute("DELETE FROM players")
    mem_db.commit()

    generate_players(mem_db, _rng(seed=7), player_count=1_000)
    run2 = _all_players(mem_db)

    assert run1 == run2


def test_different_seeds_produce_different_players(mem_db):
    generate_players(mem_db, _rng(seed=1), player_count=1_000)
    run1 = _all_players(mem_db)

    mem_db.execute("DELETE FROM players")
    mem_db.commit()

    generate_players(mem_db, _rng(seed=2), player_count=1_000)
    run2 = _all_players(mem_db)

    assert run1 != run2
