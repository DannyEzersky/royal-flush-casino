# Royal Flush Casino

A simulated dataset for a fictional social casino slot machine game made by SpinCrown Studios. The project generates player behavior data for KPI analysis and A/B testing. There is no real app — all data is synthetically produced by Python scripts.

## Language

### Core gameplay

**Spin**:
The core unit of gameplay. A single button press that consumes Coins (or Royal Tokens for a Royal Spin) and produces an instant outcome. The jackpot outcome is a Royal Flush.
_Avoid_: Round, hand, play, bet

**Royal Spin**:
A premium Spin variant with better odds and higher payouts. Costs Royal Tokens (and/or more Coins) instead of standard Coins. The subject of the A/B test.
_Avoid_: Premium spin, bonus spin, paid spin

**Royal Flush**:
The jackpot outcome of a Spin — the highest-payout result, themed after the poker hand of the same name.
_Avoid_: Jackpot (use only when referring to the payout amount, not the outcome type)

**Session**:
A continuous period of play by a Player, starting when the player opens the app and ending on app close or 30 minutes of inactivity. Records: start time, duration, spin count, coins earned, coins spent, Royal Tokens spent, and whether a purchase was made.
_Avoid_: Visit, login, gameplay window

**Spin Outcome**:
The result of a single Spin. One of five tiers: Royal Flush (jackpot), Straight Flush (second tier), Full House (mid tier), Pair (small win), Loss (most frequent). Royal Spins have better odds at Straight Flush and above, and a higher payout multiplier on all winning outcomes.
_Avoid_: Result, reward, prize

### Currency

**Coins**:
The free virtual currency. Earned through Spins, daily bonuses, and purchasable with real money. Used to fund regular Spins.
_Avoid_: Credits, chips, gold

**Royal Tokens**:
The premium virtual currency. Purchased with real money only. Used exclusively to fund Royal Spins.
_Avoid_: Gems, premium currency, tokens (too generic)

**Coin Bundle**:
A fixed-price IAP that converts real money to Coins. Three tiers: Small ($1.99 → 1,000 Coins), Medium ($4.99 → 3,000 Coins), Large ($19.99 → 15,000 Coins).
_Avoid_: Coin pack, purchase tier

**Royal Token Bundle**:
A fixed-price IAP that converts real money to Royal Tokens. Three tiers: Starter (10 tokens, $0.99), Standard (50 tokens, $3.99), Value (200 tokens, $9.99).
_Avoid_: Token pack, token purchase

### Players and activity

**Player**:
A simulated user of Royal Flush Casino.
_Avoid_: User, account, customer

**Active Player**:
A Player who completed at least one Spin on a given calendar day. Players who only log in to collect a daily bonus are not Active Players.
_Avoid_: Engaged user, logged-in user

**DAU (Daily Active Users)**:
The count of distinct Active Players on a given calendar day.

### Spend segments

**Minnow**:
A Player with $0–$4.99 in lifetime real-money spend. The majority of the player base.
_Avoid_: Free player, casual player (a Minnow may have spent a small amount)

**Dolphin**:
A Player with $5–$49.99 in lifetime real-money spend.

**Whale**:
A Player with $50+ in lifetime real-money spend. Represents ~3% of Players but drives 80%+ of revenue.
_Avoid_: VIP, high-value player, big spender

### Players and lifecycle

**Platform**:
The device platform a Player uses — iOS or Android. Set at install, never changes. iOS Players have higher average spend than Android Players; this difference is modelled in Session frequency and purchase probability.
_Avoid_: Device, OS, operating system

**Install Date**:
The calendar date a Player completed their first Spin. The anchor for all retention calculations.
_Avoid_: Registration date, signup date, join date

**FTD (First Time Depositor)**:
A Player who has made their first ever real-money purchase (Coins or Royal Tokens). Becoming an FTD is a one-time, irreversible state change.
_Avoid_: Converted player, paying player (use FTD for the first-purchase milestone specifically)

**Cohort**:
A group of Players who share the same Install Date (or install week/month). Used to compare retention and spend curves across groups with equal time-in-game.
_Avoid_: Segment, group, batch

### A/B test

**Experiment**:
The 90-day Royal Spin A/B test running July 1 – September 28, 2024. Applies to new Players only, assigned 50/50 on Install Date.

**Control Group**:
Players in the Experiment who have no access to Royal Spin.
_Avoid_: Holdout, baseline group

**Treatment Group**:
Players in the Experiment who have access to Royal Spin from day 1 of their Install Date.
_Avoid_: Test group, variant group

**Royal Token Conversion Rate**:
The percentage of Treatment Group Players who purchased Royal Tokens at least once during the test window.

### KPIs

**ARPU (Average Revenue Per User)**:
Total real-money revenue (from Coin purchases + Royal Token purchases) divided by the number of Active Players in the measurement period.

**Retention**:
Whether a Player completed at least one Spin on exactly day N relative to their Install Date. Measured at D1, D7, and D30.
_Avoid_: Re-engagement, reactivation (those imply a lapsed player returning, not a retained one)

**Churn**:
A Player is Churned if they have not completed a Spin in 7 consecutive calendar days.
_Avoid_: Inactive, lapsed, dormant

### Simulation

**Simulation Period**:
April 1 – September 28, 2024. Three months of pre-test baseline (April–June) followed by the 90-day Experiment window (July–September).

**Geographic Distribution**:
The simulated player population is drawn from six markets: US (48%), UK (13%), Germany (9%), Canada (8%), Australia (7%), Other (15%). Weights reflect 2024 social casino market data — North America dominates at ~56% combined (US + Canada), Europe accounts for ~22% (UK + Germany). Used to add geographic dimension to dashboard slices.
_Avoid_: Region, locale, territory

## Example dialogue

> **Dev**: A Player logged in three times yesterday, collected a daily bonus, but never hit the Spin button. Do they count toward DAU?
>
> **Analyst**: No. An Active Player requires at least one completed Spin. Login and bonus collection don't qualify.
>
> **Dev**: What if they're in the Treatment Group and bought Royal Tokens but ran out of time before spinning?
>
> **Analyst**: Still not Active. A purchase without a Spin doesn't count. The Churn timer isn't reset either — that's Spin-only.
>
> **Dev**: If a Whale in the Treatment Group hits a Royal Flush on a Royal Spin, which revenue stream does that Spin's cost go into?
>
> **Analyst**: Royal Token purchases. The Royal Token purchase is logged as a transaction when the Tokens are bought, not when the Spin is placed. The Spin outcome is separate from the revenue event.
>
> **Dev**: For D7 retention, do we look at the 7-day window or exactly day 7?
>
> **Analyst**: Exactly day 7 — the calendar date that is seven days after the Player's Install Date. A Player active on days 6 and 8 but not day 7 is not D7-retained.
