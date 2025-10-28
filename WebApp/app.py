# WebApp/app.py
from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)
API_URL = "http://localhost:8000/detect"  # Change to Render URL after deploy

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    try:
        resp = requests.post(API_URL, json=data)
        return jsonify(resp.json())
    except:
        return jsonify({"error": "API unreachable"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)