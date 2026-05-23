SELECT
	transaction_date,
	ROUND(SUM(amount_usd) / COUNT(DISTINCT player_id), 2) AS arppu
FROM
	transactions
GROUP BY
	transaction_date
ORDER BY
	transaction_date;