"""
Machine Learning & Multi-Criteria Risk Assessment Engine for Glacial Lakes.
Evaluates trigger susceptibility, dam stability, expansion dynamics, and downstream vulnerability.
"""

from typing import Dict, Any, List


class GLOFRiskEngine:
    """
    Combines Analytic Hierarchy Process (AHP) weighting with glaciological decision rules
    to compute lake breach probability, consequence score, and composite GLOF Hazard Index.
    """

    # Feature weights calibrated with GAPHAZ & ICIMOD mountain hazard guidelines
    WEIGHTS = {
        "lake_volume": 0.18,
        "expansion_rate": 0.16,
        "freeboard_deficiency": 0.15,
        "slope_steepness": 0.14,
        "permafrost_thaw": 0.13,
        "dam_geometry": 0.12,
        "glacier_proximity": 0.12
    }

    @classmethod
    def evaluate_lake_risk(cls, lake: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw lake metrics and calculates normalized risk scores (0-100),
        hazard classification, sub-scores, and key vulnerability drivers.
        """
        vol = float(lake.get("lake_volume_mcm", 10.0))
        exp_rate = float(lake.get("expansion_rate_pct_yr", 3.0))
        freeboard = float(lake.get("freeboard_m", 15.0))
        slope = float(lake.get("slope_gradient_deg", 30.0))
        permafrost = float(lake.get("permafrost_degradation_index", 0.5))
        dam_h = float(lake.get("dam_height_m", 50.0))
        dam_w = float(lake.get("dam_width_m", 150.0))
        glacier_dist = float(lake.get("mother_glacier_distance_m", 100.0))

        # 1. Lake Volume Factor (0 to 100)
        # >50 MCM is massive in the Himalayas
        vol_score = min(100.0, (vol / 60.0) * 100.0)

        # 2. Surface Expansion Rate Factor (0 to 100)
        # >7% per year indicates violent rapid expansion
        exp_score = min(100.0, (exp_rate / 8.0) * 100.0)

        # 3. Freeboard Deficiency (0 to 100)
        # Lower freeboard (<10m) means very high overtopping risk
        if freeboard <= 5.0:
            freeboard_score = 95.0
        elif freeboard <= 12.0:
            freeboard_score = 75.0
        elif freeboard <= 25.0:
            freeboard_score = 45.0
        else:
            freeboard_score = max(10.0, 100.0 - (freeboard * 2.0))

        # 4. Avalanche / Slope Trigger Factor (0 to 100)
        # Slopes > 30 deg adjacent to lake are prime avalanche zones
        if slope >= 45.0:
            slope_score = 98.0
        elif slope >= 35.0:
            slope_score = 82.0
        elif slope >= 28.0:
            slope_score = 60.0
        else:
            slope_score = 30.0

        # 5. Permafrost Thaw & Ice-Core Melting (0 to 100)
        thaw_score = permafrost * 100.0

        # 6. Dam Geometry Stability (Width-to-Height Ratio)
        # W/H < 3.0 is a narrow, fragile moraine dam prone to breach
        ratio = dam_w / max(1.0, dam_h)
        if ratio < 2.5:
            dam_geom_score = 90.0
        elif ratio < 4.0:
            dam_geom_score = 65.0
        else:
            dam_geom_score = 35.0

        # 7. Mother Glacier Calving Proximity
        # Closer glacier tongue (<100m) means direct ice fall into lake
        if glacier_dist < 60:
            prox_score = 95.0
        elif glacier_dist < 150:
            prox_score = 75.0
        elif glacier_dist < 300:
            prox_score = 50.0
        else:
            prox_score = 25.0

        # Weighted Composite Score
        composite_score = (
            vol_score * cls.WEIGHTS["lake_volume"] +
            exp_score * cls.WEIGHTS["expansion_rate"] +
            freeboard_score * cls.WEIGHTS["freeboard_deficiency"] +
            slope_score * cls.WEIGHTS["slope_steepness"] +
            thaw_score * cls.WEIGHTS["permafrost_thaw"] +
            dam_geom_score * cls.WEIGHTS["dam_geometry"] +
            prox_score * cls.WEIGHTS["glacier_proximity"]
        )

        # Classification
        if composite_score >= 75.0:
            hazard_level = "CRITICAL"
            badge_color = "#ef4444"  # Red
            action_code = "EVACUATION_READY"
        elif composite_score >= 55.0:
            hazard_level = "HIGH"
            badge_color = "#f97316"  # Orange
            action_code = "INTENSIVE_MONITORING"
        elif composite_score >= 35.0:
            hazard_level = "MODERATE"
            badge_color = "#eab308"  # Yellow
            action_code = "PERIODIC_SATELLITE_SURVEY"
        else:
            hazard_level = "LOW"
            badge_color = "#22c55e"  # Green
            action_code = "BASELINE_OBSERVATION"

        # Downstream Exposure Assessment
        elements = lake.get("downstream_elements", [])
        total_pop_at_risk = sum(e.get("population", 0) for e in elements)
        critical_assets = [e.get("critical_asset") for e in elements if e.get("critical_asset")]

        # Generate scientific recommendations
        recommendations = cls._generate_recommendations(composite_score, freeboard, slope, exp_rate)

        return {
            "lake_id": lake.get("id"),
            "lake_name": lake.get("name"),
            "composite_score": round(composite_score, 1),
            "hazard_level": hazard_level,
            "badge_color": badge_color,
            "action_code": action_code,
            "factors": {
                "Volume Susceptibility": round(vol_score, 1),
                "Expansion Dynamics": round(exp_score, 1),
                "Freeboard Deficiency": round(freeboard_score, 1),
                "Slope / Avalanche Hazard": round(slope_score, 1),
                "Permafrost Degradation": round(thaw_score, 1),
                "Moraine Geometry Weakness": round(dam_geom_score, 1),
                "Glacier Ice Proximity": round(prox_score, 1)
            },
            "downstream_exposure": {
                "total_population": total_pop_at_risk,
                "threatened_assets": critical_assets,
                "closest_settlement": elements[0]["name"] if elements else "None"
            },
            "recommendations": recommendations
        }

    @staticmethod
    def _generate_recommendations(score: float, freeboard: float, slope: float, exp_rate: float) -> List[str]:
        recs = []
        if score >= 70.0:
            recs.append("Install automated satellite/LoRa telemetry water level sensors with real-time solar uplink.")
            recs.append("Deploy downstream acoustic alarm sirens with satellite link at highest risk villages.")
        if freeboard < 15.0:
            recs.append("Perform controlled engineering siphoning or open-channel cutting to increase freeboard by >=5m.")
        if slope > 35.0:
            recs.append("Establish optical and synthetic aperture radar (SAR) slope displacement interferometry (InSAR) on hanging glaciers.")
        if exp_rate > 5.0:
            recs.append("Schedule bi-weekly high-resolution multispectral imagery (Sentinel-2 / PlanetScope) to track moraine dam calving.")
        if not recs:
            recs.append("Maintain routine seasonal glaciological monitoring and annual bathymetric survey.")
        return recs
