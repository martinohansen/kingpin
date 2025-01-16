import json
import sqlite3
from typing import Optional

from geopy.distance import geodesic
from pydantic import BaseModel

db = sqlite3.connect("pins.db", autocommit=True, check_same_thread=False)
db.row_factory = sqlite3.Row

Point = tuple[float, float]
"""Geographical point as (latitude, longitude)"""


class Pin(BaseModel):
    lst: str
    name: str
    note: Optional[str] = None

    # This is what we strive to collect of every pin to make it useful.
    # Depending on the origin of the pin this has to be gathered with different
    # methods.
    address: str
    latitude: float
    longitude: float
    categorizes: list[str]
    operational: bool

    # Google Maps
    google_maps_takeout_url: Optional[str] = None
    google_maps_place_id: Optional[str] = None

    def __repr__(self) -> str:
        return f"Pin({self.name})"

    @property
    def point(self) -> Point:
        return (self.latitude, self.longitude)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Pin":
        return cls(
            lst=row["list"],
            name=row["name"],
            note=row["note"],
            address=row["address"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            categorizes=json.loads(row["categorizes_json"]),
            operational=row["operational"],
            google_maps_takeout_url=row["google_maps_takeout_url"],
            google_maps_place_id=row["google_maps_place_id"],
        )


def within(km: float, point: Point, pins: list[Pin]) -> list[Pin]:
    """Return pins within km of point"""
    result = []
    for pin in pins:
        if geodesic(pin.point, point).km <= km:
            result.append(pin)
    return result


def insert(pin: Pin) -> None:
    """Insert pin into database"""
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO pins (
            list,
            name,
            note,
            address,
            latitude,
            longitude,
            categorizes_json,
            operational,
            google_maps_takeout_url,
            google_maps_place_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pin.lst,
            pin.name,
            pin.note,
            pin.address,
            pin.latitude,
            pin.longitude,
            json.dumps(pin.categorizes),
            pin.operational,
            pin.google_maps_takeout_url,
            pin.google_maps_place_id,
        ),
    )


def exists(unique: str, field: str = "google_maps_takeout_url") -> bool:
    """Check if unique exists by field"""
    cur = db.cursor()
    cur.execute(f"SELECT * FROM pins WHERE {field} = ?", (unique,))
    return cur.fetchone() is not None


def get(name: str) -> Pin | None:
    """Get pin by name"""
    cur = db.cursor()
    cur.execute("SELECT * FROM pins WHERE name LIKE ?", (name + "%",))
    if fetch := cur.fetchone():
        return Pin.from_row(fetch)
    return None


def get_many(list: Optional[str]) -> list[Pin]:
    """Get pins, optionally filtered by list"""
    cur = db.cursor()
    if list:
        cur.execute("SELECT * FROM pins WHERE list LIKE ?", (list + "%",))
    else:
        cur.execute("SELECT * FROM pins")
    return [Pin.from_row(row) for row in cur.fetchall()]


def get_lists() -> list[str]:
    """Get all unique lists"""
    cur = db.cursor()
    cur.execute("SELECT DISTINCT list FROM pins")
    return [row["list"] for row in cur.fetchall()]


def delete(name: str) -> None:
    """Delete pin by name"""
    cur = db.cursor()
    cur.execute("DELETE FROM pins WHERE name = ?", (name,))


def init() -> None:
    """Initialize database"""
    cur = db.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list TEXT NOT NULL,
            name TEXT NOT NULL,
            note TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            categorizes_json TEXT,
            operational BOOLEAN,
            google_maps_takeout_url TEXT UNIQUE,
            google_maps_place_id TEXT UNIQUE
        );
        """
    )


def initialized() -> bool:
    """Check if database is initialized"""
    cur = db.cursor()
    cur.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='pins'")
    return cur.fetchone() is not None
