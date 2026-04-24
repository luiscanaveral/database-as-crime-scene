import pytest
import pandas as pd
from database_as_crime_scene.forensic.forensic import Forensic

@pytest.fixture
def forensic_instance():
    return Forensic(conn_string="mock_conn_string")

def test_format_size(forensic_instance):
    # 1048576 bytes = 1 MB
    assert forensic_instance.format_size(1048576) == "1.00 MB"
    assert forensic_instance.format_size(2097152) == "2.00 MB"

def test_classify(forensic_instance):
    assert forensic_instance.classify(100, 10, True, False) == ("PK", "blue")
    assert forensic_instance.classify(100, 10, False, True) == ("UNIQUE", "cyan")
    
    # Critical: idx_scan == 0 and pct_vs_total > 20
    assert forensic_instance.classify(0, 25, False, False) == ("CRITICAL", "red")
    
    # Suspicious: idx_scan < 50 and pct_vs_total > 10
    assert forensic_instance.classify(40, 15, False, False) == ("SUSPICIOUS", "yellow")
    
    # Healthy: Otherwise
    assert forensic_instance.classify(100, 5, False, False) == ("HEALTHY", "green")

def test_compute_score(forensic_instance):
    # PK always returns 100
    assert forensic_instance.compute_score(0, 0, 0, True, False) == 100
    
    # UNIQUE gets +20
    # Size penalty: max(0, 30 - pct_vs_total * 0.5) => if pct_vs_total=0 => +30
    # Activity: if scan>1000 => +50
    # Total = 20 + 30 + 50 = 100
    assert forensic_instance.compute_score(0, 0, 1500, False, True) == 100
    
    # Test heavily unused penalty
    # No unique (0)
    # pct_vs_total = 60 => size penalty = max(0, 30 - 30) = 0
    # idx_scan = 0 => activity penalty = - (20 + pct_vs_heap*0.5)
    # pct_vs_heap = 100 => activity penalty = - (20 + 50) = -70
    # Total = max(0, -70) = 0
    assert forensic_instance.compute_score(100, 60, 0, False, False) == 0

def test_check_indexes(mocker, forensic_instance):
    # Mock log to avoid console output
    mocker.patch("database_as_crime_scene.forensic.forensic.log")
    
    # Mock data retrieval
    mock_indexes_df = pd.DataFrame([
        {
            "table_name": "users", "index_name": "idx_users_email", "idx_scan": 0, 
            "pct_vs_total": 25, "is_pk": False, "is_unique": False, 
            "pct_vs_heap": 50, "index_size": 1048576, "heap_size": 1048576, "total_size": 2097152
        }
    ])
    mock_selectivity_df = pd.DataFrame([
        {
            "table_name": "users", "index_name": "idx_users_email", "selectivity": 0.99
        }
    ])
    
    mocker.patch.object(forensic_instance, "_get_indexes_metadata", return_value=mock_indexes_df)
    mocker.patch.object(forensic_instance, "_get_selectivity", return_value=mock_selectivity_df)
    
    result_df = forensic_instance.check_indexes()
    
    assert len(result_df) == 1
    assert "status" in result_df.columns
    assert "score" in result_df.columns
    assert "selectivity" in result_df.columns
    assert result_df.iloc[0]["status"] == "CRITICAL"
    assert result_df.iloc[0]["index_size"] == "1.00 MB"
