SELECT
	CASE WHEN p.experiment_group IS NULL THEN 'Pre-experiment' 
		 ELSE p.experiment_group END AS experiment_group,
	ROUND(COUNT(DISTINCT t.player_id) * 100.00 / COUNT(DISTINCT p.player_id), 2) AS ftd_30_day_rate
FROM
	players p
	LEFT JOIN (SELECT player_id, MIN(transaction_date) AS ftd_date FROM transactions GROUP BY player_id) t ON p.player_id = t.player_id AND t.ftd_date <= DATE(p.install_date, '+30 day')
WHERE
	p.install_date <= DATE((SELECT MAX(install_date) FROM players), '-30 day')
	AND p.experiment_group IN ('Control', 'Treatment')
GROUP BY
	p.experiment_group
ORDER BY
	p.experiment_group;