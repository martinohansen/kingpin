import os
from typing import Optional

import googlemaps
import requests
from pydantic import BaseModel
from scrapegraphai.graphs import SmartScraperGraph

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

graph_config = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "openai/gpt-3.5-turbo",
    },
    "verbose": False,
    "headless": True,
}

SCRAPE_PROMPT = """Extract the place's physical mail address.
Set the success flag to true if you believe the address is correct and was
scraped successfully. Otherwise, set it to false and summarize the webpage
result"""


class ScrapeResult(BaseModel):
    address: Optional[str] = None

    content: Optional[str] = None
    hit_captcha: bool
    success: bool


def scrape(link: str) -> ScrapeResult:
    """Scrape link for address using LLMs"""
    result = SmartScraperGraph(
        prompt=SCRAPE_PROMPT,
        source=requests.get(link).url,
        config=graph_config,
        schema=ScrapeResult,
    ).run()
    return ScrapeResult(**result)


class Location(BaseModel):
    lat: float
    lng: float


class Geometry(BaseModel):
    location: Location


class Place(BaseModel):
    business_status: Optional[str] = None
    formatted_address: str
    geometry: Geometry
    types: list[str]
    place_id: str


def search(place: str) -> Optional[Place]:
    """Search for place using Google Maps API"""
    lookup = gmaps.places(place)

    if lookup["status"] == "OK":
        return Place(**lookup["results"][0])

    return None
