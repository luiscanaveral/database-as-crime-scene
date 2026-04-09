from rich.console import Console
from rich.syntax import Syntax
console = Console()
from common.decorators.singleton import singleton
from common.logger import log


class Notebook:
   
    def sayHello():
        print("Hello")
    def setup(self):
        Notebook.build_connection_string()
    def print(*args):
        console.print(args)
    def print_sql(multi_line_code):
        syntax = Syntax(
            multi_line_code,
            "sql",
            theme="ansi_light",
            line_numbers=True,
        )
        console.print(syntax)

@singleton        
class DatabaseAsCrimeScene:
    def __init__(self):
        self.data = []
    def setup(self):
        print("Hola")
    