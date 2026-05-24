SELECT
    d.session_date,
    ROUND(COALESCE(p.paying_dau, 0) * 100.0 / d.dau, 2) AS payer_ratio_pct
FROM (
    SELECT session_date, COUNT(DISTINCT player_id) AS dau
    FROM sessions
    WHERE spin_count >= 1
    GROUP BY session_date
) d
LEFT JOIN (
    SELECT transaction_date, COUNT(DISTINCT player_id) AS paying_dau
    FROM transactions
    GROUP BY transaction_date
) p ON p.transaction_date = d.session_date
ORDER BY
    d.session_date;
