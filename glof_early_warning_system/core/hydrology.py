"""
Hydrological & Dam-Break Engine for GLOF (Glacial Lake Outburst Flood) Modeling.
Implements empirical and physical peak discharge models (Costa, Froehlich, Huggel),
hydrograph generation, flood wave propagation, downstream attenuation, and travel time estimation.
"""

import math
from typing import Dict, List, Any


def calculate_costa_peak_discharge(volume_m3: float, dam_height_m: float) -> float:
    """
    Costa (1985) empirical formula for peak discharge:
    Q_max = 0.013 * (V_w)^0.598 * (H_d)^0.548
    """
    if volume_m3 <= 0 or dam_height_m <= 0:
        return 0.0
    return 0.013 * (volume_m3 ** 0.598) * (dam_height_m ** 0.548)


def calculate_froehlich_peak_discharge(volume_m3: float, breach_water_depth_m: float) -> float:
    """
    Froehlich (1995) empirical formula for peak breach discharge:
    Q_max = 0.607 * (V_w)^0.295 * (H_w)^1.24
    """
    if volume_m3 <= 0 or breach_water_depth_m <= 0:
        return 0.0
    return 0.607 * (volume_m3 ** 0.295) * (breach_water_depth_m ** 1.24)


def calculate_huggel_peak_discharge(volume_m3: float, dam_height_m: float) -> float:
    """
    Huggel et al. (2002) glacial lake empirical relation:
    Q_max = 0.0018 * (V_w)^0.60 * (H_d)^0.70
    Calibrated for steep Himalayan / Alpine glaciated valleys.
    """
    if volume_m3 <= 0 or dam_height_m <= 0:
        return 0.0
    return 0.0018 * (volume_m3 ** 0.60) * (dam_height_m ** 0.70)


def generate_outburst_hydrograph(
    q_peak_m3s: float,
    total_volume_m3: float,
    time_step_min: float = 2.0
) -> Dict[str, Any]:
    """
    Synthesizes a triangular/exponential dam-break outburst hydrograph.
    Peak time t_p is derived conservation of mass:
    Total Volume V = 0.5 * Q_peak * t_base => t_base = 2 * V / Q_peak.
    t_peak ~ 0.25 to 0.35 * t_base.
    """
    if q_peak_m3s <= 0 or total_volume_m3 <= 0:
        return {"time_minutes": [], "discharge_m3s": [], "peak_discharge": 0, "duration_hours": 0}

    # Time base in seconds, converted to minutes
    t_base_sec = (2.0 * total_volume_m3) / q_peak_m3s
    t_base_min = t_base_sec / 60.0

    # Cap unrealistic extremes for hydrograph plotting (between 45 mins and 600 mins)
    t_base_min = max(45.0, min(t_base_min, 480.0))
    t_peak_min = 0.30 * t_base_min

    time_series: List[float] = []
    discharge_series: List[float] = []

    current_t = 0.0
    while current_t <= t_base_min:
        time_series.append(round(current_t, 1))
        if current_t <= t_peak_min:
            # Rising limb: quadratic / steep surge
            ratio = current_t / t_peak_min
            q = q_peak_m3s * (ratio ** 1.5)
        else:
            # Recession limb: exponential decay
            decay_ratio = (current_t - t_peak_min) / (t_base_min - t_peak_min)
            q = q_peak_m3s * math.exp(-2.5 * decay_ratio)
        discharge_series.append(round(max(0.0, q), 1))
        current_t += time_step_min

    return {
        "time_minutes": time_series,
        "discharge_m3s": discharge_series,
        "peak_discharge": round(q_peak_m3s, 1),
        "time_to_peak_min": round(t_peak_min, 1),
        "duration_hours": round(t_base_min / 60.0, 2)
    }


def simulate_downstream_propagation(
    q_peak_m3s: float,
    downstream_elements: List[Dict[str, Any]],
    avg_valley_slope: float = 0.04,
    manning_n: float = 0.055,
    river_bed_width_m: float = 65.0
) -> List[Dict[str, Any]]:
    """
    Calculates flood wave propagation along the mountain canyon:
    - Attenuated peak discharge Q(x)
    - Flood wave velocity v ~ 1/n * R^(2/3) * S^(1/2) (Manning approximation)
    - Arrival time of flood front and peak
    - Inundation flow depth
    - Warning lead time classification
    """
    results = []

    for elem in downstream_elements:
        dist_km = float(elem.get("distance_km", 10.0))
        dist_m = dist_km * 1000.0

        # Costa & USACE mountain canyon attenuation factor
        # Q(x) = Q_peak / (1 + 0.028 * (dist_km ^ 0.75))
        attenuation_factor = 1.0 / (1.0 + 0.025 * (dist_km ** 0.72))
        q_at_location = q_peak_m3s * attenuation_factor

        # Estimate hydraulic radius and flood flow depth y via Manning's formula
        # Q = (1/n) * Area * R^(2/3) * S^(1/2) where Area ~ W * y, R ~ y
        # y = [ (Q * n) / (W * S^0.5) ] ^ (3/5)
        depth_m = ((q_at_location * manning_n) / (river_bed_width_m * math.sqrt(avg_valley_slope))) ** 0.60
        depth_m = max(1.2, depth_m)

        # Average wave front velocity (steep Himalayan canyon typical: 4.5 - 9 m/s)
        # v = Q / (W * y)
        velocity_ms = min(12.0, max(3.5, q_at_location / (river_bed_width_m * depth_m)))

        # Travel time in seconds and minutes
        travel_time_sec = dist_m / velocity_ms
        travel_time_min = travel_time_sec / 60.0
        peak_arrival_min = travel_time_min + 15.0  # Peak lags behind front wave

        # Risk warning urgency
        if travel_time_min < 30.0:
            urgency = "IMMINENT_CRITICAL (Red Alert)"
        elif travel_time_min < 90.0:
            urgency = "HIGH_URGENCY (Orange Alert)"
        elif travel_time_min < 180.0:
            urgency = "ELEVATED (Yellow Alert)"
        else:
            urgency = "MODERATE (Advisory)"

        results.append({
            "name": elem.get("name", "Settlement"),
            "distance_km": dist_km,
            "population": elem.get("population", 0),
            "critical_asset": elem.get("critical_asset", "Infrastructure"),
            "attenuated_peak_q_m3s": round(q_at_location, 1),
            "est_flood_depth_m": round(depth_m, 2),
            "flow_velocity_ms": round(velocity_ms, 2),
            "wave_arrival_min": round(travel_time_min, 1),
            "peak_arrival_min": round(peak_arrival_min, 1),
            "warning_status": urgency
        })

    return results
