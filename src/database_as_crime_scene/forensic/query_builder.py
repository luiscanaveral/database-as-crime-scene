QUERY_SELECTIVITY = """
            SELECT
    t.relname AS table_name,
    i.relname AS index_name,
    a.attname AS column_name,
    s.n_distinct,
    c.reltuples AS total_rows,

    ROUND(
        (CASE 
            WHEN s.n_distinct > 0 
                THEN s.n_distinct / NULLIF(c.reltuples, 0)
            ELSE abs(s.n_distinct)
        END)::numeric,
        4
    ) AS selectivity
FROM pg_index ix
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_class t ON t.oid = ix.indrelid
JOIN pg_attribute a 
    ON a.attrelid = t.oid 
    AND a.attnum = ANY(ix.indkey)
LEFT JOIN pg_stats s 
    ON s.tablename = t.relname 
    AND s.attname = a.attname
JOIN pg_class c ON c.oid = t.oid;
"""

QUERY_INDEX_METADATA = """
            SELECT 
            s.schemaname,
            s.relname AS table_name,
            s.indexrelname AS index_name,
            am.amname AS index_type,
            s.idx_scan,
            pg_relation_size(s.indexrelid) AS index_size,
            pg_relation_size(t.relid) AS heap_size,
            pg_total_relation_size(t.relid) AS total_size,
            ROUND(
                pg_relation_size(s.indexrelid)::numeric / 
                NULLIF(pg_relation_size(t.relid), 0) * 100, 
                2
            ) AS pct_of_table,
            ROUND(
                pg_relation_size(s.indexrelid)::numeric / 
                NULLIF(pg_relation_size(t.relid), 0) * 100, 
                2
            ) AS pct_vs_heap,

            ROUND(
                pg_relation_size(s.indexrelid)::numeric / 
                NULLIF(pg_total_relation_size(t.relid), 0) * 100, 
                2
            ) AS pct_vs_total,
            i.indisprimary AS is_pk,
            i.indisunique AS is_unique
        FROM pg_stat_user_indexes s
            JOIN pg_stat_user_tables t ON s.relid = t.relid
            JOIN pg_index i ON i.indexrelid = s.indexrelid
            JOIN pg_class c ON c.oid = s.indexrelid
            JOIN pg_am am ON c.relam = am.oid
            ORDER BY table_name, index_name;
        """


class QueryBuilder:
    @staticmethod
    def get_selectivity_query() -> str:
        return QUERY_SELECTIVITY

    @staticmethod
    def get_index_data_query() -> str:
        return QUERY_INDEX_METADATA
