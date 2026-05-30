import os

from IPython import get_ipython


def setup():
    ip = get_ipython()
    if ip is None:
        return

    ip.run_line_magic("load_ext", "sql")
    ip.run_line_magic("config", "SqlMagic.displaylimit = None")
    ip.run_line_magic("load_ext", "autoreload")
    ip.run_line_magic("autoreload", "2")

    ip.run_cell("""
from database_as_crime_scene.jupyter.mermaid import get_mermaid_by_table_name, draw
from database_as_crime_scene.db.connection import get_query, get_execution_plan
from database_as_crime_scene.jupyter.mermaid import generate_mermaid_from_execution_plan, draw
from database_as_crime_scene.jupyter.mermaid_execution_plan import build_execution_tree, build_flamegraph

import os
database_url = os.getenv('DATABASE_URL', 'localhost:5432')
""")
