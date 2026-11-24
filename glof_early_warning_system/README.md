# 🏔️ Himalayan GLOF Early Warning & Risk Intelligence System

An end-to-end Python, GIS, and Hydrodynamic modeling platform engineered to assess, simulate, and provide early warnings for **Glacial Lake Outburst Floods (GLOFs)** across the Hindu Kush-Himalayan (HKH) mountain ranges (India, Nepal, and Bhutan).

---

## 📌 Project Overview & Significance

Glacial lakes in the Himalayas are expanding at unprecedented rates due to climate warming and rapid glacier retreat. Catastrophic outbursts—such as the **October 2023 South Lhonak outburst flood in Sikkim** (which swept away the 1,200 MW Teesta-III Chungthang Dam) and the **June 2013 Kedarnath Chorabari disaster**—highlight the urgent need for physics-based early warning systems.

This project delivers:
1. **Curated Glacial Lake Database:** High-resolution morphological data on 10 critical Himalayan sentinel lakes (coordinates, volume, dam geometry, freeboard, expansion rates, and downstream hydropower/settlement assets).
2. **Empirical & Hydrodynamic Dam-Break Engine:** Implementation of peer-reviewed peak discharge equations (Costa 1985, Froehlich 1995, Huggel et al. 2002), impulse tsunami wave theory (Heller & Hager 2010), and breach hydrograph generation.
3. **Multi-Criteria Hazard Assessment (AHP):** 7-factor Analytic Hierarchy Process evaluating volume, expansion velocity, moraine geometry, permafrost thaw, and avalanche susceptibility.
4. **Flood Wave Routing & Evacuation Lead-Time Prediction:** Canyon wave velocity estimation (Manning's formula) and Costa/USACE peak discharge attenuation for downstream settlements.
5. **Interactive Web GIS Dashboard (Flask + Leaflet.js + Chart.js):** Real-time map with satellite imagery, dynamic simulation sliders, vulnerability radar chart, multi-year satellite expansion curves, and disaster registry.
6. **Standalone Offline Client:** An all-in-one HTML dashboard that opens directly in any browser with zero dependencies.

---

## 🏗️ System Architecture

```
glof_early_warning_system/
│
├── data/
│   ├── glacial_lakes.json         # 10 Himalayan glacial lakes database with attributes
│   ├── historical_events.json     # Registry of historical GLOF disasters (Sikkim, Kedarnath, Chamoli)
│   └── time_series_samples.json   # Multi-year satellite area & summer temperature observations
│
├── core/
│   ├── __init__.py
│   ├── hydrology.py               # Costa, Froehlich, Huggel discharge models & canyon wave routing
│   ├── risk_model.py              # AHP multi-criteria risk engine & engineering mitigation recommendations
│   ├── simulation.py              # Avalanche impulse wave & moraine breach scenario simulator
│   └── satellite.py               # NDWI/MNDWI water indices & growth trend linear regression
│
├── web/
│   ├── app.py                     # Flask REST API server
│   ├── static/
│   │   ├── css/style.css          # Dark Alpine theme styling & responsive grid
│   │   └── js/main.js             # Leaflet GIS, Chart.js integrations & live simulation triggers
│   └── templates/
│       └── index.html             # Main web dashboard interface
│
├── tests/
│   └── test_glof_engine.py        # Automated unit test suite verifying physics calculations
│
├── cli.py                         # Full command-line interface for batch evaluation & simulation
├── standalone_glof_dashboard.html # Single-file, zero-dependency browser dashboard
├── requirements.txt               # Dependencies (Flask, pandas, numpy)
└── run_app.bat                    # One-click Windows runner
```

---

## 🔬 Scientific Framework & Mathematical Models

### 1. Breach Peak Discharge ($Q_{max}$)
- **Costa (1985) Empirical Peak Discharge:**
  $$Q_{max} = 0.013 \cdot (V_w)^{0.598} \cdot (H_d)^{0.548}$$
  *(where $V_w$ is water volume in $\text{m}^3$, $H_d$ is moraine dam crest height in meters)*

- **Froehlich (1995) Breach Peak Discharge:**
  $$Q_{max} = 0.607 \cdot (V_w)^{0.295} \cdot (H_w)^{1.24}$$
  *(where $H_w$ is depth of water above breach invert)*

- **Huggel et al. (2002) Glacial Lake Scaling:**
  $$Q_{max} = 0.0018 \cdot (V_w)^{0.60} \cdot (H_d)^{0.70}$$

### 2. Avalanche Displacement Impulse Wave (Heller & Hager, 2010)
When an ice or rock mass falls into a glacial lake, the initial displacement wave height $H_0$ is modeled as:
$$H_0 = 0.35 \cdot h_{lake} \cdot \left(\frac{V_{avalanche}}{h_{lake}^3}\right)^{0.32} \cdot \sin(\alpha)$$

If the wave height at the moraine crest exceeds the lake freeboard ($H_{crest} > \text{Freeboard}$), overtopping occurs, triggering erosive trench incision and moraine breaching.

### 3. Downstream Canyon Flood Propagation & Attenuation
Flood wave travel velocity along steep mountain gorges is calculated using Manning's equation:
$$v = \frac{1}{n} \cdot R^{2/3} \cdot S_0^{1/2}$$
Attenuated peak discharge with distance $x$ (km):
$$Q(x) = \frac{Q_{max}}{1 + 0.025 \cdot x^{0.72}}$$

---

## 🚀 How to Run the Project

### Option A: Interactive Web Dashboard (Flask)

1. Make sure Python 3.9+ is installed.
2. In this directory, run:
   ```bash
   python web/app.py
   ```
   *(Or simply double-click `run_app.bat` on Windows)*
3. Open your browser to:
   ```
   http://localhost:5000
   ```

### Option B: Standalone Offline Dashboard (Instant Double-Click)
Double-click `standalone_glof_dashboard.html` in Windows Explorer or open it in any web browser (Chrome, Edge, Firefox). It contains all embedded datasets, Leaflet maps, and client-side physics engines—**no local server required!**

### Option C: Command-Line Interface (CLI)

- **List all monitored lakes and current hazard tiers:**
  ```bash
  python cli.py list
  ```

- **Run detailed multi-criteria risk assessment for a specific lake:**
  ```bash
  python cli.py assess GL-IND-SKM-001
  ```

- **Run hydrodynamic simulation (e.g. 2.5 million $\text{m}^3$ ice avalanche into South Lhonak):**
  ```bash
  python cli.py simulate GL-IND-SKM-001 --vol 2500000
  ```

- **Simulate moraine dam piping/collapse:**
  ```bash
  python cli.py simulate GL-IND-SKM-001 --type breach
  ```

---

## 🧪 Running Automated Unit Tests

Run the test suite to verify physical calculations, AHP risk models, and hydrograph generation:
```bash
python -m unittest discover tests
```

---

## 📊 Monitored Himalayan Sentinel Lakes

| Lake ID | Lake Name | Region / Country | Elevation | Volume (MCM) | Hazard Status |
|---|---|---|---|---|---|
| `GL-IND-SKM-001` | **South Lhonak Lake** | North Sikkim, India | 5,200 m | 65.8 | **CRITICAL (78.5/100)** |
| `GL-IND-UTK-002` | **Chorabari Lake** | Kedarnath, Uttarakhand | 3,960 m | 0.85 | **HIGH (56.8/100)** |
| `GL-NPL-EVE-003` | **Imja Tsho** | Khumbu / Everest, Nepal | 5,010 m | 78.0 | **HIGH (61.5/100)** |
| `GL-NPL-DOL-004` | **Tsho Rolpa** | Rolwaling, Nepal | 4,580 m | 85.9 | **HIGH (67.2/100)** |
| `GL-IND-HMP-005` | **Gepang Gath Lake** | Lahaul, Himachal Pradesh | 4,060 m | 28.5 | **HIGH (69.9/100)** |
| `GL-BTN-LUN-006` | **Thorthormi Tsho** | Lunana, Bhutan | 4,428 m | 115.0 | **CRITICAL (80.7/100)** |
| `GL-IND-UTK-007` | **Chamoli / Rishiganga** | Chamoli, Uttarakhand | 4,200 m | 1.25 | **HIGH (61.4/100)** |
| `GL-IND-SKM-008` | **Shako Cho Lake** | North Sikkim, India | 5,100 m | 24.0 | **HIGH (61.6/100)** |
| `GL-IND-LDK-009` | **Kyagar Lake** | Karakoram / Ladakh | 4,750 m | 45.0 | **HIGH (72.4/100)** |
| `GL-BTN-GAS-010` | **Lemthang Tsho** | Gasa, Bhutan | 4,420 m | 12.0 | **MODERATE (52.9/100)** |
