SELECT
    p.experiment_group,
    ROUND(AVG(s.spin_count), 2) AS avg_spins_per_session
FROM
    players p
    JOIN sessions s ON p.player_id = s.player_id
WHERE
    p.experiment_group IN ('Control', 'Treatment')
    AND s.spin_count >= 1
GROUP BY
    p.experiment_group
ORDER BY
    p.experiment_group;