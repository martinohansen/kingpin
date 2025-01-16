import csv
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlite3 import IntegrityError
from typing import Optional

import typer
from pydantic import BaseModel
from rich import print
from rich.progress import Progress
from typing_extensions import Annotated

from lib import lookup, pins

app = typer.Typer()


class Takeout(BaseModel):
    """Google takeout data entry"""

    name: str
    note: Optional[str]
    url: str


def _process(lst: str, t: Takeout) -> Optional[pins.Pin]:
    """Maybe scrape pin to search and enrich with Google Maps data"""

    if t.url is None:
        raise ValueError(f"{t!r} has no Google Maps URL")

    result = lookup.scrape(t.url)
    if not result.success or result.address is None:
        logging.warning(f"unable to scrape {t!r}: {result!r}")
        return None

    query = t.name + " " + result.address
    if place := lookup.search(query):

        # Check if place is operational
        operational = True
        if status := place.business_status:
            if "CLOSED" in status:
                operational = False

        return pins.Pin(
            lst=lst,
            name=t.name,
            note=t.note,
            address=place.formatted_address,
            latitude=place.geometry.location.lat,
            longitude=place.geometry.location.lng,
            categorizes=place.types,
            operational=operational,
            google_maps_place_id=place.place_id,
        )

    logging.error(f"unable to lookup {t!r} with {query!r}: {result}")
    return None


@app.command()
def load(
    file: str,
    lst: Annotated[
        Optional[str],
        typer.Option(
            "--list",
            help="Pin type e.g. 'want to go'",
        ),
    ] = None,
):
    """
    Load Google Takeout files into database

    Scrapes the link to reverse lookup the place using the Google Maps API.
    """

    if not pins.initialized():
        pins.init()

    duplicates = 0
    failed = 0
    success = 0
    total = 0

    path = os.path.normpath(file)
    _, ext = os.path.splitext(path)

    # List name defaults to filename without extension
    lst = lst or path.split(os.sep)[-1].removesuffix(ext)

    match ext:
        case ".json":
            # TODO(Martin): Handle GeoJSON format for starred places
            raise NotImplementedError("GeoJSON format not supported")

        case ".csv":
            # Handle Google Takeout CSV format. This is pins like "want to go"
            # and "favorites" unlike starred places which can be exported using
            # GeoJSON.
            takeouts: list[Takeout] = []
            with open(path, newline="") as f:
                reader = csv.reader(f)
                next(reader)  # skip header

                for row in reader:
                    total += 1

                    t = Takeout(name=row[0], note=row[1], url=row[2])
                    if pins.exists(t.url):
                        duplicates += 1
                        logging.debug(f"{t!r} already exists")
                        continue

                    takeouts.append(t)

            # Exit nicely if nothing is to process
            if len(takeouts) == 0:
                if duplicates == total:
                    print("File already processed")
                else:
                    print("No new pins to process")
                return

            with Progress() as progress:
                task = progress.add_task("Processing...", total=len(takeouts))

                with ThreadPoolExecutor() as executor:
                    futures = {executor.submit(_process, lst, t): t for t in takeouts}

                    # Handle futures as they complete, writing successful
                    # results to database and logging failures
                    for future in as_completed(futures):
                        progress.update(task, advance=1)

                        if pin := future.result():
                            try:
                                pins.insert(pin)
                                success += 1
                            except IntegrityError:
                                logging.error(
                                    f"inserting {pin!r}, this should not happen!"
                                )
                                failed += 1
                        else:
                            failed += 1

    print(f"\nProcessed {success} pin(s) ({total=} {duplicates=} {failed=})")
    exit(1 if failed > 0 else 0)
