SELECT
	p.experiment_group,
	ROUND(
		COUNT(DISTINCT CASE
			WHEN s.session_date = DATE(p.install_date, '+1 day') AND s.spin_count >= 1
			THEN p.player_id
		END) * 100.00 / COUNT(DISTINCT p.player_id), 2
	 ) AS d1_retention,
	 ROUND(
		COUNT(DISTINCT CASE
			WHEN s.session_date = DATE(p.install_date, '+7 day') AND s.spin_count >= 1
			THEN p.player_id
		END) * 100.00 / COUNT(DISTINCT p.player_id), 2
	 ) AS d7_retention,
	 ROUND(
		COUNT(DISTINCT CASE
			WHEN s.session_date = DATE(p.install_date, '+30 day') AND s.spin_count >= 1
			THEN p.player_id
		END) * 100.00 / COUNT(DISTINCT p.player_id), 2
	 ) AS d30_retention
FROM
	players p
	LEFT JOIN sessions s ON p.player_id = s.player_id
WHERE 
	p.install_date <= DATE((SELECT MAX(session_date) FROM sessions), '-30 day')
	AND p.experiment_group IN ('Control', 'Treatment')
GROUP BY
	p.experiment_group
ORDER BY
	p.experiment_group;