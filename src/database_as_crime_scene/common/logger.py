from rich.console import Console
from rich.syntax import Syntax
from rich_tools import df_to_table


console = Console()

def log(message:str, type:str="info"):
    if type == "info":
        console.print(message)
    elif type == "error":
        console.print_error(message)
    elif type == "warning":
        console.print_warning(message)
    elif type == "success":
        console.print_success(message)
    elif type == "debug":
        console.print_debug(message)
    elif type == "trace":
        console.print_trace(message)
    elif type == "table":
        console.print(df_to_table(message))
    elif type == "tree":
        console.print_tree(message)
    elif type == "json":
        console.print_json(message)
    elif type == "markdown":
        console.print_markdown(message)
    elif type == "syntax":
        console.print_syntax(message)
    elif type == "text":
        console.print_text(message)
    elif type == "log":
        console.print_log(message)
    else:
        console.print(message)
    