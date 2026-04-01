-- Initialize database schema (DDL only)
-- This script only runs if the database hasn't been initialized yet

DO $$
BEGIN

    -- Guard: skip if already initialized
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'users_profile'
    ) THEN
        RAISE NOTICE 'Database already initialized, skipping...';
        RETURN;
    END IF;

    RAISE NOTICE 'Initializing database schema...';

    -- Tables
    CREATE TABLE users_profile (
        id           BIGSERIAL PRIMARY KEY,
        email        TEXT NOT NULL UNIQUE,
        name         TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE posts (
        id           BIGSERIAL PRIMARY KEY,
        fk_user_id   BIGINT NOT NULL,
        content      TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE comments (
        id           BIGSERIAL PRIMARY KEY,
        fk_user_id   BIGINT NOT NULL,
        fk_post_id   BIGINT NOT NULL,
        content      TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE friends (
        user_id      BIGINT NOT NULL,
        friend_id    BIGINT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, friend_id),
        CHECK (user_id <> friend_id)
    );

    -- Indexes
    CREATE INDEX idx_users_profile_email ON users_profile (email);
    CREATE INDEX idx_posts_fk_user_id ON posts (fk_user_id);
    CREATE INDEX idx_posts_created_at ON posts (created_at);
    CREATE INDEX idx_comments_fk_post_id ON comments (fk_post_id);
    CREATE INDEX idx_comments_fk_user_id ON comments (fk_user_id);
    CREATE INDEX idx_friends_user_id ON friends (user_id);
    CREATE INDEX idx_friends_friend_id ON friends (friend_id);

    -- Foreign keys
    ALTER TABLE posts
        ADD CONSTRAINT posts_fk_user
        FOREIGN KEY (fk_user_id) REFERENCES users_profile(id);

    ALTER TABLE comments
        ADD CONSTRAINT comments_fk_user
        FOREIGN KEY (fk_user_id) REFERENCES users_profile(id);

    ALTER TABLE comments
        ADD CONSTRAINT comments_fk_post
        FOREIGN KEY (fk_post_id) REFERENCES posts(id);

    ALTER TABLE friends
        ADD CONSTRAINT friends_fk_user
        FOREIGN KEY (user_id) REFERENCES users_profile(id);

    ALTER TABLE friends
        ADD CONSTRAINT friends_fk_friend
        FOREIGN KEY (friend_id) REFERENCES users_profile(id);

    RAISE NOTICE 'Schema initialization complete!';

END $$;
