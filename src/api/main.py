import os, json, gzip, io
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
import redis.asyncio as redis
import pandas as pd

from src.astro.swisseph_api import build_ephemeris
from src.astro.features import make_features
from src.ml.model import AstroLSTM
from src.chart.visualize import generate_chart

structlog.configure(processors=[structlog.stdlib.add_log_level, structlog.processors.JSONRenderer()])
logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Vedic-Astro ML Trading API", version="1.0.0", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))

@app.get("/health/live")
async def liveness(): return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    try:
        await r.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.get("/api/now")
@limiter.limit("60/minute")
async def now(ayanamsa: str = Query("Lahiri")):
    key = f"now:{ayanamsa}"
    cached = await r.get(key)
    if cached: return json.loads(cached)
    eph = build_ephemeris(pd.Timestamp.utcnow(), ayanamsa)
    out = {"status": "success", "timestamp": datetime.utcnow().isoformat(), "ayanamsa": ayanamsa, "planets": eph.to_dict(orient="records")[0]}
    await r.setex(key, 60, json.dumps(out))
    logger.info("now", ayanamsa=ayanamsa)
    return out

@app.get("/api/ephemeris/{start}/{end}/{step}")
@limiter.limit("10/minute")
async def ephemeris_range(start: str, end: str, step: str, ayanamsa: str = Query("Lahiri"), format: str = Query("json"), compress: bool = Query(False)):
    try:
        start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date")
    freq = {"daily": "D", "hourly": "H"}.get(step, f"{step}H")
    dates = pd.date_range(start_dt, end_dt, freq=freq, inclusive="both")
    df = build_ephemeris(dates, ayanamsa)
    if format == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        if compress:
            gz = io.BytesIO()
            with gzip.GzipFile(fileobj=gz, mode="wb") as f: f.write(buf.getvalue().encode())
            gz.seek(0)
            return StreamingResponse(gz, media_type="application/gzip", headers={"Content-Disposition": f"attachment; filename=ephemeris_{start}_{end}.csv.gz"})
        return StreamingResponse(io.BytesIO(buf.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=ephemeris_{start}_{end}.csv"})
    return {"status": "success", "start": start, "end": end, "step": step, "rows": len(df), "data": df.to_dict(orient="records")}

class PredictIn(BaseModel):
    ticker: str
    horizon: int = 1
    date: Optional[str] = None
    ayanamsa: str = "Lahiri"

@app.post("/api/predict")
@limiter.limit("100/minute")
async def predict(payload: PredictIn, background: BackgroundTasks):
    ticker, horizon, date_str, ayanamsa = payload.ticker, payload.horizon, payload.date, payload.ayanamsa
    if ticker not in {"Gold", "Silver", "Bitcoin", "EURUSD"}: raise HTTPException(status_code=400, detail="Unsupported ticker")
    dt = pd.to_datetime(date_str or pd.Timestamp.utcnow())
    df_feat = make_features(ticker, dt, ayanamsa)
    model = AstroLSTM.load_from_registry(ticker, horizon)
    pred = model.predict(df_feat)
    background.add_task(logger.info, "prediction", ticker=ticker, horizon=horizon, signal=pred["signal"], confidence=pred["confidence"])
    return pred

@app.get("/")
async def root(): return {"message": "Vedic-Astro ML Trading API", "docs": "/docs"}
