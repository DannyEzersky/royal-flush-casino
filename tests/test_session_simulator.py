import random
import sqlite3

import pytest

import config
import db
from players import generate_players
from session_simulator import (
    DAILY_PLAY_PROB,
    ROYAL_SPIN_PARTICIPATION,
    generate_sessions,
)

PLAYER_COUNT = 500


@pytest.fixture(scope="module")
def sim_db():
    """Shared in-memory DB: generate players once, then sessions once."""
    conn = sqlite3.connect(":memory:")
    db.create_schema(conn)
    generate_players(conn, random.Random(42), player_count=PLAYER_COUNT)
    generate_sessions(conn, random.Random(7))
    yield conn
    conn.close()


# --- Invariant: every Session has at least one Spin ---

def test_no_session_has_zero_spins(sim_db):
    (bad,) = sim_db.execute("SELECT COUNT(*) FROM sessions WHERE spin_count <= 0").fetchone()
    assert bad == 0, f"{bad} sessions have spin_count <= 0"


# --- Invariant: Control Group players never spend Royal Tokens ---

def test_control_group_no_royal_tokens_in_sessions(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM sessions s
        JOIN players p ON s.player_id = p.player_id
        WHERE p.experiment_group = 'Control' AND s.royal_tokens_spent > 0
    """).fetchone()
    assert bad == 0, f"{bad} Control Group sessions have royal_tokens_spent > 0"


def test_pre_experiment_players_no_royal_tokens(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM sessions s
        JOIN players p ON s.player_id = p.player_id
        WHERE p.experiment_group IS NULL AND s.royal_tokens_spent > 0
    """).fetchone()
    assert bad == 0, f"{bad} non-Experiment sessions have royal_tokens_spent > 0"


# --- Invariant: spin_count is always a positive integer ---

def test_spin_count_always_positive(sim_db):
    (bad,) = sim_db.execute("SELECT COUNT(*) FROM sessions WHERE spin_count < 1").fetchone()
    assert bad == 0


# --- Invariant: Whale players have more sessions per day than Minnows ---

def test_whales_have_more_sessions_per_day_than_minnows(sim_db):
    rows = sim_db.execute("""
        SELECT p.spend_segment,
               COUNT(s.session_id) * 1.0 / COUNT(DISTINCT p.player_id) AS sessions_per_player
        FROM players p
        LEFT JOIN sessions s ON p.player_id = s.player_id
        WHERE p.spend_segment IN ('Minnow', 'Whale')
        GROUP BY p.spend_segment
    """).fetchall()
    rates = {seg: spp for seg, spp in rows}
    assert "Whale" in rates and "Minnow" in rates, f"Missing segment data: {rates}"
    assert rates["Whale"] > rates["Minnow"], (
        f"Whale {rates['Whale']:.2f} sessions/player not > Minnow {rates['Minnow']:.2f}"
    )


# --- Spins table: every row references a valid session ---

def test_all_spin_rows_reference_valid_session(sim_db):
    (orphans,) = sim_db.execute("""
        SELECT COUNT(*) FROM spins sp
        LEFT JOIN sessions s ON sp.session_id = s.session_id
        WHERE s.session_id IS NULL
    """).fetchone()
    assert orphans == 0, f"{orphans} spin rows have no matching session"


# --- Spins table: Royal Spins only for Treatment Group in Experiment window ---

def test_royal_spins_only_for_treatment_group(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM spins sp
        JOIN players p ON sp.player_id = p.player_id
        WHERE sp.spin_type = 'royal'
          AND (p.experiment_group IS NULL OR p.experiment_group = 'Control')
    """).fetchone()
    assert bad == 0, f"{bad} Royal Spins attributed to non-Treatment players"


def test_royal_spins_only_within_experiment_window(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM spins
        WHERE spin_type = 'royal'
          AND (spin_date < ? OR spin_date > ?)
    """, (config.EXPERIMENT_START.isoformat(), config.EXPERIMENT_END.isoformat())).fetchone()
    assert bad == 0, f"{bad} Royal Spins outside the Experiment window"


# --- Spins table: payout multipliers match spin type ---

def test_spin_multipliers_non_negative(sim_db):
    (bad,) = sim_db.execute(
        "SELECT COUNT(*) FROM spins WHERE payout_multiplier < 0"
    ).fetchone()
    assert bad == 0


def test_regular_spins_have_no_royal_token_cost(sim_db):
    (bad,) = sim_db.execute(
        "SELECT COUNT(*) FROM spins WHERE spin_type = 'regular' AND royal_tokens_wagered != 0"
    ).fetchone()
    assert bad == 0


def test_royal_spins_have_no_coin_cost(sim_db):
    (bad,) = sim_db.execute(
        "SELECT COUNT(*) FROM spins WHERE spin_type = 'royal' AND coins_wagered != 0"
    ).fetchone()
    assert bad == 0


# --- Sessions are only generated on or after a player's install date ---

def test_sessions_not_before_install_date(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM sessions s
        JOIN players p ON s.player_id = p.player_id
        WHERE s.session_date < p.install_date
    """).fetchone()
    assert bad == 0, f"{bad} sessions before player install date"


# --- Session aggregates are internally consistent ---

def test_sessions_table_has_rows(sim_db):
    (count,) = sim_db.execute("SELECT COUNT(*) FROM sessions").fetchone()
    assert count > 0, "No sessions generated"


def test_spins_table_has_rows(sim_db):
    (count,) = sim_db.execute("SELECT COUNT(*) FROM spins").fetchone()
    assert count > 0, "No spins generated"
