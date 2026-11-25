# Campus3D — Folium edition

A standalone, teaching-oriented rewrite of the Campus3D project. The original
application used Django, GeoDjango/PostGIS, django-leaflet, djgeojson, a
database, and several separately managed Leaflet plugins. This edition removes
the web framework and database and uses **Python + Folium** to generate one
interactive HTML map.

## What is included

- 306 building polygons converted from the original `UON_Buildings.shp`
  shapefile to `data/buildings.geojson`.
- Building styling by the source `usage` attribute.
- Building popups and hover labels.
- Search by building name.
- Switchable OpenStreetMap and CARTO light basemaps.
- Layer control, current-location control, fullscreen, scale, coordinate
  display, minimap and distance/area measurement.
- Optional route calculation by clicking an origin and destination on the map.
  This uses the public OSRM routing service through Leaflet Routing Machine.

## Requirements

- Python 3.9 or newer
- Internet connection to load online map tiles and the optional routing service

## Installation

Create and activate a virtual environment (recommended):

### Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python campus.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python campus.py
```

Then open `output/campus_map.html` in a modern browser. No server is required.

## Data and coordinate reference system

The supplied building shapefile is in geographic WGS 84 (longitude/latitude).
Its 306 polygon features are converted to GeoJSON, which is read directly by
Folium. The original fields are retained, including:

- `bldid`: building identifier
- `name`: building name
- `usage`: building use/category
- `descriptio`: description
- `no_ofFloor`: number of floors
- `height`: height
- `depth`: depth
- `entrace`: entrance attribute, where populated
- `photo`: photo attribute, where populated

The original ZIP contains no populated SQLite tables and does not include
separate school or department datasets. Therefore, the Folium edition maps
the building layer only; it does not invent or fabricate school/department
features. The original GeoTIFF basemap is not included in this minimal
runtime because displaying it requires additional raster-processing/browser
components and it is not needed for the core vector-map lesson.

## Using the map

1. Type a building name into the search box and choose a result.
2. Click a building polygon to inspect its attributes.
3. Use the layer control to change the basemap or show/hide buildings.
4. Use the location button to request the browser's current location.
5. Use the ruler icon to measure distances and areas.
6. For a route, click the map once for the origin and again for the
   destination. The route service requires internet access. Click **Clear
   route** to remove the route and start again.

## Classroom exercises (Level 300)

1. **Inspect the data:** open `data/buildings.geojson` and identify the
   geometry type and the attributes of a selected feature.
2. **Change symbology:** edit `building_style()` in `campus.py` to use a
   different colour for each building use.
3. **Change the popup:** add `depth` or `photo` to the building popup.
4. **Add a point layer:** create a small GeoJSON file of campus facilities
   and add it as another `folium.GeoJson` layer.
5. **Create a choropleth:** join a CSV table to geographic features using a
   common building ID and visualize a numeric attribute.
6. **Change the map extent:** modify `DEFAULT_CENTER` and `DEFAULT_ZOOM`.
7. **Discuss limitations:** compare straight-line distance with a routed
   distance and discuss the implications of using a public routing service.

## Project structure

```text
campus-folium/
├── campus.py
├── requirements.txt
├── README.md
├── data/
│   └── buildings.geojson
└── output/
    └── .gitkeep
```

## Notes

- Folium creates the HTML/JavaScript map; students write Python, not a
  separate frontend application.
- Basemap tiles, geolocation and routing need a network connection. Browser
  geolocation also requires permission and a secure context (usually HTTPS or
  localhost).
- The routing feature uses the public OSRM demo backend; it is suitable for
  classroom demonstration, not production service guarantees.
- Building boundaries and attributes are reproduced from the supplied source
  data. Their accuracy has not been independently surveyed or validated.
