import sqlite3


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            player_id        INTEGER PRIMARY KEY,
            install_date     TEXT    NOT NULL,  -- YYYY-MM-DD
            spend_segment    TEXT    NOT NULL,  -- Minnow | Dolphin | Whale
            market           TEXT    NOT NULL,  -- US | UK | Germany | Canada | Australia | Other
            platform         TEXT    NOT NULL,  -- iOS | Android
            experiment_group TEXT               -- Control | Treatment | NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id          INTEGER PRIMARY KEY,
            player_id           INTEGER NOT NULL REFERENCES players(player_id),
            session_date        TEXT    NOT NULL,  -- YYYY-MM-DD
            start_time          TEXT    NOT NULL,  -- HH:MM:SS
            duration_seconds    INTEGER NOT NULL,
            spin_count          INTEGER NOT NULL,
            coins_earned        INTEGER NOT NULL,
            coins_spent         INTEGER NOT NULL,
            royal_tokens_spent  INTEGER NOT NULL,
            purchase_made       INTEGER NOT NULL   -- 0 | 1
        );

        CREATE TABLE IF NOT EXISTS spins (
            spin_id              INTEGER PRIMARY KEY,
            session_id           INTEGER NOT NULL REFERENCES sessions(session_id),
            player_id            INTEGER NOT NULL REFERENCES players(player_id),
            spin_date            TEXT    NOT NULL,  -- YYYY-MM-DD
            spin_type            TEXT    NOT NULL,  -- regular | royal
            outcome              TEXT    NOT NULL,  -- Royal Flush | Straight Flush | Full House | Pair | Loss
            coins_wagered        INTEGER NOT NULL,
            coins_won            INTEGER NOT NULL,
            royal_tokens_wagered INTEGER NOT NULL,
            payout_multiplier    REAL    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   INTEGER PRIMARY KEY,
            player_id        INTEGER NOT NULL REFERENCES players(player_id),
            transaction_date TEXT    NOT NULL,  -- YYYY-MM-DD
            currency_type    TEXT    NOT NULL,  -- coin | royal_token
            bundle_tier      TEXT    NOT NULL,  -- small/medium/large or starter/standard/value
            amount_usd       REAL    NOT NULL,
            quantity_received INTEGER NOT NULL
        );
    """)
    conn.commit()


def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
