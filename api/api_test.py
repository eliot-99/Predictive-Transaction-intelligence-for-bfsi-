# ========================================================
# TEST SCRIPT FOR MODULE 3 FASTAPI API
# Starts server + Runs 3 test cases + Shows results
# ========================================================

import requests
import json
import threading
import time
from datetime import datetime

# Import your API app (adjust path if needed)
from main import app  # Assuming main.py is in the same folder

# Global flag to check if server is running
server_running = False

# Function to start the server in background
def start_server():
    global server_running
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    server_running = True

# Start server in thread
print("Starting API server in background...")
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Wait for server to start (up to 10 seconds)
print("Waiting for server to start...")
for i in range(10):
    try:
        requests.get("http://127.0.0.1:8000/")
        print("Server is ready!")
        server_running = True
        break
    except requests.exceptions.ConnectionError:
        time.sleep(1)
        print(f"Waiting... ({i+1}/10)")

if not server_running:
    print("Server failed to start. Check main.py and dependencies.")
    exit(1)

# API URL
url = "http://127.0.0.1:8000/detect"

# Test Case 1: HIGH-RISK (Should trigger alert)
print("\n" + "="*60)
print("TEST CASE 1: HIGH-RISK TRANSACTION (Expected: Alert Triggered)")
print("="*60)
high_risk_data = {
    "User_ID": 99999,
    "Transaction_Amount": 75000000,  # High amount
    "Transaction_Location": "Russia",  # Foreign
    "Merchant_ID": 1234,
    "Device_ID": 999999,  # New device
    "Card_Type": "UzCard",
    "Transaction_Currency": "UZS",
    "Transaction_Status": "Successful",
    "Previous_Transaction_Count": 1,
    "Distance_Between_Transactions_km": 5000,
    "Time_Since_Last_Transaction_min": 2,
    "Authentication_Method": "Password",
    "Transaction_Velocity": 15,  # High velocity
    "Transaction_Category": "Transfer",
    "Transaction_Hour": 2,  # Night
    "Transaction_Day": 28,
    "Transaction_Month": 10,
    "Transaction_Weekday": 1,
    "Log_Transaction_Amount": 18.2,
    "Velocity_Distance_Interact": 75000,
    "Amount_Velocity_Interact": 1125000000,
    "Time_Distance_Interact": 10000,
    "Hour_sin": 0.0,
    "Hour_cos": 1.0,
    "Weekday_sin": 0.0,
    "Weekday_cos": 1.0
}

try:
    response = requests.post(url, json=high_risk_data)
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS: API responded correctly")
        print("Raw Response:")
        print(json.dumps(result, indent=2))
        print(f"\nSummary: Alert Triggered = {result['alert_triggered']}, Reasons = {len(result['alert_reasons'])}")
    else:
        print(f"ERROR: Status Code {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"ERROR: {e}")

# Test Case 2: SAFE TRANSACTION (Should not trigger alert)
print("\n" + "="*60)
print("TEST CASE 2: SAFE TRANSACTION (Expected: No Alert)")
print("="*60)
safe_data = {
    "User_ID": 10001,
    "Transaction_Amount": 500000,  # Low amount
    "Transaction_Location": "Tashkent",  # Local
    "Merchant_ID": 5678,
    "Device_ID": 10001,  # Known device
    "Card_Type": "UzCard",
    "Transaction_Currency": "UZS",
    "Transaction_Status": "Successful",
    "Previous_Transaction_Count": 50,
    "Distance_Between_Transactions_km": 10,
    "Time_Since_Last_Transaction_min": 60,
    "Authentication_Method": "2FA",
    "Transaction_Velocity": 1,  # Low velocity
    "Transaction_Category": "Purchase",
    "Transaction_Hour": 14,  # Daytime
    "Transaction_Day": 28,
    "Transaction_Month": 10,
    "Transaction_Weekday": 1,
    "Log_Transaction_Amount": 13.1,
    "Velocity_Distance_Interact": 10,
    "Amount_Velocity_Interact": 500000,
    "Time_Distance_Interact": 600,
    "Hour_sin": 0.0,
    "Hour_cos": -1.0,
    "Weekday_sin": 0.0,
    "Weekday_cos": 1.0
}

try:
    response = requests.post(url, json=safe_data)
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS: API responded correctly")
        print("Raw Response:")
        print(json.dumps(result, indent=2))
        print(f"\nSummary: Alert Triggered = {result['alert_triggered']}, Reasons = {len(result['alert_reasons'])}")
    else:
        print(f"ERROR: Status Code {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"ERROR: {e}")

# Test Case 3: EDGE CASE (Partial alert, e.g., high velocity but low amount)
print("\n" + "="*60)
print("TEST CASE 3: EDGE CASE (Expected: Partial Alert)")
print("="*60)
edge_data = {
    "User_ID": 10002,
    "Transaction_Amount": 40000000,  # Medium amount
    "Transaction_Location": "Tashkent",  # Local
    "Merchant_ID": 5678,
    "Device_ID": 10002,  # Known
    "Card_Type": "UzCard",
    "Transaction_Currency": "UZS",
    "Transaction_Status": "Successful",
    "Previous_Transaction_Count": 20,
    "Distance_Between_Transactions_km": 100,
    "Time_Since_Last_Transaction_min": 30,
    "Authentication_Method": "2FA",
    "Transaction_Velocity": 12,  # High velocity
    "Transaction_Category": "Purchase",
    "Transaction_Hour": 14,  # Daytime
    "Transaction_Day": 28,
    "Transaction_Month": 10,
    "Transaction_Weekday": 1,
    "Log_Transaction_Amount": 17.5,
    "Velocity_Distance_Interact": 1200,
    "Amount_Velocity_Interact": 480000000,
    "Time_Distance_Interact": 3000,
    "Hour_sin": 0.0,
    "Hour_cos": -1.0,
    "Weekday_sin": 0.0,
    "Weekday_cos": 1.0
}

try:
    response = requests.post(url, json=edge_data)
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS: API responded correctly")
        print("Raw Response:")
        print(json.dumps(result, indent=2))
        print(f"\nSummary: Alert Triggered = {result['alert_triggered']}, Reasons = {len(result['alert_reasons'])}")
    else:
        print(f"ERROR: Status Code {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*60)
print("ALL TESTS COMPLETE!")
print("API is LIVE at: http://127.0.0.1:8000/docs")
print("Swagger UI for manual testing: http://127.0.0.1:8000/docs")