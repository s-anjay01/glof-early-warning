"""
GLOF Early Warning and Risk Assessment Core Engine.
"""

from .hydrology import (
    calculate_costa_peak_discharge,
    calculate_froehlich_peak_discharge,
    calculate_huggel_peak_discharge,
    generate_outburst_hydrograph,
    simulate_downstream_propagation
)
from .risk_model import GLOFRiskEngine
from .simulation import simulate_avalanche_trigger, simulate_moraine_breach
from .satellite import calculate_ndwi, calculate_mndwi, analyze_lake_growth_timeseries

__all__ = [
    "calculate_costa_peak_discharge",
    "calculate_froehlich_peak_discharge",
    "calculate_huggel_peak_discharge",
    "generate_outburst_hydrograph",
    "simulate_downstream_propagation",
    "GLOFRiskEngine",
    "simulate_avalanche_trigger",
    "simulate_moraine_breach",
    "calculate_ndwi",
    "calculate_mndwi",
    "analyze_lake_growth_timeseries"
]
