from database_as_crime_scene.forensic.query_builder import QueryBuilder, QUERY_SELECTIVITY, QUERY_INDEX_METADATA

def test_get_selectivity_query():
    assert QueryBuilder.get_selectivity_query() == QUERY_SELECTIVITY

def test_get_index_data_query():
    assert QueryBuilder.get_index_data_query() == QUERY_INDEX_METADATA
