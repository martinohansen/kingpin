#!/usr/bin/env python3
"""
pinctl - A command-line client for interacting with PinServer

Usage:
    python -m pinctl.cli <data_path> <command> [options]

Commands:
    stats                   - Show data statistics
    list [limit]           - List pins (default: 20)
    search <query> [limit] - Search pins (default: 10)
    categories             - List all categories
    category <name>        - List pins in category
    near <lat> <lng> [km]  - Find pins near coordinates (default: 10km)
    details <name>         - Get detailed info for a pin
"""

import logging
import sys
from pathlib import Path

from kingpin.pin import PinServer


def setup_logging() -> logging.Logger:
    """Setup basic logging"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return logging.getLogger("pinctl")


def show_stats(pin_server: PinServer) -> None:
    """Show data statistics"""
    total_pins = len(pin_server.pins)
    categories = pin_server.get_all_categories()

    pins_with_coords = sum(1 for p in pin_server.pins if p.latitude and p.longitude)
    pins_with_notes = sum(1 for p in pin_server.pins if p.notes)
    pins_with_ratings = sum(1 for p in pin_server.pins if p.rating)

    print("📊 Pin Statistics")
    print(f"Total pins: {total_pins}")
    print(f"Categories: {len(categories)}")
    print(f"Pins with coordinates: {pins_with_coords}")
    print(f"Pins with notes: {pins_with_notes}")
    print(f"Pins with ratings: {pins_with_ratings}")


def list_pins(pin_server: PinServer, limit: int = 20) -> None:
    """List pins"""
    pins = pin_server.pins[:limit]

    if not pins:
        print("No pins found.")
        return

    print(f"📍 Showing {len(pins)} pins:")
    for i, pin in enumerate(pins, 1):
        print(f"{i:3d}. {pin.name}")
        if pin.address:
            print(f"     📍 {pin.address}")
        if pin.categories:
            print(f"     🏷️  {', '.join(pin.categories)}")


def search_pins(pin_server: PinServer, query: str, limit: int = 10) -> None:
    """Search pins"""
    pins = pin_server.search_places(query, limit)

    if not pins:
        print(f"No pins found matching '{query}'")
        return

    print(f"🔍 Found {len(pins)} pins matching '{query}':")
    for i, pin in enumerate(pins, 1):
        print(f"{i:3d}. {pin.name}")
        if pin.address:
            print(f"     📍 {pin.address}")
        if pin.categories:
            print(f"     🏷️  {', '.join(pin.categories)}")


def list_categories(pin_server: PinServer) -> None:
    """List all categories"""
    categories = pin_server.get_all_categories()

    if not categories:
        print("No categories found.")
        return

    print(f"🏷️  Found {len(categories)} categories:")
    for category in categories:
        count = len(pin_server.get_places_by_category(category))
        print(f"  • {category} ({count} pins)")


def list_category_pins(pin_server: PinServer, category: str) -> None:
    """List pins in a category"""
    pins = pin_server.get_places_by_category(category)

    if not pins:
        print(f"No pins found in category '{category}'")
        return

    print(f"🏷️  {len(pins)} pins in category '{category}':")
    for i, pin in enumerate(pins, 1):
        print(f"{i:3d}. {pin.name}")
        if pin.address:
            print(f"     📍 {pin.address}")


def find_pins_near(
    pin_server: PinServer, lat: float, lng: float, radius_km: float = 10
) -> None:
    """Find pins near coordinates"""
    pins = pin_server.get_places_near(lat, lng, radius_km)

    if not pins:
        print(f"No pins found within {radius_km}km of ({lat:.6f}, {lng:.6f})")
        return

    print(f"🌍 Found {len(pins)} pins within {radius_km}km:")
    for pin in pins:
        print(f"  • {pin.name}")
        if pin.address:
            print(f"    📍 {pin.address}")
        if pin.latitude and pin.longitude:
            distance = (
                (abs(pin.latitude - lat) ** 2 + abs(pin.longitude - lng) ** 2) ** 0.5
            ) * 111
            print(f"    📏 ~{distance:.1f}km away")


def show_pin_details(pin_server: PinServer, name: str) -> None:
    """Show detailed pin information"""
    matching_pins = [p for p in pin_server.pins if name.lower() in p.name.lower()]

    if not matching_pins:
        print(f"No pin found with name containing '{name}'")
        return

    if len(matching_pins) > 1:
        print(f"Found {len(matching_pins)} matching pins, showing first:")

    pin = matching_pins[0]

    print(f"📍 {pin.name}")
    if pin.address:
        print(f"Address: {pin.address}")
    if pin.latitude and pin.longitude:
        print(f"Coordinates: {pin.latitude:.6f}, {pin.longitude:.6f}")
    if pin.categories:
        print(f"Categories: {', '.join(pin.categories)}")
    if pin.notes:
        print(f"Notes: {pin.notes}")
    if pin.date_saved:
        print(f"Saved: {pin.date_saved}")
    if pin.url:
        print(f"URL: {pin.url}")
    if pin.rating:
        print(f"Rating: {pin.rating}")
    if pin.place_id:
        print(f"Place ID: {pin.place_id}")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    data_path = sys.argv[1]
    command = sys.argv[2]

    # Validate data path
    if not Path(data_path).exists():
        print(f"Error: Data path does not exist: {data_path}")
        sys.exit(1)

    # Setup logging and create PinServer
    logger = setup_logging()
    pin_server = PinServer(data_path, logger)

    if len(pin_server.pins) == 0:
        print("Warning: No pins loaded from data path")
        return

    # Process commands
    try:
        if command == "stats":
            show_stats(pin_server)

        elif command == "list":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            list_pins(pin_server, limit)

        elif command == "search":
            if len(sys.argv) < 4:
                print("Error: search requires a query")
                sys.exit(1)
            query = sys.argv[3]
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            search_pins(pin_server, query, limit)

        elif command == "categories":
            list_categories(pin_server)

        elif command == "category":
            if len(sys.argv) < 4:
                print("Error: category requires a category name")
                sys.exit(1)
            category = sys.argv[3]
            list_category_pins(pin_server, category)

        elif command == "near":
            if len(sys.argv) < 5:
                print("Error: near requires latitude and longitude")
                sys.exit(1)
            lat = float(sys.argv[3])
            lng = float(sys.argv[4])
            radius = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
            find_pins_near(pin_server, lat, lng, radius)

        elif command == "details":
            if len(sys.argv) < 4:
                print("Error: details requires a pin name")
                sys.exit(1)
            name = sys.argv[3]
            show_pin_details(pin_server, name)

        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

    except ValueError as e:
        print(f"Error: Invalid numeric argument - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
