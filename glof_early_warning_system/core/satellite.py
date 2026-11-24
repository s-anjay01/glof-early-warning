"""
Satellite Remote Sensing & Water Index Analysis for Glacial Lake Monitoring.
Implements NDWI (McFeeters) and MNDWI (Xu) algorithms, multi-temporal area growth calculation,
and satellite change detection metrics.
"""

from typing import Dict, Any, List


def calculate_ndwi(green_band: float, nir_band: float) -> float:
    """
    McFeeters (1996) Normalized Difference Water Index:
    NDWI = (Green - NIR) / (Green + NIR)
    Positive values (> 0.2) typically correspond to open water bodies.
    """
    denominator = green_band + nir_band
    if denominator == 0:
        return 0.0
    return (green_band - nir_band) / denominator


def calculate_mndwi(green_band: float, swir_band: float) -> float:
    """
    Xu (2006) Modified Normalized Difference Water Index:
    MNDWI = (Green - SWIR) / (Green + SWIR)
    Superior in rugged alpine terrain as it separates water from snow/ice and mountain shadows.
    """
    denominator = green_band + swir_band
    if denominator == 0:
        return 0.0
    return (green_band - swir_band) / denominator


def analyze_lake_growth_timeseries(timeseries_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes historical satellite-derived surface area, growth velocity,
    and temperature correlations.
    """
    years = timeseries_entry.get("years", [])
    areas = timeseries_entry.get("lake_area_km2", [])
    ndwi = timeseries_entry.get("satellite_ndwi_mean", [])
    temps = timeseries_entry.get("mean_summer_temp_c", [])

    if len(years) < 2 or len(areas) < 2:
        return {"error": "Insufficient time series points"}

    t_span = years[-1] - years[0]
    total_area_change = areas[-1] - areas[0]
    annual_rate_km2_yr = total_area_change / max(1, t_span)
    pct_total_growth = (total_area_change / areas[0]) * 100.0

    # Linear slope estimate (simple regression)
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(areas) / n
    numerator = sum((years[i] - mean_x) * (areas[i] - mean_y) for i in range(n))
    denominator = sum((years[i] - mean_x) ** 2 for i in range(n))
    growth_slope = numerator / denominator if denominator != 0 else 0.0

    return {
        "lake_name": timeseries_entry.get("name"),
        "start_year": years[0],
        "latest_year": years[-1],
        "initial_area_km2": areas[0],
        "latest_area_km2": areas[-1],
        "net_area_expansion_km2": round(total_area_change, 3),
        "total_growth_percentage": round(pct_total_growth, 1),
        "annual_expansion_rate_km2_yr": round(growth_slope, 4),
        "recent_ndwi": ndwi[-1] if ndwi else None,
        "recent_summer_temp_c": temps[-1] if temps else None,
        "note": timeseries_entry.get("event_note", "")
    }
