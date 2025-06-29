import os
import sys
from pathlib import Path

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

    # Convert directory path to list of JSON files
    data_path = Path(path)
    if not data_path.exists():
        print(f"Data path does not exist: {data_path}", file=sys.stderr)
        sys.exit(1)
        
    json_files = list(data_path.rglob("*.json"))
    if not json_files:
        print(f"No JSON files found in {data_path}", file=sys.stderr)
        sys.exit(1)
        
    file_paths = [str(f) for f in json_files]

    # Initialize the pin server
    pin_server = PinServer(file_paths, get_logger("pin_server"))

    # Initialize the pin provider tools
    PinProvider(app, pin_server)

    # Run the MCP server
    app.run(transport="http")


if __name__ == "__main__":
    main()
