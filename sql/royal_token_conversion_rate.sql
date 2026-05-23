SELECT
	ROUND(COUNT(DISTINCT t.player_id) * 100.0 / COUNT(DISTINCT p.player_id), 2) AS royal_token_conversion_rate
FROM
	players p 
	LEFT JOIN transactions t ON p.player_id = t.player_id AND t.currency_type = 'royal_token'
WHERE
	p.experiment_group = 'Treatment'