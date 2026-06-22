"""Generate an Aquitaine administrative map from OpenStreetMap/geodata.

This script is intentionally separate from map-generator.py. The existing random
generator is useful for procedural prototypes, while this tool creates a
data-driven map where each province corresponds to one historical Aquitaine
département.

The gameplay province bitmap is kept clean and non-antialiased. Styled terrain,
roads, railways, rivers, forests, urban areas, and city markers are exported as
separate visual layers.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import unicodedata
import copy
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
from PIL import Image, ImageDraw
import numpy as np

AQUITAINE_BBOX_WGS84 = (-2.55, 42.25, 1.65, 45.75)
DEFAULT_PROJECTION = "EPSG:2154"  # Lambert-93, metric CRS for mainland France.
OSM_ATTRIBUTION = "© OpenStreetMap contributors, ODbL"

HISTORICAL_AQUITAINE_DEPARTEMENTS = [
    {"code": "24", "name": "Dordogne", "prefecture": "Périgueux", "color": (142, 183, 120)},
    {"code": "33", "name": "Gironde", "prefecture": "Bordeaux", "color": (173, 132, 91)},
    {"code": "40", "name": "Landes", "prefecture": "Mont-de-Marsan", "color": (91, 145, 112)},
    {"code": "47", "name": "Lot-et-Garonne", "prefecture": "Agen", "color": (156, 118, 154)},
    {"code": "64", "name": "Pyrénées-Atlantiques", "prefecture": "Pau", "color": (132, 151, 190)},
]

STYLE_PALETTES = {
    "modern-strategy": {
        "land": (142, 151, 119),
        "water": (38, 56, 71),
        "coast": (63, 107, 122),
        "forest": (79, 113, 80),
        "urban": (216, 209, 191),
        "province_border": (255, 255, 255),
        "province_border_alpha": 70,
        "river": (96, 165, 205),
        "river_alpha": 190,
        "road": (240, 216, 160),
        "road_alpha": 220,
        "rail": (59, 59, 63),
        "rail_alpha": 220,
        "city": (255, 241, 199),
        "city_alpha": 235,
        "prefecture": (255, 255, 255),
        "prefecture_alpha": 255,
    }
}

# Only lightweight line/point layers are kept for the strategy-game overview.
# Heavy polygon layers (forests, urban, water bodies) are intentionally omitted:
# they cover the full Aquitaine bounding box and generate dozens of Overpass
# sub-queries, which is the main source of the slow-download warning.
OSM_LAYER_CONFIGS = [
    {
        "name": "cities",
        # Only proper cities and large towns — excludes villages/hamlets.
        "tags": {"place": ["city", "town"]},
        "geometry_types": {"Point"},
        "overlay": "cities.png",
        "line_width": None,
    },
    {
        "name": "roads",
        # Motorways, trunk roads, and primary roads only — the main circulation axes.
        "tags": {"highway": ["motorway", "trunk", "primary"]},
        "geometry_types": {"LineString", "MultiLineString"},
        "overlay": "roads.png",
        "line_width": 4,
    },
    {
        "name": "railways",
        # Main rail lines only (no yards, sidings, or light rail).
        "tags": {"railway": "rail"},
        "geometry_types": {"LineString", "MultiLineString"},
        "overlay": "railways.png",
        "line_width": 3,
    },
    {
        "name": "rivers",
        # Major rivers only — streams and canals are excluded for legibility.
        "tags": {"waterway": ["river"]},
        "geometry_types": {"LineString", "MultiLineString"},
        "overlay": "rivers.png",
        "line_width": 2,
    },
]


@dataclass
class Province:
    code: str
    name: str
    prefecture: str
    color: tuple[int, int, int]
    geometry: Any | None = None
    center_x: float | None = None
    center_y: float | None = None
    lon: float | None = None
    lat: float | None = None
    area_km2: float | None = None

    @property
    def id(self) -> int:
        return int(self.code)


@dataclass
class MapBounds:
    left: float
    bottom: float
    right: float
    top: float
    width: int
    height: int
    projection: str

    def project(self, x: float, y: float) -> tuple[int, int]:
        col = int(round((x - self.left) * self.width / (self.right - self.left)))
        row = int(round((self.top - y) * self.height / (self.top - self.bottom)))
        return col, row


class GenerationError(RuntimeError):
    """Raised when required geodata or dependencies are missing."""


def normalize_name(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


def clean_gdf(gdf: Any) -> Any:
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if hasattr(gdf.geometry, "make_valid"):
        gdf = gdf.copy()
        gdf.geometry = gdf.geometry.make_valid()
    else:
        gdf = gdf.copy()
        gdf.geometry = gdf.geometry.buffer(0)
    return gdf[gdf.geometry.notna()].copy()


def import_geopandas():
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise GenerationError(
            "GeoPandas is required for geospatial processing. Install it with: "
            "python -m pip install geopandas rasterio shapely pyogrio"
        ) from exc
    return gpd


def import_osmnx():
    try:
        import osmnx as ox
    except ImportError:
        return None
    return ox


def import_rasterio():
    try:
        import rasterio
    except ImportError as exc:
        raise GenerationError(
            "Rasterio is required for rasterizing province polygons. Install it with: "
            "python -m pip install rasterio"
        ) from exc
    return rasterio


def load_departement_boundaries(args: argparse.Namespace):
    gpd = import_geopandas()

    if args.boundaries is not None:
        print(f"Loading département boundaries from {args.boundaries}")
        gdf = gpd.read_file(args.boundaries)
    else:
        ox = import_osmnx()
        if ox is None:
            raise GenerationError(
                "No --boundaries file was provided and OSMnx is not installed. "
                "Install OSMnx or provide a GeoJSON/GeoPackage file containing "
                "admin_level=6 French département boundaries."
            )

        print("Downloading Aquitaine département boundaries from OpenStreetMap...")
        print("Using per-département named queries (fast — no large bbox scan).")

        dept_gdfs: list[Any] = []
        for dept in HISTORICAL_AQUITAINE_DEPARTEMENTS:
            query_name = f"{dept['name']}, France"
            print(f"  Fetching boundary for {query_name}…")
            try:
                dept_gdf = ox.geocode_to_gdf(query_name, which_result=1)
                dept_gdf["ref"] = dept["code"]
                dept_gdf["name"] = dept["name"]
                dept_gdfs.append(dept_gdf)
            except Exception as exc:
                raise GenerationError(
                    f"Could not download boundary for {query_name}: {exc}"
                ) from exc

        import pandas as pd
        gdf = pd.concat(dept_gdfs, ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")

    gdf = clean_gdf(gdf)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    gdf = gdf.to_crs(args.projection)
    gdf = gdf.explode(index_parts=False)
    gdf = clean_gdf(gdf)

    selected_rows: list[Any] = []
    expected = {dept["code"]: dept for dept in HISTORICAL_AQUITAINE_DEPARTEMENTS}
    expected_names = {normalize_name(dept["name"]): dept["code"] for dept in HISTORICAL_AQUITAINE_DEPARTEMENTS}

    codes_to_pick = copy.deepcopy(expected)
    for _, row in gdf.iterrows():
        code = extract_departement_code(row)
        name = str(row.get("name", ""))
        if code in codes_to_pick or normalize_name(name) in expected_names:
            selected_rows.append(row)
            codes_to_pick.pop(code, None)
            expected_name = expected_names.pop(normalize_name(name), None)

    print(f"Selected rows: {selected_rows}")
    if len(selected_rows) != len(expected):
        found = sorted({extract_departement_code(row) or str(row.get("name", "")) for row in selected_rows})
        raise GenerationError(
            f"Expected {len(expected)} Aquitaine départements, found {len(selected_rows)}: {found}. "
            "Provide --boundaries with French admin_level=6 boundaries, or fix the OSM query."
        )

    selected = gpd.GeoDataFrame(selected_rows, crs=gdf.crs).copy()
    selected["code"] = selected.apply(extract_departement_code, axis=1)
    if "name" not in selected.columns:
        selected["name"] = ""
    selected["name"] = selected["name"].fillna("")
    selected["name_norm"] = selected["name"].map(normalize_name)

    rows = []
    for dept in HISTORICAL_AQUITAINE_DEPARTEMENTS:
        mask = (selected["code"] == dept["code"]) | (selected["name_norm"] == normalize_name(dept["name"]))
        matches = selected[mask]
        if matches.empty:
            raise GenerationError(f"Could not find département {dept['code']} {dept['name']}")
        row = matches.iloc[0]
        rows.append(
            Province(
                code=dept["code"],
                name=dept["name"],
                prefecture=dept["prefecture"],
                color=dept["color"],
                geometry=row.geometry,
                area_km2=float(row.geometry.area / 1_000_000),
            )
        )

    return gpd.GeoDataFrame([row.__dict__ for row in rows], geometry="geometry", crs=gdf.crs), selected


def extract_departement_code(row: Any) -> str | None:
    for column in ("ref", "ref:INSEE", "INSEE", "code", "admin_level_6_ref"):
        if column in row and row[column] is not None:
            value = str(row[column]).strip()
            if value.startswith("FR-"):
                value = value.split("-", 1)[1]
            if value.isdigit() and len(value) == 2:
                return value

    iso_column = None
    for column in row.index:
        if str(column).casefold() in {"iso3166-2", "iso3166_2"}:
            iso_column = column
            break
    if iso_column is not None and row[iso_column] is not None:
        value = str(row[iso_column]).strip().split(";")[0]
        if "-" in value:
            value = value.rsplit("-", 1)[1]
        if value.isdigit() and len(value) == 2:
            return value

    return None


def build_bounds(provinces_gdf: Any, width: int, height: int, projection: str, buffer_meters: float) -> MapBounds:
    bounds = provinces_gdf.total_bounds
    left = float(bounds[0]) - buffer_meters
    bottom = float(bounds[1]) - buffer_meters
    right = float(bounds[2]) + buffer_meters
    top = float(bounds[3]) + buffer_meters
    return MapBounds(left=left, bottom=bottom, right=right, top=top, width=width, height=height, projection=projection)


def rasterize_province_ids(provinces_gdf: Any, bounds: MapBounds) -> Any:
    import numpy as np
    from rasterio import features
    from rasterio.transform import from_bounds

    shapes = []
    for _, row in provinces_gdf.iterrows():
        shapes.append((row.geometry, int(row.code)))

    transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, bounds.width, bounds.height)
    province_ids = features.rasterize(
        shapes=shapes,
        out_shape=(bounds.height, bounds.width),
        transform=transform,
        fill=0,
        dtype=np.uint32,
        all_touched=True,
    )
    return province_ids


def province_ids_to_rgb(province_ids: Any, provinces_gdf: Any) -> Any:
    import numpy as np

    height, width = province_ids.shape
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for _, row in provinces_gdf.iterrows():
        image[province_ids == int(row.code)] = np.array(row.color, dtype=np.uint8)
    return image


def save_provinces_bmp(image: Any, output_dir: Path) -> None:
    from PIL import Image

    path = output_dir / "provinces.bmp"
    pil_image = Image.fromarray(image, mode="RGB")
    pil_image.save(path)
    pil_image.close()
    print(f"Wrote {path}")


def save_provinces_csv(provinces_gdf: Any, output_dir: Path) -> None:
    path = output_dir / "provinces.csv"
    with path.open("w", newline="") as fd:
        writer = csv.writer(fd, delimiter=";")
        for _, row in provinces_gdf.iterrows():
            color = row.color
            writer.writerow([int(row.code), int(color[0]), int(color[1]), int(color[2])])
    print(f"Wrote {path}")


def compute_province_centers(provinces_gdf: Any, bounds: MapBounds) -> None:
    for _, row in provinces_gdf.iterrows():
        point = row.geometry.representative_point()
        col, row_pixel = bounds.project(float(point.x), float(point.y))
        provinces_gdf.at[row.name, "center_x"] = col
        provinces_gdf.at[row.name, "center_y"] = row_pixel


def save_province_metadata(provinces_gdf: Any, output_dir: Path) -> None:
    path = output_dir / "province_metadata.csv"
    with path.open("w", newline="") as fd:
        writer = csv.DictWriter(
            fd,
            delimiter=";",
            fieldnames=[
                "province_id",
                "name",
                "code",
                "prefecture",
                "red",
                "green",
                "blue",
                "center_x",
                "center_y",
                "area_km2",
            ],
        )
        writer.writeheader()
        for _, row in provinces_gdf.iterrows():
            color = row.color
            writer.writerow(
                {
                    "province_id": int(row.code),
                    "name": row.name,
                    "code": row.code,
                    "prefecture": row.prefecture,
                    "red": int(color[0]),
                    "green": int(color[1]),
                    "blue": int(color[2]),
                    "center_x": row.center_x,
                    "center_y": row.center_y,
                    "area_km2": round(float(row.area_km2 or 0), 2),
                }
            )
    print(f"Wrote {path}")


def save_definition_csv(provinces_gdf: Any, output_dir: Path) -> None:
    path = output_dir / "definition.csv"
    with path.open("w", newline="") as fd:
        writer = csv.DictWriter(
            fd,
            delimiter=";",
            fieldnames=["province_id", "name", "code", "prefecture", "color", "center_x", "center_y"],
        )
        writer.writeheader()
        for _, row in provinces_gdf.iterrows():
            color = row.color
            writer.writerow(
                {
                    "province_id": int(row.code),
                    "name": row.name,
                    "code": row.code,
                    "prefecture": row.prefecture,
                    "color": f"{color[0]},{color[1]},{color[2]}",
                    "center_x": row.center_x,
                    "center_y": row.center_y,
                }
            )
    print(f"Wrote {path}")


def compute_adjacencies(provinces_gdf: Any, min_border_length_m: float) -> list[tuple[int, int]]:
    rows = list(provinces_gdf.iterrows())
    adjacencies: list[tuple[int, int]] = []

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            left_name, left = rows[i]
            right_name, right = rows[j]
            intersection = left.geometry.boundary.intersection(right.geometry.boundary)
            if getattr(intersection, "length", 0.0) >= min_border_length_m:
                adjacencies.append((int(left.code), int(right.code)))

    return sorted(adjacencies)


def save_adjacencies_csv(adjacencies: Iterable[tuple[int, int]], output_dir: Path) -> None:
    path = output_dir / "adjacencies.csv"
    with path.open("w", newline="") as fd:
        writer = csv.writer(fd, delimiter=";")
        for left, right in adjacencies:
            writer.writerow([left, right])
    print(f"Wrote {path}")


def extract_osm_layers(args: argparse.Namespace, aoi_geometry: Any, output_dir: Path) -> dict[str, Any]:
    gpd = import_geopandas()
    cache_dir = args.osm_cache or (output_dir / "osm-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    layers: dict[str, Any] = {}
    for config in OSM_LAYER_CONFIGS:
        layer_path = cache_dir / f"{config['name']}.geojson"
        if layer_path.exists():
            print(f"Loading cached OSM layer {config['name']} from {layer_path}")
            layer = gpd.read_file(layer_path)
        else:
            layer = download_osm_layer(config, aoi_geometry, args.projection)
            if layer is not None and not layer.empty:
                try:
                    layer.to_file(layer_path, driver="GeoJSON")
                    print(f"Wrote cached OSM layer {layer_path}")
                except Exception as exc:  # pragma: no cover - depends on optional GeoJSON drivers.
                    print(f"Warning: could not cache {config['name']}: {exc}")
        layers[config["name"]] = clean_layer(layer, aoi_geometry, args.projection, config["geometry_types"])

    return layers


def download_osm_layer(config: dict[str, Any], aoi_geometry: Any, projection: str) -> Any | None:
    ox = import_osmnx()
    if ox is None:
        print(f"Warning: OSMnx is not installed; skipping OSM layer '{config['name']}'.")
        return None

    # Convert the dissolved AOI polygon (tight fit) to WGS-84.
    # Using the actual département union instead of the rectangular bbox
    # reduces the query area by ~30 % and avoids the Overpass sub-query warning.
    aoi_wgs84 = to_wgs84(aoi_geometry, projection)
    print(f"Downloading OSM layer '{config['name']}'…")
    try:
        return ox.features_from_polygon(aoi_wgs84, tags=config["tags"])
    except Exception as exc:  # pragma: no cover - network/API dependent.
        print(f"Warning: could not download OSM layer '{config['name']}': {exc}")
        return None


def clean_layer(layer: Any | None, aoi_geometry: Any, projection: str, geometry_types: set[str]) -> Any:
    gpd = import_geopandas()
    empty = gpd.GeoDataFrame(geometry=[], crs=projection)
    if layer is None or layer.empty:
        return empty

    layer = clean_gdf(layer)
    if layer.crs is None:
        layer = layer.set_crs("EPSG:4326")
    layer = layer.to_crs(projection)
    layer = layer[layer.geometry.geom_type.isin(geometry_types)].copy()
    if not layer.empty:
        aoi = gpd.GeoSeries([aoi_geometry], crs=projection)
        layer = layer[layer.geometry.intersects(aoi.union_all() if hasattr(aoi, "union_all") else aoi.unary_union)]
        layer = layer.clip(aoi)
        layer = clean_gdf(layer)
    return layer


def to_wgs84(geometry: Any, projection: str) -> Any:
    gpd = import_geopandas()
    return gpd.GeoSeries([geometry], crs=projection).to_crs("EPSG:4326").iloc[0]


def render_terrain(province_ids: Any, layers: dict[str, Any], bounds: MapBounds, palette: dict[str, Any]) -> Any:
    import numpy as np

    # Flat land colour — polygon terrain layers (forests, urban, water bodies)
    # have been removed for performance.  The province colour fill provides
    # enough visual distinction for a grand-strategy overview.
    image = np.full((bounds.height, bounds.width, 3), palette["land"], dtype=np.uint8)
    image = draw_province_borders(image, province_ids, palette)

    if "rivers" in layers and not layers["rivers"].empty:
        image = draw_line_layer(image, layers["rivers"], bounds, palette["river"], palette["river_alpha"], 2)
    if "roads" in layers and not layers["roads"].empty:
        image = draw_line_layer(image, layers["roads"], bounds, palette["road"], palette["road_alpha"], 4)
    if "railways" in layers and not layers["railways"].empty:
        image = draw_line_layer(image, layers["railways"], bounds, palette["rail"], palette["rail_alpha"], 2)
    if "cities" in layers and not layers["cities"].empty:
        image = draw_point_layer(image, layers["cities"], bounds, palette["city"], palette["city_alpha"], 4)

    return image


def blend_mask(image: Any, mask: Any, color: tuple[int, int, int], alpha: float) -> Any:
    """Alpha-composite a boolean *mask* of *color* onto *image*.

    Parameters
    ----------
    image:
        H×W×3 uint8 NumPy array (the base image, modified out-of-place).
    mask:
        H×W boolean (or uint8) array. True pixels receive the blend.
    color:
        RGB tuple for the overlay colour.
    alpha:
        Blend strength in [0, 1]. 0 = fully transparent, 1 = fully opaque.

    Returns
    -------
    H×W×3 uint8 NumPy array with the mask blended in.
    """
    import numpy as np

    mask_float = mask.astype(float)[:, :, None]          # (H, W, 1) for broadcasting
    color_array = np.array(color, dtype=float).reshape(1, 1, 3)
    # Linear interpolation between base image and overlay colour, only where mask is set.
    blended = image.astype(float) * (1.0 - alpha) + color_array * alpha
    result = np.where(mask_float > 0, blended, image.astype(float))
    return np.clip(result, 0, 255).astype(np.uint8)


def draw_province_borders(image: Any, province_ids: Any, palette: dict[str, Any]) -> Any:
    import numpy as np

    horizontal_rows, horizontal_cols = np.where(province_ids[:, 1:] != province_ids[:, :-1])
    vertical_rows, vertical_cols = np.where(province_ids[1:, :] != province_ids[:-1, :])

    border = np.zeros_like(province_ids, dtype=bool)
    border[horizontal_rows, horizontal_cols] = True
    border[horizontal_rows, horizontal_cols + 1] = True
    border[vertical_rows, vertical_cols] = True
    border[vertical_rows + 1, vertical_cols] = True

    alpha = palette["province_border_alpha"] / 255.0
    return blend_mask(image, border, palette["province_border"], alpha)


def iter_line_coordinates(geometry: Any) -> Iterable[tuple[float, float]]:
    geom_type = getattr(geometry, "geom_type", "")
    if geom_type == "LineString":
        yield from geometry.coords
    elif geom_type == "MultiLineString":
        for line in geometry.geoms:
            yield from line.coords


def draw_line_layer(image: Any, layer: Any, bounds: MapBounds, color: tuple[int, int, int], alpha: int, width: int) -> Any:
    from PIL import Image, ImageDraw
    import numpy as np

    pil_image = Image.fromarray(image, mode="RGB")
    draw = ImageDraw.Draw(pil_image, "RGBA")
    draw_color = (*color, alpha)

    for _, row in layer.iterrows():
        points = [bounds.project(x, y) for x, y in iter_line_coordinates(row.geometry)]
        if len(points) >= 2:
            draw.line(points, fill=draw_color, width=width, joint="curve")

    result = np.asarray(pil_image.convert("RGB"))
    pil_image.close()
    return result


def draw_point_layer(image: Any, layer: Any, bounds: MapBounds, color: tuple[int, int, int], alpha: int, radius: int) -> Any:
    from PIL import Image, ImageDraw

    pil_image = Image.fromarray(image, mode="RGB")
    draw = ImageDraw.Draw(pil_image, "RGBA")
    draw_color = (*color, alpha)

    for _, row in layer.iterrows():
        point = row.geometry.representative_point()
        x, y = bounds.project(float(point.x), float(point.y))
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=draw_color,
            outline=(40, 40, 40, 220),
            width=1,
        )

    result = np.asarray(pil_image.convert("RGB"))
    pil_image.close()
    return result


def save_terrain(image: Any, output_dir: Path) -> None:
    from PIL import Image

    path = output_dir / "terrain.png"
    pil_image = Image.fromarray(image, mode="RGB")
    pil_image.save(path)
    pil_image.close()
    print(f"Wrote {path}")


def render_preview(
    province_ids: Any,
    provinces_gdf: Any,
    layers: dict[str, Any],
    bounds: MapBounds,
    palette: dict[str, Any],
) -> Any:
    """Composite a full in-game preview image.

    The preview starts from the per-province colour fill (the gameplay bitmap),
    then blends every overlay layer on top in draw order:
      province borders → rivers → roads → railways → cities

    This gives an accurate representation of what the map looks like in-game
    with all overlays active, without requiring a game engine to combine them.

    Parameters
    ----------
    province_ids:
        H×W uint32 array of province codes produced by rasterize_province_ids.
    provinces_gdf:
        GeoDataFrame with a ``color`` column per province.
    layers:
        Dict of layer name → GeoDataFrame, as returned by extract_osm_layers.
    bounds:
        MapBounds describing the projected coordinate extent and pixel size.
    palette:
        Style palette dict (colours and alpha values).

    Returns
    -------
    H×W×3 uint8 NumPy array ready to be saved as an image.
    """
    # Start from the province colour fill — the canonical gameplay bitmap.
    image = province_ids_to_rgb(province_ids, provinces_gdf)

    # Province borders on top of the fill.
    image = draw_province_borders(image, province_ids, palette)

    # Overlay layers in ascending visual priority.
    if "rivers" in layers and not layers["rivers"].empty:
        image = draw_line_layer(image, layers["rivers"], bounds, palette["river"], palette["river_alpha"], 2)
    if "roads" in layers and not layers["roads"].empty:
        image = draw_line_layer(image, layers["roads"], bounds, palette["road"], palette["road_alpha"], 4)
    if "railways" in layers and not layers["railways"].empty:
        image = draw_line_layer(image, layers["railways"], bounds, palette["rail"], palette["rail_alpha"], 2)
    if "cities" in layers and not layers["cities"].empty:
        image = draw_point_layer(image, layers["cities"], bounds, palette["city"], palette["city_alpha"], 4)

    return image


def save_preview(image: Any, output_dir: Path) -> None:
    """Write the preview image to *output_dir*/preview.png."""
    path = output_dir / "preview.png"
    pil_image = Image.fromarray(image, mode="RGB")
    pil_image.save(path)
    pil_image.close()
    print(f"Wrote {path}")


def save_overlay(layer: Any, bounds: MapBounds, palette: dict[str, Any], config: dict[str, Any], output_dir: Path) -> None:
    overlay_name = config["overlay"]
    if overlay_name is None or layer is None or layer.empty:
        return

    canvas = np.zeros((bounds.height, bounds.width, 4), dtype=np.uint8)
    pil_image = Image.fromarray(canvas, mode="RGBA")
    draw = ImageDraw.Draw(pil_image, "RGBA")

    if config["line_width"] is not None:
        color_key = "road" if config["name"] == "roads" else "rail" if config["name"] == "railways" else "river"
        draw_color = (*palette[color_key], palette[f"{color_key}_alpha"])
        for _, row in layer.iterrows():
            points = [bounds.project(x, y) for x, y in iter_line_coordinates(row.geometry)]
            if len(points) >= 2:
                draw.line(points, fill=draw_color, width=config["line_width"], joint="curve")
    else:
        draw_color = (*palette["city"], palette["city_alpha"])
        for _, row in layer.iterrows():
            point = row.geometry.representative_point()
            x, y = bounds.project(float(point.x), float(point.y))
            draw.ellipse(
                [x - 4, y - 4, x + 4, y + 4],
                fill=draw_color,
                outline=(40, 40, 40, 220),
                width=1,
            )

    path = output_dir / "overlays" / overlay_name
    path.parent.mkdir(parents=True, exist_ok=True)
    pil_image.save(path)
    pil_image.close()
    print(f"Wrote {path}")


def save_layers_geojson(layers: dict[str, Any], output_dir: Path) -> None:
    geojson_dir = output_dir / "geojson"
    geojson_dir.mkdir(parents=True, exist_ok=True)
    for name, layer in layers.items():
        if layer is None or layer.empty:
            continue
        path = geojson_dir / f"{name}.geojson"
        try:
            layer.to_file(path, driver="GeoJSON")
            print(f"Wrote {path}")
        except Exception as exc:  # pragma: no cover - depends on optional GeoJSON drivers.
            print(f"Warning: could not write GeoJSON layer {path}: {exc}")


def save_metadata(
    args: argparse.Namespace,
    provinces_gdf: Any,
    bounds: MapBounds,
    adjacencies: list[tuple[int, int]],
    layers: dict[str, Any],
    elapsed_seconds: float,
) -> None:
    provinces = []
    for _, row in provinces_gdf.iterrows():
        color = row.color
        provinces.append(
            {
                "province_id": int(row.code),
                "name": row.name,
                "code": row.code,
                "prefecture": row.prefecture,
                "color": {"red": int(color[0]), "green": int(color[1]), "blue": int(color[2])},
                "center": {"x": int(row.center_x), "y": int(row.center_y)},
                "area_km2": round(float(row.area_km2 or 0), 2),
            }
        )

    metadata = {
        "name": "Historical Aquitaine administrative map",
        "description": "One province per historical Aquitaine département, enriched with optional OpenStreetMap layers.",
        "attribution": OSM_ATTRIBUTION,
        "projection": bounds.projection,
        "bounds": asdict(bounds),
        "width": bounds.width,
        "height": bounds.height,
        "style": args.style,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "provinces": provinces,
        "adjacencies": [{"from": left, "to": right} for left, right in adjacencies],
        "layers": {name: int(len(layer)) for name, layer in layers.items()},
    }

    path = args.output / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_aquitaine_map.py",
        description="Generate a historical Aquitaine administrative province map from OSM/geodata.",
        epilog=(
            "Example: python scripts/map-generator/generate_aquitaine_map.py "
            "--output maps/aquitaine --width 3000 --height 2400"
        ),
    )
    parser.add_argument("--output", type=Path, required=True, help="Folder where generated map data is placed.")
    parser.add_argument("--width", type=positive_int, default=3000, help="Width of the map in pixels. Defaults to 3000.")
    parser.add_argument("--height", type=positive_int, default=2400, help="Height of the map in pixels. Defaults to 2400.")
    parser.add_argument(
        "--boundaries",
        type=Path,
        help=(
            "Optional GeoJSON/GeoPackage containing French admin_level=6 département boundaries. "
            "If omitted, OSMnx is used to download boundaries from OpenStreetMap."
        ),
    )
    parser.add_argument(
        "--osm-cache",
        type=Path,
        help="Folder used to cache downloaded OSM layers. Defaults to <output>/osm-cache.",
    )
    parser.add_argument("--projection", default=DEFAULT_PROJECTION, help="Metric CRS used for rasterization. Defaults to EPSG:2154.")
    parser.add_argument(
        "--aoi-buffer-meters",
        type=non_negative_float,
        default=10_000,
        help="Buffer around Aquitaine used for the rendered map bounds. Defaults to 10000.",
    )
    parser.add_argument(
        "--min-border-length-m",
        type=non_negative_float,
        default=500,
        help="Minimum shared border length for province adjacency. Defaults to 500 meters.",
    )
    parser.add_argument("--style", choices=sorted(STYLE_PALETTES), default="modern-strategy", help="Visual style preset.")
    parser.add_argument("--no-osm-layers", action="store_true", help="Skip optional OSM city/road/rail/terrain layers.")
    parser.add_argument(
        "--fast-mode",
        action="store_true",
        help=(
            "Skip ALL OSM downloads (equivalent to --no-osm-layers --no-terrain --no-overlays). "
            "Produces only province boundaries, metadata, and adjacency data — zero network calls. "
            "Useful for iteration/testing or when you only need the province bitmap."
        ),
    )
    parser.add_argument("--no-terrain", action="store_true", help="Skip terrain.png rendering.")
    parser.add_argument("--no-overlays", action="store_true", help="Skip transparent road/rail/river/city overlay PNGs.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help=(
            "Render preview.png: province colours + borders + all overlay layers composited into "
            "a single image, showing exactly what the in-game map looks like with all overlays active."
        ),
    )
    return parser


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid non-negative float value")
    return parsed


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    start_time = time.time()
    args.output.mkdir(parents=True, exist_ok=True)

    print("Generate historical Aquitaine administrative map")
    print(f"Output folder: {args.output}")
    print(f"Map size: {args.width}x{args.height}")
    print(f"Projection: {args.projection}")
    print("OpenStreetMap data attribution: © OpenStreetMap contributors, ODbL")

    # --fast-mode is a shortcut for --no-osm-layers + rendering skips.
    if args.fast_mode:
        args.no_osm_layers = True
        args.no_terrain = True
        args.no_overlays = True
        print("Fast mode: skipping all OSM downloads and terrain rendering.")

    # Raise OSMnx's Overpass max query area so that the remaining lightweight
    # line/point layers (roads, rivers, cities) do not trigger the sub-query
    # warning.  50 GB covers Aquitaine (~68 000 km²) in a single request.
    ox = import_osmnx()
    if ox is not None:
        ox.settings.max_query_area_size = 50_000_000_000

    provinces_gdf, _raw_boundaries = load_departement_boundaries(args)
    bounds = build_bounds(provinces_gdf, args.width, args.height, args.projection, args.aoi_buffer_meters)
    compute_province_centers(provinces_gdf, bounds)

    province_ids = rasterize_province_ids(provinces_gdf, bounds)
    province_image = province_ids_to_rgb(province_ids, provinces_gdf)
    save_provinces_bmp(province_image, args.output)
    save_provinces_csv(provinces_gdf, args.output)
    save_province_metadata(provinces_gdf, args.output)
    save_definition_csv(provinces_gdf, args.output)

    adjacencies = compute_adjacencies(provinces_gdf, args.min_border_length_m)
    save_adjacencies_csv(adjacencies, args.output)

    aoi_geometry = provinces_gdf.union_all() if hasattr(provinces_gdf, "union_all") else provinces_gdf.geometry.unary_union
    aoi_geometry = aoi_geometry.buffer(args.aoi_buffer_meters)

    layers: dict[str, Any] = {}
    if args.no_osm_layers:
        print("Skipping optional OSM layers.")
    else:
        layers = extract_osm_layers(args, aoi_geometry, args.output)
        if not args.no_terrain:
            palette = STYLE_PALETTES[args.style]
            terrain_image = render_terrain(province_ids, layers, bounds, palette)
            save_terrain(terrain_image, args.output)
        if not args.no_overlays:
            palette = STYLE_PALETTES[args.style]
            for config in OSM_LAYER_CONFIGS:
                save_overlay(layers.get(config["name"]), bounds, palette, config, args.output)
        save_layers_geojson(layers, args.output)

    if args.preview:
        if args.no_osm_layers:
            # No overlay layers were downloaded; render province colours + borders only.
            print("Warning: --preview without OSM layers — rendering province fill and borders only.")
        palette = STYLE_PALETTES[args.style]
        preview_image = render_preview(province_ids, provinces_gdf, layers, bounds, palette)
        save_preview(preview_image, args.output)

    elapsed_seconds = time.time() - start_time
    save_metadata(args, provinces_gdf, bounds, adjacencies, layers, elapsed_seconds)
    print(f"Finished in {elapsed_seconds:.2f} seconds")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)