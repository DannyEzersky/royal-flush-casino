SELECT
	session_date,
	ROUND(AVG(spin_count), 2) AS avg_spin_count
FROM
	sessions
GROUP BY
	session_date
ORDER BY
	session_date;