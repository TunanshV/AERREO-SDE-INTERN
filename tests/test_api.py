from io import BytesIO

from fastapi.testclient import TestClient

from app.main import FILES, app


client = TestClient(app)


def setup_function() -> None:
    FILES.clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_kml_returns_point_and_polygon_measurements() -> None:
    kml = b'''<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>
    <Placemark><name>park</name><Polygon><outerBoundaryIs><LinearRing><coordinates>77,28 77.001,28 77.001,28.001 77,28.001 77,28</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
    <Placemark><name>marker</name><Point><coordinates>77,28</coordinates></Point></Placemark>
    </Document></kml>'''
    response = client.post("/api/files/", files={"file": ("survey.kml", BytesIO(kml), "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 201
    payload = response.json()
    assert payload["feature_count"] == 2
    measurements = client.get(f"/api/files/{payload['id']}/measurements/").json()
    assert measurements[0]["measurement"]["area_square_meters"] > 0
    assert measurements[1]["measurement"] is None
    assert measurements[1]["properties"]["name"] == "marker"


def test_rejects_unsupported_extension() -> None:
    response = client.post("/api/files/", files={"file": ("survey.geojson", b"{}", "application/json")})
    assert response.status_code == 400