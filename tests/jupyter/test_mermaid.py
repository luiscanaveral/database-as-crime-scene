import pytest
from database_as_crime_scene.jupyter.mermaid import format_node_label, generate_mermaid_from_execution_plan

def test_format_node_label():
    node = {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Actual Total Time": 1.25,
        "Actual Rows": 100
    }
    label = format_node_label(node)
    assert "Seq Scan" in label
    assert "Table: users" in label
    assert "Time: 1.25 ms" in label
    assert "Rows: 100" in label

def test_generate_mermaid_from_execution_plan():
    plan_json = [{
        "Plan": {
            "Node Type": "Hash Join",
            "Actual Total Time": 10.0,
            "Plans": [
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "table1",
                    "Actual Total Time": 2.0
                },
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "table2",
                    "Actual Total Time": 3.0
                }
            ]
        }
    }]
    
    mermaid_str = generate_mermaid_from_execution_plan(plan_json)
    
    assert mermaid_str.startswith("flowchart TD")
    assert "Hash Join" in mermaid_str
    assert "table1" in mermaid_str
    assert "table2" in mermaid_str
    # 3 nodes should mean 3 node definitions and 2 edges
    assert "-->" in mermaid_str

def test_get_mermaid_by_table_name(mocker):
    mock_create_engine = mocker.patch("database_as_crime_scene.jupyter.mermaid.create_engine")
    mock_inspect = mocker.patch("database_as_crime_scene.jupyter.mermaid.inspect")
    
    mock_inspector = mocker.MagicMock()
    mock_inspect.return_value = mock_inspector
    
    mock_inspector.get_table_names.return_value = ["users", "posts"]
    mock_inspector.get_foreign_keys.return_value = []
    # Test column generation
    mock_inspector.get_columns.return_value = [
        {"name": "id", "type": "INTEGER"},
        {"name": "email", "type": "VARCHAR(255)"}
    ]
    mock_inspector.get_pk_constraint.return_value = {"constrained_columns": ["id"]}
    
    from database_as_crime_scene.jupyter.mermaid import get_mermaid_by_table_name
    
    mermaid_str = get_mermaid_by_table_name("mock_conn", "public", "users")
    
    assert "erDiagram" in mermaid_str
    assert "users {" in mermaid_str
    assert "INTEGER id PK" in mermaid_str
    assert "VARCHAR email" in mermaid_str

def test_get_mermaid_by_view_name(mocker):
    mock_create_engine = mocker.patch("database_as_crime_scene.jupyter.mermaid.create_engine")
    mock_inspect = mocker.patch("database_as_crime_scene.jupyter.mermaid.inspect")
    
    mock_inspector = mocker.MagicMock()
    mock_inspect.return_value = mock_inspector
    
    mock_inspector.get_view_names.return_value = ["user_stats"]
    mock_inspector.get_columns.return_value = [
        {"name": "stat_id", "type": "INTEGER"}
    ]
    
    from database_as_crime_scene.jupyter.mermaid import get_mermaid_by_view_name
    
    mermaid_str = get_mermaid_by_view_name("mock_conn", "public", "user_stats")
    
    assert "erDiagram" in mermaid_str
    assert "user_stats {" in mermaid_str
    assert "INTEGER stat_id" in mermaid_str
