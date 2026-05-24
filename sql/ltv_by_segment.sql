SELECT
    p.spend_segment,
    COUNT(DISTINCT p.player_id)                              AS total_players,
    COUNT(DISTINCT t.player_id)                              AS paying_players,
    ROUND(COUNT(DISTINCT t.player_id) * 100.0
          / COUNT(DISTINCT p.player_id), 2)                  AS conversion_pct,
    ROUND(COALESCE(SUM(t.amount_usd), 0)
          / COUNT(DISTINCT p.player_id), 2)                  AS ltv_all_players,
    ROUND(COALESCE(SUM(t.amount_usd), 0)
          / NULLIF(COUNT(DISTINCT t.player_id), 0), 2)       AS ltv_paying_only
FROM players p
LEFT JOIN transactions t ON t.player_id = p.player_id
GROUP BY p.spend_segment
ORDER BY ltv_all_players DESC;
