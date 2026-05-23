SELECT
	s.session_date,
	ROUND(SUM(t.amount_usd) / COUNT(DISTINCT s.player_id), 2) AS arpu
FROM
	sessions s
	LEFT JOIN transactions t ON s.player_id = t.player_id AND s.session_date = t.transaction_date
GROUP BY
	s.session_date
ORDER BY
	s.session_date;