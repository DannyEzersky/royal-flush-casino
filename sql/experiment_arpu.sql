SELECT
    grp.experiment_group,
    ROUND(rev.total_revenue / grp.active_players, 2) AS arpu
FROM
    (SELECT 
        CASE WHEN p.experiment_group IS NULL THEN 'Pre-experiment' 
             ELSE p.experiment_group END AS experiment_group,
        COUNT(DISTINCT s.player_id) AS active_players
     FROM players p
     LEFT JOIN sessions s ON p.player_id = s.player_id AND s.spin_count >= 1
     GROUP BY p.experiment_group) grp
    JOIN
    (SELECT 
        CASE WHEN p.experiment_group IS NULL THEN 'Pre-experiment' 
             ELSE p.experiment_group END AS experiment_group,
        SUM(t.amount_usd) AS total_revenue
     FROM players p
     LEFT JOIN transactions t ON p.player_id = t.player_id
     GROUP BY p.experiment_group) rev
    ON grp.experiment_group = rev.experiment_group
WHERE
	grp.experiment_group IN ('Control', 'Treatment');