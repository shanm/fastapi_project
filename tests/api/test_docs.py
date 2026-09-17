from fastapi.testclient import TestClient


def test_docs_is_available_and_csp_allows_swagger_assets():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text
    csp = response.headers["Content-Security-Policy"]
    assert "https://cdn.jsdelivr.net" in csp
    assert "script-src" in csp
    assert "style-src" in csp


def test_application_endpoints_keep_strict_csp():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
