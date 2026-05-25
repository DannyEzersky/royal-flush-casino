-- Cumulative LTV per install-month cohort at D7, D30, D60, D90.
-- Late cohorts will have NULL for windows that haven't fully elapsed
-- (e.g. an August cohort has no D90 data if the simulation ends in September).
SELECT
    STRFTIME('%Y-%m', p.install_date) AS install_month,
    COUNT(DISTINCT p.player_id)                                AS cohort_size,
    ROUND(
        SUM(CASE WHEN JULIANDAY(t.transaction_date) - JULIANDAY(p.install_date) <= 7
                 THEN t.amount_usd END)
        / COUNT(DISTINCT p.player_id), 2)                      AS d7_ltv,
    ROUND(
        SUM(CASE WHEN JULIANDAY(t.transaction_date) - JULIANDAY(p.install_date) <= 30
                 THEN t.amount_usd END)
        / COUNT(DISTINCT p.player_id), 2)                      AS d30_ltv,
    ROUND(
        SUM(CASE WHEN JULIANDAY(t.transaction_date) - JULIANDAY(p.install_date) <= 60
                 THEN t.amount_usd END)
        / COUNT(DISTINCT p.player_id), 2)                      AS d60_ltv,
    ROUND(
        SUM(CASE WHEN JULIANDAY(t.transaction_date) - JULIANDAY(p.install_date) <= 90
                 THEN t.amount_usd END)
        / COUNT(DISTINCT p.player_id), 2)                      AS d90_ltv
FROM players p
LEFT JOIN transactions t ON t.player_id = p.player_id
GROUP BY install_month
ORDER BY install_month;
