from fastapi import FastAPI, HTTPException
from pathlib import Path
import logging

from backend.logger import setup_logging
from backend.recommender_fp import FPGrowthRecommender
from backend.recommender_dl import DLRecommender 

setup_logging()
logger = logging.getLogger("hybrid_api")

app = FastAPI(title="Hybrid Recommender API")

# FP-Growth Recommender
fp_rec = FPGrowthRecommender("data/rules.csv")

# DL Recommender
MODEL_PATH = Path("models/ncf_model.pt")
dl_rec = DLRecommender(MODEL_PATH) 

# API Endpoints
@app.get("/recommend/by-item")
def rec_by_item(item: str, top_k: int = 5):
    res = fp_rec.recommend(item, top_k)
    if not res:
        raise HTTPException(404, "Không tìm thấy gợi ý.")
    return {"item": item, "suggestions": res}

# API Endpoint for DL Recommender
@app.get("/recommend/by-user")
def rec_by_user(user_id: int, top_k: int = 5):
    res = dl_rec.recommend(user_id, top_k)
    if not res:
        raise HTTPException(404, "Không tìm thấy gợi ý.")
    return {"user_id": user_id, "suggestions": res}
