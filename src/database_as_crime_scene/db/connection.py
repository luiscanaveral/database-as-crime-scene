import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import pandas as pd


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



def get_engine(dbschema='public') -> Engine:
    """
    Creates SQLAlchemist Engine 
    """
    return create_engine(get_database_url(), 
        future=True, 
        connect_args={'options': f"-csearch_path={dbschema}"}
    )

def get_query(sql):
    """
    Gets Pandas Dataframe based on SQL code
    """
    df = pd.read_sql(sql, get_engine())
    return df

def get_execution_plan(sql):
    """
    Get Execution plan for sql script in JSON Format
    """
    df = get_query(f"""
    EXPLAIN (
        ANALYZE,
        BUFFERS,
        VERBOSE,
        FORMAT JSON
        ) {sql}""")
    return df["QUERY PLAN"][0]