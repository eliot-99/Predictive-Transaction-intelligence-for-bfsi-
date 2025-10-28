# api/main.py
import pandas as pd
import joblib
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import os

app = FastAPI(title="Real-Time Fraud Engine", version="3.0")

# Load
preprocessor = joblib.load("preprocessor.pkl")
session = ort.InferenceSession("fraud_model.onnx")
input_name = session.get_inputs()[0].name

FRAUD_SIGNATURES = {
    "high_amount": 50_000_000,
    "foreign_country": ["Russia", "Turkey", "USA", "China", "UAE"],
    "velocity_threshold": 10,
    "night_transaction": (0, 5),
}

USER_BEHAVIOR = {}

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
    alert_reasons: list
    timestamp: str

def evaluate_risk(tx: dict) -> dict:
    df = pd.DataFrame([tx])
    tx_id = int(datetime.now().timestamp() * 1000)
    df.insert(0, 'Transaction_ID', tx_id)

    X = preprocessor.transform(df.drop(columns=['Transaction_ID', 'User_ID'], errors='ignore'))
    if hasattr(X, 'toarray'): X = X.toarray().astype(np.float32)
    prob = float(session.run(None, {input_name: X})[0][0][0])
    model_pred = int(prob > 0.5)

    reasons = []
    boost = 0.0

    if tx['Transaction_Amount'] > FRAUD_SIGNATURES['high_amount']: reasons.append("High Amount"); boost += 0.35
    if FRAUD_SIGNATURES['night_transaction'][0] <= tx['Transaction_Hour'] < FRAUD_SIGNATURES['night_transaction'][1]: reasons.append("Night"); boost += 0.25
    if tx['Transaction_Velocity'] > FRAUD_SIGNATURES['velocity_threshold']: reasons.append("High Velocity"); boost += 0.20
    if tx['Transaction_Location'] in FRAUD_SIGNATURES['foreign_country']: reasons.append("Foreign"); boost += 0.25

    user_id = tx['User_ID']
    if user_id not in USER_BEHAVIOR:
        USER_BEHAVIOR[user_id] = {'devices': set(), 'tx_count_1h': 0, 'last_hour': datetime.now().hour}
    b = USER_BEHAVIOR[user_id]

    if tx['Device_ID'] not in b['devices']: reasons.append("New Device"); boost += 0.30; b['devices'].add(tx['Device_ID'])
    h = datetime.now().hour
    if h != b['last_hour']: b['tx_count_1h'] = 0; b['last_hour'] = h
    b['tx_count_1h'] += 1
    if b['tx_count_1h'] > 8: reasons.append("Burst"); boost += 0.20

    final_risk = min(prob + boost, 1.0)
    alert = final_risk > 0.7 or model_pred == 1

    return {
        "Transaction_ID": tx_id,
        "User_ID": user_id,
        "Fraud_Probability": round(prob, 4),
        "Final_Risk_Score": round(final_risk, 4),
        "isFraud_pred": model_pred,
        "alert_triggered": alert,
        "alert_reasons": reasons,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/detect", response_model=AlertResponse)
def detect(transaction: Transaction):
    return evaluate_risk(transaction.model_dump())

@app.get("/")
def home():
    return {"status": "real time risk detection engine LIVE", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))