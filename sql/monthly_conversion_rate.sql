SELECT
	STRFTIME('%Y-%m', p.install_date),
	ROUND(COUNT(ftd.ftd) * 100.0 / COUNT(DISTINCT p.player_id), 2) AS monthly_conversion_rate
FROM
	players p
	LEFT JOIN
	-- Subquery: get FTD
	(
		SELECT 
			player_id, 
			MIN(transaction_date) AS ftd 
		FROM 
			transactions 
		GROUP BY 
			player_id
	) ftd
	ON ftd.player_id = p.player_id
WHERE 
	p.install_date <= DATE((SELECT MAX(install_date) FROM players), '-30 day')
GROUP BY
	STRFTIME('%Y-%m', p.install_date)
ORDER BY
	STRFTIME('%Y-%m', p.install_date);