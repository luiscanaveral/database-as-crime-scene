EXPLAIN ANALYZE
    SELECT p.id, count(c.id)
    FROM posts p
    LEFT JOIN comments c ON c.fk_post_id = p.id
    WHERE p.fk_user_id = 12345
    GROUP BY p.id;