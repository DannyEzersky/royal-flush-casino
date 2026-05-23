SELECT
	p.install_date,
	ROUND(
		COUNT(DISTINCT CASE
			WHEN s.session_date = DATE(p.install_date, '+1 day') AND s.spin_count >= 1
			THEN p.player_id
		END) * 100.00 / COUNT(DISTINCT p.player_id), 2
	 ) AS d1_retention
FROM
	players p
	LEFT JOIN sessions s ON p.player_id = s.player_id
WHERE 
	p.install_date <= DATE((SELECT MAX(session_date) FROM sessions), '-1 day')
GROUP BY
	p.install_date
ORDER BY
	p.install_date;