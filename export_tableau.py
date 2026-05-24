"""
Reads from royal_flush_casino.db and writes four CSV files to exports/
for Tableau Public consumption (star-schema layout).

  dim_players.csv       — one row per player (dimension)
  fact_sessions.csv     — one row per player per day (fact)
  fact_transactions.csv — one row per transaction (fact)
  retention_cohorts.csv — pre-aggregated D1/D7/D30 cohorts (Tableau LOD for
                          cohort analysis is painful; pre-aggregate instead)

Usage: python export_tableau.py
"""

import csv
import sqlite3
from pathlib import Path

import config

EXPORT_DIR = Path("exports")
ROW_WARN   = 9_000_000   # warn before hitting Tableau's 10M row limit


def _write(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)
    n = len(rows)
    flag = "  ⚠ approaching Tableau 10M limit" if n >= ROW_WARN else ""
    print(f"  {path.name}: {n:,} rows{flag}")


# ---------------------------------------------------------------------------
# dim_players.csv
# ---------------------------------------------------------------------------

def build_dim_players(conn: sqlite3.Connection) -> None:
    print("Building dim_players.csv...")

    sql = """
        WITH player_tx AS (
            SELECT
                player_id,
                ROUND(SUM(amount_usd), 2) AS total_revenue,
                MIN(transaction_date)     AS first_purchase_date
            FROM transactions
            GROUP BY player_id
        )
        SELECT
            p.player_id,
            p.install_date,
            STRFTIME('%Y-%m', p.install_date)   AS install_month,
            p.spend_segment,
            p.market,
            p.platform,
            p.experiment_group,
            COALESCE(pt.total_revenue, 0)        AS total_revenue,
            COUNT(s.session_id)                  AS total_sessions,
            COALESCE(SUM(s.spin_count), 0)       AS total_spins,
            pt.first_purchase_date,
            MAX(s.session_date)                  AS last_session_date
        FROM players p
        LEFT JOIN sessions s   ON s.player_id  = p.player_id
        LEFT JOIN player_tx pt ON pt.player_id = p.player_id
        GROUP BY p.player_id
        ORDER BY p.player_id
    """
    cur  = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    _write(
        EXPORT_DIR / "dim_players.csv",
        rows,
        ["player_id", "install_date", "install_month", "spend_segment",
         "market", "platform", "experiment_group",
         "total_revenue", "total_sessions", "total_spins",
         "first_purchase_date", "last_session_date"],
    )


# ---------------------------------------------------------------------------
# fact_sessions.csv
# ---------------------------------------------------------------------------

def build_fact_sessions(conn: sqlite3.Connection) -> None:
    print("Building fact_sessions.csv...")

    sql = """
        WITH daily_tx AS (
            SELECT
                player_id,
                transaction_date,
                ROUND(SUM(amount_usd), 2) AS daily_revenue
            FROM transactions
            GROUP BY player_id, transaction_date
        )
        SELECT
            s.player_id,
            s.session_date,
            SUM(s.spin_count)              AS spin_count,
            SUM(s.coins_spent)             AS coins_spent,
            SUM(s.royal_tokens_spent)      AS royal_tokens_spent,
            MAX(s.purchase_made)           AS purchase_made,
            COALESCE(dt.daily_revenue, 0)  AS daily_revenue,
            p.spend_segment,
            p.market,
            p.platform,
            p.experiment_group,
            p.install_date
        FROM sessions s
        JOIN players p  ON p.player_id = s.player_id
        LEFT JOIN daily_tx dt
               ON dt.player_id       = s.player_id
              AND dt.transaction_date = s.session_date
        GROUP BY s.player_id, s.session_date
        ORDER BY s.session_date, s.player_id
    """
    cur  = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    _write(
        EXPORT_DIR / "fact_sessions.csv",
        rows,
        ["player_id", "session_date", "spin_count", "coins_spent",
         "royal_tokens_spent", "purchase_made", "daily_revenue",
         "spend_segment", "market", "platform", "experiment_group", "install_date"],
    )


# ---------------------------------------------------------------------------
# fact_transactions.csv
# ---------------------------------------------------------------------------

def build_fact_transactions(conn: sqlite3.Connection) -> None:
    print("Building fact_transactions.csv...")

    sql = """
        SELECT
            t.transaction_id,
            t.player_id,
            t.transaction_date,
            t.currency_type,
            t.bundle_tier,
            t.amount_usd,
            t.quantity_received,
            p.spend_segment,
            p.market,
            p.platform,
            p.experiment_group,
            p.install_date
        FROM transactions t
        JOIN players p ON p.player_id = t.player_id
        ORDER BY t.transaction_date, t.transaction_id
    """
    cur  = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    _write(
        EXPORT_DIR / "fact_transactions.csv",
        rows,
        ["transaction_id", "player_id", "transaction_date", "currency_type",
         "bundle_tier", "amount_usd", "quantity_received",
         "spend_segment", "market", "platform", "experiment_group", "install_date"],
    )


# ---------------------------------------------------------------------------
# retention_cohorts.csv
# ---------------------------------------------------------------------------

def build_retention_cohorts(conn: sqlite3.Connection) -> None:
    print("Building retention_cohorts.csv...")

    sql = """
        SELECT
            p.install_date,
            COUNT(DISTINCT p.player_id) AS cohort_size,
            ROUND(
                COUNT(DISTINCT CASE
                    WHEN s1.session_date = DATE(p.install_date, '+1 day')
                         AND s1.spin_count >= 1 THEN p.player_id END
                ) * 100.0 / COUNT(DISTINCT p.player_id), 2
            ) AS d1_retention_pct,
            ROUND(
                COUNT(DISTINCT CASE
                    WHEN s7.session_date = DATE(p.install_date, '+7 day')
                         AND s7.spin_count >= 1 THEN p.player_id END
                ) * 100.0 / COUNT(DISTINCT p.player_id), 2
            ) AS d7_retention_pct,
            ROUND(
                COUNT(DISTINCT CASE
                    WHEN s30.session_date = DATE(p.install_date, '+30 day')
                         AND s30.spin_count >= 1 THEN p.player_id END
                ) * 100.0 / COUNT(DISTINCT p.player_id), 2
            ) AS d30_retention_pct
        FROM players p
        LEFT JOIN sessions s1  ON s1.player_id   = p.player_id
                               AND s1.session_date = DATE(p.install_date, '+1 day')
                               AND s1.spin_count  >= 1
        LEFT JOIN sessions s7  ON s7.player_id   = p.player_id
                               AND s7.session_date = DATE(p.install_date, '+7 day')
                               AND s7.spin_count  >= 1
        LEFT JOIN sessions s30 ON s30.player_id  = p.player_id
                               AND s30.session_date = DATE(p.install_date, '+30 day')
                               AND s30.spin_count >= 1
        WHERE p.install_date <= DATE((SELECT MAX(session_date) FROM sessions), '-30 day')
        GROUP BY p.install_date
        ORDER BY p.install_date
    """
    cur  = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    _write(
        EXPORT_DIR / "retention_cohorts.csv",
        rows,
        ["install_date", "cohort_size",
         "d1_retention_pct", "d7_retention_pct", "d30_retention_pct"],
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    conn = sqlite3.connect(config.DB_PATH)
    try:
        build_dim_players(conn)
        build_fact_sessions(conn)
        build_fact_transactions(conn)
        build_retention_cohorts(conn)
    finally:
        conn.close()
    print("Done. Files written to exports/")


if __name__ == "__main__":
    main()
