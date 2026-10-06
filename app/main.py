from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from .measurements import extract_measurements
from .models import FeatureMeasurement, FileRecord, FileSummary
from .parsers import load_geodata


app = FastAPI(
    title="Geospatial File Measurement API",
    version="1.0.0",
    description="Upload a KML or zipped Shapefile and receive feature measurements.",
)
FILES: dict[str, FileRecord] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/files/", response_model=FileSummary, status_code=201)
async def upload_file(file: UploadFile = File(...)) -> FileSummary:
    filename = file.filename or "upload"
    try:
        frame = load_geodata(filename, await file.read())
        features = extract_measurements(frame)
    except (ValueError, OSError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    file_id = uuid4().hex
    summary = FileSummary(
        id=file_id,
        filename=filename,
        feature_count=len(features),
        crs=frame.crs.to_string() if frame.crs is not None else None,
        status="COMPLETED",
    )
    FILES[file_id] = FileRecord(summary=summary, features=features)
    return summary


@app.get("/api/files/{file_id}/", response_model=FileSummary)
def file_information(file_id: str) -> FileSummary:
    record = FILES.get(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")
    return record.summary


@app.get("/api/files/{file_id}/measurements/", response_model=list[FeatureMeasurement])
def file_measurements(file_id: str) -> list[FeatureMeasurement]:
    record = FILES.get(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")
    return [feature.model_dump() for feature in record.features]