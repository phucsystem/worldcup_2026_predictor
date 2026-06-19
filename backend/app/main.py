from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.briefs import router as briefs_router
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
