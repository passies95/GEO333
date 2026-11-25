"""
Campus3D — a small, standalone Folium campus map.

Run:
    python -m pip install -r requirements.txt
    python campus.py

The program reads data/buildings.geojson and writes output/campus_map.html.
No web framework, database server, or frontend build system is required.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import folium
from branca.element import MacroElement
from folium.plugins import (
    Fullscreen,
    LocateControl,
    MeasureControl,
    MiniMap,
    MousePosition,
    Search,
)

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "buildings.geojson"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "campus_map.html"

# Approximate centre of the University of Nairobi main campus.
DEFAULT_CENTER = (-1.2798, 36.8166)
DEFAULT_ZOOM = 16


def load_buildings(path: Path = DATA_FILE) -> dict:
    """Load campus building polygons from a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Keep the data folder beside campus.py."
        )

    with path.open(encoding="utf-8") as source:
        data = json.load(source)

    if data.get("type") != "FeatureCollection":
        raise ValueError("The buildings dataset must be a GeoJSON FeatureCollection.")

    return data


def building_style(feature: dict) -> dict:
    """Style polygons by their recorded building use."""
    usage = str(feature.get("properties", {}).get("usage", "")).lower()
    color = "#2563eb" if usage == "multipurpose" else "#d97706"
    return {
        "color": color,
        "weight": 1.4,
        "fillColor": color,
        "fillOpacity": 0.28,
    }


def popup_fields(feature: dict) -> dict:
    """Return a compact, HTML-safe popup for a building."""
    props = feature.get("properties", {})
    name = props.get("name") or "Unnamed building"
    usage = props.get("usage") or "Not recorded"
    description = props.get("descriptio") or "No description available."
    floors = props.get("no_ofFloor")
    height = props.get("height")
    building_id = feature.get("id", props.get("bldid", "N/A"))

    rows = [
        f"<h4 style='margin:0 0 8px'>{name}</h4>",
        f"<b>Building ID:</b> {building_id}",
        f"<br><b>Use:</b> {usage}",
        f"<br><b>Description:</b> {description}",
    ]
    if floors not in (None, ""):
        rows.append(f"<br><b>Floors:</b> {floors}")
    if height not in (None, ""):
        rows.append(f"<br><b>Height:</b> {height} m")
    return {"html": "".join(rows)}


def add_route_on_two_clicks(map_object: folium.Map) -> None:
    """Add an optional OSRM route tool: click the map twice (start, destination)."""
    route_control = MacroElement()
    route_control._template = __import__("jinja2").Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            var points = [];
            var routeControl = null;
            var help = L.control({position: 'bottomleft'});
            help.onAdd = function () {
                var div = L.DomUtil.create('div', 'route-help');
                div.style.cssText = 'background:white;padding:8px 10px;border-radius:4px;'
                    + 'box-shadow:0 1px 5px #999;font:12px/1.4 Arial;max-width:210px;';
                div.innerHTML = '<b>Simple routing</b><br>Click the map twice: origin, then destination.'
                    + '<br><button type="button" id="campus-clear-route" '
                    + 'style="margin-top:5px">Clear route</button>';
                L.DomEvent.disableClickPropagation(div);
                return div;
            };
            help.addTo(map);

            map.on('click', function (event) {
                if (points.length === 2) {
                    points.forEach(function (marker) { map.removeLayer(marker); });
                    points = [];
                    if (routeControl) {
                        map.removeControl(routeControl);
                        routeControl = null;
                    }
                }
                points.push(L.marker(event.latlng).addTo(map));
                if (points.length === 1) {
                    points[0].bindPopup('Route origin').openPopup();
                }
                if (points.length === 2) {
                    points[1].bindPopup('Route destination').openPopup();
                    if (routeControl) map.removeControl(routeControl);
                    routeControl = L.Routing.control({
                        waypoints: [points[0].getLatLng(), points[1].getLatLng()],
                        routeWhileDragging: false,
                        show: true,
                        addWaypoints: false,
                        fitSelectedRoutes: true,
                        lineOptions: {styles: [{color: '#2563eb', opacity: 0.85, weight: 6}]}
                    }).addTo(map);
                }
            });

            document.addEventListener('click', function (event) {
                if (event.target && event.target.id === 'campus-clear-route') {
                    points.forEach(function (marker) { map.removeLayer(marker); });
                    points = [];
                    if (routeControl) {
                        map.removeControl(routeControl);
                        routeControl = null;
                    }
                }
            });
        })();
        {% endmacro %}
        """
    )
    map_object.get_root().header.add_child(
        folium.Element(
            '<link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css">'
            '<script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>'
        )
    )
    map_object.add_child(route_control)


def build_map(buildings_data: dict) -> folium.Map:
    """Create the interactive campus map."""
    campus_map = folium.Map(
        location=DEFAULT_CENTER,
        zoom_start=DEFAULT_ZOOM,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    # Two selectable basemaps. Tile services require an internet connection.
    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
        control=True,
        show=True,
    ).add_to(campus_map)
    folium.TileLayer(
        tiles="CartoDB positron",
        name="Carto light",
        control=True,
        show=False,
    ).add_to(campus_map)

    buildings = folium.GeoJson(
        buildings_data,
        style_function=building_style,
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "#dc2626",
            "fillOpacity": 0.65,
        },
        popup=folium.GeoJsonPopup(
            fields=["name", "usage", "descriptio", "no_ofFloor", "height", "bldid"],
            aliases=[
                "Building",
                "Use",
                "Description",
                "Floors",
                "Height (m)",
                "Building ID",
            ],
            localize=True,
            labels=True,
            max_width=320,
        ),
        tooltip=folium.GeoJsonTooltip(
            fields=["name"],
            aliases=["Building:"],
            sticky=True,
        ),
        name="Buildings",
        show=True,
    ).add_to(campus_map)

    # Search by the building name.
    Search(
        layer=buildings,
        search_label="name",
        search_zoom=19,
        geom_type="Polygon",
        placeholder="Search building name...",
        collapsed=False,
    ).add_to(campus_map)

    # Useful GIS/map-reading tools.
    LocateControl(
        auto_start=False,
        strings={"title": "Show my location"},
        position="topleft",
    ).add_to(campus_map)
    MeasureControl(
        position="topleft",
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        primary_area_unit="sqmeters",
        secondary_area_unit="acres",
    ).add_to(campus_map)
    Fullscreen(position="topright", title="Full screen", title_cancel="Exit full screen").add_to(campus_map)
    MousePosition(
        position="bottomright",
        separator=" | ",
        prefix="Coordinates:",
        num_digits=6,
    ).add_to(campus_map)
    MiniMap(toggle_display=True, position="bottomright").add_to(campus_map)

    folium.LayerControl(collapsed=False, position="topright").add_to(campus_map)
    add_route_on_two_clicks(campus_map)

    # Fit the map to the dataset extent when bounds are available.
    bounds = folium.utilities.get_bounds(buildings_data)
    if bounds and bounds != [[0, 0], [0, 0]]:
        campus_map.fit_bounds(bounds, padding=(20, 20))

    # Small map information panel.
    info = """
    <div style="
        position: fixed; bottom: 28px; left: 12px; z-index: 9999;
        background: rgba(255,255,255,.94); padding: 8px 11px;
        border: 1px solid #bbb; border-radius: 4px;
        font: 12px/1.45 Arial; max-width: 230px;">
      <b>Campus3D — Folium edition</b><br>
      Search for a building, toggle map layers, measure distances,
      or click twice to request a route.
    </div>
    """
    campus_map.get_root().html.add_child(folium.Element(info))
    return campus_map


def main() -> None:
    """Build and save the standalone HTML map."""
    data = load_buildings()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    campus_map = build_map(data)
    campus_map.save(str(OUTPUT_FILE))
    print(f"Map created: {OUTPUT_FILE}")
    print(f"Buildings loaded: {len(data.get('features', []))}")
    print("Open output/campus_map.html in a web browser.")


if __name__ == "__main__":
    main()
