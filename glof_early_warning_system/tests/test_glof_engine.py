"""
Unit tests for GLOF Early Warning Engine calculations and models.
"""

import unittest
import json
import os
from core.hydrology import (
    calculate_costa_peak_discharge,
    calculate_froehlich_peak_discharge,
    calculate_huggel_peak_discharge,
    generate_outburst_hydrograph,
    simulate_downstream_propagation
)
from core.risk_model import GLOFRiskEngine
from core.simulation import simulate_avalanche_trigger, simulate_moraine_breach
from core.satellite import calculate_ndwi, calculate_mndwi, analyze_lake_growth_timeseries


class TestGLOFEngine(unittest.TestCase):

    def setUp(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "glacial_lakes.json")
        with open(data_path, "r", encoding="utf-8") as f:
            self.lakes = json.load(f)
        self.south_lhonak = self.lakes[0]

    def test_peak_discharge_calculations(self):
        # 30 million m3 water, 50m dam height
        vol = 30_000_000.0
        h = 50.0

        q_costa = calculate_costa_peak_discharge(vol, h)
        q_froehlich = calculate_froehlich_peak_discharge(vol, h)
        q_huggel = calculate_huggel_peak_discharge(vol, h)

        self.assertGreater(q_costa, 1000.0)
        self.assertGreater(q_froehlich, 1000.0)
        self.assertGreater(q_huggel, 500.0)

    def test_hydrograph_generation(self):
        hydro = generate_outburst_hydrograph(q_peak_m3s=4500.0, total_volume_m3=25_000_000.0)
        self.assertIn("time_minutes", hydro)
        self.assertIn("discharge_m3s", hydro)
        self.assertGreater(len(hydro["time_minutes"]), 10)
        self.assertEqual(hydro["peak_discharge"], 4500.0)
        self.assertGreater(max(hydro["discharge_m3s"]), 4000.0)

    def test_downstream_propagation(self):
        elements = self.south_lhonak["downstream_elements"]
        results = simulate_downstream_propagation(q_peak_m3s=5200.0, downstream_elements=elements)
        self.assertEqual(len(results), len(elements))

        # Check attenuation: closer village has higher peak discharge than farther village
        first_q = results[0]["attenuated_peak_q_m3s"]
        last_q = results[-1]["attenuated_peak_q_m3s"]
        self.assertGreater(first_q, last_q)

        # Arrival time must increase with distance
        self.assertLess(results[0]["wave_arrival_min"], results[-1]["wave_arrival_min"])

    def test_risk_assessment_engine(self):
        eval_result = GLOFRiskEngine.evaluate_lake_risk(self.south_lhonak)
        self.assertIn("composite_score", eval_result)
        self.assertIn("hazard_level", eval_result)
        self.assertIn("factors", eval_result)
        self.assertGreaterEqual(eval_result["composite_score"], 0.0)
        self.assertLessEqual(eval_result["composite_score"], 100.0)
        self.assertEqual(eval_result["hazard_level"], "CRITICAL")

    def test_avalanche_simulation(self):
        res = simulate_avalanche_trigger(self.south_lhonak, avalanche_volume_m3=2_000_000.0)
        self.assertIn("initial_wave_height_m", res)
        self.assertIn("peak_discharge_m3s", res)
        self.assertIn("hydrograph", res)
        self.assertIn("downstream_impact", res)

    def test_satellite_indices(self):
        # Water reflects green and strongly absorbs NIR/SWIR
        ndwi = calculate_ndwi(green_band=0.45, nir_band=0.08)
        self.assertGreater(ndwi, 0.5)

        mndwi = calculate_mndwi(green_band=0.45, swir_band=0.05)
        self.assertGreater(mndwi, 0.6)

    def test_time_series_analyzer(self):
        ts_path = os.path.join(os.path.dirname(__file__), "..", "data", "time_series_samples.json")
        with open(ts_path, "r", encoding="utf-8") as f:
            ts_data = json.load(f)
        analysis = analyze_lake_growth_timeseries(ts_data["GL-IND-SKM-001"])
        self.assertIn("annual_expansion_rate_km2_yr", analysis)
        self.assertIn("total_growth_percentage", analysis)


if __name__ == "__main__":
    unittest.main()
