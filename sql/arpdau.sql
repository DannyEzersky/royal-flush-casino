SELECT
    d.session_date,
    ROUND(COALESCE(r.daily_rev, 0) / d.dau, 4) AS arpdau
FROM (
    SELECT session_date, COUNT(DISTINCT player_id) AS dau
    FROM sessions
    WHERE spin_count >= 1
    GROUP BY session_date
) d
LEFT JOIN (
    SELECT transaction_date, SUM(amount_usd) AS daily_rev
    FROM transactions
    GROUP BY transaction_date
) r ON r.transaction_date = d.session_date
ORDER BY
    d.session_date;
