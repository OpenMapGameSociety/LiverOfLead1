# generate_aquitaine_map.py

Generates a data-driven map of historical Aquitaine from OpenStreetMap, where each province corresponds to one of the five historical départements. Designed for use in a grand strategy game.

## Output

A full run produces the following files inside `--output`:

| File | Description |
|---|---|
| `provinces.bmp` | Gameplay province bitmap — one flat colour per province, no anti-aliasing |
| `provinces.csv` | `province_id;R;G;B` colour table |
| `province_metadata.csv` | Per-province id, name, code, prefecture, colour, pixel centre, area |
| `definition.csv` | Compact province definition table for the game engine |
| `adjacencies.csv` | Pairs of adjacent province ids sharing a border ≥ `--min-border-length-m` |
| `metadata.json` | Full run summary: bounds, projection, provinces, adjacencies, layer counts |
| `terrain.png` | Styled terrain image with province borders and all OSM layers composited |
| `preview.png` | In-game preview: province colours + borders + all overlays (requires `--preview`) |
| `overlays/roads.png` | Transparent RGBA overlay — motorways, trunk and primary roads |
| `overlays/railways.png` | Transparent RGBA overlay — main rail lines |
| `overlays/rivers.png` | Transparent RGBA overlay — major rivers |
| `overlays/cities.png` | Transparent RGBA overlay — city and town markers |
| `geojson/*.geojson` | Raw GeoJSON for each downloaded OSM layer |
| `osm-cache/*.geojson` | Cached OSM downloads (reused on subsequent runs) |

## Requirements

Python 3.10 or later.

```bash
pip install geopandas rasterio shapely pyogrio osmnx pillow numpy
```

`osmnx` is optional — it is only needed when `--boundaries` is not provided and OSM data has not been cached yet. All other dependencies are required.

## Usage

```
python generate_aquitaine_map.py --output <folder> [options]
```

### Quickstart

```bash
# Full run: download boundaries + OSM layers, render terrain, overlays, and a preview
python generate_aquitaine_map.py \
  --output maps/aquitaine \
  --preview

# Iterate fast on province shapes only — zero network calls
python generate_aquitaine_map.py \
  --output maps/aquitaine \
  --fast-mode

# Re-use cached OSM data on subsequent runs (no re-download)
python generate_aquitaine_map.py \
  --output maps/aquitaine \
  --osm-cache maps/aquitaine/osm-cache \
  --preview
```

### All options

| Flag | Default | Description |
|---|---|---|
| `--output PATH` | *(required)* | Folder where all output files are written. Created if it does not exist. |
| `--width INT` | `3000` | Map width in pixels. |
| `--height INT` | `2400` | Map height in pixels. |
| `--boundaries PATH` | *(none)* | GeoJSON or GeoPackage file containing French `admin_level=6` département boundaries. When omitted the script downloads them from OSM via `osmnx`. |
| `--osm-cache PATH` | `<output>/osm-cache` | Folder for cached OSM layer downloads. Subsequent runs load from cache instead of querying Overpass again. |
| `--projection CRS` | `EPSG:2154` | Metric CRS used for rasterization (Lambert-93). Change only if targeting a different region. |
| `--aoi-buffer-meters FLOAT` | `10000` | Buffer in metres added around the province union for the map extent and OSM query area. |
| `--min-border-length-m FLOAT` | `500` | Minimum shared boundary length (metres) for two provinces to be considered adjacent. |
| `--style NAME` | `modern-strategy` | Colour palette preset. Currently only `modern-strategy` is available. |
| `--no-osm-layers` | off | Skip all OSM downloads (boundaries are still fetched if `--boundaries` is not provided). Produces the province bitmap, metadata, and adjacency files only. |
| `--fast-mode` | off | Shortcut for `--no-osm-layers --no-terrain --no-overlays`. Zero network calls after boundaries are available. Useful for rapid iteration. |
| `--no-terrain` | off | Skip `terrain.png` rendering. |
| `--no-overlays` | off | Skip the transparent overlay PNGs in `overlays/`. |
| `--preview` | off | Render `preview.png` — province colours + borders + all overlay layers composited into a single image, showing exactly what the map looks like in-game with all overlays active. |

## Boundary data

By default the script fetches each département boundary individually by name from the OpenStreetMap Nominatim / Overpass API using `osmnx.geocode_to_gdf`. This is fast (5 small requests) and does not trigger the large-area sub-query warning.

If you prefer to work offline or need reproducible data, download the boundaries once and pass them via `--boundaries`:

```bash
# Download French départements from data.gouv.fr (GeoJSON, ~3 MB)
curl -L "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson" \
  -o departements.geojson

python generate_aquitaine_map.py \
  --output maps/aquitaine \
  --boundaries departements.geojson \
  --preview
```

The file must contain polygons with at least one of: a `ref` / `ref:INSEE` / `INSEE` column with the 2-digit département code, or a `name` column matching the French département name.

## OSM layer caching

OSM layers (roads, railways, rivers, cities) are cached as GeoJSON files in `<output>/osm-cache/` after the first download. Subsequent runs load from cache automatically — no Overpass queries are made. To force a re-download, delete the cache folder or individual `.geojson` files inside it.

Use `--osm-cache` to share a single cache across multiple output folders:

```bash
python generate_aquitaine_map.py \
  --output maps/aquitaine-3000x2400 \
  --osm-cache shared/osm-cache \
  --width 3000 --height 2400

python generate_aquitaine_map.py \
  --output maps/aquitaine-1920x1080 \
  --osm-cache shared/osm-cache \
  --width 1920 --height 1080
```

## Provinces

The five historical Aquitaine départements and their default colours:

| Code | Département | Prefecture | Colour (R, G, B) |
|---|---|---|---|
| 24 | Dordogne | Périgueux | (142, 183, 120) |
| 33 | Gironde | Bordeaux | (173, 132, 91) |
| 40 | Landes | Mont-de-Marsan | (91, 145, 112) |
| 47 | Lot-et-Garonne | Agen | (156, 118, 154) |
| 64 | Pyrénées-Atlantiques | Pau | (132, 151, 190) |

Colours can be changed by editing `HISTORICAL_AQUITAINE_DEPARTEMENTS` at the top of the script.

## Attribution

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, ODbL.
