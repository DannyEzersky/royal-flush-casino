SELECT
    d.date AS churn_date,
    COUNT(DISTINCT s.player_id) AS churned_players
FROM (
    SELECT DISTINCT session_date AS date 
    FROM sessions
) d
JOIN (
    SELECT player_id, MAX(session_date) AS last_session
    FROM sessions
    GROUP BY player_id
) s ON s.last_session = DATE(d.date, '-7 day')
GROUP BY d.date
ORDER BY d.date;