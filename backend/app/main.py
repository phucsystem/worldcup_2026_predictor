import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.briefs import router as briefs_router
from app.api.fixtures import router as fixtures_router, stars_router
from app.api.logs import router as logs_router
from app.api.standings import router as standings_router
from app.api.tournament import router as tournament_router
from app.logging_config import configure_logging, stop_logging
from app.observability import configure_tracing

configure_logging()
configure_tracing()
log = logging.getLogger("app.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # uvicorn runs this on graceful shutdown (incl. the SIGTERM from `docker
    # stop`), where atexit would not fire — flush buffered log rows here.
    stop_logging()


app = FastAPI(title="World Cup Intelligence API", lifespan=lifespan)


@app.exception_handler(Exception)
async def _log_unhandled(request: Request, exc: Exception) -> JSONResponse:
    """Persist unhandled request errors (with traceback) before returning 500.
    FastAPI handles HTTPException separately, so this only sees real bugs."""
    log.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(briefs_router)
app.include_router(standings_router)
app.include_router(fixtures_router)
app.include_router(stars_router)
app.include_router(tournament_router)
app.include_router(logs_router)
# Local/dev-only trigger endpoints (unauthenticated) — see app/api/admin.py warning.
app.include_router(admin_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
