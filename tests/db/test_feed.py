import pytest
from unittest.mock import MagicMock
from sqlalchemy import text
from database_as_crime_scene.db import feed

@pytest.fixture
def mock_engine_conn(mocker):
    """Mocks get_engine and returns the mock connection context."""
    mock_get_engine = mocker.patch("database_as_crime_scene.db.feed.get_engine")
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    
    mock_conn = MagicMock()
    # Mock the context manager behavior for with engine.begin() as conn:
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    # Mock the context manager behavior for with engine.connect() as conn:
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    
    return mock_conn

def test_add_users(mock_engine_conn):
    mock_result = MagicMock()
    mock_result.rowcount = 2
    mock_engine_conn.execute.return_value = mock_result
    
    users = [("test1@test.com", "Test One"), ("test2@test.com", "Test Two")]
    inserted = feed.add_users(users, batch_size=2)
    
    assert inserted == 2
    mock_engine_conn.execute.assert_called_once()
    args, _ = mock_engine_conn.execute.call_args
    query_str = str(args[0])
    assert "INSERT INTO users_profile" in query_str
    assert "('test1@test.com', 'Test One')" in query_str
    assert "('test2@test.com', 'Test Two')" in query_str

def test_add_posts(mock_engine_conn):
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_engine_conn.execute.return_value = mock_result
    
    posts = [(1, "Content")]
    inserted = feed.add_posts(posts)
    
    assert inserted == 1
    args, _ = mock_engine_conn.execute.call_args
    query_str = str(args[0])
    assert "INSERT INTO posts" in query_str
    assert "(1, 'Content')" in query_str

def test_generate_bulk_users(mock_engine_conn):
    mock_result = MagicMock()
    mock_result.rowcount = 100
    mock_engine_conn.execute.return_value = mock_result
    
    inserted = feed.generate_bulk_users(1, 100)
    
    assert inserted == 100
    mock_engine_conn.execute.assert_called_once()
    args, kwargs = mock_engine_conn.execute.call_args
    query_str = str(args[0])
    assert "FROM generate_series(:start_id, :end_id)" in query_str
    assert args[1] == {"start_id": 1, "end_id": 100}

def test_seed_database_with_faker(mocker):
    # Mock all the individual generation functions
    mocker.patch("database_as_crime_scene.db.feed.generate_fake_users", return_value=10)
    mocker.patch("database_as_crime_scene.db.feed.generate_fake_posts", return_value=20)
    mocker.patch("database_as_crime_scene.db.feed.generate_fake_comments", return_value=30)
    mocker.patch("database_as_crime_scene.db.feed.generate_bulk_friendships", return_value=40)
    mocker.patch("database_as_crime_scene.db.feed.generate_bulk_metrics", return_value=50)
    mocker.patch("database_as_crime_scene.db.feed.generate_bulk_events", return_value=60)
    mocker.patch("database_as_crime_scene.db.feed.generate_bulk_logs", return_value=70)
    
    results = feed.seed_database_with_faker(num_users=10, posts_per_user=2, comments_per_post=1, friendships_per_user=4)
    
    assert results["users"] == 10
    assert results["posts"] == 20
    assert results["comments"] == 30
    assert results["friendships"] == 40
    assert results["metrics"] == 50
    assert results["events"] == 60
    assert results["logs"] == 70
