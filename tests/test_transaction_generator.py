import random
import sqlite3

import pytest

import config
import db
from players import generate_players
from session_simulator import generate_sessions
from transaction_generator import generate_transactions

# Valid prices looked up once at module load
_VALID_PRICES = (
    {amt for amt, _ in config.COIN_BUNDLES.values()} |
    {amt for amt, _ in config.ROYAL_TOKEN_BUNDLES.values()}
)
_VALID_COIN_TIERS  = set(config.COIN_BUNDLES.keys())
_VALID_TOKEN_TIERS = set(config.ROYAL_TOKEN_BUNDLES.keys())


@pytest.fixture(scope="module")
def sim_db():
    conn = sqlite3.connect(":memory:")
    db.create_schema(conn)
    generate_players(conn, random.Random(42), player_count=500)
    generate_sessions(conn, random.Random(7))
    generate_transactions(conn, random.Random(13))
    yield conn
    conn.close()


# --- Table populated ---

def test_transactions_table_populated(sim_db):
    (count,) = sim_db.execute("SELECT COUNT(*) FROM transactions").fetchone()
    assert count > 0, "No transactions generated"


# --- Hard invariant: Control Group never gets Royal Token transactions ---

def test_no_control_group_royal_token_transactions(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM transactions t
        JOIN players p ON t.player_id = p.player_id
        WHERE p.experiment_group = 'Control' AND t.currency_type = 'royal_token'
    """).fetchone()
    assert bad == 0, f"{bad} Control Group transactions have currency_type = 'royal_token'"


# --- Hard invariant: non-experiment players never get Royal Token transactions ---

def test_no_non_experiment_royal_token_transactions(sim_db):
    (bad,) = sim_db.execute("""
        SELECT COUNT(*) FROM transactions t
        JOIN players p ON t.player_id = p.player_id
        WHERE p.experiment_group IS NULL AND t.currency_type = 'royal_token'
    """).fetchone()
    assert bad == 0, f"{bad} non-experiment transactions have currency_type = 'royal_token'"


# --- Hard invariant: every amount_usd exactly matches a configured bundle price ---

def test_all_amounts_match_valid_bundle_prices(sim_db):
    prices = sim_db.execute("SELECT DISTINCT amount_usd FROM transactions").fetchall()
    for (price,) in prices:
        assert price in _VALID_PRICES, f"Invalid price ${price} in transactions"


# --- Hard invariant: bundle tiers are valid for their currency type ---

def test_all_bundle_tiers_valid(sim_db):
    rows = sim_db.execute(
        "SELECT DISTINCT currency_type, bundle_tier FROM transactions"
    ).fetchall()
    for currency_type, tier in rows:
        if currency_type == "coin":
            assert tier in _VALID_COIN_TIERS, f"Invalid coin tier: {tier!r}"
        else:
            assert tier in _VALID_TOKEN_TIERS, f"Invalid token tier: {tier!r}"


# --- Sanity check: Whale revenue share >= 70% ---

def test_whale_revenue_exceeds_70_pct(sim_db):
    rows = sim_db.execute("""
        SELECT p.spend_segment, ROUND(SUM(t.amount_usd), 2) AS revenue
        FROM transactions t
        JOIN players p ON t.player_id = p.player_id
        GROUP BY p.spend_segment
    """).fetchall()
    revenue = {seg: rev for seg, rev in rows}
    total = sum(revenue.values())
    assert total > 0, "Total revenue is zero"
    whale_share = revenue.get("Whale", 0) / total
    assert whale_share >= 0.70, (
        f"Whale revenue share {whale_share:.1%} < 70% "
        f"(Whale ${revenue.get('Whale',0):.0f} / Total ${total:.0f})"
    )


# --- Sanity check: Treatment Group has higher Royal Token rate than Control ---

def test_treatment_higher_royal_token_rate_than_control(sim_db):
    rows = sim_db.execute("""
        SELECT p.experiment_group,
               COUNT(*) AS total,
               SUM(CASE WHEN t.currency_type = 'royal_token' THEN 1 ELSE 0 END) AS royal_count
        FROM transactions t
        JOIN players p ON t.player_id = p.player_id
        WHERE p.experiment_group IS NOT NULL
        GROUP BY p.experiment_group
    """).fetchall()
    rates = {grp: royal / total for grp, total, royal in rows}
    assert rates.get("Treatment", 0) > rates.get("Control", 0), (
        f"Treatment Royal Token rate {rates.get('Treatment', 0):.1%} "
        f"not > Control {rates.get('Control', 0):.1%}"
    )


# --- FTD derivable as earliest transaction per player ---

def test_ftd_derivable_from_transactions(sim_db):
    rows = sim_db.execute("""
        SELECT player_id, MIN(transaction_date) AS ftd_date
        FROM transactions
        GROUP BY player_id
    """).fetchall()
    assert len(rows) > 0, "No players have transactions"
    for player_id, ftd_date in rows:
        assert ftd_date is not None, f"Player {player_id} has NULL ftd_date"


# --- Every transaction references a valid player ---

def test_all_transactions_reference_valid_player(sim_db):
    (orphans,) = sim_db.execute("""
        SELECT COUNT(*) FROM transactions t
        LEFT JOIN players p ON t.player_id = p.player_id
        WHERE p.player_id IS NULL
    """).fetchone()
    assert orphans == 0, f"{orphans} transactions reference non-existent players"


# --- Transaction count: at least one transaction per purchasing session,
#     at most two (Whale Treatment sessions can generate Coin + Royal Token) ---

def test_transaction_count_bounds(sim_db):
    (purchasing_sessions,) = sim_db.execute(
        "SELECT COUNT(*) FROM sessions WHERE purchase_made = 1"
    ).fetchone()
    (transactions,) = sim_db.execute("SELECT COUNT(*) FROM transactions").fetchone()
    assert transactions >= purchasing_sessions, (
        f"{transactions} transactions < {purchasing_sessions} purchasing sessions"
    )
    assert transactions <= purchasing_sessions * 2, (
        f"{transactions} transactions > 2× {purchasing_sessions} purchasing sessions"
    )
