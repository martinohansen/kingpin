import json
import logging
from pathlib import Path
from typing import List, Union

from pydantic import ValidationError

from .models import GeoJsonFeature, GeoJsonFormat, Pin, TakeoutPlace


class PinServer:
    """Manages Google Takeout saved places data"""

    def __init__(self, data_path: str, logger: logging.Logger):
        self.logger = logger
        self.pins: List[Pin] = []
        self.load_data(Path(data_path))

    def load_data(self, path: Path) -> None:
        """Load saved places from all JSON files in the data directory"""
        if not path.exists():
            self.logger.error(f"Data path does not exist: {path}")
            return

        # Find all JSON files in the directory and subdirectories
        json_files = list(path.rglob("*.json"))

        if not json_files:
            self.logger.error(f"No JSON files found in {path}")
            return

        self.logger.info(f"Found {len(json_files)} JSON files to process")
        all_pins = []

        for json_file in json_files:
            self.logger.info(f"Loading data from: {json_file}")
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                pins_from_file = self._parse_places_data(data)
                all_pins.extend(pins_from_file)
                self.logger.info(
                    f"Loaded {len(pins_from_file)} pins from {json_file.name}"
                )

            except Exception as e:
                self.logger.warning(f"Error loading data from {json_file}: {e}")
                continue

        self.pins = all_pins
        self.logger.info(
            f"Total loaded: {len(self.pins)} pins from {len(json_files)} files"
        )

    def _parse_places_data(self, data: Union[dict, list]) -> List[Pin]:
        """Parse Google Takeout places data into Pin objects using Pydantic"""
        places = []

        # Try to parse as GeoJSON format first
        try:
            if isinstance(data, dict) and "features" in data:
                geojson = GeoJsonFormat.model_validate(data)
                for feature in geojson.features:
                    pin = self._convert_geojson_to_pin(feature)
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
                pin = self._convert_takeout_to_pin(takeout_place)
                if pin:
                    places.append(pin)
        except ValidationError as e:
            self.logger.warning(f"Failed to parse data as Takeout format: {e}")

        return places

    def _convert_geojson_to_pin(self, feature: GeoJsonFeature) -> Pin:
        """Convert GeoJSON feature to Pin"""
        coords = feature.geometry.coordinates
        return Pin(
            name=feature.properties.name or "Unknown",
            address=feature.properties.address,
            latitude=coords[1] if len(coords) >= 2 else None,
            longitude=coords[0] if len(coords) >= 2 else None,
            place_id=feature.properties.place_id,
            categories=feature.properties.categories,
            notes=feature.properties.comment,
            date_saved=feature.properties.date,
            url=feature.properties.url,
            rating=feature.properties.rating,
        )

    def _convert_takeout_to_pin(self, takeout_place: TakeoutPlace) -> Pin:
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
            categories=takeout_place.categories,
            notes=takeout_place.comment or takeout_place.note,
            date_saved=takeout_place.date,
            url=takeout_place.url,
            rating=takeout_place.rating,
        )

    def search_places(self, query: str, limit: int = 10) -> List[Pin]:
        """Search places by name, address, or notes"""
        query_lower = query.lower()
        results = []

        for place in self.pins:
            # Search in name, address, notes, and categories
            searchable_text = " ".join(
                filter(
                    None,
                    [
                        place.name,
                        place.address,
                        place.notes,
                        " ".join(place.categories or []),
                    ],
                )
            ).lower()

            if query_lower in searchable_text:
                results.append(place)

            if len(results) >= limit:
                break

        return results

    def get_places_by_category(self, category: str) -> List[Pin]:
        """Get all places in a specific category"""
        category_lower = category.lower()
        return [
            place
            for place in self.pins
            if any(cat.lower() == category_lower for cat in (place.categories or []))
        ]

    def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for place in self.pins:
            categories.update(place.categories or [])
        return sorted(list(categories))

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
