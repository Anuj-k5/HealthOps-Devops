from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app


def main():
    client = app.test_client()
    headers = {"Authorization": "Bearer healthops-api-token"}

    health = client.get("/healthz")
    ready = client.get("/readyz")
    metrics = client.get("/metrics")
    unauthorized = client.get("/api/v1/patients")
    created = client.post(
        "/api/v1/patients",
        json={"name": "CI Smoke Patient", "age": 28, "disease": "validation"},
        headers=headers,
    )
    created_id = created.get_json()["id"]
    deleted = client.delete(f"/api/v1/patients/{created_id}", headers=headers)

    assert health.status_code == 200, health.status_code
    assert ready.status_code == 200, ready.status_code
    assert metrics.status_code == 200, metrics.status_code
    assert b"healthops_patients_total" in metrics.data, metrics.data[:500]
    assert unauthorized.status_code == 401, unauthorized.status_code
    assert created.status_code == 201, created.status_code
    assert deleted.status_code == 204, deleted.status_code

    print("Backend smoke tests passed.")


if __name__ == "__main__":
    main()
