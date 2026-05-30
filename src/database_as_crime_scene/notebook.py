import os

from IPython import get_ipython

from .common.decorators.singleton import singleton
from .common.logger import log
from .db.connection import get_execution_plan, get_query
from .jupyter.mermaid import draw, draw_execution_plan, generate_mermaid_from_execution_plan, get_mermaid_by_table_name, get_mermaid_by_view_name
from .jupyter.mermaid_execution_plan import build_execution_tree, build_flamegraph


class Notebook:
    def say_hello(self):
        print("Hello")

    def build_connection_string(self):
        pass

    def setup(self):
        log("Notebook Setup", log_type="setup")
        ip = get_ipython()
        if ip is None:
            return

        ip.run_line_magic("load_ext", "sql")
        ip.run_line_magic("config", "SqlMagic.displaylimit = None")
        ip.run_line_magic("load_ext", "autoreload")
        ip.run_line_magic("autoreload", "2")

        database_url = os.getenv("DATABASE_URL", "localhost:5432")
        ip.user_ns.update(
            {
                "get_mermaid_by_table_name": get_mermaid_by_table_name,
                "get_mermaid_by_view_name": get_mermaid_by_view_name,
                "draw": draw,
                "draw_execution_plan": draw_execution_plan,
                "get_query": get_query,
                "get_execution_plan": get_execution_plan,
                "generate_mermaid_from_execution_plan": generate_mermaid_from_execution_plan,
                "build_execution_tree": build_execution_tree,
                "build_flamegraph": build_flamegraph,
                "database_url": database_url,
                "log":log,
            }
        )
        log("Setup complete", log_type="success")

    def print(self, *args):
        log(args)

    def print_sql(self, multi_line_code):
        log(multi_line_code, log_type="syntax")


@singleton
class DatabaseAsCrimeScene:
    def __init__(self):
        self.data = []

    def setup(self):
        print("Hola")
