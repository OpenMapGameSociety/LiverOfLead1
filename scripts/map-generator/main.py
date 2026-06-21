"""Command-line entry point for map generation."""

import argparse
from pathlib import Path

import os
import time

from src.map_generator import *
from src.perlin import *

def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for map generation.
    """
    def check_positive(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
        return ivalue

    def check_non_negative(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid non-negative int value")
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
    parser.add_argument(
        "--erode-steps",
        type=check_non_negative,
        default=10,
        help="Number of erosion passes to apply during map generation. Defaults to 10.",
    )
    parser.add_argument(
        "--erode-width",
        type=check_non_negative,
        default=3,
        help="Width of the erosion in pixels. Defaults to 3.",
    )
    parser.add_argument(
        "--enable-gif",
        action="store_true",
        help="Save the generated map animation to test.gif.",
    )
    parser.add_argument(
        "--enable-gen-png",
        action="store_true",
        help="Save each generation steps in its own png file.",
    )
    parser.add_argument(
        "--gen-erosion-pictures",
        action="store_true",
        help="Also save the erosion steps in the gif and/or the intermediate png files.",
    )
    return parser

def main() -> int:
    """Run the map generator CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if not (args.enable_gif or args.enable_gen_png) and args.gen_erosion_pictures:
        parser.error("--gen-erosion-pictures needs to be used with either --enable-gif or --enable-gen-png")

    print(f"Generate map data in folder: {args.folder_name}")
    print("Random Seedlings Mode")
    print(f"Erosion steps : {args.erode_steps}, erosion width : {args.erode_width}")
    os.makedirs(args.folder_name, exist_ok=True)
    map_generator = MapGenerator(args.width, args.height, args.folder_name,
            save_gif=args.enable_gif,
            save_intermediate=args.enable_gen_png,
            save_erosion=args.gen_erosion_pictures)

    # Generating the province map
    print("Starting Generation ...")
    start_time = time.time()
    map_generator.generate_random_provinces_map_seedlings(args.province_size)
    print(f"Finished seedlings generation")
    map_generator.grow_pixel()
    for i in range(args.erode_steps):
        print(f"Erosion phase {i}/{args.erode_steps}")
        map_generator.erode_map(args.erode_width)
        map_generator.grow_pixel()

    map_generator.generate_image()
    map_generator.generate_provinces_csv()
    print(f"Elapsed {time.time() - start_time:.2f} seconds")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
