from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.briefs import router as briefs_router
from app.api.fixtures import router as fixtures_router, stars_router
from app.api.standings import router as standings_router

app = FastAPI(title="World Cup Intelligence API")

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
# Local/dev-only trigger endpoints (unauthenticated) — see app/api/admin.py warning.
app.include_router(admin_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
