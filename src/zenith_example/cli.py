"""Command line interface for zenith-example."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from zenith_example import __version__
from zenith_example.core import get_greeting

app: typer.Typer = typer.Typer(
    name="zenith-example",
    help="Demonstration and showcase repository instantiated from the Zenith template.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console: Console = Console()


def version_callback(value: bool) -> None:
    """Print the version and exit.

    Raises
    ------
    typer.Exit
        Always exits when version flag is given.

    """
    if value:
        console.print(
            f"[bold cyan]zenith-example[/bold cyan]"
            f" version [green]{__version__}[/green]"
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
def greet(
    name: Annotated[
        str,
        typer.Argument(help="The name to greet."),
    ] = "World",
) -> None:
    """Display a personalized greeting."""
    greeting = get_greeting(name)
    console.print(f"[bold green]✨ {greeting}[/bold green]")


def main() -> None:
    """Execute the CLI application."""
    app()


if __name__ == "__main__":
    main()
