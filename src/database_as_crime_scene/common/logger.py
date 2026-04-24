from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich_tools import df_to_table

console = Console()


def log(message, log_type: str = "info"):
    if log_type == "info":
        console.log(f"[cyan]{message}[/cyan]")
    elif log_type == "error":
        console.print(f"[bold red]ERROR:[/bold red] {message}")
    elif log_type == "warning":
        console.print(f"[yellow]WARNING:[/yellow] {message}")
    elif log_type == "success":
        console.print(f"[green]SUCCESS:[/green] {message}")
    elif log_type == "debug":
        console.print(f"[magenta]DEBUG:[/magenta] {message}")
    elif log_type == "trace":
        console.print(f"[dim]TRACE:[/dim] {message}")
    elif log_type == "table":
        console.print(df_to_table(message))
    elif log_type == "tree":
        console.print(message)  # expect a Tree object
    elif log_type == "json":
        console.print(JSON.from_data(message))
    elif log_type == "markdown":
        console.print(Markdown(message))
    elif log_type == "syntax":
        syntax = Syntax(message, "sql", theme="ansi_light", line_numbers=True)
        console.print(syntax)
    else:
        console.print(message)
