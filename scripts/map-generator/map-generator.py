"""Command-line entry point for map generation."""

import argparse
from pathlib import Path

import os, sys
from random import randint, shuffle, choice
import time
from PIL import Image
import numpy as np

class MapGenerator:

    PROVINCES_BMP_NAME = "provinces.bmp"
    PROVINCES_CSV_NAME = "provinces.csv"

    TEST_GIF_NAME = "test.gif"
    INTERMEDIATE_IMAGE_NAME = "intermediate{}.png"
    GIF_FRAME_PERIOD = 100

    def __init__(self, width : int, height : int, folder_path : str,
            save_gif=False,
            save_intermediate=False,
            save_erosion=False):
        self.w = width
        self.h = height
        self.folder = folder_path
        self.init_map()

        self.inverted = False

        self.save_gif = save_gif
        self.gif_images = []
        self.save_intermediate = save_intermediate
        self.save_erosion = save_erosion

    def init_map(self) -> None:
        """Init the map with empty pixels"""
        self.image = np.zeros((self.w, self.h, 3), np.uint8)
        self.gif_images = []

    def _end_generation_step(self) -> None:
        """Internally called at the end of each generation steps"""
        if self.save_gif:
            self.gif_images.append(Image.fromarray(self.image, mode="RGB"))
        if self.save_intermediate:
            path = os.path.join(self.folder, MapGenerator.INTERMEDIATE_IMAGE_NAME).format(len(self.gif_images) - 1)
            pil_image = Image.fromarray(self.image, mode="RGB")
            pil_image.save(path)
            pil_image.close()

    def generate_image(self) -> None:
        """Generate the provinces bmp picture after the generation steps"""
        provinces_bmp_path = os.path.join(self.folder, MapGenerator.PROVINCES_BMP_NAME)
        pil_image = Image.fromarray(self.image, mode="RGB")
        pil_image.save(provinces_bmp_path)
        pil_image.close()
        if self.save_gif and len(self.gif_images) > 1:
            path = os.path.join(self.folder, MapGenerator.TEST_GIF_NAME)
            self.gif_images[0].save(path,
                save_all=True, append_images=self.gif_images[1:], optimize=False, duration=MapGenerator.GIF_FRAME_PERIOD, loop=0)
            
    def generate_provinces_csv(self) -> None:
        """Generate the provinces csv file from the current provinces picture"""
        w = self.w
        h = self.h

        colors = set()
        for x in range(w):
            for y in range(h):
                colors.add(tuple(self.image[x, y]))

        file_path = os.path.join(self.folder, MapGenerator.PROVINCES_CSV_NAME)
        with open(file_path, "w") as fd:
            for i, color in enumerate(colors):
                fd.write(f"{i};{color[0]};{color[1]};{color[2]}\n")

    def generate_random_provinces_map_seedlings(self, province_size : int) -> None:
        """Generate a number seedlings, lone pixels with a unique color that can be used to grow the map
        """
        w = self.w
        h = self.h
        nmb_seedlings = int(w*h/province_size)

        # Generate the first pixels
        seedlings = set()
        colors = set([(0, 0, 0)]) # Pure black use for empty
        for _ in range(nmb_seedlings):
            coords = (randint(0, w-1), randint(0, h-1))
            while coords in seedlings:
                coords = (randint(0, w-1), randint(0, h-1))
            seedlings.add(coords)

            color = (randint(0, 255), randint(0, 255), randint(0, 255))
            while color in colors:
                color = (randint(0, 255), randint(0, 255), randint(0, 255))
            colors.add(color)
            self.image[coords[0], coords[1]] = color

    def erode_map(self, passes : int) -> None:
        """Erode color boundaries. Execute a certain number of passes"""
        if passes <= 0:
            if self.save_erosion:
                self._end_generation_step()
            return
        w, h = self.w, self.h
        empty_pixel = np.zeros(3, np.uint8)
        if self.inverted:
            for y in reversed(range(h)):
                for x in reversed(range(w)):
                    if x == 0 or x == w - 1 or h == 0 or y == h - 1 or \
                            np.any(self.image[x, y] != self.image[x - 1, y]) or \
                            np.any(self.image[x, y] != self.image[x, y - 1]):
                        self.image[x, y] = empty_pixel
            self.inverted = False
            self.erode_map(passes - 1)
            return
        for y in range(h):
            for x in range(w):
                if x == 0 or x == w - 1 or h == 0 or y == h - 1 or \
                        np.any(self.image[x, y] != self.image[x + 1, y]) or \
                        np.any(self.image[x, y] != self.image[x, y + 1]):
                    self.image[x, y] = empty_pixel

        self.inverted = True
        self.erode_map(passes - 1)
        return
    
    def grow_pixel(self) -> None:
        """Grows already placed pixels in the empty space of the province map"""
        w, h = self.w, self.h
        empty_pixel = np.zeros(3, np.uint8)

        # Get the pixels that can seed
        set_seedlings = set()
        for y in range(h-1):
            for x in range(w-1):
                if np.any(self.image[x, y] != self.image[x + 1, y]):
                    if np.any(self.image[x, y] != empty_pixel):
                        set_seedlings.add((x, y))
                    if np.any(self.image[x + 1, y] != empty_pixel):
                        set_seedlings.add((x + 1, y))
                if np.any(self.image[x, y] != self.image[x, y + 1]):
                    if np.any(self.image[x, y] != empty_pixel):
                        set_seedlings.add((x, y))
                    if np.any(self.image[x, y + 1] != empty_pixel):
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
                if 0 <= nx < w and 0 <= ny < h and np.all(self.image[nx, ny] == empty_pixel):
                    self.image[nx, ny] = self.image[x, y].copy()
                    list_seedlings.append((nx, ny))
                    assigned = True
                    break
            if not assigned:
                list_seedlings[idx] = list_seedlings[-1]
                list_seedlings.pop()
        self._end_generation_step()


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
