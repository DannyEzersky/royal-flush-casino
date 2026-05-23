SELECT
	STRFTIME('%Y-%m', session_date) AS month, 
	COUNT(DISTINCT player_id) AS mau
FROM
	sessions
WHERE 
	spin_count >= 1
GROUP BY 
	STRFTIME('%Y-%m', session_date)
ORDER BY 
	STRFTIME('%Y-%m', session_date);