EXPLAIN ANALYZE
    SELECT p.*
    FROM friends f
    JOIN posts p ON p.fk_user_id = f.friend_id
    WHERE f.user_id = 12345
    ORDER BY p.created_at DESC
    LIMIT 50;