import os
import time

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from ..common.logger import log


def get_database_url() -> str:
    """
    build connection string based on ENV vars
    """
    return (
        f"postgresql://"
        f"{os.environ['DB_USER']}:"
        f"{os.environ['DB_PASSWORD']}@"
        f"{os.environ['DB_HOST_INSIDE_CONTAINER']}:"
        f"{os.environ.get('DB_PORT', '5432')}/"
        f"{os.environ['DB_NAME']}"
    )


def get_engine(dbschema="public") -> Engine:
    """
    Creates SQLAlchemist Engine
    """
    return create_engine(
        get_database_url(),
        future=True,
        connect_args={"options": f"-csearch_path={dbschema}"},
    )


def get_query(sql, with_meta=False):
    """
    Gets Pandas Dataframe based on SQL code.

    If with_meta=True, returns (df, meta) where meta is a dict with:
    rows_count, execution_time, cols_count.
    """
    start = time.time()
    df = pd.read_sql(sql, get_engine())
    elapsed = time.time() - start
    if with_meta:
        meta = {
            "rows_count": len(df),
            "execution_time": round(elapsed, 4),
            "cols_count": len(df.columns),
        }
        return df, meta
    return df


def get_execution_plan(sql, timeout_msg=None):
    """
    Get Execution plan for sql script in JSON Format

    Note: EXPLAIN ANALYZE actually executes the query — for large tables
    this may take a while.
    """
    log("Running EXPLAIN ANALYZE — query is being executed...", log_type="info")
    log("This may take a while for large tables (metrics, events, logs)", log_type="warning")
    start = time.time()
    df = get_query(f"""
    EXPLAIN (
        ANALYZE,
        BUFFERS,
        VERBOSE,
        FORMAT JSON
        ) {sql}""")
    elapsed = time.time() - start
    log(f"EXPLAIN ANALYZE completed in {elapsed:.2f}s", log_type="success")
    return df["QUERY PLAN"][0]
