from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, RootModel


class Pin(BaseModel):
    """Represents a saved place from Google Takeout data"""

    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    date_saved: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = None


class Location(BaseModel):
    """Location data from Google Takeout format"""
    address: Optional[str] = None
    latitudeE7: Optional[int] = None
    longitudeE7: Optional[int] = None


class TakeoutPlace(BaseModel):
    """Google Takeout direct format"""
    name: Optional[str] = None
    title: Optional[str] = None
    location: Optional[Location] = None
    placeId: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    comment: Optional[str] = None
    note: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = None
    address: Optional[str] = None  # Sometimes address is at root level


class GeoJsonGeometry(BaseModel):
    """GeoJSON geometry"""
    type: str = "Point"
    coordinates: List[float] = Field(default_factory=list)


class GeoJsonProperties(BaseModel):
    """GeoJSON properties"""
    name: Optional[str] = None
    address: Optional[str] = None
    place_id: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    comment: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = None


class GeoJsonFeature(BaseModel):
    """GeoJSON feature"""
    type: str = "Feature"
    geometry: GeoJsonGeometry
    properties: GeoJsonProperties


class GeoJsonFormat(BaseModel):
    """GeoJSON format container"""
    type: str = "FeatureCollection"
    features: List[GeoJsonFeature]


class TakeoutFormat(RootModel):
    """Google Takeout direct format - can be a list or dict"""
    root: Union[List[TakeoutPlace], Dict[str, Any]]
