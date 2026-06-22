"""Perlin Noise generator, based on the noise packet"""

from noise import snoise2, pnoise2
import numpy as np

class PerlinGenerator:
    def __init__(self, width : int, height : int,
            scale=10, octaves=6,
            persistence=0.5, lacunarity=2.0):
        """
        Perlin Noise Generator.
        :param int width: The width of the picture.
        :param int height: The height of the picture.
        :param int scale: The number of octaves in the noise generation. An octave is another noise generated ontop the previous one.
        :param float persistence: When adding the octave to the result, the amplitude of the noise is multiplied by the persistence.
        :param float lacunarity: The frequency of succesive octave is controlled by the lacunarity.
        """
        self.width = width
        self.height = height
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity

    def generate_perlin(self) -> np.ndarray:
        """
        Generate a normalized pure Perlin noise picture. Output a float array in the interval [0, 1]
        :rtype: ndarray
        """
        xs = np.arange(self.width) / self.scale
        ys = np.arange(self.height) / self.scale

        base = np.random.rand() * 100000
        print(self.octaves)
        img = np.array([
            [pnoise2(x, y, octaves=self.octaves, persistence=self.persistence, lacunarity=self.lacunarity, base=int(base)) for x in xs]
            for y in ys
        ])

        return (img - img.min()) / (img.max() - img.min())
    
    def generate_simplex(self) -> np.ndarray:
        """
        Generate a normalized Simplex noise picture. Output a float array in the interval [0, 1]
        :rtype: ndarray
        """
        xs = np.arange(self.width) / self.scale
        ys = np.arange(self.height) / self.scale

        base = np.random.rand() * 100000

        img = np.array([
            [snoise2(x, y, octaves=self.octaves, persistence=self.persistence, lacunarity=self.lacunarity, base=base) for x in xs]
            for y in ys
        ])

        return (img - img.min()) / (img.max() - img.min())
