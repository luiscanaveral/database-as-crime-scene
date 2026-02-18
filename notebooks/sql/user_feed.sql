EXPLAIN ANALYZE
    SELECT p.*
    FROM posts p
    WHERE p.fk_user_id = 12345
    ORDER BY created_at DESC
    LIMIT 20;