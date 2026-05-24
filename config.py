from datetime import date

SIMULATION_START = date(2024, 4, 1)
SIMULATION_END = date(2024, 9, 28)

EXPERIMENT_START = date(2024, 7, 1)
EXPERIMENT_END = date(2024, 9, 28)

PLAYER_COUNT = 50_000

# Spend segment distribution (must sum to 1.0)
SEGMENT_WEIGHTS = {
    "Minnow": 0.90,
    "Dolphin": 0.07,
    "Whale": 0.03,
}

# Geographic market distribution (must sum to 1.0)
MARKET_WEIGHTS = {
    "US": 0.48,
    "UK": 0.13,
    "Germany": 0.09,
    "Canada": 0.08,
    "Australia": 0.07,
    "Other": 0.15,
}

# Platform distribution (must sum to 1.0)
# iOS skews higher-spending; ARPU difference is modelled in the Session Simulator (issue #4)
PLATFORM_WEIGHTS = {
    "iOS": 0.58,
    "Android": 0.42,
}

# Coin bundle tiers: (amount_usd, coins)
COIN_BUNDLES = {
    "micro":  (2.99,    1_000),
    "small":  (29.99,  10_000),
    "medium": (79.99,  30_000),
    "large":  (349.99, 150_000),
}

# Royal Token bundle tiers: (amount_usd, tokens)
ROYAL_TOKEN_BUNDLES = {
    "starter":  (9.99,   100),
    "standard": (39.99,  500),
    "value":    (99.99, 2_000),
}

DB_PATH = "royal_flush_casino.db"
