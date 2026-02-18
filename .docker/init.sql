-- Initialize database schema

CREATE TABLE users_profile (
    id           BIGSERIAL PRIMARY KEY,
    email        TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_profile_email ON users_profile (email);

CREATE TABLE posts (
    id           BIGSERIAL PRIMARY KEY,
    fk_user_id   BIGINT NOT NULL REFERENCES users_profile(id),
    content      TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE INDEX idx_posts_fk_user_id ON posts (fk_user_id);
CREATE INDEX idx_posts_created_at ON posts (created_at);

CREATE TABLE comments (
    id           BIGSERIAL PRIMARY KEY,
    fk_user_id   BIGINT NOT NULL REFERENCES users_profile(id),
    fk_post_id   BIGINT NOT NULL REFERENCES posts(id),
    content      TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comments_fk_post_id ON comments (fk_post_id);
CREATE INDEX idx_comments_fk_user_id ON comments (fk_user_id);

CREATE TABLE friends (
    user_id      BIGINT NOT NULL REFERENCES users_profile(id),
    friend_id    BIGINT NOT NULL REFERENCES users_profile(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, friend_id),
    CHECK (user_id <> friend_id)
);

CREATE INDEX idx_friends_user_id ON friends (user_id);
CREATE INDEX idx_friends_friend_id ON friends (friend_id);

-- Insert sample data


SET synchronous_commit = off;

INSERT INTO users_profile (email, name)
SELECT
    'user' || gs || '@example.com',
    'User ' || gs
FROM generate_series(1, 1000000) gs;


INSERT INTO posts (fk_user_id, content)
SELECT
    u.id,
    'Post content from user ' || u.id || ' #' || gs
FROM users_profile u
JOIN LATERAL generate_series(1, (10 + floor(random() * 41))::int) gs ON true;

INSERT INTO comments (fk_user_id, fk_post_id, content)
SELECT
    (random() * 1000000)::bigint + 1,
    p.id,
    'Comment on post ' || p.id
FROM posts p
JOIN LATERAL generate_series(1, (floor(random() * 11))::int) gs ON true;

INSERT INTO friends (user_id, friend_id)
SELECT
    u.id,
    (random() * 1000000)::bigint + 1
FROM users_profile u
JOIN generate_series(1, 20) gs ON true
ON CONFLICT DO NOTHING;

ANALYZE;

SET synchronous_commit = on;

