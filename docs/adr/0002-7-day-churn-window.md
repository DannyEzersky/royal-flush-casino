# Churn window is 7 consecutive days without a Spin

A Player is considered Churned after 7 consecutive calendar days with no completed Spin. This is the primary churn definition used in all SQL queries and dashboard metrics.

Social casino players are expected to engage daily or near-daily — the genre is built around daily bonuses, streaks, and frequent short sessions. A 7-day window reflects this cadence: a player who goes a full week without spinning has genuinely disengaged. A longer window (e.g. 30 days, common in mid-core games) is too conservative for this genre and would understate early dropoff, which is the most actionable signal in the data.

## Considered options

- **30-day window** — standard for mid-core and RPG games where weekly or bi-weekly play is normal. Too conservative for a daily-engagement slot game.
- **14-day window** — middle ground, but lacks industry precedent for social casino specifically.
- **7-day window (chosen)** — matches social casino industry standard; aligns with the daily bonus cycle that defines the genre's engagement loop.
