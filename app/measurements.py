from __future__ import annotations

import geopandas as gpd

from .models import FeatureMeasurement
from .parsers import json_geometry


SUPPORTED = {"Polygon", "MultiPolygon", "LineString", "MultiLineString", "Point", "MultiPoint"}


def _metric_frame(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if frame.crs is None:
        return frame
    if frame.crs.is_geographic:
        estimated = frame.estimate_utm_crs()
        if estimated is not None:
            return frame.to_crs(estimated)
    return frame


def extract_measurements(frame: gpd.GeoDataFrame) -> list[FeatureMeasurement]:
    projected = _metric_frame(frame)
    source_crs = frame.crs.to_string() if frame.crs is not None else None
    results = []
    for index, (_, row) in enumerate(frame.iterrows()):
        geometry = row.geometry
        geometry_type = geometry.geom_type if geometry is not None else "Unknown"
        values = None
        error = None
        if geometry is None or geometry.is_empty:
            error = "Geometry is empty"
        elif geometry_type in {"Polygon", "MultiPolygon"}:
            values = {"area_square_meters": float(projected.iloc[index].geometry.area)}
        elif geometry_type in {"LineString", "MultiLineString"}:
            values = {"length_meters": float(projected.iloc[index].geometry.length)}
        elif geometry_type not in SUPPORTED:
            error = f"Measurement is not supported for geometry type {geometry_type}"
        properties = {key: value for key, value in row.items() if key != "geometry"}
        results.append(FeatureMeasurement(
            feature_id=index,
            geometry_type=geometry_type,
            geometry=json_geometry(geometry),
            crs=source_crs,
            properties=properties,
            measurement=values,
            measurement_error=error,
        ))
    return results