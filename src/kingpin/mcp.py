from difflib import SequenceMatcher

from fastmcp import FastMCP

from .pin import PinServer


class PinProvider:
    def __init__(self, mcp: FastMCP, ps: PinServer):
        self.mcp = mcp
        self.ps = ps

        # Register tools with the MCP server
        mcp.tool(self.list_lists)
        mcp.tool(self.list_pins)
        mcp.tool(self.search_pins)
        mcp.tool(self.get_pin_details)
        mcp.tool(self.find_pins_near)

    def list_lists(self) -> str:
        """List all available pin lists with counts."""
        lists = self.ps.get_all_lists()

        if not lists:
            return "No lists found."

        result = f"{len(lists)} lists:\n"
        for i, pin_list in enumerate(lists, 1):
            pin_count = len(self.ps.get_pins_by_list(pin_list.name))
            result += f"{i}. {pin_list.name} ({pin_count})\n"

        return result

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
            result += f"{i}. {place.name}"
            if not list_name:
                result += f" ({place.list_name})"
            result += "\n"

            if place.address:
                result += f"   Address: {place.address}\n"
            if place.notes:
                result += f"   Notes: {place.notes}\n"

            if with_links:
                if place.url:
                    result += f"   Link: {place.url}\n"
                elif place.latitude and place.longitude:
                    result += f"   Maps: https://maps.google.com/?q={place.latitude},{place.longitude}\n"

            result += "\n"

        return result.rstrip()

    def search_pins(
        self, query: str, limit: int = 30, offset: int = 0, with_links: bool = False
    ) -> str:
        """Search pins with fuzzy matching and pagination.

        Args:
            query: Search term
            limit: Max results (default: 30, max: 100)
            offset: Skip N results (default: 0)
            with_links: Include Google Maps links (default: False)
        """
        # Validate
        if not query or not query.strip():
            return "Error: query required"
        if limit < 1:
            return "Error: limit must be ≥ 1"
        if limit > 100:
            limit = 100
        if offset < 0:
            return "Error: offset must be ≥ 0"

        all_places = self.ps.search_places(
            query.strip(), limit + offset + 50
        )  # Get extra for offset
        total_found = len(all_places)
        places = all_places[offset : offset + limit]

        if not places:
            if offset >= total_found:
                return f"No results at offset {offset}. Found {total_found} total matches for '{query}'"
            return f"No matches for '{query}'"

        result = f"Search '{query}': {len(places)}/{total_found} (from #{offset + 1})\n"

        for i, place in enumerate(places, offset + 1):
            result += f"{i}. {place.name} ({place.list_name})\n"
            if place.address:
                result += f"   Address: {place.address}\n"
            if place.notes:
                result += f"   Notes: {place.notes}\n"

            if with_links:
                if place.url:
                    result += f"   Link: {place.url}\n"
                elif place.latitude and place.longitude:
                    result += f"   Maps: https://maps.google.com/?q={place.latitude},{place.longitude}\n"

            result += "\n"

        return result.rstrip()

    def get_pin_details(self, place_name: str, with_links: bool = True) -> str:
        """Get detailed pin information with links.

        Args:
            place_name: Name or partial name to find
            with_links: Include all available links (default: True)
        """
        if not place_name or not place_name.strip():
            return "Error: place name required"

        place_name = place_name.strip()

        # Find exact matches first
        matches = [p for p in self.ps.pins if place_name.lower() in p.name.lower()]

        # Try fuzzy matching if no exact matches
        if not matches:
            fuzzy = []
            for pin in self.ps.pins:
                similarity = SequenceMatcher(
                    None, place_name.lower(), pin.name.lower()
                ).ratio()
                if similarity > 0.6:
                    fuzzy.append((pin, similarity))

            if fuzzy:
                fuzzy.sort(key=lambda x: x[1], reverse=True)
                matches = [match[0] for match in fuzzy[:1]]

        if not matches:
            # Suggest alternatives
            suggestions = [
                p.name
                for p in self.ps.pins
                if any(word in p.name.lower() for word in place_name.lower().split())
            ][:3]
            if suggestions:
                return f"Not found: '{place_name}'. Try: {', '.join(suggestions)}"
            return f"Not found: '{place_name}'"

        place = matches[0]

        result = f"{place.name} ({place.list_name})\n"

        if place.address:
            result += f"Address: {place.address}\n"
        if place.latitude and place.longitude:
            result += f"Coordinates: {place.latitude:.6f}, {place.longitude:.6f}\n"
        if place.notes:
            result += f"Notes: {place.notes}\n"

        if with_links:
            if place.url:
                result += f"Direct link: {place.url}\n"
            if place.latitude and place.longitude:
                result += f"Google Maps: https://maps.google.com/?q={place.latitude},{place.longitude}\n"
            if place.place_id:
                result += f"Place ID link: https://maps.google.com/place?q=place_id:{place.place_id}\n"

        if place.date_saved:
            result += f"Saved: {place.date_saved}\n"

        return result.rstrip()

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
            result += f"{i}. {place.name} ({place.list_name})\n"
            if place.address:
                result += f"   Address: {place.address}\n"
            if place.latitude and place.longitude:
                result += f"   Location: {place.latitude:.4f},{place.longitude:.4f}\n"

            if with_links:
                if place.url:
                    result += f"   Link: {place.url}\n"
                elif place.latitude and place.longitude:
                    result += f"   Maps: https://maps.google.com/?q={place.latitude},{place.longitude}\n"

            result += "\n"

        return result.rstrip()
