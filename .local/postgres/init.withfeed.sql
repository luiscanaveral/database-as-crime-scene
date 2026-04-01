-- Initialize database schema
-- This script only runs if the database hasn't been initialized yet

DO $$
BEGIN
    -- Check if tables already exist
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users_profile'
    ) THEN
        RAISE NOTICE 'Database already initialized, skipping initialization...';
    ELSE
        RAISE NOTICE 'Initializing database...';
        RAISE NOTICE 'Start time: %', clock_timestamp();
        
        -- Create tables
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

        -- Insert sample data
        RAISE NOTICE 'Creating sample data - Start time: %', clock_timestamp();
        SET synchronous_commit = off;
        PERFORM pg_reload_conf();

        RAISE NOTICE 'Inserting users...';
        INSERT INTO users_profile (email, name)
        SELECT
            'user' || gs || '@example.com',
            'User ' || gs
        FROM generate_series(1, 1000000) gs;

        RAISE NOTICE 'Inserting posts...';
        INSERT INTO posts (fk_user_id, content)
        SELECT
            u.id,
            'Post content from user ' || u.id || ' #' || gs
        FROM users_profile u
        JOIN LATERAL generate_series(1, (10 + floor(random() * 41))::int) gs ON true;

        RAISE NOTICE 'Inserting comments...';
        WITH max_user AS (
            SELECT max(id) AS max_id FROM users_profile
        )
        INSERT INTO comments (fk_user_id, fk_post_id, content)
        SELECT
            floor(random() * max_user.max_id)::bigint + 1,
            p.id,
            'Comment on post ' || p.id
        FROM posts p
        CROSS JOIN max_user
        JOIN LATERAL generate_series(1, (floor(random() * 11))::int) gs ON true;

        RAISE NOTICE 'Inserting friends...';
        WITH max_user AS (
            SELECT max(id) AS max_id FROM users_profile
        )
        INSERT INTO friends (user_id, friend_id)
        SELECT
            LEAST(u.id, friend_id),
            GREATEST(u.id, friend_id)
        FROM users_profile u
        CROSS JOIN max_user
        JOIN LATERAL (
            SELECT floor(random() * max_user.max_id)::bigint + 1 AS friend_id
        ) r ON true
        JOIN generate_series(1, 20) gs ON true
        WHERE u.id <> friend_id
        ON CONFLICT DO NOTHING;

        RAISE NOTICE 'Running ANALYZE...';
        ANALYZE;
        SET synchronous_commit = on;

        -- create indexes and foreign keys after bulk load
        RAISE NOTICE 'Creating indexes...';
        CREATE INDEX idx_users_profile_email ON users_profile (email);
        CREATE INDEX idx_posts_fk_user_id ON posts (fk_user_id);
        CREATE INDEX idx_posts_created_at ON posts (created_at);
        CREATE INDEX idx_comments_fk_post_id ON comments (fk_post_id);
        CREATE INDEX idx_comments_fk_user_id ON comments (fk_user_id);
        CREATE INDEX idx_friends_user_id ON friends (user_id);
        CREATE INDEX idx_friends_friend_id ON friends (friend_id);

        RAISE NOTICE 'Creating foreign keys...';
        ALTER TABLE posts
        ADD CONSTRAINT posts_fk_user
        FOREIGN KEY (fk_user_id)
        REFERENCES users_profile(id);

        ALTER TABLE comments
        ADD CONSTRAINT comments_fk_user
        FOREIGN KEY (fk_user_id)
        REFERENCES users_profile(id);

        ALTER TABLE comments
        ADD CONSTRAINT comments_fk_post
        FOREIGN KEY (fk_post_id)
        REFERENCES posts(id);

        ALTER TABLE friends
        ADD CONSTRAINT friends_fk_user
        FOREIGN KEY (user_id)
        REFERENCES users_profile(id);

        ALTER TABLE friends
        ADD CONSTRAINT friends_fk_friend
        FOREIGN KEY (friend_id)
        REFERENCES users_profile(id);
        
        RAISE NOTICE 'Database initialization complete!';
        RAISE NOTICE 'End time: %', clock_timestamp();
    END IF;
END $$;
