import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import health, translate

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)


def create_app() -> FastAPI:
    """Application factory."""

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Attach a per-request ID for traceability; echoed as X-Request-ID."""
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/")
    async def root() -> FileResponse:
        """Serve the translator web UI."""

        return FileResponse("app/static/index.html")

    app.include_router(health.router)
    app.include_router(translate.router)

    return app


app = create_app()
