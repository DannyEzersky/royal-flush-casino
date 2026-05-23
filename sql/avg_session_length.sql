SELECT
	session_date,
	ROUND(AVG(duration_seconds / 60), 2) AS avg_session_minutes
FROM
	sessions
GROUP BY
	session_date
ORDER BY
	session_date