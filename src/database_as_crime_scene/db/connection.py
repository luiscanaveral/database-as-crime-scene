import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_database_url() -> str:
    """
    Build PostgreSQL connection string from environment variables.
    """
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    db = os.environ["DB_PASSWORD"]

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"



def get_engine() -> Engine:
    """
    Creates SQLAlchemist Engine 
    """
    return create_engine(get_database_url(), future=True)