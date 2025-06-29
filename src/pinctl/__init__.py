import argparse
import json
import logging
import sys
from typing import List

from pydantic import BaseModel

from kingpin.models import Pin, PinList
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


def list_pins(
    pin_server: PinServer, list_name: str | None = None, limit: int = 20
) -> None:
    """List pins from a specific list or all pins"""
    if list_name:
        pins = pin_server.get_pins_by_list(list_name)[:limit]
    else:
        pins = pin_server.pins[:limit]

    class Pins(BaseModel):
        pins: List[Pin]
        count: int
        limit: int
        list_name: str | None = None

    response = Pins(pins=pins, count=len(pins), limit=limit, list_name=list_name)

    print(response.model_dump_json(indent=2))


def search_pins(pin_server: PinServer, query: str, limit: int = 10) -> None:
    """Search pins across all lists"""
    pins = pin_server.search_places(query, limit)

    class Search(BaseModel):
        query: str
        pins: List[Pin]
        count: int
        limit: int

    response = Search(query=query, pins=pins, count=len(pins), limit=limit)

    print(response.model_dump_json(indent=2))


def list_lists(pin_server: PinServer) -> None:
    """List all available lists"""
    lists = pin_server.get_all_lists()

    class Lists(BaseModel):
        lists: List[PinList]
        count: int

    response = Lists(lists=lists, count=len(lists))
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

    # lists command
    lists_parser = commands.add_parser("lists", help="List all available lists")
    lists_parser.add_argument("files", nargs="+", help="JSON files to process")

    # list command
    list_parser = commands.add_parser("list", help="List pins")
    list_parser.add_argument(
        "--list-name",
        type=str,
        help="List name to filter pins by",
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of pins to show (default: 20)",
    )
    list_parser.add_argument("files", nargs="+", help="JSON files to process")

    # search command
    search_parser = commands.add_parser(
        "search", help="Search pins by name, address, or notes"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results (default: 10)"
    )
    search_parser.add_argument("files", nargs="+", help="JSON files to process")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Use the files provided directly (shell will expand globs)
    file_paths = args.files
    if not file_paths:
        print("No files provided", file=sys.stderr)
        sys.exit(1)
        
    pin_server = PinServer(file_paths, logger)

    # Process commands
    if args.command == "stats":
        show_stats(pin_server)
    elif args.command == "lists":
        list_lists(pin_server)
    elif args.command == "list":
        list_pins(pin_server, getattr(args, "list_name", None), args.limit)
    elif args.command == "search":
        search_pins(pin_server, args.query, args.limit)


if __name__ == "__main__":
    main()
