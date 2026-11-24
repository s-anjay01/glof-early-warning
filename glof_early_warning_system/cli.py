"""
GLOF Early Warning and Hazard Assessment Command-Line Interface.
Usage:
    python cli.py list
    python cli.py assess <lake_id>
    python cli.py simulate <lake_id> [--type avalanche|breach] [--vol 1500000]
    python cli.py export-report <lake_id> [--output filename.json]
"""

import sys
import os
import json
import argparse

# Ensure safe output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.hydrology import simulate_downstream_propagation
from core.risk_model import GLOFRiskEngine
from core.simulation import simulate_avalanche_trigger, simulate_moraine_breach
from core.satellite import analyze_lake_growth_timeseries


def load_lakes():
    path = os.path.join(os.path.dirname(__file__), "data", "glacial_lakes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_timeseries():
    path = os.path.join(os.path.dirname(__file__), "data", "time_series_samples.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_list():
    lakes = load_lakes()
    print("=" * 95)
    print(f"{'ID':<16} | {'Lake Name':<28} | {'Region':<22} | {'Vol (MCM)':<10} | {'Hazard'}")
    print("=" * 95)
    for lk in lakes:
        risk = GLOFRiskEngine.evaluate_lake_risk(lk)
        print(f"{lk['id']:<16} | {lk['name']:<28} | {lk['region']:<22} | {lk['lake_volume_mcm']:<10} | {risk['hazard_level']} ({risk['composite_score']}/100)")
    print("=" * 95)


def cmd_assess(lake_id: str):
    lakes = load_lakes()
    lake = next((l for l in lakes if l["id"].lower() == lake_id.lower()), None)
    if not lake:
        print(f"Error: Lake with ID '{lake_id}' not found.")
        return

    risk = GLOFRiskEngine.evaluate_lake_risk(lake)
    print("\n" + "=" * 70)
    print(f"GLACIAL LAKE HAZARD ASSESSMENT: {lake['name']} ({lake['id']})")
    print("=" * 70)
    print(f"Location: {lake['region']}, {lake['country']} ({lake['basin']})")
    print(f"Coordinates: {lake['lat']:.4f}°N, {lake['lon']:.4f}°E | Elevation: {lake['elevation_m']} m")
    print(f"Surface Area: {lake['lake_area_km2']} km² | Volume: {lake['lake_volume_mcm']} MCM | Max Depth: {lake['max_depth_m']} m")
    print(f"Dam Type: {lake['dam_type']} (Height: {lake['dam_height_m']}m, Width: {lake['dam_width_m']}m, Freeboard: {lake['freeboard_m']}m)")
    print("-" * 70)
    print(f"OVERALL RISK SCORE: {risk['composite_score']} / 100")
    print(f"HAZARD LEVEL:       {risk['hazard_level']}")
    print(f"OPERATIONAL CODE:   {risk['action_code']}")
    print("-" * 70)
    print("Multi-Criteria Vulnerability Factors (0 - 100):")
    for factor, score in risk["factors"].items():
        filled = int(score / 5)
        bar = "#" * filled + "-" * (20 - filled)
        print(f"  - {factor:<26}: [{bar}] {score:>5.1f}%")
    print("-" * 70)
    print(f"Downstream Exposure:")
    print(f"  Total Estimated Population at Direct Risk: {risk['downstream_exposure']['total_population']:,}")
    print(f"  Critical Assets Threatened: {', '.join(risk['downstream_exposure']['threatened_assets'])}")
    print("-" * 70)
    print("Recommended Mitigation & Early Warning Directives:")
    for i, rec in enumerate(risk["recommendations"], 1):
        print(f"  {i}. {rec}")
    print("=" * 70 + "\n")


def cmd_simulate(lake_id: str, trigger_type: str = "avalanche", vol_m3: float = 1_500_000.0):
    lakes = load_lakes()
    lake = next((l for l in lakes if l["id"].lower() == lake_id.lower()), None)
    if not lake:
        print(f"Error: Lake with ID '{lake_id}' not found.")
        return

    if trigger_type == "avalanche":
        res = simulate_avalanche_trigger(lake, avalanche_volume_m3=vol_m3)
    else:
        res = simulate_moraine_breach(lake, breach_depth_fraction=0.60)

    print("\n" + "=" * 75)
    print(f"HYDRODYNAMIC SIMULATION RESULT: {lake['name']}")
    print(f"Trigger Scenario: {res['trigger_type']}")
    print("=" * 75)
    if trigger_type == "avalanche":
        print(f"Avalanche Volume Input:   {vol_m3:,.0f} m³")
        print(f"Initial Impulse Wave:     {res['initial_wave_height_m']} m")
        print(f"Wave Height at Dam Crest: {res['wave_at_dam_crest_m']} m (Dam Freeboard: {res['freeboard_m']} m)")
        print(f"Moraine Overtopping:      {'YES - BREACH TRIGGERED' if res['breach_occurred'] else 'NO OVERTOPPING'}")
    print(f"Peak Outburst Discharge:  {res['peak_discharge_m3s']:,} m³/s")
    print(f"Drained Volume:           {res['water_released_mcm']} MCM ({res['lake_volume_drained_pct']}% of lake)")
    print("-" * 75)
    print("DOWNSTREAM FLOOD PROPAGATION & EARLY WARNING TIMELINE:")
    print(f"{'Location':<24} | {'Dist (km)':<10} | {'Arrival (min)':<14} | {'Depth (m)':<10} | {'Alert Status'}")
    print("-" * 75)
    for item in res["downstream_impact"]:
        print(f"{item['name']:<24} | {item['distance_km']:<10.1f} | {item['wave_arrival_min']:<14.1f} | {item['est_flood_depth_m']:<10.2f} | {item['warning_status']}")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="GLOF Early Warning and Hazard Assessment Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")

    subparsers.add_parser("list", help="List all monitored glacial lakes and hazard states")

    assess_p = subparsers.add_parser("assess", help="Compute comprehensive risk assessment for a lake")
    assess_p.add_argument("lake_id", help="Glacial lake ID (e.g. GL-IND-SKM-001)")

    sim_p = subparsers.add_parser("simulate", help="Run hydrodynamic outburst flood simulation")
    sim_p.add_argument("lake_id", help="Glacial lake ID")
    sim_p.add_argument("--type", choices=["avalanche", "breach"], default="avalanche", help="Trigger mechanism")
    sim_p.add_argument("--vol", type=float, default=1500000.0, help="Avalanche displacement volume in m³")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list()
    elif args.command == "assess":
        cmd_assess(args.lake_id)
    elif args.command == "simulate":
        cmd_simulate(args.lake_id, args.type, args.vol)
    else:
        cmd_list()


if __name__ == "__main__":
    main()
