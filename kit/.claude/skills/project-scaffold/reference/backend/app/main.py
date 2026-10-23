from fastapi import FastAPI

from app.controllers import health_controller, user_controller
from app.controllers.error_handlers import register_error_handlers
from app.core.config import get_settings

ROUTERS = [health_controller.router, user_controller.router]


def create_app(wire_dependencies: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, docs_url="/api/docs", openapi_url="/api/openapi.json",
                  redoc_url=None)
    for router in ROUTERS:
        app.include_router(router)
    register_error_handlers(app)
    if wire_dependencies:
        from app.container import PROVIDERS

        app.dependency_overrides.update(PROVIDERS)
    return app


app = create_app()
