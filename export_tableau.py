"""
Reads from royal_flush_casino.db and writes three CSV files to exports/
for Tableau Public consumption.

Usage: python export_tableau.py
"""

import csv
import sqlite3
from pathlib import Path

import config

SQL_DIR    = Path("sql")
EXPORT_DIR = Path("exports")
ROW_WARN   = 9_000_000   # warn before hitting Tableau's 10M row limit

EXPERIMENT_GROUPS = ("Control", "Treatment")
SEGMENTS          = ("Minnow", "Dolphin", "Whale")
PLATFORMS         = ("iOS", "Android")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(conn: sqlite3.Connection, filename: str) -> list[dict]:
    """Execute a SQL file and return rows as a list of dicts."""
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


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
# experiment_results.csv
# ---------------------------------------------------------------------------

def build_experiment_results(conn: sqlite3.Connection) -> None:
    print("Building experiment_results.csv...")

    # --- Overall breakdown ---
    arpu_overall = {r["experiment_group"]: r["arpu"]
                    for r in _run(conn, "experiment_arpu.sql")}
    retention    = {r["experiment_group"]: r
                    for r in _run(conn, "experiment_retention.sql")}
    spins        = {r["experiment_group"]: r["avg_spins_per_session"]
                    for r in _run(conn, "experiment_spins_per_session.sql")}
    ftd30        = {r["experiment_group"]: r["ftd_30_day_rate"]
                    for r in _run(conn, "experiment_ftd_30day.sql")}
    conv         = {r["experiment_group"]: r["conversion_rate"]
                    for r in _run(conn, "experiment_conversion_rate.sql")}

    # royal_token_conversion_rate.sql returns one scalar for Treatment only
    royal_rate = _run(conn, "royal_token_conversion_rate.sql")[0]["royal_token_conversion_rate"]

    overall_rows = []
    for grp in EXPERIMENT_GROUPS:
        ret = retention.get(grp, {})
        overall_rows.append({
            "experiment_group":                grp,
            "breakdown_type":                  "Overall",
            "breakdown_value":                 "Overall",
            "arpu":                            arpu_overall.get(grp),
            "arppu":                           None,
            "conversion_rate_pct":             conv.get(grp),
            "ftd_30day_rate_pct":              ftd30.get(grp),
            "d1_retention_pct":                ret.get("d1_retention"),
            "d7_retention_pct":                ret.get("d7_retention"),
            "d30_retention_pct":               ret.get("d30_retention"),
            "avg_spins_per_session":           spins.get(grp),
            "royal_token_conversion_rate_pct": royal_rate if grp == "Treatment" else None,
        })

    # --- Segment breakdown ---
    arpu_seg  = {(r["experiment_group"], r["spend_segment"]): r["arpu"]
                 for r in _run(conn, "experiment_arpu_by_segment.sql")}
    arppu_seg = {(r["experiment_group"], r["spend_segment"]): r["arppu"]
                 for r in _run(conn, "experiment_arppu_by_segment.sql")}

    segment_rows = []
    for grp in EXPERIMENT_GROUPS:
        for seg in SEGMENTS:
            segment_rows.append({
                "experiment_group":                grp,
                "breakdown_type":                  "Segment",
                "breakdown_value":                 seg,
                "arpu":                            arpu_seg.get((grp, seg)),
                "arppu":                           arppu_seg.get((grp, seg)),
                "conversion_rate_pct":             None,
                "ftd_30day_rate_pct":              None,
                "d1_retention_pct":                None,
                "d7_retention_pct":                None,
                "d30_retention_pct":               None,
                "avg_spins_per_session":           None,
                "royal_token_conversion_rate_pct": None,
            })

    # --- Platform breakdown ---
    # experiment_arpu_by_platform.sql returns Pre-experiment rows too — filter here
    arpu_plat = {
        (r["experiment_group"], r["platform"]): r["arpu"]
        for r in _run(conn, "experiment_arpu_by_platform.sql")
        if r["experiment_group"] in EXPERIMENT_GROUPS
    }

    platform_rows = []
    for grp in EXPERIMENT_GROUPS:
        for plat in PLATFORMS:
            platform_rows.append({
                "experiment_group":                grp,
                "breakdown_type":                  "Platform",
                "breakdown_value":                 plat,
                "arpu":                            arpu_plat.get((grp, plat)),
                "arppu":                           None,
                "conversion_rate_pct":             None,
                "ftd_30day_rate_pct":              None,
                "d1_retention_pct":                None,
                "d7_retention_pct":                None,
                "d30_retention_pct":               None,
                "avg_spins_per_session":           None,
                "royal_token_conversion_rate_pct": None,
            })

    _write(
        EXPORT_DIR / "experiment_results.csv",
        overall_rows + segment_rows + platform_rows,
        ["experiment_group", "breakdown_type", "breakdown_value",
         "arpu", "arppu", "conversion_rate_pct", "ftd_30day_rate_pct",
         "d1_retention_pct", "d7_retention_pct", "d30_retention_pct",
         "avg_spins_per_session", "royal_token_conversion_rate_pct"],
    )


# ---------------------------------------------------------------------------
# players_data.csv
# ---------------------------------------------------------------------------

def build_players_data(conn: sqlite3.Connection) -> None:
    print("Building players_data.csv...")

    # Pre-aggregate transactions to avoid Cartesian product with sessions.
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
        EXPORT_DIR / "players_data.csv",
        rows,
        ["player_id", "install_date", "install_month", "spend_segment",
         "market", "platform", "experiment_group",
         "total_revenue", "total_sessions", "total_spins",
         "first_purchase_date", "last_session_date"],
    )


# ---------------------------------------------------------------------------
# daily_sessions.csv
# ---------------------------------------------------------------------------

def build_daily_sessions(conn: sqlite3.Connection) -> None:
    print("Building daily_sessions.csv...")

    # Aggregate transactions to player+date first to avoid row-multiplication
    # when a player has multiple sessions on the same day.
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
        EXPORT_DIR / "daily_sessions.csv",
        rows,
        ["player_id", "session_date", "spin_count", "coins_spent",
         "royal_tokens_spent", "purchase_made", "daily_revenue",
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
        LEFT JOIN sessions s1  ON s1.player_id  = p.player_id
                               AND s1.session_date = DATE(p.install_date, '+1 day')
                               AND s1.spin_count >= 1
        LEFT JOIN sessions s7  ON s7.player_id  = p.player_id
                               AND s7.session_date = DATE(p.install_date, '+7 day')
                               AND s7.spin_count >= 1
        LEFT JOIN sessions s30 ON s30.player_id = p.player_id
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
        build_experiment_results(conn)
        build_players_data(conn)
        build_daily_sessions(conn)
        build_retention_cohorts(conn)
    finally:
        conn.close()
    print("Done. Files written to exports/")


if __name__ == "__main__":
    main()
