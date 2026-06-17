"""Command-line entry point for map generation."""

import argparse
from pathlib import Path

import os, sys
from PIL import Image

PROVINCES_BMP_NAME = "provinces.bmp"

def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for map generation.
    """
    def check_positive(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
        return ivalue
    
    parser = argparse.ArgumentParser(
        prog="map-generator.py",
        description="Generate a random map for the engine",
        epilog="Example: map-generator map 500 600 80",
    )

    parser.add_argument(
        "folder_name",
        type=Path,
        help="Folder where generated map data is placed.",
    )
    parser.add_argument(
        "width",
        type=check_positive,
        help="The width in pixel of the map.",
    )
    parser.add_argument(
        "height",
        type=check_positive,
        help="The height in pixel of the map.",
    )
    parser.add_argument(
        "province_size",
        type=check_positive,
        help="The average province size in pixels.",
    )
    return parser

def generate_random_provinces_map_seedling(
        image_path : str,
        dims : tuple[int, int],
        province_size : int) -> Image:
    """Create a random provinces map. The placement of the provinces is random and no size is guaranteed
    """
    image = Image.new("RGB", dims)
    
    return image

def main() -> int:
    """Run the map generator CLI."""
    parser = build_parser()
    args = parser.parse_args()

    print(f"Generate map data in folder: {args.folder_name}")
    os.makedirs(args.folder_name, exist_ok=True)

    # Generating the province map
    provinces_bmp_path = os.path.join(args.folder_name, PROVINCES_BMP_NAME)
    image = generate_random_provinces_map_seedling(provinces_bmp_path, (args.width, args.height), args.province_size)


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
