SELECT
    grp.experiment_group,
    ROUND(rev.payer_count * 100.0 / grp.active_players, 2) AS conversion_rate
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
        COUNT(DISTINCT t.player_id) AS payer_count
     FROM players p
     LEFT JOIN transactions t ON p.player_id = t.player_id
     GROUP BY p.experiment_group) rev
    ON grp.experiment_group = rev.experiment_group
WHERE
	grp.experiment_group IN ('Control', 'Treatment')