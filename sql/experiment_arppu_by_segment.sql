SELECT 
    CASE WHEN p.experiment_group IS NULL THEN 'Pre-experiment' 
         ELSE p.experiment_group END AS experiment_group,
    p.spend_segment,
    ROUND(SUM(t.amount_usd) / COUNT(DISTINCT t.player_id), 2) AS arppu
FROM 
	players p
	LEFT JOIN 
	transactions t ON p.player_id = t.player_id
WHERE
	p.experiment_group IN ('Control', 'Treatment')
GROUP BY 
	p.experiment_group, p.spend_segment
ORDER BY 
	p.experiment_group, p.spend_segment;