SELECT
	session_date, 
	COUNT(DISTINCT player_id) AS dau
FROM
	sessions
WHERE 
	spin_count >= 1
GROUP BY 
	session_date
ORDER BY 
	session_date;