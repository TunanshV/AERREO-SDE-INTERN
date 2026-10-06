from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import geopandas as gpd
from shapely.geometry import shape


ALLOWED_EXTENSIONS = {".kml", ".zip"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _coordinates(value: str) -> list[tuple[float, float]]:
    result = []
    for pair in value.strip().split():
        values = pair.split(",")
        result.append((float(values[0]), float(values[1])))
    return result


def _parse_kml(path: Path) -> gpd.GeoDataFrame:
    root = ElementTree.parse(path).getroot()
    rows: list[dict[str, Any]] = []
    for placemark in root.iter():
        if _local_name(placemark.tag) != "Placemark":
            continue
        properties: dict[str, Any] = {}
        geometry = None
        for child in placemark.iter():
            name = _local_name(child.tag)
            text = (child.text or "").strip()
            if name == "name" and text:
                properties["name"] = text
            elif name == "SimpleData" and child.attrib.get("name"):
                properties[child.attrib["name"]] = text
            elif name == "Data" and child.attrib.get("name"):
                value = next((item.text for item in child if _local_name(item.tag) == "value"), "")
                properties[child.attrib["name"]] = value or ""
            elif name == "Point" and text == "":
                coordinate_node = next((item for item in child if _local_name(item.tag) == "coordinates"), None)
                if coordinate_node is not None:
                    coordinates = _coordinates(coordinate_node.text or "")
                    geometry = {"type": "Point", "coordinates": coordinates[0]}
            elif name in {"LineString", "Polygon"} and text == "":
                coordinate_node = next((item for item in child.iter() if _local_name(item.tag) == "coordinates"), None)
                if coordinate_node is None:
                    continue
                coordinates = _coordinates(coordinate_node.text or "")
                if name == "LineString":
                    geometry = {"type": name, "coordinates": coordinates}
                else:
                    geometry = {"type": name, "coordinates": [coordinates]}
        if geometry is not None:
            rows.append({**properties, "geometry": shape(geometry)})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def load_geodata(filename: str, content: bytes) -> gpd.GeoDataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .kml files and .zip Shapefile archives are supported")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / Path(filename).name
        source.write_bytes(content)
        if suffix == ".kml":
            return _parse_kml(source)
        with zipfile.ZipFile(source) as archive:
            members = [member for member in archive.namelist() if not member.endswith("/")]
            if not any(Path(member).suffix.lower() == ".shp" for member in members):
                raise ValueError("The ZIP archive does not contain a Shapefile (.shp)")
            extraction_root = (root / "shapefile").resolve()
            for member in members:
                target = (extraction_root / member).resolve()
                if os.path.commonpath((str(extraction_root), str(target))) != str(extraction_root):
                    raise ValueError("The ZIP archive contains an unsafe path")
            archive.extractall(extraction_root)
            shp_path = next((path for path in extraction_root.rglob("*.shp")), None)
            if shp_path is None:
                raise ValueError("The ZIP archive does not contain a readable Shapefile")
            return gpd.read_file(shp_path)


def json_geometry(geometry: Any) -> dict[str, Any]:
    return json.loads(json.dumps(geometry.__geo_interface__))