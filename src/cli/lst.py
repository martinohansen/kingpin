from collections import defaultdict
from enum import Enum
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from lib import pins

app = typer.Typer()


class Output(str, Enum):
    table = "table"
    markdown = "markdown"
    mk = "mk"


def _organize_by_categories(
    pins: list[pins.Pin],
    min_group_size=2,
) -> dict[str, list[pins.Pin]]:
    """
    Organize pins into categories by selecting the most specific valid category
    for each pin.

    This function groups pins into categories such that: 1) they are assigned to
    the most specific (least common) category they belong to 2) categories must
    have at least min_group_size pins across all pins to be eligible.
    """
    category_counts: dict[str, int] = defaultdict(int)
    for pin in pins:
        for cat in pin.categorizes:
            category_counts[cat] += 1

    grouped = defaultdict(list)
    for pin in pins:
        sorted_cats = sorted(
            pin.categorizes,
            key=lambda x: (category_counts[x], x),
        )

        selected_cat = None
        for cat in sorted_cats:
            if category_counts[cat] >= min_group_size:
                selected_cat = cat
                break
        if not selected_cat:
            selected_cat = sorted_cats[0] if sorted_cats else "other"

        grouped[selected_cat].append(pin)

    return grouped


@app.command("list")
@app.command("ls", hidden=True)
def lst(
    name: Annotated[
        Optional[str],
        typer.Argument(),
    ] = None,
    first: Annotated[
        int,
        typer.Option("--first", "-f", help="Display first N pins"),
    ] = 50,
    nearby: Annotated[
        Optional[str],
        typer.Option("--nearby", "-n", help="Filter by nearby"),
    ] = None,
    within: Annotated[
        float,
        typer.Option("--within", "-km", help="Filter by within kilometers of nearby"),
    ] = 50,
    categorize: Annotated[
        bool,
        typer.Option("--categorize", "-c", help="Group by categories"),
    ] = False,
    output: Annotated[
        Output,
        typer.Option("--output", "-o", help="Output format"),
    ] = Output.table,
):
    """List pins in database"""
    p = pins.get_many(name)
    if len(p) == 0:
        print("No pins found")
        return

    # TODO(Martin): Implement PostGIS to speed up the filtering by distances
    # if this becomes a bottleneck. Currently listing every pin (~350) and
    # filtering takes <1s.
    if nearby:
        # TODO(Martin): Implement location lookup
        p = pins.within(within, (55.676098, 12.568337), p)

    console = Console()
    match output:
        case Output.table:
            table = Table(title="Pins")

            if categorize:
                table.add_column("List", no_wrap=True)
                table.add_column("Category", no_wrap=True)
                table.add_column("Title", no_wrap=True)
                table.add_column("Address", no_wrap=True)
                table.add_column("Link", style="blue")
            else:
                table.add_column("List", no_wrap=True)
                table.add_column("Title", no_wrap=True)
                table.add_column("Address", no_wrap=True)
                table.add_column("Link", style="blue")

            count = 0
            if categorize:
                grouped = _organize_by_categories(p)
                for cat, items in grouped.items():
                    for pin in items:
                        if count < first:
                            table.add_row(
                                pin.lst,
                                cat,
                                pin.name,
                                pin.address,
                                pin.google_maps_takeout_url,
                            )
                        count += 1
            else:
                for pin in p:
                    if count < first:
                        table.add_row(
                            pin.lst,
                            pin.name,
                            pin.address,
                            pin.google_maps_takeout_url,
                        )
                    count += 1

            console.print(table)
            console.print(f"{min(count, first)}/{count}", justify="center")

        case Output.markdown | Output.mk:
            lines = ["# Pins"]
            if categorize:
                grouped = _organize_by_categories(p)
                for cat, items in grouped.items():
                    lines.append(f"## {cat}")
                    for pin in items:
                        address_link = f"[{pin.address}]({pin.google_maps_takeout_url})"
                        lines.append(f"- {pin.name}, {address_link}")
            else:
                for pin in p:
                    address_link = f"[{pin.address}]({pin.google_maps_takeout_url})"
                    lines.append(f"- {pin.name}, {address_link}")

            console.print("\n".join(lines))
