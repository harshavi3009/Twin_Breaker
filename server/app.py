import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")

app = FastAPI(title="Twin-Breaker (SYNTHETIC)")
app.mount("/vendor", StaticFiles(directory=os.path.join(WEB_DIR, "vendor")), name="vendor")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "mode": "live", "synthetic": True}


@app.get("/api/episodes")
def episodes() -> list[dict]:
    return [
        {"episode_id": "P1A-s0007", "pair": "P1", "role": "A"},
        {"episode_id": "P1B-s0007", "pair": "P1", "role": "B"},
    ]


@app.get("/api/episodes/{episode_id}")
def episode(episode_id: str, lam: float = 1.0) -> dict:
    # STUB: belief and decision output arrive with the P8 runner and P9 decide step
    return {"episode_id": episode_id, "lam": lam, "minutes": [], "synthetic": True, "note": "STUB"}


@app.post("/api/inject")
def inject() -> dict:
    # STUB: red-team injection arrives in P12
    return {"ok": True, "injected": 0, "trace": {}}
