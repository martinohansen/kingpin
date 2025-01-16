import logging

import typer
from rich import print
from rich.logging import RichHandler
from typing_extensions import Annotated

from cli import chat, load, lst
from lib import lookup, pins

app = typer.Typer(add_completion=False)
app.add_typer(load.app)
app.add_typer(lst.app)
app.add_typer(chat.app)


@app.command()
@app.command("get", hidden=True)
def describe(
    name: Annotated[str, typer.Argument(help="Name of pin to describe")],
):
    """Describe pin in database"""

    if pin := pins.get(name):
        print(pin)
    else:
        print(f"{name} not found")


@app.command()
@app.command("rm", hidden=True)
def delete(name: str) -> None:
    """Delete pin from database"""
    if pin := pins.get(name):
        typer.confirm(f"Delete {pin!r}?", abort=True)
        pins.delete(name)


@app.command()
def search(query: str) -> None:
    """Search for places using Google Maps API"""
    print(lookup.search(query))


@app.command()
def lists() -> None:
    """List all unique pin types in database"""
    print(pins.get_lists())


@app.callback()
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose logging"),
    ] = False,
):
    """
    Manage Google Maps pins

    Google makes it deliberately hard to export your data. This tool tries to
    help you get your pins out of Google without losing context about them. Lets
    hope we make it work before Maps hits the graveyard 🪦
    """
    level = logging.WARNING
    if verbose:
        level = logging.INFO

    logging.basicConfig(
        level=level, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
    )
