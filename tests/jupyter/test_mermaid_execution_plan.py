import pytest
from database_as_crime_scene.jupyter.mermaid_execution_plan import classify_node, format_label, build_execution_tree, build_flamegraph

def test_classify_node():
    assert classify_node({"Actual Total Time": 60}) == "slow"
    assert classify_node({"Actual Total Time": 20}) == "medium"
    assert classify_node({"Actual Total Time": 5}) == "fast"

def test_format_label():
    node = {
        "Node Type": "Index Scan",
        "Relation Name": "users",
        "Index Name": "idx_users_id",
        "Actual Startup Time": 0.05,
        "Actual Total Time": 1.25,
        "Actual Rows": 10,
        "Index Cond": "(id = 1)"
    }
    
    label = format_label(node)
    assert "<b>Index Scan</b>" in label
    assert "Table: users" in label
    assert "Index: idx_users_id" in label
    assert "Time: 0.05 → 1.25 ms" in label
    assert "Rows: 10" in label
    assert "Index Cond: (id = 1)" in label

def test_build_execution_tree():
    plan = {
        "Node Type": "Hash Join",
        "Actual Total Time": 20.0,
        "Plans": [
            {"Node Type": "Seq Scan", "Relation Name": "t1", "Actual Total Time": 2.0}
        ]
    }
    
    mermaid_str = build_execution_tree(plan)
    assert "flowchart TD" in mermaid_str
    assert "Hash Join" in mermaid_str
    assert ":::medium" in mermaid_str # 20.0 is medium
    assert ":::fast" in mermaid_str # 2.0 is fast
    assert "classDef" in mermaid_str

def test_build_flamegraph():
    plan = {
        "Node Type": "Hash Join",
        "Actual Total Time": 60.0,
        "Plans": [
            {"Node Type": "Seq Scan", "Relation Name": "t1", "Actual Total Time": 2.0}
        ]
    }
    
    flame_str = build_flamegraph(plan)
    assert "flowchart LR" in flame_str
    assert "Hash Join" in flame_str
    assert ":::slow" in flame_str # 60.0 is slow
    assert "classDef" in flame_str
