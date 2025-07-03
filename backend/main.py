from __future__ import annotations

import time
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException

from backend.logger import setup_logging
from backend.recommender_fp import FPGrowthRecommender
from backend.recommender_dl import DLRecommender


setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Hybrid Recommender API", version="1.0.0")

try:
    fp_rec = FPGrowthRecommender(Path("/app/data/rules.csv"))
    logger.info("Loaded FP‑Growth rules")
except Exception as e:
    logger.exception("Failed to load FP‑Growth rules: %s", e)
    raise

try:
    dl_rec = DLRecommender(Path("/app/models/ncf_model.pt"))
    logger.info("Loaded NCF model")
except Exception as e:
    logger.exception("Failed to load DL model: %s", e)
    raise

@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = f"{request.method} {request.url.path}"
    t0 = time.perf_counter()

    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = (time.perf_counter() - t0) * 1_000  # ms
        status = response.status_code if response else 500
        logger.info("%s | %d | %.2f ms", idem, status, duration)

@app.get("/recommend/by-item")
def rec_by_item(item: str, top_k: int = 5):
    logger.info("by‑item request item=%s top_k=%d", item, top_k)
    recs = fp_rec.recommend(item, top_k)
    if not recs:
        raise HTTPException(404, detail="No rule‑based suggestions.")
    return {"item": item, "suggestions": recs}

@app.get("/recommend/by-user")
def rec_by_user(user_id: int, top_k: int = 5):
    logger.info("by‑user request user_id=%s top_k=%d", user_id, top_k)
    recs = dl_rec.recommend(user_id, top_k)
    if not recs:
        raise HTTPException(404, detail="No DL suggestions.")
    return {"user_id": user_id, "suggestions": recs}
