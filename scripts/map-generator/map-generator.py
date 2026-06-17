"""Command-line entry point for map generation."""

import argparse
from pathlib import Path

import os, sys
from random import randint, shuffle, choice
from PIL import Image
import numpy as np

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
        province_size : int) -> np.ndarray:
    """Create a random provinces map. The placement of the provinces is random and no size is guaranteed
    """
    image = np.zeros((dims[0], dims[1], 3), np.uint8)

    w = dims[0]
    h = dims[1]
    nmb_seedlings = int(w*h/province_size)

    # Generate the first pixels
    seedlings = set()
    colors = set([(0, 0, 0)]) # Pure black use for empty
    for i in range(nmb_seedlings):
        coords = (randint(0, w-1), randint(0, h-1))
        while coords in seedlings:
            coords = (randint(0, w-1), randint(0, h-1))
        seedlings.add(coords)

        color = (randint(0, 255), randint(0, 255), randint(0, 255))
        while color in colors:
            color = (randint(0, 255), randint(0, 255), randint(0, 255))
        colors.add(color)
        image[coords[0], coords[1]] = color

    # Grow the pixels randomly
    list_seedlings = list(seedlings)
    empty_pixel = np.zeros(3, np.uint8)
    while len(list_seedlings):
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        shuffle(directions)
        idx = randint(0, len(list_seedlings) - 1)
        x, y = list_seedlings[idx]
        assigned = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and np.all(image[nx, ny] == empty_pixel):
                image[nx, ny] = image[x, y]
                list_seedlings.append((nx, ny))
                assigned = True
                break
        if not assigned:
            list_seedlings[idx] = list_seedlings[-1]
            list_seedlings.pop()

    return image

def main() -> int:
    """Run the map generator CLI."""
    parser = build_parser()
    args = parser.parse_args()

    print(f"Generate map data in folder: {args.folder_name}")
    os.makedirs(args.folder_name, exist_ok=True)

    # Generating the province map
    provinces_bmp_path = os.path.join(args.folder_name, PROVINCES_BMP_NAME)
    image = generate_random_provinces_map_seedling(provinces_bmp_path, (args.height, args.width), args.province_size)

    pil_image = Image.fromarray(image, mode="RGB")
    pil_image.save(provinces_bmp_path)
    pil_image.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
