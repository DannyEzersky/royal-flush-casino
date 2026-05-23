SELECT
    dau.month,
    ROUND(dau.avg_dau * 100.0 / mau.mau, 2) AS dau_mau_ratio
FROM
	-- Subquery 1: average DAU per month
	(
		SELECT 
			STRFTIME('%Y-%m', session_date) AS month,
			AVG(daily_dau) AS avg_dau
		FROM (
			SELECT session_date, COUNT(DISTINCT player_id) AS daily_dau
			FROM sessions
			WHERE spin_count >= 1
			GROUP BY session_date
		)
		GROUP BY STRFTIME('%Y-%m', session_date)
	) dau
    JOIN
    -- Subquery 2: MAU per month
	(
		SELECT 
			STRFTIME('%Y-%m', session_date) AS month,
			COUNT(DISTINCT player_id) AS mau
		FROM 
			sessions
		WHERE 
			spin_count >= 1
		GROUP BY 
			STRFTIME('%Y-%m', session_date)
	) mau
    ON dau.month = mau.month
ORDER BY 
	dau.month;