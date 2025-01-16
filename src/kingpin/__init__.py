import os
import sys

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

from .mcp import PinProvider
from .pin import PinServer


def main():
    # Initialize the server
    app = FastMCP(
        "kingpin",
        instructions="""
Kingpin provides tools for interacting with your Google Maps pins and saved
places.
""",
    )

    path = str(os.getenv("KINGPIN_DATA_PATH", "."))
    if len(sys.argv) > 1:
        path = sys.argv[1]

    # Initialize the pin server
    pin_server = PinServer(path, get_logger("pin_server"))

    # Initialize the pin provider tools
    PinProvider(app, pin_server)

    # Run the MCP server
    app.run(transport="http")


if __name__ == "__main__":
    main()
