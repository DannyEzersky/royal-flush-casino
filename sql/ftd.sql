SELECT
    ftd_date,
    COUNT(player_id) AS ftd_count
FROM (
    SELECT 
		player_id, MIN(transaction_date) AS ftd_date
	FROM 
		transactions
	GROUP BY 
		player_id
)
GROUP BY 
	ftd_date
ORDER BY 
	ftd_date;