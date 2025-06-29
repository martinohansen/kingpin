import json
import logging
from pathlib import Path
from typing import List, Union

from pydantic import ValidationError

from .models import GeoJsonFeature, GeoJsonFormat, Pin, TakeoutPlace, MapListFormat, MapListItem, PinList


class PinServer:
    """Manages Google Takeout saved places data"""

    def __init__(self, file_paths: List[str], logger: logging.Logger):
        self.logger = logger
        self.pins: List[Pin] = []
        self.lists: List[PinList] = []
        self.load_data(file_paths)

    def load_data(self, file_paths: List[str]) -> None:
        """Load saved places from specified JSON files"""
        if not file_paths:
            self.logger.error("No file paths provided")
            return

        self.logger.info(f"Found {len(file_paths)} JSON files to process")
        all_pins = []
        all_lists = []

        for file_path in file_paths:
            json_file = Path(file_path)
            if not json_file.exists():
                self.logger.warning(f"File does not exist: {json_file}")
                continue
                
            self.logger.info(f"Loading data from: {json_file}")
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Use filename (without extension) as list name
                list_name = json_file.stem
                pins_from_file = self._parse_places_data(data, list_name)
                all_pins.extend(pins_from_file)
                
                # Create PinList object
                pin_list = PinList(name=list_name, type="custom")
                all_lists.append(pin_list)
                
                self.logger.info(
                    f"Loaded {len(pins_from_file)} pins from {json_file.name} into list '{list_name}'"
                )

            except Exception as e:
                self.logger.warning(f"Error loading data from {json_file}: {e}")
                continue

        self.pins = all_pins
        self.lists = all_lists
        self.logger.info(
            f"Total loaded: {len(self.pins)} pins from {len(file_paths)} files"
        )

    def _parse_places_data(self, data: Union[dict, list], list_name: str) -> List[Pin]:
        """Parse Google Takeout places data into Pin objects using Pydantic"""
        places = []

        # Try to parse as GeoJSON format first
        try:
            if isinstance(data, dict) and "features" in data:
                geojson = GeoJsonFormat.model_validate(data)
                for feature in geojson.features:
                    pin = self._convert_geojson_to_pin(feature, list_name)
                    if pin:
                        places.append(pin)
                return places
        except ValidationError:
            pass

        # Try to parse as Google Maps List format
        try:
            if isinstance(data, dict) and "list" in data:
                map_list = MapListFormat.model_validate(data)
                for item in map_list.list.listItems:
                    pin = self._convert_maplist_to_pin(item, list_name)
                    if pin:
                        places.append(pin)
                return places
        except ValidationError:
            pass

        # Try to parse as Takeout format (list of places)
        try:
            if isinstance(data, list):
                takeout_places = [TakeoutPlace.model_validate(item) for item in data]
            else:
                # Single place object
                takeout_places = [TakeoutPlace.model_validate(data)]

            for takeout_place in takeout_places:
                pin = self._convert_takeout_to_pin(takeout_place, list_name)
                if pin:
                    places.append(pin)
        except ValidationError as e:
            self.logger.warning(f"Failed to parse data as Takeout format: {e}")

        return places

    def _convert_geojson_to_pin(self, feature: GeoJsonFeature, list_name: str) -> Pin:
        """Convert GeoJSON feature to Pin"""
        coords = feature.geometry.coordinates
        
        # Try to get name from nested location first, then from top level
        name = "Unknown"
        if feature.properties.location and feature.properties.location.name:
            name = feature.properties.location.name
        elif feature.properties.name:
            name = feature.properties.name
        
        # Try to get address from nested location first, then from top level
        address = None
        if feature.properties.location and feature.properties.location.address:
            address = feature.properties.location.address
        elif feature.properties.address:
            address = feature.properties.address
        
        return Pin(
            name=name,
            address=address,
            latitude=coords[1] if len(coords) >= 2 and coords[1] != 0 else None,
            longitude=coords[0] if len(coords) >= 2 and coords[0] != 0 else None,
            place_id=feature.properties.place_id,
            notes=feature.properties.comment,
            date_saved=feature.properties.date,
            url=feature.properties.google_maps_url or feature.properties.url,
            list_name=list_name,
        )

    def _convert_maplist_to_pin(self, item: MapListItem, list_name: str) -> Pin:
        """Convert Google Maps List item to Pin"""
        # Handle coordinates conversion from E7 format
        latitude = None
        longitude = None
        if item.place and item.place.latLng:
            if item.place.latLng.latE7:
                latitude = item.place.latLng.latE7 / 1e7
            if item.place.latLng.lngE7:
                longitude = item.place.latLng.lngE7 / 1e7

        # Extract address from place data
        address = None
        place_id = None
        url = None
        if item.place:
            address = item.place.singleLineAddress
            place_id = item.place.mid
        
        # Extract URL from viewer data
        if item.viewer:
            url = item.viewer.url

        return Pin(
            name=item.title or "Unknown",
            address=address,
            latitude=latitude,
            longitude=longitude,
            place_id=place_id,
            notes=None,  # Not available in this format
            date_saved=item.createTime,
            url=url,
            list_name=list_name,
        )

    def _convert_takeout_to_pin(self, takeout_place: TakeoutPlace, list_name: str) -> Pin:
        """Convert TakeoutPlace to Pin"""
        # Handle coordinates conversion from E7 format
        latitude = None
        longitude = None
        if takeout_place.location:
            if takeout_place.location.latitudeE7:
                latitude = takeout_place.location.latitudeE7 / 1e7
            if takeout_place.location.longitudeE7:
                longitude = takeout_place.location.longitudeE7 / 1e7

        return Pin(
            name=takeout_place.name or takeout_place.title or "Unknown",
            address=takeout_place.location.address
            if takeout_place.location
            else takeout_place.address,
            latitude=latitude,
            longitude=longitude,
            place_id=takeout_place.placeId,
            notes=takeout_place.comment or takeout_place.note,
            date_saved=takeout_place.date,
            url=takeout_place.url,
            list_name=list_name,
        )

    def search_places(self, query: str, limit: int = 10) -> List[Pin]:
        """Search places by name, address, or notes"""
        query_lower = query.lower()
        results = []

        for place in self.pins:
            # Search in name, address, and notes
            searchable_text = " ".join(
                filter(
                    None,
                    [
                        place.name,
                        place.address,
                        place.notes,
                    ],
                )
            ).lower()

            if query_lower in searchable_text:
                results.append(place)

            if len(results) >= limit:
                break

        return results

    def get_places_near(
        self, lat: float, lng: float, radius_km: float = 10
    ) -> List[Pin]:
        """Get places within a radius (simple distance calculation)"""
        results = []

        for place in self.pins:
            if place.latitude is None or place.longitude is None:
                continue

            # Simple distance calculation (not perfect for large distances)
            lat_diff = abs(place.latitude - lat)
            lng_diff = abs(place.longitude - lng)

            # Rough conversion: 1 degree ≈ 111 km
            distance_km = ((lat_diff**2 + lng_diff**2) ** 0.5) * 111

            if distance_km <= radius_km:
                results.append(place)

        return results

    def get_all_lists(self) -> List[PinList]:
        """Get all lists"""
        return self.lists

    def get_pins_by_list(self, list_name: str) -> List[Pin]:
        """Get all pins from a specific list"""
        return [pin for pin in self.pins if pin.list_name == list_name]
        
    def get_list_names(self) -> List[str]:
        """Get all unique list names"""
        return [pin_list.name for pin_list in self.lists]
