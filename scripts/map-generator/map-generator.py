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

def generate_random_provinces_map_seedlings(
        dims : tuple[int, int],
        province_size : int) -> np.ndarray:
    """Generate a number seedlings, lone pixels with a unique color that can be used to grow the map
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

    return image


def erode_map(image : np.ndarray, passes : int) -> np.ndarray:
    """Erode color boundaries. Execute a certain number of passes"""
    if passes <= 0:
        return image
    w, h, _ = image.shape
    empty_pixel = np.zeros(3, np.uint8)
    if erode_map.inverted:
        for y in reversed(range(h)):
            for x in reversed(range(w)):
                if x == 0 or x == w - 1 or h == 0 or y == h - 1 or \
                        np.any(image[x, y] != image[x - 1, y]) or \
                        np.any(image[x, y] != image[x, y - 1]):
                    image[x, y] = empty_pixel
        erode_map.inverted = False
        return erode_map(image, passes - 1)
    for y in range(h):
        for x in range(w):
            if x == 0 or x == w - 1 or h == 0 or y == h - 1 or \
                    np.any(image[x, y] != image[x + 1, y]) or \
                    np.any(image[x, y] != image[x, y + 1]):
                image[x, y] = empty_pixel

    erode_map.inverted = True
    return erode_map(image, passes - 1)
erode_map.inverted = False

def grow_pixel(image : np.ndarray) -> np.ndarray:
    w, h, _ = image.shape
    empty_pixel = np.zeros(3, np.uint8)

    # Get the pixels that can seed
    set_seedlings = set()
    for y in range(h-1):
        for x in range(w-1):
            if np.any(image[x, y] != image[x + 1, y]):
                if np.any(image[x, y] != empty_pixel):
                    set_seedlings.add((x, y))
                if np.any(image[x + 1, y] != empty_pixel):
                    set_seedlings.add((x + 1, y))
            if np.any(image[x, y] != image[x, y + 1]):
                if np.any(image[x, y] != empty_pixel):
                    set_seedlings.add((x, y))
                if np.any(image[x, y + 1] != empty_pixel):
                    set_seedlings.add((x, y + 1))

    list_seedlings = list(set_seedlings)
    while len(list_seedlings):
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        shuffle(directions)
        idx = randint(0, len(list_seedlings) - 1)
        x, y = list_seedlings[idx]
        assigned = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and np.all(image[nx, ny] == empty_pixel):
                image[nx, ny] = image[x, y].copy()
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

    gif_frames = []
    def save_gif_frame(image):
        gif_frames.append(Image.fromarray(image, mode="RGB"))
    def save_gif(path):
        gif_frames[0].save(path,
               save_all=True, append_images=gif_frames[1:], optimize=False, duration=400, loop=0)

    # Generating the province map
    provinces_bmp_path = os.path.join(args.folder_name, PROVINCES_BMP_NAME)
    image = generate_random_provinces_map_seedlings((args.height, args.width), args.province_size)
    save_gif_frame(image)
    image = grow_pixel(image)
    save_gif_frame(image)
    for i in range(5):
        image = erode_map(image, 2)
        save_gif_frame(image)
        image = grow_pixel(image)
        save_gif_frame(image)
        print(i)

    save_gif("test.gif")

    pil_image = Image.fromarray(image, mode="RGB")
    pil_image.save(provinces_bmp_path)
    pil_image.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
