# Geospatial File Measurement API

FastAPI service that accepts a KML file or a ZIP archive containing a Shapefile, extracts feature data, and calculates metric measurements.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive OpenAPI documentation.

## API

### Upload

`POST /api/files/` with multipart field `file`. Accepted files are `.kml` and `.zip` archives containing `.shp`, `.shx`, `.dbf`, and optionally `.prj` files.

The response includes an ID, original filename, feature count, source CRS, and `COMPLETED` status.

### File information

`GET /api/files/{id}/` returns the upload summary.

### Measurements

`GET /api/files/{id}/measurements/` returns each feature's ID, geometry type, GeoJSON geometry, CRS, attributes, and measurement. Polygon areas are returned in square meters and line lengths in meters. Points have no measurement. Unsupported or empty geometries are represented with `measurement_error` instead of failing the entire upload.

## Architecture

`app/parsers.py` validates and reads KML or zipped Shapefile input. `app/measurements.py` projects geographic data to an estimated local UTM CRS before calculating area or length, avoiding degree-based measurements. `app/main.py` exposes the API and stores processed records in memory for this assignment.

For production, the in-memory repository should be replaced with persistent metadata storage and object storage, and large uploads should move to a background job queue.

## Tests

```powershell
pytest
```
