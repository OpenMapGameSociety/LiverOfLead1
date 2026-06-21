# Map Generator
```
usage: map-generator.py [-h] [--erode-steps ERODE_STEPS] [--erode-width ERODE_WIDTH] [--enable-gif] [--enable-gen-png]
                        [--gen-erosion-pictures]
                        folder_name width height province_size

Generate a random map for the engine

positional arguments:
  folder_name           Folder where generated map data is placed.
  width                 The width in pixel of the map.
  height                The height in pixel of the map.
  province_size         The average province size in pixels.

options:
  -h, --help            show this help message and exit
  --erode-steps ERODE_STEPS
                        Number of erosion passes to apply during map generation. Defaults to 10.
  --erode-width ERODE_WIDTH
                        Width of the erosion in pixels. Defaults to 3.
  --enable-gif          Save the generated map animation to test.gif.
  --enable-gen-png      Save each generation steps in its own png file.
  --gen-erosion-pictures
                        Also save the erosion steps in the gif and/or the intermediate png files.

Example: map-generator map 500 600 80
```