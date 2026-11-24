"""
Flask Web Application for GLOF Early Warning and Risk Assessment System.
"""

import os
import sys
import json
from flask import Flask, render_template, jsonify, request

# Add parent directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from core.hydrology import simulate_downstream_propagation
from core.risk_model import GLOFRiskEngine
from core.simulation import simulate_avalanche_trigger, simulate_moraine_breach
from core.satellite import analyze_lake_growth_timeseries

app = Flask(__name__)


def get_data_file(filename: str):
    path = os.path.join(BASE_DIR, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/lakes", methods=["GET"])
def api_get_lakes():
    lakes = get_data_file("glacial_lakes.json")
    results = []
    for lake in lakes:
        risk = GLOFRiskEngine.evaluate_lake_risk(lake)
        item = dict(lake)
        item["risk_assessment"] = risk
        results.append(item)
    return jsonify(results)


@app.route("/api/lakes/<lake_id>", methods=["GET"])
def api_get_lake(lake_id: str):
    lakes = get_data_file("glacial_lakes.json")
    lake = next((l for l in lakes if l["id"].lower() == lake_id.lower()), None)
    if not lake:
        return jsonify({"error": f"Lake '{lake_id}' not found"}), 404

    risk = GLOFRiskEngine.evaluate_lake_risk(lake)
    lake_data = dict(lake)
    lake_data["risk_assessment"] = risk
    return jsonify(lake_data)


@app.route("/api/timeseries/<lake_id>", methods=["GET"])
def api_get_timeseries(lake_id: str):
    timeseries_data = get_data_file("time_series_samples.json")
    entry = timeseries_data.get(lake_id.upper())
    if not entry:
        return jsonify({"found": False, "message": "No specific multi-year satellite time series for this lake."})

    growth_analysis = analyze_lake_growth_timeseries(entry)
    return jsonify({
        "found": True,
        "raw_data": entry,
        "analysis": growth_analysis
    })


@app.route("/api/historical", methods=["GET"])
def api_get_historical():
    historical = get_data_file("historical_events.json")
    return jsonify(historical)


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json() or {}
    lake_id = data.get("lake_id", "GL-IND-SKM-001")
    trigger = data.get("trigger_type", "avalanche")

    lakes = get_data_file("glacial_lakes.json")
    lake = next((l for l in lakes if l["id"].lower() == lake_id.lower()), None)
    if not lake:
        return jsonify({"error": f"Lake '{lake_id}' not found"}), 404

    if trigger == "avalanche":
        vol = float(data.get("avalanche_volume_m3", 2_000_000.0))
        angle = float(data.get("impact_angle_deg", 45.0))
        result = simulate_avalanche_trigger(lake, avalanche_volume_m3=vol, impact_angle_deg=angle)
    else:
        width = float(data.get("breach_width_m", 60.0))
        depth_fraction = float(data.get("breach_depth_fraction", 0.60))
        result = simulate_moraine_breach(lake, breach_width_m=width, breach_depth_fraction=depth_fraction)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
