import logging
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import onnxruntime as ort
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

MODEL_PATH = Path(os.getenv("MODEL_PATH", "fraud_model.onnx"))
PREPROC_PATH = Path(os.getenv("PREPROC_PATH", "preprocessor.pkl"))
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fraud-api")

FRAUD_SIGNATURES = {
    "high_amount": 50_000_000,
    "foreign_country": ["Russia", "Turkey", "USA", "China", "UAE"],
    "velocity_threshold": 10,
    "night_transaction": (0, 5),
}

USER_BEHAVIOR: Dict[int, Dict[str, Any]] = {}
BEHAVIOR_LOCK = Lock()


class Transaction(BaseModel):
    User_ID: int
    Transaction_Amount: float
    Transaction_Location: str
    Merchant_ID: int
    Device_ID: int
    Card_Type: str
    Transaction_Currency: str
    Transaction_Status: str
    Previous_Transaction_Count: int
    Distance_Between_Transactions_km: float
    Time_Since_Last_Transaction_min: int
    Authentication_Method: str
    Transaction_Velocity: int
    Transaction_Category: str
    Transaction_Hour: int
    Transaction_Day: int
    Transaction_Month: int
    Transaction_Weekday: int
    Log_Transaction_Amount: float
    Velocity_Distance_Interact: float
    Amount_Velocity_Interact: float
    Time_Distance_Interact: float
    Hour_sin: float
    Hour_cos: float
    Weekday_sin: float
    Weekday_cos: float


class AlertResponse(BaseModel):
    Transaction_ID: int
    User_ID: int
    Fraud_Probability: float
    Final_Risk_Score: float
    isFraud_pred: int
    alert_triggered: bool
    alert_reasons: List[str]
    timestamp: str


def load_artifacts() -> Tuple[Any, ort.InferenceSession, str]:
    if not PREPROC_PATH.exists():
        raise FileNotFoundError(f"Preprocessor not found at {PREPROC_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    preprocessor = joblib.load(PREPROC_PATH)
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    return preprocessor, session, input_name


def evaluate_risk(
    payload: Dict[str, Any],
    preprocessor: Any,
    session: ort.InferenceSession,
    input_name: str,
) -> Dict[str, Any]:
    frame = pd.DataFrame([payload])
    tx_id = int(datetime.utcnow().timestamp() * 1000)
    frame.insert(0, "Transaction_ID", tx_id)
    try:
        features = preprocessor.transform(frame.drop(columns=["Transaction_ID", "User_ID"], errors="ignore"))
        if hasattr(features, "toarray"):
            features = features.toarray()
        features = np.asarray(features, dtype=np.float32)
        result = session.run(None, {input_name: features})
        probability = float(result[0][0][0])
    except Exception as exc:
        logger.exception("Model inference failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Model inference failed") from exc

    prediction = int(probability > 0.5)
    reasons: List[str] = []
    boost = 0.0

    if payload["Transaction_Amount"] > FRAUD_SIGNATURES["high_amount"]:
        reasons.append("High Amount")
        boost += 0.35
    if FRAUD_SIGNATURES["night_transaction"][0] <= payload["Transaction_Hour"] < FRAUD_SIGNATURES["night_transaction"][1]:
        reasons.append("Night")
        boost += 0.25
    if payload["Transaction_Velocity"] > FRAUD_SIGNATURES["velocity_threshold"]:
        reasons.append("High Velocity")
        boost += 0.20
    if payload["Transaction_Location"] in FRAUD_SIGNATURES["foreign_country"]:
        reasons.append("Foreign")
        boost += 0.25

    now = datetime.utcnow()
    user_id = payload["User_ID"]

    with BEHAVIOR_LOCK:
        profile = USER_BEHAVIOR.setdefault(user_id, {"devices": set(), "tx_count_1h": 0, "last_hour": now.hour})
        if payload["Device_ID"] not in profile["devices"]:
            reasons.append("New Device")
            boost += 0.30
            profile["devices"].add(payload["Device_ID"])
        if now.hour != profile["last_hour"]:
            profile["tx_count_1h"] = 0
            profile["last_hour"] = now.hour
        profile["tx_count_1h"] += 1
        if profile["tx_count_1h"] > 8:
            reasons.append("Burst")
            boost += 0.20

    final_score = min(probability + boost, 1.0)
    alert = final_score > 0.7 or prediction == 1

    return {
        "Transaction_ID": tx_id,
        "User_ID": user_id,
        "Fraud_Probability": round(probability, 4),
        "Final_Risk_Score": round(final_score, 4),
        "isFraud_pred": prediction,
        "alert_triggered": alert,
        "alert_reasons": reasons,
        "timestamp": now.isoformat(),
    }


app = FastAPI(
    title="Real-Time Fraud Detection Engine",
    description="ONNX and rules based fraud detection service",
    version="3.0",
)


def get_artifacts() -> Tuple[Any, ort.InferenceSession, str]:
    artifacts = getattr(app.state, "artifacts", None)
    if artifacts is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model artifacts not loaded")
    return artifacts


@app.on_event("startup")
async def on_startup() -> None:
    try:
        app.state.artifacts = load_artifacts()
        logger.info("Model artifacts loaded")
    except Exception as exc:
        logger.exception("Failed to initialize model artifacts")
        raise RuntimeError("Failed to initialize model artifacts") from exc


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if hasattr(app.state, "artifacts"):
        delattr(app.state, "artifacts")


@app.post("/detect", response_model=AlertResponse)
def detect(transaction: Transaction) -> Dict[str, Any]:
    preprocessor, session, input_name = get_artifacts()
    return evaluate_risk(transaction.model_dump(), preprocessor, session, input_name)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "LIVE",
        "model": MODEL_PATH.name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    _ = get_artifacts()
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
