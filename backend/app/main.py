import logging
import time

from fastapi import FastAPI, Request

from app.api.v1.routers import memory, research, sources
from app.core.config import get_settings
from app.db.session import Base, engine
from app.logging.config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("app.startup", extra={"environment": settings.environment})


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "http.request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


app.include_router(research.router, prefix=settings.api_v1_prefix)
app.include_router(sources.router, prefix=settings.api_v1_prefix)
app.include_router(memory.router, prefix=settings.api_v1_prefix)
