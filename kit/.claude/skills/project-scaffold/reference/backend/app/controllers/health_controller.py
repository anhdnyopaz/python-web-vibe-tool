from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.usecases.system.interfaces import ICheckHealthUseCase

router = APIRouter(prefix="/api", tags=["system"])


def get_check_health() -> ICheckHealthUseCase:
    """Placeholder — container.py gắn implementation thật."""
    raise NotImplementedError


class HealthResponse(BaseModel):
    status: str
    database: str
    cache: str


def _label(ok: bool) -> str:
    return "ok" if ok else "down"


@router.get("/health", response_model=HealthResponse)
def check_health(response: Response,
                 usecase: ICheckHealthUseCase = Depends(get_check_health)) -> HealthResponse:
    result = usecase.execute()
    if not result.healthy:
        response.status_code = 503
    return HealthResponse(status=_label(result.healthy), database=_label(result.database),
                          cache=_label(result.cache))
