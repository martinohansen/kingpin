import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from pydantic import BaseModel

from kingpin.models import Pin
from kingpin.pin import PinServer

logger = logging.getLogger("pinctl")


def show_stats(pin_server: PinServer) -> None:
    """Show data statistics"""
    total_pins = len(pin_server.pins)
    pins_with_coords = sum(1 for p in pin_server.pins if p.latitude and p.longitude)
    pins_with_notes = sum(1 for p in pin_server.pins if p.notes)

    # List statistics
    all_lists = pin_server.get_all_lists()
    list_stats = {
        pin_list.name: len(pin_server.get_pins_by_list(pin_list.name))
        for pin_list in all_lists
    }

    response = {
        "total_pins": total_pins,
        "pins_with_coordinates": pins_with_coords,
        "pins_with_notes": pins_with_notes,
        "total_lists": len(all_lists),
        "lists": list_stats,
    }

    print(json.dumps(response, indent=2))


def list_pins(ps: PinServer) -> None:
    pins = ps.pins

    class Pins(BaseModel):
        pins: List[Pin]
        count: int

    response = Pins(pins=pins, count=len(pins))

    print(response.model_dump_json(indent=2))


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="A command-line interface for PinServer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    commands = parser.add_subparsers(dest="command", help="Available commands")

    # stats command
    stats_parser = commands.add_parser("stats", help="Show data statistics")
    stats_parser.add_argument("files", nargs="+", help="JSON files to process")

    # list command
    list_parser = commands.add_parser("list", help="List pins")
    list_parser.add_argument("files", nargs="+", help="JSON files to process")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    pin_server = PinServer([Path(f) for f in args.files], logger)

    # Process commands
    if args.command == "stats":
        show_stats(pin_server)
    elif args.command == "list":
        list_pins(pin_server)


if __name__ == "__main__":
    main()
