from typing import Any

from pydantic import BaseModel, Field


class FeatureMeasurement(BaseModel):
    feature_id: int
    geometry_type: str
    geometry: dict[str, Any]
    crs: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    measurement: dict[str, float] | None = None
    measurement_error: str | None = None


class FileSummary(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str | None = None
    status: str


class FileRecord(BaseModel):
    summary: FileSummary
    features: list[FeatureMeasurement]