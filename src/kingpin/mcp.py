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
        """List all available pin lists"""
        lists = self.ps.get_all_lists()
        
        if not lists:
            return "No lists found."
        
        result = f"Found {len(lists)} lists:\n\n"
        for i, pin_list in enumerate(lists, 1):
            pin_count = len(self.ps.get_pins_by_list(pin_list.name))
            result += f"{i}. **{pin_list.name}** ({pin_count} pins, type: {pin_list.type})\n"
        
        return result

    def list_pins(self, list_name: str | None = None, limit: int = 20) -> str:
        """List pins from a specific list or all pins"""
        if list_name:
            places = self.ps.get_pins_by_list(list_name)[:limit]
            if not places:
                return f"No pins found in list '{list_name}'."
            result = f"Found {len(places)} pins in list '{list_name}':\n\n"
        else:
            places = self.ps.pins[:limit]
            if not places:
                return "No pins found."
            result = f"Found {len(places)} pins:\n\n"
            
        for i, place in enumerate(places, 1):
            result += f"{i}. **{place.name}** (from {place.list_name})\n"
            if place.address:
                result += f"   📍 {place.address}\n"
            if place.notes:
                result += f"   📝 Notes: {place.notes}\n"
            result += "\n"

        return result

    def search_pins(self, query: str, limit: int = 10) -> str:
        """Search pins by name, address, or notes across all lists"""
        places = self.ps.search_places(query, limit)

        if not places:
            return f"No places found matching '{query}'"

        result = f"Found {len(places)} places matching '{query}':\n\n"
        for i, place in enumerate(places, 1):
            result += f"{i}. **{place.name}** (from {place.list_name})\n"
            if place.address:
                result += f"   📍 {place.address}\n"
            if place.notes:
                result += f"   📝 Notes: {place.notes}\n"
            result += "\n"

        return result

    def get_pin_details(self, place_name: str) -> str:
        """Get detailed information about a specific pin"""
        # Find the place
        matching_places = [
            p for p in self.ps.pins if place_name.lower() in p.name.lower()
        ]

        if not matching_places:
            return f"No place found with name containing '{place_name}'"

        place = matching_places[0]  # Take the first match

        result = f"**{place.name}** (from {place.list_name})\n\n"
        if place.address:
            result += f"📍 **Address:** {place.address}\n"
        if place.latitude and place.longitude:
            result += (
                f"🌍 **Coordinates:** {place.latitude:.6f}, {place.longitude:.6f}\n"
            )
        if place.notes:
            result += f"📝 **Notes:** {place.notes}\n"
        if place.date_saved:
            result += f"📅 **Saved:** {place.date_saved}\n"
        if place.url:
            result += f"🔗 **URL:** {place.url}\n"
        if place.place_id:
            result += f"🆔 **Place ID:** {place.place_id}\n"

        return result

    def find_pins_near(
        self, latitude: float, longitude: float, radius_km: float = 10
    ) -> str:
        """Find pins near a specific location"""
        places = self.ps.get_places_near(latitude, longitude, radius_km)

        if not places:
            return f"No pins found within {radius_km}km of ({latitude:.6f}, {longitude:.6f})"

        result = f"Found {len(places)} places within {radius_km}km:\n\n"
        for place in places:
            result += f"• **{place.name}** (from {place.list_name})"
            if place.address:
                result += f" - {place.address}"
            result += "\n"

        return result
