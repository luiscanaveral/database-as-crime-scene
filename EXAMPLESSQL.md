# Example SQL Queries

## Schema Overview

- **users_profile** — user accounts (id, email, name, created_at)
- **posts** — user posts (id, fk_user_id, content, created_at)
- **comments** — comments on posts (id, fk_user_id, fk_post_id, content, created_at)
- **friends** — bidirectional friendships (user_id, friend_id, created_at)
- **metrics** — time-series app metrics (id, metric_name, value, recorded_at)
- **events** — app events (id UUID, user_id, event_type, created_at)
- **logs** — app logs (id, session_id, message, timestamp)

---

## Long-Running Queries

### 1. Full scan on telemetry — no time filter

```sql
SELECT metric_name, avg(value), max(value), min(value), count(*)
FROM metrics
GROUP BY metric_name;
```

### 2. Aggregation over the entire events table

```sql
SELECT event_type, count(*), count(DISTINCT user_id)
FROM events
GROUP BY event_type
ORDER BY count(*) DESC;
```

### 3. Text search on logs — no index on `message`

```sql
SELECT session_id, count(*) AS error_count
FROM logs
WHERE message ILIKE '%error%'
   OR message ILIKE '%fail%'
   OR message ILIKE '%timeout%'
GROUP BY session_id
ORDER BY error_count DESC;
```

### 4. Cross-table aggregation without filters

```sql
SELECT
    u.id,
    u.name,
    (SELECT count(*) FROM posts WHERE fk_user_id = u.id) AS post_count,
    (SELECT count(*) FROM comments WHERE fk_user_id = u.id) AS comment_count,
    (SELECT count(*) FROM friends WHERE user_id = u.id OR friend_id = u.id) AS friend_count
FROM users_profile u
ORDER BY u.id;
```

### 5. All posts + comments for every user — multiple sequential scans

```sql
SELECT
    u.name,
    p.content                                           AS post_content,
    p.created_at                                        AS post_date,
    c.content                                           AS comment_content,
    c.created_at                                        AS comment_date,
    cu.name                                             AS commenter_name
FROM users_profile u
    JOIN posts p ON p.fk_user_id = u.id
    JOIN comments c ON c.fk_post_id = p.id
    JOIN users_profile cu ON cu.id = c.fk_user_id
ORDER BY u.id, p.created_at;
```

### 6. Friend-of-friend expansion (explosive join)

```sql
SELECT
    u.id      AS user_id,
    u.name    AS user_name,
    f2.friend_id AS friend_of_friend_id,
    uf.name   AS friend_of_friend_name
FROM users_profile u
    JOIN friends f1 ON f1.user_id = u.id
    JOIN friends f2 ON f2.user_id = f1.friend_id
    JOIN users_profile uf ON uf.id = f2.friend_id
WHERE u.id <> f2.friend_id
ORDER BY u.id;
```

### 7. Time-series self-join — compare consecutive metric readings

```sql
SELECT
    a.metric_name,
    a.recorded_at                           AS current_ts,
    a.value                                 AS current_value,
    b.recorded_at                           AS previous_ts,
    b.value                                 AS previous_value,
    (a.value - b.value) / NULLIF(b.value, 0) * 100 AS pct_change
FROM metrics a
    JOIN metrics b
        ON b.metric_name = a.metric_name
        AND b.recorded_at = (
            SELECT max(recorded_at)
            FROM metrics
            WHERE metric_name = a.metric_name
              AND recorded_at < a.recorded_at
        )
ORDER BY a.metric_name, a.recorded_at;
```

---

## Join Types

### 8. INNER JOIN — users with their posts

```sql
SELECT u.name, p.content, p.created_at
FROM users_profile u
    JOIN posts p ON p.fk_user_id = u.id;
```

### 9. LEFT JOIN — all users, with or without posts

```sql
SELECT u.name, p.id AS post_id, p.content
FROM users_profile u
    LEFT JOIN posts p ON p.fk_user_id = u.id
ORDER BY u.name;
```

### 10. RIGHT JOIN — posts and their commenters (less common, mirror of LEFT JOIN)

```sql
SELECT p.id AS post_id, u.name AS commenter, c.content
FROM comments c
    RIGHT JOIN posts p ON p.id = c.fk_post_id
    LEFT JOIN users_profile u ON u.id = c.fk_user_id;
```

### 11. FULL OUTER JOIN — match friendships in both directions

```sql
SELECT
    COALESCE(f1.user_id, f2.friend_id)   AS user_id,
    COALESCE(f1.friend_id, f2.user_id)   AS friend_id
FROM friends f1
    FULL OUTER JOIN friends f2
        ON f2.user_id = f1.friend_id
        AND f2.friend_id = f1.user_id
WHERE f1.user_id IS NULL OR f2.user_id IS NULL;
```

### 12. SELF JOIN — mutual friends recommendation

```sql
SELECT
    f1.user_id      AS user_a,
    f2.friend_id    AS suggested_friend,
    count(*)        AS mutual_count
FROM friends f1
    JOIN friends f2 ON f2.user_id = f1.friend_id
WHERE f2.friend_id <> f1.user_id
  AND (f1.user_id, f2.friend_id) NOT IN (
    SELECT user_id, friend_id FROM friends
)
GROUP BY f1.user_id, f2.friend_id
ORDER BY mutual_count DESC;
```

### 13. CROSS JOIN — all users × all event types (analytics grid)

```sql
SELECT
    u.id      AS user_id,
    e_types.event_type,
    count(e.id) AS event_count
FROM users_profile u
    CROSS JOIN (
        SELECT DISTINCT event_type FROM events
    ) e_types
    LEFT JOIN events e
        ON e.user_id = u.id
        AND e.event_type = e_types.event_type
GROUP BY u.id, e_types.event_type
ORDER BY u.id, e_types.event_type;
```

### 14. Semi-join via EXISTS — users who have commented

```sql
SELECT u.id, u.name, u.email
FROM users_profile u
WHERE EXISTS (
    SELECT 1
    FROM comments c
    WHERE c.fk_user_id = u.id
);
```

### 15. Anti-join via NOT EXISTS — users who never posted

```sql
SELECT u.id, u.name, u.email
FROM users_profile u
WHERE NOT EXISTS (
    SELECT 1
    FROM posts p
    WHERE p.fk_user_id = u.id
);
```

### 16. LATERAL join — top 3 comments per post

```sql
SELECT
    p.id        AS post_id,
    c.id        AS comment_id,
    c.content   AS comment_text,
    u.name      AS commenter
FROM posts p
    CROSS JOIN LATERAL (
        SELECT id, content, fk_user_id
        FROM comments
        WHERE fk_post_id = p.id
        ORDER BY created_at DESC
        LIMIT 3
    ) c
    JOIN users_profile u ON u.id = c.fk_user_id
ORDER BY p.id, c.id;
```

### 17. Multi-way join with aggregation — user engagement summary

```sql
SELECT
    u.id,
    u.name,
    count(DISTINCT p.id)                              AS total_posts,
    count(DISTINCT c.id)                              AS total_comments_received,
    count(DISTINCT fr.user_id)                        AS friend_count
FROM users_profile u
    LEFT JOIN posts p ON p.fk_user_id = u.id
    LEFT JOIN comments c ON c.fk_post_id = p.id
    LEFT JOIN friends fr ON fr.friend_id = u.id
GROUP BY u.id, u.name
ORDER BY total_posts DESC;
```
