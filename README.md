# Royal Flush Casino — Player Behavior & A/B Test Analysis

> An end-to-end data analytics portfolio project simulating player behavior for a fictional social casino slot machine game. Built to demonstrate the analytics skills expected in a **Gaming Analyst** role: KPI design, cohort analysis, A/B test evaluation, and BI-ready data modeling.

**[View Live Tableau Dashboard →](https://public.tableau.com/app/profile/danny.ezersky/viz/ProjectDashboard_17795442475170/OverviewDashboard)**

---

## Overview

SpinCrown Studios operates **Royal Flush Casino**, a mobile social casino slot machine. This project simulates 50,000 players across a 181-day period (April – September 2024), generates realistic behavioral data, and uses it to evaluate the impact of a new premium feature — the **Royal Spin mechanic** — through a controlled A/B experiment.

The full pipeline covers:

- Synthetic player and session data generation with configurable parameters
- A/B experiment simulation (Royal Spin feature, July – September 2024)
- 20+ SQL KPI queries across retention, revenue, engagement, and conversion
- BI-ready CSV exports structured for dynamic Tableau calculation
- A/B test findings deck built programmatically in PowerPoint

---

## Key Findings — Royal Spin A/B Test

The Royal Spin mechanic introduced a new premium spin type funded by **Royal Tokens**, a purchasable in-app currency. Treatment players received access to this feature; Control players did not.

### Headline Result

| Metric | Control | Treatment | Delta |
|---|---|---|---|
| ARPU | $16.56 | $23.17 | **+40.0%** |
| Conversion Rate | 18.32% | 19.23% | +0.91pp |
| FTD 30-Day Rate | 15.84% | 16.66% | +0.82pp |
| D7 Retention | 20.89% | 21.16% | +0.27pp |
| Avg Spins / Session | 69.45 | 70.77 | +1.9% |

Retention and engagement guardrails all passed — the ARPU lift was driven purely by monetisation, not artificial inflation of playtime.

### Where the Lift Came From

**Spend segment breakdown:**

| Segment | Control ARPU | Treatment ARPU | Delta |
|---|---|---|---|
| Whale | $414.30 | $557.38 | **+34.5%** |
| Dolphin | $18.56 | $15.02 | -19.1% ⚠ |
| Minnow | $0.38 | $0.34 | -10.5% |

The additive token model worked as designed for Whales — Royal Token purchases stacked on top of existing coin spend. For Dolphins and Minnows, the substitutive model caused **cannibalization**: Royal Token purchases replaced coin purchases rather than adding to them. Dolphin coin revenue fell by $5,808 while Royal Token revenue only added back $3,905 — a net loss of $1,903 for that segment.

**Platform breakdown:**

| Platform | Control ARPU | Treatment ARPU | Delta |
|---|---|---|---|
| iOS | $17.65 | $28.08 | **+59.1%** |
| Android | $15.09 | $16.46 | +9.1% |

iOS players responded 6.5× more strongly to the Royal Spin feature than Android players, consistent with the platform's higher baseline monetisation propensity.

**Royal Token revenue impact:**

Only **8.39%** of Treatment players purchased Royal Tokens — yet those players generated **$55,419**, accounting for **23.2%** of all Treatment revenue. A textbook high-value cohort effect amplified by the premium mechanic.

### Recommendation

- **Ship** Royal Spin to Whale players on iOS immediately — the lift is strong and no guardrails were triggered
- **Fix first** for Dolphins — redesign as an additive-only model before broad rollout to avoid continued cannibalization
- **Monitor** Whale revenue concentration post-launch (93.0% in Treatment vs 88.8% in Control)

---

## Methodology Notes

### Why No Spike Is Visible on July 1st in Overall Metrics

The experiment enrolled players on their **install date**, not retroactively. Players who installed before July 1 were not assigned to a group — meaning experiment participants were a growing subset of the active population throughout July. By the time the cohort was large enough to move aggregate DAU or ARPU meaningfully, the signal had already been diluted across the full player base. This is expected **population dilution** and does not indicate a weak effect — the within-group comparison is the correct unit of analysis.

### Known Limitation — Static Spend Segments

Spend segments (Minnow, Dolphin, Whale) are assigned at **install time** using a fixed probability distribution and do not change based on observed player behavior. In production, segments would typically be derived from rolling spend windows and updated periodically. This simplification means the simulation cannot model segment migration — a player who starts spending more will not graduate to Whale status mid-simulation. Treat segment-level findings as directional rather than precise.

### Further Analysis — CUPED

The experiment used a simple pre/post comparison. In a production setting, applying **CUPED** (Controlled-experiment Using Pre-Experiment Data) would reduce variance in the ARPU estimate by conditioning on each player's pre-experiment revenue. With a 181-day simulation window and a 90-day experiment period, there is sufficient pre-experiment data for each cohort to make this tractable. CUPED would tighten confidence intervals and potentially surface significant effects in the Dolphin and Minnow segments that are currently inconclusive.

---

## Project Structure

```
royal-flush-casino/
│
├── simulate.py               # Entry point — runs the full simulation
├── config.py                 # All simulation parameters (player count, weights, dates)
├── db.py                     # SQLite schema definition
├── players.py                # Player generator
├── spin_engine.py            # Spin outcome engine (RNG, payout logic)
├── session_simulator.py      # Session simulator (daily play, Royal Spin logic)
├── transaction_generator.py  # IAP transaction generator
│
├── sql/                      # 20+ KPI query files
│   ├── dau.sql               # Daily Active Users
│   ├── arpu.sql              # Average Revenue Per User
│   ├── retention_d1/d7/d30   # Cohort retention curves
│   ├── churn.sql             # 7-day churn window (ADR-0002)
│   ├── experiment_*.sql      # A/B test breakdowns
│   └── ...
│
├── export_tableau.py         # Generates the three Tableau-ready CSVs
│
├── exports/
│   ├── players_data.csv      # One row per player — lifetime metrics + attributes
│   ├── daily_sessions.csv    # One row per player per day — session + revenue detail
│   └── experiment_results.csv# Pre-aggregated A/B test summary
│
├── build_presentation.py     # Builds the A/B test PowerPoint deck programmatically
├── exports/
│   └── royal_spin_ab_test.pptx
│
├── tableau/
│   └── Project Dashboard.twb # Tableau workbook
│
├── tests/                    # pytest test suite (47 tests)
├── docs/
│   ├── adr/                  # Architecture Decision Records
│   └── prd-simulation-dataset.md
└── CONTEXT.md                # Domain model and design decisions
```

---

## How to Run

**Requirements:** Python 3.11+, packages listed in `requirements.txt`

```bash
pip install -r requirements.txt
```

**1. Generate the database** (~2 minutes, deterministic)

```bash
py simulate.py --seed 42
```

This creates `royal_flush_casino.db` (~1.9 GB) with 50,000 players, their sessions, spins, and transactions across the full 181-day simulation period.

**2. Export CSVs for Tableau**

```bash
py export_tableau.py
```

Writes three files to `exports/` — the database is not included in this repo due to its size.

**3. Build the A/B test presentation**

```bash
py build_presentation.py
```

Writes `exports/royal_spin_ab_test.pptx`.

**4. Run the test suite**

```bash
py -m pytest
```

---

## Tableau Dashboard

The live dashboard covers DAU/MAU trends, ARPU, retention curves, A/B experiment results, and segment breakdowns — all calculated dynamically from the player-level and daily-session exports.

**[Open in Tableau Public →](https://public.tableau.com/app/profile/danny.ezersky/viz/ProjectDashboard_17795442475170/OverviewDashboard)**

---

## Tech Stack

| Tool | Usage |
|---|---|
| **Python** | Simulation engine, data generation, export scripting |
| **SQLite** | Relational database storing all player, session, and transaction data |
| **SQL** | 20+ KPI queries covering retention, revenue, engagement, and A/B analysis |
| **Tableau Public** | Interactive BI dashboards with dynamic KPI calculation |
| **python-pptx** | Programmatic PowerPoint generation for the A/B test findings deck |
| **Claude Code** | AI-assisted development — simulation design, query authoring, export logic |

---

## Simulation Parameters

| Parameter | Value |
|---|---|
| Players | 50,000 |
| Simulation period | Apr 1 – Sep 28, 2024 (181 days) |
| Experiment period | Jul 1 – Sep 28, 2024 (90 days) |
| Spend segments | Minnow 90% / Dolphin 7% / Whale 3% |
| Platforms | iOS 58% / Android 42% |
| Markets | US 48% / UK 13% / DE 9% / CA 8% / AU 7% / Other 15% |
| Daily play probability | Minnow 22% / Dolphin 50% / Whale 80% |
| Churn window | 7 days (ADR-0002) |
| Random seed | 42 |
