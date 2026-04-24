import pytest
import os
import pandas as pd
from database_as_crime_scene.db.connection import get_database_url, get_engine, get_query, get_execution_plan

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DB_USER", "testuser")
    monkeypatch.setenv("DB_PASSWORD", "testpass")
    monkeypatch.setenv("DB_HOST_INSIDE_CONTAINER", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")

def test_get_database_url(mock_env_vars):
    url = get_database_url()
    assert url == "postgresql://testuser:testpass@localhost:5432/testdb"

def test_get_database_url_default_port(monkeypatch):
    monkeypatch.setenv("DB_USER", "testuser")
    monkeypatch.setenv("DB_PASSWORD", "testpass")
    monkeypatch.setenv("DB_HOST_INSIDE_CONTAINER", "localhost")
    monkeypatch.setenv("DB_NAME", "testdb")
    # Don't set DB_PORT to test the default '5432'
    if "DB_PORT" in os.environ:
        monkeypatch.delenv("DB_PORT")
        
    url = get_database_url()
    assert url == "postgresql://testuser:testpass@localhost:5432/testdb"

def test_get_engine(mocker, mock_env_vars):
    mock_create_engine = mocker.patch("database_as_crime_scene.db.connection.create_engine")
    
    engine = get_engine(dbschema="myschema")
    
    mock_create_engine.assert_called_once_with(
        "postgresql://testuser:testpass@localhost:5432/testdb",
        future=True,
        connect_args={"options": "-csearch_path=myschema"}
    )
    assert engine == mock_create_engine.return_value

def test_get_query(mocker):
    mock_get_engine = mocker.patch("database_as_crime_scene.db.connection.get_engine")
    mock_read_sql = mocker.patch("database_as_crime_scene.db.connection.pd.read_sql")
    
    mock_read_sql.return_value = pd.DataFrame({"col1": [1, 2]})
    
    df = get_query("SELECT * FROM table")
    
    mock_get_engine.assert_called_once()
    mock_read_sql.assert_called_once_with("SELECT * FROM table", mock_get_engine.return_value)
    assert len(df) == 2

def test_get_execution_plan(mocker):
    mock_get_query = mocker.patch("database_as_crime_scene.db.connection.get_query")
    
    # Mock returning a DataFrame with "QUERY PLAN" column
    mock_get_query.return_value = pd.DataFrame({"QUERY PLAN": [{"Plan": {}}]})
    
    plan = get_execution_plan("SELECT * FROM table")
    
    # Assert get_query was called with the EXPLAIN string
    args, _ = mock_get_query.call_args
    assert "EXPLAIN" in args[0]
    assert "SELECT * FROM table" in args[0]
    assert "FORMAT JSON" in args[0]
    
    # Assert it returns the first element of the "QUERY PLAN" column
    assert plan == {"Plan": {}}
