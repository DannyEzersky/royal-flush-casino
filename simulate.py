import argparse
import os
import random
import time

import config
import db
from players import generate_players
from session_simulator import generate_sessions
from transaction_generator import generate_transactions


def derive_rng(master_seed: int, purpose: str) -> random.Random:
    """Return an independent RNG seeded deterministically from master_seed + purpose."""
    derived = hash((master_seed, purpose)) & 0x7FFF_FFFF
    return random.Random(derived)


def main() -> None:
    parser = argparse.ArgumentParser(description="Royal Flush Casino data simulator")
    parser.add_argument("--seed", type=int, required=True, help="Master RNG seed")
    args = parser.parse_args()

    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)

    conn = db.open_db(config.DB_PATH)
    db.create_schema(conn)

    player_rng      = derive_rng(args.seed, "players")
    session_rng     = derive_rng(args.seed, "sessions")
    transaction_rng = derive_rng(args.seed, "transactions")

    t0 = time.time()

    print("Generating players...")
    generate_players(conn, player_rng)
    print(f"  done in {time.time()-t0:.1f}s")

    t1 = time.time()
    print("Generating sessions and spins...")
    generate_sessions(conn, session_rng)
    print(f"  done in {time.time()-t1:.1f}s")

    t2 = time.time()
    print("Generating transactions...")
    generate_transactions(conn, transaction_rng)
    print(f"  done in {time.time()-t2:.1f}s")

    conn.close()
    print(f"Database created: {config.DB_PATH}  (total {time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
