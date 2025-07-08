from fastmcp import FastMCP

from .pin import PinServer


class PinProvider:
    def __init__(self, mcp: FastMCP, ps: PinServer):
        self.mcp = mcp
        self.ps = ps

        # Register tools with the MCP server
        mcp.tool(self.list_lists)
        mcp.tool(self.list_pins)
        mcp.tool(self.get_pins)
        mcp.tool(self.find_pins_near)

    def list_lists(self) -> str:
        """List all available pin lists with counts."""
        lists = self.ps.get_all_lists()

        if not lists:
            return "No lists found."

        result = f"{len(lists)} lists: "
        list_items = []
        for i, pin_list in enumerate(lists, 1):
            pin_count = len(self.ps.get_pins_by_list(pin_list.name))
            list_items.append(f"{i}.{pin_list.name}({pin_count})")

        return result + " | ".join(list_items)

    def list_pins(
        self,
        list_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
        with_links: bool = False,
    ) -> str:
        """List pins with pagination support.

        Args:
            list_name: List name (None for all pins)
            limit: Max pins to return (default: 50, max: 200)
            offset: Skip N pins from start (default: 0)
            with_links: Include Google Maps links (default: False)
        """
        # Validate
        if limit < 1:
            return "Error: limit must be ≥ 1"
        if limit > 200:
            limit = 200
        if offset < 0:
            return "Error: offset must be ≥ 0"

        if list_name:
            if list_name not in self.ps.get_list_names():
                return f"List '{list_name}' not found. Available: {', '.join(self.ps.get_list_names())}"
            all_places = self.ps.get_pins_by_list(list_name)
        else:
            all_places = self.ps.pins

        total = len(all_places)
        places = all_places[offset : offset + limit]

        if not places:
            if offset >= total:
                return f"Offset {offset} exceeds {total} total pins"
            return "No pins found"

        # Header
        if list_name:
            result = f"{list_name}: {len(places)}/{total} (from #{offset + 1})\n"
        else:
            result = f"All pins: {len(places)}/{total} (from #{offset + 1})\n"

        # List pins
        for i, place in enumerate(places, offset + 1):
            if place.place_id:
                result += f"{i}. {place.name} (ID:{place.place_id})"
            else:
                result += f"{i}. {place.name} (No ID)"
            if not list_name:
                result += f" ({place.list_name})"

            details = []
            if place.address:
                details.append(f"Addr: {place.address}")
            if place.notes:
                details.append(f"Notes: {place.notes}")
            if with_links:
                if place.url:
                    details.append(f"Link: {place.url}")
                elif place.latitude and place.longitude:
                    details.append(
                        f"Maps: https://maps.google.com/?q={place.latitude},{place.longitude}"
                    )

            if details:
                result += f" | {' | '.join(details)}"
            result += "\n"

        return result.rstrip()

    def get_pins(
        self,
        place_ids: list[str] | None = None,
        names: list[str] | None = None,
        with_links: bool = True,
    ) -> str:
        """Get detailed pin information for multiple pins by place IDs or exact names.

        Args:
            place_ids: List of Google Maps place IDs
            names: List of exact pin names (fallback for pins without place IDs)
            with_links: Include all available links (default: True)
        """
        if not place_ids and not names:
            return "Error: Must provide either place_ids or names"

        results = []
        not_found = []

        # Process place IDs first
        if place_ids:
            for pin_id in place_ids:
                place = self.ps.get_pin_by_place_id(pin_id)
                if not place:
                    not_found.append(f"ID:{pin_id}")
                    continue
                results.append(self._format_pin_details(place, with_links))

        # Process names as fallback
        if names:
            for name in names:
                place = self.ps.get_pin_by_exact_name(name)
                if not place:
                    not_found.append(f"Name:{name}")
                    continue
                results.append(self._format_pin_details(place, with_links))

        result = "\n".join(results)
        if not_found:
            result += f"\nNot found: {', '.join(not_found)}"

        return result

    def _format_pin_details(self, place, with_links: bool) -> str:
        """Format pin details for display"""
        details = [f"{place.name} ({place.list_name})"]

        if place.address:
            details.append(f"Addr: {place.address}")
        if place.latitude and place.longitude:
            details.append(f"Coords: {place.latitude:.6f},{place.longitude:.6f}")
        if place.notes:
            details.append(f"Notes: {place.notes}")
        if place.date_saved:
            details.append(f"Saved: {place.date_saved}")

        if with_links:
            if place.url:
                details.append(f"Direct: {place.url}")
            if place.latitude and place.longitude:
                details.append(
                    f"Maps: https://maps.google.com/?q={place.latitude},{place.longitude}"
                )
            if place.place_id:
                details.append(
                    f"PlaceID: https://maps.google.com/place?q=place_id:{place.place_id}"
                )

        return " | ".join(details)

    def find_pins_near(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10,
        limit: int = 30,
        offset: int = 0,
        with_links: bool = False,
    ) -> str:
        """Find pins near coordinates with pagination.

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            radius_km: Search radius in km (max: 500)
            limit: Max results (default: 30, max: 100)
            offset: Skip N results (default: 0)
            with_links: Include Google Maps links (default: False)
        """
        # Validate
        if not (-90 <= latitude <= 90):
            return "Error: latitude must be -90 to 90"
        if not (-180 <= longitude <= 180):
            return "Error: longitude must be -180 to 180"
        if radius_km <= 0:
            return "Error: radius must be > 0"
        if radius_km > 500:
            radius_km = 500
        if limit < 1:
            return "Error: limit must be ≥ 1"
        if limit > 100:
            limit = 100
        if offset < 0:
            return "Error: offset must be ≥ 0"

        all_places = self.ps.get_places_near(latitude, longitude, radius_km)
        total = len(all_places)
        places = all_places[offset : offset + limit]

        if not places:
            if offset >= total:
                return (
                    f"No results at offset {offset}. Found {total} within {radius_km}km"
                )
            return f"No pins within {radius_km}km of {latitude:.3f},{longitude:.3f}"

        result = f"Within {radius_km}km: {len(places)}/{total} (from #{offset + 1})\n"

        for i, place in enumerate(places, offset + 1):
            if place.place_id:
                result += f"{i}. {place.name} (ID:{place.place_id}) ({place.list_name})"
            else:
                result += f"{i}. {place.name} (No ID) ({place.list_name})"

            details = []
            if place.address:
                details.append(f"Addr: {place.address}")
            if place.latitude and place.longitude:
                details.append(f"Loc: {place.latitude:.4f},{place.longitude:.4f}")
            if with_links:
                if place.url:
                    details.append(f"Link: {place.url}")
                elif place.latitude and place.longitude:
                    details.append(
                        f"Maps: https://maps.google.com/?q={place.latitude},{place.longitude}"
                    )

            if details:
                result += f" | {' | '.join(details)}"
            result += "\n"

        return result.rstrip()
