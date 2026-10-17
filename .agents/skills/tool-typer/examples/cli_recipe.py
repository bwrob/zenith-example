"""Canonical Typer CLI application recipe for Zenith projects."""

from typing import Annotated

import typer
from rich.console import Console

# In real packages, import from the parent package:
# from package import __version__
# from package.core import core_business_logic
__version__ = "0.1.0"


def core_business_logic(target: str) -> str:
    return f"Processed {target}"


app = typer.Typer(
    name="my-app",
    help="High-performance CLI application.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(
            f"[bold cyan]my-app[/bold cyan] version [green]{__version__}[/green]"
        )
        raise typer.Exit


@app.callback()
def main_callback(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Entry point callback for global options."""


@app.command()
def run(
    target: Annotated[str, typer.Argument(help="Target item to process.")] = "default",
) -> None:
    """Execute primary command workflow."""
    result = core_business_logic(target)
    console.print(f"[bold green]✨ {result}[/bold green]")


def main() -> None:
    """Execute the CLI application."""
    app()


if __name__ == "__main__":
    main()
