from typing import Any, Dict, Optional, Union
from typing import List as ListType

from pydantic import BaseModel, Field, RootModel


class PinList(BaseModel):
    """Represents a list of pins"""

    name: str  # The filename/list name
    type: str = "custom"  # Always "custom" for now


class Pin(BaseModel):
    """Represents a saved place from Google Takeout data"""

    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    notes: Optional[str] = None
    date_saved: Optional[str] = None
    url: Optional[str] = None
    list_name: str  # The list/file this pin originated from


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
    comment: Optional[str] = None
    note: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    address: Optional[str] = None  # Sometimes address is at root level


class GeoJsonGeometry(BaseModel):
    """GeoJSON geometry"""

    type: str = "Point"
    coordinates: ListType[float] = Field(default_factory=list)


class GeoJsonLocation(BaseModel):
    """Location nested in GeoJSON properties"""

    name: Optional[str] = None
    address: Optional[str] = None
    country_code: Optional[str] = None


class GeoJsonProperties(BaseModel):
    """GeoJSON properties"""

    name: Optional[str] = None
    address: Optional[str] = None
    place_id: Optional[str] = None
    comment: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    google_maps_url: Optional[str] = None
    location: Optional[GeoJsonLocation] = None


class GeoJsonFeature(BaseModel):
    """GeoJSON feature"""

    type: str = "Feature"
    geometry: GeoJsonGeometry
    properties: GeoJsonProperties


class GeoJsonFormat(BaseModel):
    """GeoJSON format container"""

    type: str = "FeatureCollection"
    features: ListType[GeoJsonFeature]


# Google Maps List format models
class MapListFeatureId(BaseModel):
    """Feature ID in Google Maps list format"""

    cellId: Optional[str] = None
    fprint: Optional[str] = None


class MapListLatLng(BaseModel):
    """Coordinates in Google Maps list format (E7 format)"""

    latE7: Optional[int] = None
    lngE7: Optional[int] = None


class MapListPlace(BaseModel):
    """Place in Google Maps list format"""

    featureId: Optional[MapListFeatureId] = None
    latLng: Optional[MapListLatLng] = None
    query: Optional[str] = None
    singleLineAddress: Optional[str] = None
    mid: Optional[str] = None


class MapListViewer(BaseModel):
    """Viewer information in Google Maps list format"""

    url: Optional[str] = None


class MapListItem(BaseModel):
    """Item in Google Maps list"""

    place: Optional[MapListPlace] = None
    title: Optional[str] = None
    createTime: Optional[str] = None
    updateTime: Optional[str] = None
    viewer: Optional[MapListViewer] = None


class MapList(BaseModel):
    """Google Maps list container"""

    displayName: Optional[str] = None
    listItems: ListType[MapListItem] = Field(default_factory=list)


class MapListFormat(BaseModel):
    """Google Maps list format root"""

    list: MapList


class TakeoutFormat(RootModel):
    """Google Takeout direct format - can be a list or dict"""

    root: Union[ListType[TakeoutPlace], Dict[str, Any]]
