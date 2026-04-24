"""
Data feeding utilities for adding more data to the database.
Based on the schema defined in init.sql
"""

from datetime import datetime
from typing import List, Optional, Tuple

from faker import Faker
from sqlalchemy import text

from ..common.logger import log
from .connection import get_engine

fake = Faker()


def add_users(users: List[Tuple[str, str]], batch_size: int = 1000) -> int:
    """
    Add new users to the users_profile table.

    Args:
        users: List of tuples (email, name)
        batch_size: Number of records to insert per batch

    Returns:
        Number of users inserted
    """
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(users), batch_size):
            batch = users[i : i + batch_size]
            values = ", ".join([f"('{email}', '{name}')" for email, name in batch])

            query = text(f"""
                INSERT INTO users_profile (email, name)
                VALUES {values}
                ON CONFLICT (email) DO NOTHING
            """)

            result = conn.execute(query)
            inserted += result.rowcount

    return inserted


def add_posts(posts: List[Tuple[int, str]], batch_size: int = 1000) -> int:
    """
    Add new posts to the posts table.

    Args:
        posts: List of tuples (user_id, content)
        batch_size: Number of records to insert per batch

    Returns:
        Number of posts inserted
    """
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(posts), batch_size):
            batch = posts[i : i + batch_size]
            values = ", ".join(
                [f"({user_id}, '{content}')" for user_id, content in batch]
            )

            query = text(f"""
                INSERT INTO posts (fk_user_id, content)
                VALUES {values}
            """)

            result = conn.execute(query)
            inserted += result.rowcount

    return inserted


def add_comments(comments: List[Tuple[int, int, str]], batch_size: int = 1000) -> int:
    """
    Add new comments to the comments table.

    Args:
        comments: List of tuples (user_id, post_id, content)
        batch_size: Number of records to insert per batch

    Returns:
        Number of comments inserted
    """
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(comments), batch_size):
            batch = comments[i : i + batch_size]
            values = ", ".join(
                [
                    f"({user_id}, {post_id}, '{content}')"
                    for user_id, post_id, content in batch
                ]
            )

            query = text(f"""
                INSERT INTO comments (fk_user_id, fk_post_id, content)
                VALUES {values}
            """)

            result = conn.execute(query)
            inserted += result.rowcount

    return inserted


def add_friends(friendships: List[Tuple[int, int]], batch_size: int = 1000) -> int:
    """
    Add new friendships to the friends table.

    Args:
        friendships: List of tuples (user_id, friend_id)
        batch_size: Number of records to insert per batch

    Returns:
        Number of friendships inserted
    """
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(friendships), batch_size):
            batch = friendships[i : i + batch_size]
            values = ", ".join(
                [f"({user_id}, {friend_id})" for user_id, friend_id in batch]
            )

            query = text(f"""
                INSERT INTO friends (user_id, friend_id)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """)

            result = conn.execute(query)
            inserted += result.rowcount

    return inserted


def generate_bulk_users(
    start_id: int,
    count: int,
    email_template: str = "user{}@example.com",
    name_template: str = "User {}",
) -> int:
    """
    Generate and insert bulk users using database-side generation.

    Args:
        start_id: Starting ID for user generation
        count: Number of users to generate
        email_template: Email template with {} placeholder
        name_template: Name template with {} placeholder

    Returns:
        Number of users inserted
    """
    engine = get_engine()

    with engine.begin() as conn:
        query = text(f"""
            INSERT INTO users_profile (email, name)
            SELECT
                '{email_template.replace("{}", "' || gs || '")}',
                '{name_template.replace("{}", "' || gs || '")}'
            FROM generate_series(:start_id, :end_id) gs
            ON CONFLICT (email) DO NOTHING
        """)

        result = conn.execute(
            query, {"start_id": start_id, "end_id": start_id + count - 1}
        )

    return result.rowcount


def generate_bulk_posts_for_users(
    user_ids: Optional[List[int]] = None,
    posts_per_user_min: int = 10,
    posts_per_user_max: int = 50,
    content_template: str = "Post content from user {} #{}",
) -> int:
    """
    Generate and insert bulk posts for users.

    Args:
        user_ids: List of user IDs (None = all users)
        posts_per_user_min: Minimum posts per user
        posts_per_user_max: Maximum posts per user
        content_template: Content template with {} placeholders

    Returns:
        Number of posts inserted
    """
    engine = get_engine()

    with engine.begin() as conn:
        user_filter = ""
        if user_ids:
            user_filter = f"WHERE u.id IN ({','.join(map(str, user_ids))})"

        query = text(f"""
            INSERT INTO posts (fk_user_id, content)
            SELECT
                u.id,
                'Post content from user ' || u.id || ' #' || gs
            FROM users_profile u
            {user_filter}
            JOIN LATERAL generate_series(
                1, 
                (:min_posts + floor(random() * (:max_posts - :min_posts + 1))::int)
            ) gs ON true
        """)

        result = conn.execute(
            query, {"min_posts": posts_per_user_min, "max_posts": posts_per_user_max}
        )

    return result.rowcount


def generate_bulk_comments_for_posts(
    post_ids: Optional[List[int]] = None, comments_per_post_max: int = 10
) -> int:
    """
    Generate and insert bulk comments for posts.

    Args:
        post_ids: List of post IDs (None = all posts)
        comments_per_post_max: Maximum comments per post

    Returns:
        Number of comments inserted
    """
    engine = get_engine()

    with engine.begin() as conn:
        post_filter = ""
        if post_ids:
            post_filter = f"WHERE p.id IN ({','.join(map(str, post_ids))})"

        query = text(f"""
            WITH max_user AS (
                SELECT max(id) AS max_id FROM users_profile
            )
            INSERT INTO comments (fk_user_id, fk_post_id, content)
            SELECT
                floor(random() * max_user.max_id)::bigint + 1,
                p.id,
                'Comment on post ' || p.id || ' #' || gs
            FROM posts p
            CROSS JOIN max_user
            {post_filter}
            JOIN LATERAL generate_series(
                1, 
                (floor(random() * :max_comments)::int)
            ) gs ON true
        """)

        result = conn.execute(query, {"max_comments": comments_per_post_max + 1})

    return result.rowcount


def generate_bulk_friendships(
    user_ids: Optional[List[int]] = None, friendships_per_user: int = 20
) -> int:
    """
    Generate and insert bulk friendships.

    Args:
        user_ids: List of user IDs (None = all users)
        friendships_per_user: Number of friendships per user

    Returns:
        Number of friendships inserted
    """
    engine = get_engine()

    with engine.begin() as conn:
        user_filter = ""
        if user_ids:
            user_filter = f"WHERE u.id IN ({','.join(map(str, user_ids))})"

        query = text(f"""
            WITH max_user AS (
                SELECT max(id) AS max_id FROM users_profile
            )
            INSERT INTO friends (user_id, friend_id)
            SELECT
                LEAST(u.id, friend_id),
                GREATEST(u.id, friend_id)
            FROM users_profile u
            CROSS JOIN max_user
            {user_filter}
            JOIN LATERAL (
                SELECT floor(random() * max_user.max_id)::bigint + 1 AS friend_id
            ) r ON true
            JOIN generate_series(1, :friendships_per_user) gs ON true
            WHERE u.id <> friend_id
            ON CONFLICT DO NOTHING
        """)

        result = conn.execute(query, {"friendships_per_user": friendships_per_user})

    return result.rowcount


# Faker-based data generation functions


def generate_fake_users(count: int, batch_size: int = 1000) -> int:
    """
    Generate and insert fake users using Faker.

    Args:
        count: Number of users to generate
        batch_size: Number of records to insert per batch

    Returns:
        Number of users inserted
    """
    users = [(fake.unique.email(), fake.name()) for _ in range(count)]
    return add_users(users, batch_size)


def generate_fake_posts(
    user_ids: Optional[List[int]] = None,
    posts_per_user: int = 10,
    batch_size: int = 1000,
) -> int:
    """
    Generate and insert fake posts using Faker.

    Args:
        user_ids: List of user IDs (None = fetch from database)
        posts_per_user: Number of posts per user
        batch_size: Number of records to insert per batch

    Returns:
        Number of posts inserted
    """
    if user_ids is None:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM users_profile"))
            user_ids = [row[0] for row in result]

    posts = []
    for user_id in user_ids:
        for _ in range(posts_per_user):
            content = fake.paragraph(nb_sentences=3)
            posts.append((user_id, content))

    return add_posts(posts, batch_size)


def generate_fake_comments(
    post_ids: Optional[List[int]] = None,
    comments_per_post: int = 5,
    batch_size: int = 1000,
) -> int:
    """
    Generate and insert fake comments using Faker.

    Args:
        post_ids: List of post IDs (None = fetch from database)
        comments_per_post: Number of comments per post
        batch_size: Number of records to insert per batch

    Returns:
        Number of comments inserted
    """
    engine = get_engine()

    if post_ids is None:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM posts"))
            post_ids = [row[0] for row in result]

    # Get user IDs for random assignment
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM users_profile"))
        user_ids = [row[0] for row in result]

    if not user_ids:
        return 0

    comments = []
    for post_id in post_ids:
        for _ in range(comments_per_post):
            user_id = fake.random_element(user_ids)
            content = fake.sentence(nb_words=10)
            comments.append((user_id, post_id, content))

    return add_comments(comments, batch_size)


def seed_database_with_faker(
    num_users: int = 100,
    posts_per_user: int = 10,
    comments_per_post: int = 5,
    friendships_per_user: int = 20,
) -> dict:
    """
    Seed the entire database with fake data.

    Args:
        num_users: Number of users to create
        posts_per_user: Number of posts per user
        comments_per_post: Number of comments per post
        friendships_per_user: Number of friendships per user

    Returns:
        Dictionary with counts of inserted records
    """
    start_time = datetime.now()

    log(f"Generating {num_users} fake users...")
    users_count = generate_fake_users(num_users)

    log(f"Generating posts ({posts_per_user} per user)...")
    posts_count = generate_fake_posts(posts_per_user=posts_per_user)

    log(f"Generating comments ({comments_per_post} per post)...")
    comments_count = generate_fake_comments(comments_per_post=comments_per_post)

    log(f"Generating friendships ({friendships_per_user} per user)...")
    friendships_count = generate_bulk_friendships(
        friendships_per_user=friendships_per_user
    )

    log("Generating 10,000,000 metrics rows...")
    metrics_count = generate_bulk_metrics(10_000_000)

    log("Generating 10,000,000 events rows...")
    events_count = generate_bulk_events(10_000_000)

    log("Generating 10,000,000 logs rows...")
    logs_count = generate_bulk_logs(10_000_000)

    results = {
        "users": users_count,
        "posts": posts_count,
        "comments": comments_count,
        "friendships": friendships_count,
        "metrics": metrics_count,
        "events": events_count,
        "logs": logs_count,
    }

    end_time = datetime.now()
    duration = end_time - start_time

    log(f"\nSeeding complete in {duration}!")
    for key, value in results.items():
        log(f"  {key}: {value}", type="info")

    return results


def generate_bulk_metrics(count: int = 1_000_000, batch_size: int = 100_000) -> int:
    """Insert bulk rows into metrics using DB-side generation."""
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for start in range(1, count + 1, batch_size):
            end = min(start + batch_size - 1, count)
            result = conn.execute(
                text("""
                INSERT INTO metrics (metric_name, value, recorded_at)
                SELECT
                    (ARRAY['cpu_usage','memory_usage','disk_io','network_latency','error_rate'])[floor(random() * 5 + 1)::int],
                    round((random() * 100)::numeric, 2),
                    now() - (random() * interval '365 days')
                FROM generate_series(:start, :end)
            """),
                {"start": start, "end": end},
            )
            inserted += result.rowcount

    return inserted


def generate_bulk_events(count: int = 1_000_000, batch_size: int = 100_000) -> int:
    """Insert bulk rows into events using DB-side generation."""
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for start in range(1, count + 1, batch_size):
            end = min(start + batch_size - 1, count)
            result = conn.execute(
                text("""
                INSERT INTO events (id, user_id, event_type, created_at)
                SELECT
                    gen_random_uuid(),
                    floor(random() * 10000 + 1)::int,
                    (ARRAY['click','view','purchase','signup','logout'])[floor(random() * 5 + 1)::int],
                    now() - (random() * interval '365 days')
                FROM generate_series(:start, :end)
            """),
                {"start": start, "end": end},
            )
            inserted += result.rowcount

    return inserted


def generate_bulk_logs(count: int = 1_000_000, batch_size: int = 100_000) -> int:
    """Insert bulk rows into logs using DB-side generation."""
    engine = get_engine()
    inserted = 0

    with engine.begin() as conn:
        for start in range(1, count + 1, batch_size):
            end = min(start + batch_size - 1, count)
            result = conn.execute(
                text("""
                INSERT INTO logs (session_id, message, timestamp)
                SELECT
                    'session-' || floor(random() * 100000 + 1)::int,
                    (ARRAY['INFO: request processed','WARN: slow query','ERROR: connection failed','DEBUG: cache miss'])[floor(random() * 4 + 1)::int] || ' #' || gs,
                    now() - (random() * interval '365 days')
                FROM generate_series(:start, :end) gs
            """),
                {"start": start, "end": end},
            )
            inserted += result.rowcount

    return inserted


if __name__ == "__main__":
    import sys

    # Default values
    num_users = 100
    posts_per_user = 10
    comments_per_post = 5
    friendships_per_user = 20

    # Parse command line arguments
    if len(sys.argv) > 1:
        num_users = int(sys.argv[1])
    if len(sys.argv) > 2:
        posts_per_user = int(sys.argv[2])
    if len(sys.argv) > 3:
        comments_per_post = int(sys.argv[3])
    if len(sys.argv) > 4:
        friendships_per_user = int(sys.argv[4])

    seed_database_with_faker(
        num_users=num_users,
        posts_per_user=posts_per_user,
        comments_per_post=comments_per_post,
        friendships_per_user=friendships_per_user,
    )
