from fastapi.testclient import TestClient

from app.controllers import health_controller
from app.main import create_app
from app.usecases.system.interfaces import HealthOutput, ICheckHealthUseCase


class FakeCheckHealth(ICheckHealthUseCase):
    def __init__(self, output: HealthOutput) -> None:
        self.output = output

    def execute(self) -> HealthOutput:
        return self.output


def _client(output: HealthOutput) -> TestClient:
    app = create_app(wire_dependencies=False)
    app.dependency_overrides[health_controller.get_check_health] = lambda: FakeCheckHealth(output)
    return TestClient(app)


def test_health_ok() -> None:
    response = _client(HealthOutput(database=True, cache=True)).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "cache": "ok"}


def test_health_returns_503_when_dependency_down() -> None:
    response = _client(HealthOutput(database=False, cache=True)).get("/api/health")

    assert response.status_code == 503
    assert response.json()["database"] == "down"
