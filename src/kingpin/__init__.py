import os
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

from .mcp import PinProvider
from .pin import PinServer

app = FastMCP(
    "kingpin",
    instructions="""
Kingpin provides tools for interacting with your Google Maps pins and saved
places.
""",
)


def main():
    logger = get_logger("kingpin")

    path = Path(os.getenv("KINGPIN_DATA_PATH", "."))
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])

    # Read all JSON files at path
    files = list(path.rglob("*.json"))
    if not files:
        logger.error("no files at %s", path)
        sys.exit(1)

    # Initialize the pin server
    ps = PinServer(files, logger)

    # Initialize the pin provider tools
    PinProvider(app, ps)

    # Run the MCP server
    app.run(transport="http")


if __name__ == "__main__":
    main()
