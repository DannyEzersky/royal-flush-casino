# PRD: Royal Flush Casino Simulation Dataset

## Problem Statement

As a data analyst building a portfolio project, I have no dataset to work with. To demonstrate social casino gaming KPI analysis — including DAU trends, ARPU, retention curves, churn, and A/B test evaluation — I need a realistic, richly structured dataset that mirrors what a real social casino game (Royal Flush Casino by SpinCrown Studios) would produce. Without this, I cannot build meaningful SQL analyses or Tableau dashboards.

## Solution

Build a Python simulation system that generates six months of synthetic player behavior data (April 1 – September 28, 2024) for Royal Flush Casino. The simulation produces Player records, Session logs, Spin events, and Transaction records that realistically model the Minnow/Dolphin/Whale spend distribution, the daily bonus and Spin engagement loop, and the Royal Spin A/B Experiment. The output feeds a SQL KPI query library and Tableau Public dashboards.

## User Stories

### Data generation — Players

1. As a data analyst, I want to generate a realistic population of Players with stable attributes (Install Date, spend segment, geographic market, Experiment assignment), so that my dataset has a consistent player base to analyze.
2. As a data analyst, I want Player Install Dates distributed across the Simulation Period, so that retention curves have enough Cohort depth to show D1, D7, and D30 patterns.
3. As a data analyst, I want ~5% of Players to be Whales driving 80%+ of revenue, so that my ARPU and spend segment analysis reflects real social casino economics.
4. As a data analyst, I want Players distributed across six geographic markets (US 40%, UK 15%, Germany 10%, Canada 10%, Australia 10%, Other 15%), so that the dashboard can slice KPIs by market.
5. As a data analyst, I want Players who install during the Experiment window (July 1 – September 28) to be assigned 50/50 to Control or Treatment Group, so that the Experiment is properly randomized.
6. As a data analyst, I want Treatment Group Players to have access to Royal Spin from their Install Date, so that the A/B test reflects a real feature rollout.
7. As a data analyst, I want Control Group Players to have no access to Royal Spin at all during the Experiment window, so that the control condition is clean.

### Data generation — Sessions

8. As a data analyst, I want each simulated day to produce Session records per Active Player, so that I can analyze session frequency and duration.
9. As a data analyst, I want Sessions to record start time, duration, spin count, coins earned, coins spent, Royal Tokens spent, and whether a purchase was made, so that session-level aggregations are possible in SQL.
10. As a data analyst, I want Players who only collect a daily bonus (no Spins) to not generate Active Player records for that day, so that DAU is not inflated by passive logins.
11. As a data analyst, I want session frequency and spin count to vary by spend segment, so that Whales appear more engaged than Minnows in the data.

### Data generation — Spins

12. As a data analyst, I want each Spin to produce one of five Spin Outcomes (Royal Flush, Straight Flush, Full House, Pair, Loss) drawn from the correct probability distribution, so that outcome frequency data is realistic.
13. As a data analyst, I want Royal Spins to have better odds at Straight Flush and above and a higher payout multiplier on all winning outcomes, so that the premium nature of Royal Spin is reflected in the data.
14. As a data analyst, I want the full simulation to be reproducible from a single integer seed, so that I can regenerate the identical dataset at any time.

### Data generation — Transactions

15. As a data analyst, I want Coin Bundle purchases drawn from three tiers (Small $1.99, Medium $4.99, Large $19.99), so that transaction data reflects realistic IAP patterns.
16. As a data analyst, I want Royal Token Bundle purchases drawn from three tiers (Starter $0.99, Standard $3.99, Value $9.99), so that the two revenue streams are separately trackable.
17. As a data analyst, I want FTD status to be marked as a one-time, irreversible state change per Player, so that first-purchase conversion analysis is accurate.
18. As a data analyst, I want Whale Players to be far more likely to purchase Large Coin Bundles and Value Royal Token Bundles, so that the spend distribution is realistic.
19. As a data analyst, I want Treatment Group Players to have a higher Royal Token purchase probability than Control Group Players, so that the Experiment drives a detectable ARPU difference.

### KPI queries

20. As a data analyst, I want a SQL query for DAU (distinct Active Players per calendar day), so that I can plot daily engagement trends.
21. As a data analyst, I want a SQL query for ARPU (total real-money revenue divided by Active Players per period), so that I can benchmark monetization.
22. As a data analyst, I want SQL queries for D1, D7, and D30 Retention, so that I can show Cohort-based retention curves.
23. As a data analyst, I want a SQL query for Churn (Players with no Spin in 7 consecutive days), so that I can track the churn rate over the Simulation Period.
24. As a data analyst, I want a SQL query comparing ARPU between Control and Treatment Groups, so that I can measure the Experiment's primary metric.
25. As a data analyst, I want a SQL query for D7 Retention by Experiment group, so that I can evaluate the guardrail metric.
26. As a data analyst, I want a SQL query for Royal Token Conversion Rate (% of Treatment Players who purchased Royal Tokens at least once during the test window), so that I can measure the secondary Experiment metric.
27. As a data analyst, I want a SQL query for FTD rate over time, so that I can track first-purchase conversion trends.
28. As a data analyst, I want all KPI queries filterable by spend segment (Minnow, Dolphin, Whale) and geographic market, so that I can slice KPIs along both dimensions in the dashboard.

### Tableau exports

29. As a data analyst, I want flat CSV exports aggregated to the level Tableau needs (daily DAU, daily ARPU, Cohort retention tables, Experiment comparison tables), so that I can connect Tableau Public without complex joins.
30. As a data analyst, I want the Tableau exports to include all required dimensions (date, market, spend segment, experiment group) as columns, so that dashboard filters work without additional data preparation.

### Testing

31. As a data analyst, I want the Player Generator to produce a population with the correct segment distribution (±2%) for large N, so that I can trust the downstream data.
32. As a data analyst, I want the Spin Outcome Engine to produce outcome frequencies within expected ranges over many trials, so that the odds tables are implemented correctly.
33. As a data analyst, I want the Session Simulator to never produce a Session with zero Spins, so that DAU integrity is guaranteed.
34. As a data analyst, I want the Transaction Generator to never produce a Royal Token Bundle purchase attributed to a Control Group Player, so that Experiment contamination is impossible.

## Implementation Decisions

### Data schema

Four core tables produced by the simulation:

- **players** — one row per Player: `player_id`, `install_date`, `spend_segment`, `market`, `experiment_group` (null for Players who installed before the Experiment window)
- **sessions** — one row per Session: `session_id`, `player_id`, `session_date`, `start_time`, `duration_seconds`, `spin_count`, `coins_earned`, `coins_spent`, `royal_tokens_spent`, `purchase_made`
- **spins** — one row per Spin: `spin_id`, `session_id`, `player_id`, `spin_date`, `spin_type` (regular/royal), `outcome`, `coins_wagered`, `coins_won`, `royal_tokens_wagered`, `payout_multiplier`
- **transactions** — one row per purchase: `transaction_id`, `player_id`, `transaction_date`, `currency_type` (coin/royal_token), `bundle_tier`, `amount_usd`, `quantity_received`

### Module 1 — Player Generator

Produces the full player population as a deterministic output given a seed and config. Config controls: total player count, Simulation Period bounds, segment ratios, market distribution weights, and Experiment window. The RNG is seeded internally; no randomness escapes the module interface.

### Module 2 — Spin Outcome Engine

Pure function: `spin(spin_type, segment, rng) -> SpinOutcome`. Encapsulates the two probability tables (regular Spin odds, Royal Spin odds) and payout multipliers. No I/O, no state. Accepts an RNG instance rather than seeding internally so the caller controls reproducibility.

### Module 3 — Session Simulator

Drives each Player through each day of the Simulation Period. Determines: does this Player play today? How many Sessions? How many Spins per Session? Delegates Spin resolution to Module 2. Enforces the Royal Spin gate — only Treatment Group Players may generate Royal Spins, and only during the Experiment window.

### Module 4 — Transaction Generator

For each Session where `purchase_made = true`, generates one or more Transaction records. Bundle tier selection is weighted by spend segment. Enforces the invariant that Control Group Players never produce Royal Token Bundle transactions. Includes sanity checks that transaction totals reconcile with ARPU expectations within a configured tolerance.

### Module 5 — KPI Query Library

One `.sql` file per metric: `dau.sql`, `arpu.sql`, `retention_d1.sql`, `retention_d7.sql`, `retention_d30.sql`, `churn.sql`, `ftd_rate.sql`, `royal_token_conversion.sql`, `experiment_arpu_comparison.sql`, `experiment_retention_d7.sql`. All queries target SQLite. All are parameterizable by date range and filterable by market and spend segment.

### Module 6 — Tableau Data Prep

Python script that runs the KPI queries and writes CSV exports: `daily_kpis.csv`, `cohort_retention.csv`, `experiment_results.csv`, `spend_segment_summary.csv`. Column names use snake_case with no special characters for Tableau compatibility.

### Reproducibility

The full simulation is driven by a single integer seed passed at entry. Each module receives a derived RNG so the seed propagates deterministically. Running `python simulate.py --seed 42` twice must produce byte-identical output.

### Storage format

Output is SQLite (`.db` file) for portability — no hosted database required. The Tableau Data Prep module reads from SQLite and writes CSVs. This keeps the project fully self-contained and runnable offline.

## Testing Decisions

A good test checks observable output distributions and hard invariants — not which internal functions were called or how they are structured. Tests should assert on the statistical properties and correctness of the generated data.

### Module 1 — Player Generator (full tests)

- Segment distribution is within ±2% of configured ratios for N ≥ 10,000 Players
- Market distribution is within ±2% of configured weights for N ≥ 10,000 Players
- All Players installed during the Experiment window have a non-null `experiment_group`
- No Player installed before July 1, 2024 has an `experiment_group`
- Control/Treatment split is 50/50 (±3%) within the Experiment window

### Module 2 — Spin Outcome Engine (full tests)

- Regular Spin outcome frequencies over 100,000 trials match configured odds within ±1%
- Royal Spin probability of (Royal Flush + Straight Flush + Full House) is measurably higher than regular Spin over 100,000 trials
- Loss is the most frequent outcome for both Spin types
- Payout multiplier for every Royal Spin outcome is strictly greater than the corresponding regular Spin outcome

### Module 3 — Session Simulator (full tests)

- No Session record has `spin_count = 0`
- No Control Group Player has `royal_tokens_spent > 0` in any Session
- Whale Players produce a higher average sessions-per-day than Minnows across the Simulation Period
- `spin_count` is always a positive integer

### Module 4 — Transaction Generator (sanity checks only)

- No Control Group Player has a Royal Token Bundle transaction
- Total revenue attributed to Whale Players exceeds 70% of total simulated revenue
- Every `amount_usd` value exactly matches a valid Coin Bundle or Royal Token Bundle price

### Modules 5 and 6 — No automated tests

KPI queries and Tableau exports will be validated manually against expected KPI ranges after generation.

## Out of Scope

- A real game application, UI, or backend
- Real payment processing or real user accounts
- More than six geographic markets
- Player-to-player interactions, leaderboards, or social features
- Push notifications or other engagement mechanics
- A/B testing any feature other than Royal Spin
- Retention windows beyond D30
- Churn reactivation modeling (a Churned Player does not return in the simulation)
- Localized pricing by market (all prices are USD regardless of player market)
- Automated tests for SQL queries or Tableau exports

## Further Notes

- The simulation is runnable end-to-end with a single command: `python simulate.py --seed 42`
- All SQL queries target SQLite for portability
- Tableau Public has a 10M row limit; simulation scale should be calibrated to stay well under this
- SpinCrown Studios and Royal Flush Casino are fictional — no real company or game is implied
- To publish this PRD as a GitHub issue: initialize a git repo, add a GitHub remote, install the `gh` CLI, then run `gh issue create --title "PRD: Royal Flush Casino Simulation Dataset" --label "ready-for-agent" --body-file docs/prd-simulation-dataset.md`
