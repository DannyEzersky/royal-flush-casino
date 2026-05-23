SELECT
	p.install_date,
	ROUND(COUNT(DISTINCT t.player_id) * 100.00 / COUNT(DISTINCT p.player_id), 2) AS ftd_30_day_rate
FROM
	players p
	LEFT JOIN (SELECT player_id, MIN(transaction_date) AS ftd_date FROM transactions GROUP BY player_id) t ON p.player_id = t.player_id AND t.ftd_date <= DATE(p.install_date, '+30 day')
WHERE
	p.install_date <= DATE((SELECT MAX(install_date) FROM players), '-30 day')
GROUP BY
	p.install_date
ORDER BY
	p.install_date;