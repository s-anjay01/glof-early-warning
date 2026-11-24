/**
 * GLOF Early Warning and Risk Assessment Web Client.
 * Connects to Flask REST endpoints and orchestrates Leaflet & Chart.js.
 */

let mapInstance = null;
let lakesData = [];
let currentLake = null;
let radarChartInstance = null;
let hydrographChartInstance = null;
let timeseriesChartInstance = null;
let mapMarkers = {};
let downstreamLayerGroup = null;

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupEventHandlers();
    loadLakesData();
    loadHistoricalData();
});

function initMap() {
    // Centered on the Himalayas (Sikkim / Nepal / Uttarakhand)
    mapInstance = L.map("map").setView([29.0, 83.5], 6);

    // OpenTopoMap & Satellite Layer Options
    const topoLayer = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
        maxZoom: 17,
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
    });

    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });

    // Default to Satellite layer for glaciological context
    esriSatellite.addTo(mapInstance);

    const baseMaps = {
        "Satellite Imagery": esriSatellite,
        "Topographic Relief": topoLayer
    };
    L.control.layers(baseMaps).addTo(mapInstance);

    downstreamLayerGroup = L.layerGroup().addTo(mapInstance);
}

function setupEventHandlers() {
    const lakeSelect = document.getElementById("lake-selector");
    lakeSelect.addEventListener("change", (e) => {
        selectLakeById(e.target.value);
    });

    const triggerSelect = document.getElementById("trigger-type");
    triggerSelect.addEventListener("change", (e) => {
        const isAvalanche = e.target.value === "avalanche";
        document.getElementById("avalanche-controls").style.display = isAvalanche ? "grid" : "none";
        document.getElementById("breach-controls").style.display = isAvalanche ? "none" : "grid";
    });

    // Sliders live values
    const avalVolSlider = document.getElementById("avalanche-vol-slider");
    avalVolSlider.addEventListener("input", (e) => {
        const valMCM = (parseFloat(e.target.value) / 1000000).toFixed(2);
        document.getElementById("aval-vol-val").innerText = `${valMCM} MCM`;
    });

    const breachDepthSlider = document.getElementById("breach-depth-slider");
    breachDepthSlider.addEventListener("input", (e) => {
        document.getElementById("breach-depth-val").innerText = `${e.target.value}%`;
    });

    const runSimBtn = document.getElementById("run-simulation-btn");
    runSimBtn.addEventListener("click", () => {
        executeSimulation();
    });

    // Tab buttons
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const targetTab = e.target.getAttribute("data-tab");
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            e.target.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });
}

async function loadLakesData() {
    try {
        const res = await fetch("/api/lakes");
        lakesData = await res.json();

        updateKpiCounters(lakesData);
        populateLakeSelector(lakesData);
        plotLakesOnMap(lakesData);

        // Select the first high-profile lake (South Lhonak)
        if (lakesData.length > 0) {
            selectLakeById(lakesData[0].id);
        }
    } catch (err) {
        console.error("Failed to load lakes data:", err);
    }
}

function updateKpiCounters(lakes) {
    let criticalCount = 0;
    let totalVolumeMCM = 0;
    let totalExposedPop = 0;

    lakes.forEach(l => {
        if (l.risk_assessment.hazard_level === "CRITICAL") criticalCount++;
        totalVolumeMCM += (l.lake_volume_mcm || 0);
        const elements = l.downstream_elements || [];
        totalExposedPop += elements.reduce((acc, curr) => acc + (curr.population || 0), 0);
    });

    document.getElementById("kpi-monitored").innerText = lakes.length;
    document.getElementById("kpi-critical").innerText = criticalCount;
    document.getElementById("kpi-volume").innerText = `${totalVolumeMCM.toFixed(1)} MCM`;
    document.getElementById("kpi-exposed").innerText = totalExposedPop.toLocaleString();
}

function populateLakeSelector(lakes) {
    const sel = document.getElementById("lake-selector");
    sel.innerHTML = "";
    lakes.forEach(lake => {
        const opt = document.createElement("option");
        opt.value = lake.id;
        opt.innerText = `${lake.name} (${lake.region}, ${lake.country}) - ${lake.risk_assessment.hazard_level}`;
        sel.appendChild(opt);
    });
}

function plotLakesOnMap(lakes) {
    lakes.forEach(lake => {
        const risk = lake.risk_assessment;
        const color = risk.badge_color || "#38bdf8";

        const marker = L.circleMarker([lake.lat, lake.lon], {
            radius: 8,
            fillColor: color,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85
        }).addTo(mapInstance);

        const popupContent = `
            <div style="font-family: system-ui; min-width: 180px;">
                <h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px;">${lake.name}</h4>
                <div style="font-size: 11px; color: #475569; margin-bottom: 6px;">${lake.region}, ${lake.country}</div>
                <div style="font-size: 12px; margin-bottom: 4px;"><strong>Volume:</strong> ${lake.lake_volume_mcm} MCM</div>
                <div style="font-size: 12px; margin-bottom: 4px;"><strong>Freeboard:</strong> ${lake.freeboard_m} m</div>
                <div style="font-size: 12px; margin-bottom: 8px;"><strong>Hazard:</strong> <span style="color:${color}; font-weight:700;">${risk.hazard_level} (${risk.composite_score}/100)</span></div>
                <button onclick="window.selectLakeById('${lake.id}')" style="background:#0284c7; color:#fff; border:none; padding:4px 8px; border-radius:4px; cursor:pointer; font-size:11px; width:100%;">Analyze in Simulator</button>
            </div>
        `;
        marker.bindPopup(popupContent);
        mapMarkers[lake.id] = marker;
    });
}

window.selectLakeById = function(lakeId) {
    const lake = lakesData.find(l => l.id === lakeId);
    if (!lake) return;
    currentLake = lake;

    document.getElementById("lake-selector").value = lakeId;

    // Pan map to lake
    mapInstance.setView([lake.lat, lake.lon], 9);
    if (mapMarkers[lakeId]) {
        mapMarkers[lakeId].openPopup();
    }

    // Render downstream flow paths on map
    renderDownstreamPaths(lake);

    // Update lake overview panel
    renderLakeDeepDive(lake);

    // Load satellite time series chart
    loadTimeSeriesChart(lakeId);

    // Run baseline simulation
    executeSimulation();
};

function renderDownstreamPaths(lake) {
    downstreamLayerGroup.clearLayers();
    const downstream = lake.downstream_elements || [];
    if (!downstream.length) return;

    // Connect lake to downstream elements with dashed hazard vector
    const pathCoords = [[lake.lat, lake.lon]];
    
    downstream.forEach((elem, idx) => {
        // Approximate river valley coordinates (downstream gradient)
        // Offset latitude/longitude according to mountain drainage direction
        const latOffset = (idx + 1) * -0.08;
        const lonOffset = (idx + 1) * 0.04;
        const pt = [lake.lat + latOffset, lake.lon + lonOffset];
        pathCoords.push(pt);

        const assetMarker = L.circleMarker(pt, {
            radius: 5,
            fillColor: "#fb923c",
            color: "#ffffff",
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(downstreamLayerGroup);

        assetMarker.bindPopup(`
            <div style="font-size:12px;">
                <strong>${elem.name}</strong> (${elem.distance_km} km)<br>
                <em>${elem.critical_asset || 'Settlement'}</em><br>
                Pop: ${(elem.population || 0).toLocaleString()}
            </div>
        `);
    });

    L.polyline(pathCoords, {
        color: "#38bdf8",
        weight: 3,
        dashArray: "6, 8",
        opacity: 0.8
    }).addTo(downstreamLayerGroup);
}

function renderLakeDeepDive(lake) {
    const risk = lake.risk_assessment;
    const scoreElem = document.getElementById("deepdive-score");
    scoreElem.innerText = risk.composite_score;
    scoreElem.style.color = risk.badge_color;

    const levelElem = document.getElementById("deepdive-level");
    levelElem.innerText = `${risk.hazard_level} RISK - ${risk.action_code}`;
    levelElem.className = `badge badge-${getBadgeClass(risk.hazard_level)}`;

    // Quick metrics
    document.getElementById("dd-elevation").innerText = `${lake.elevation_m} m`;
    document.getElementById("dd-area").innerText = `${lake.lake_area_km2} km²`;
    document.getElementById("dd-volume").innerText = `${lake.lake_volume_mcm} MCM`;
    document.getElementById("dd-freeboard").innerText = `${lake.freeboard_m} m`;
    document.getElementById("dd-dam").innerText = lake.dam_type;
    document.getElementById("dd-slope").innerText = `${lake.slope_gradient_deg}°`;

    // Recommendations
    const recsUl = document.getElementById("deepdive-recommendations");
    recsUl.innerHTML = "";
    (risk.recommendations || []).forEach(r => {
        const li = document.createElement("li");
        li.innerText = r;
        recsUl.appendChild(li);
    });

    renderRadarChart(risk.factors);
}

function getBadgeClass(hazard) {
    switch (hazard.toUpperCase()) {
        case "CRITICAL": return "red";
        case "HIGH": return "orange";
        case "MODERATE": return "yellow";
        default: return "green";
    }
}

function renderRadarChart(factors) {
    const labels = Object.keys(factors);
    const dataValues = Object.values(factors);

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    const ctx = document.getElementById("radarChart").getContext("2d");
    radarChartInstance = new Chart(ctx, {
        type: "radar",
        data: {
            labels: labels,
            datasets: [{
                label: "Vulnerability Index (%)",
                data: dataValues,
                backgroundColor: "rgba(6, 182, 212, 0.25)",
                borderColor: "#06b6d4",
                pointBackgroundColor: "#38bdf8",
                pointBorderColor: "#fff",
                pointHoverBackgroundColor: "#fff",
                pointHoverBorderColor: "#06b6d4"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: "rgba(255, 255, 255, 0.1)" },
                    grid: { color: "rgba(255, 255, 255, 0.1)" },
                    pointLabels: { color: "#9ca3af", font: { size: 10 } },
                    ticks: { display: false, max: 100, min: 0 }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

async function loadTimeSeriesChart(lakeId) {
    try {
        const res = await fetch(`/api/timeseries/${lakeId}`);
        const data = await res.json();
        const ctx = document.getElementById("timeSeriesChart").getContext("2d");

        if (timeseriesChartInstance) {
            timeseriesChartInstance.destroy();
        }

        if (!data.found) {
            document.getElementById("timeseries-note").innerText = "No multi-year satellite time-series profile for this specific lake.";
            return;
        }

        document.getElementById("timeseries-note").innerText = `Net Area Growth: +${data.analysis.total_growth_percentage}% (${data.analysis.start_year} - ${data.analysis.latest_year}). ${data.analysis.note}`;

        timeseriesChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.raw_data.years,
                datasets: [
                    {
                        label: "Lake Area (km²)",
                        data: data.raw_data.lake_area_km2,
                        borderColor: "#38bdf8",
                        backgroundColor: "rgba(56, 189, 248, 0.15)",
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: "Mean Summer Temp (°C)",
                        data: data.raw_data.mean_summer_temp_c,
                        borderColor: "#f97316",
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#9ca3af" }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#38bdf8" },
                        title: { display: true, text: 'Area (km²)', color: '#38bdf8' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: "#f97316" },
                        title: { display: true, text: 'Summer Temp (°C)', color: '#f97316' }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#e5e7eb", font: { size: 11 } } }
                }
            }
        });
    } catch (err) {
        console.error("Error loading time-series:", err);
    }
}

async function executeSimulation() {
    if (!currentLake) return;

    const trigger = document.getElementById("trigger-type").value;
    const payload = {
        lake_id: currentLake.id,
        trigger_type: trigger
    };

    if (trigger === "avalanche") {
        payload.avalanche_volume_m3 = parseFloat(document.getElementById("avalanche-vol-slider").value);
        payload.impact_angle_deg = 45.0;
    } else {
        payload.breach_width_m = 65.0;
        payload.breach_depth_fraction = parseFloat(document.getElementById("breach-depth-slider").value) / 100.0;
    }

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const simResult = await res.json();
        renderSimulationResults(simResult);
    } catch (err) {
        console.error("Simulation error:", err);
    }
}

function renderSimulationResults(res) {
    // KPI boxes
    if (res.trigger_type.includes("Avalanche")) {
        document.getElementById("res-wave").innerText = `${res.initial_wave_height_m} m`;
        document.getElementById("res-overtop").innerText = `${res.overtopping_height_m} m`;
    } else {
        document.getElementById("res-wave").innerText = "N/A (Breach)";
        document.getElementById("res-overtop").innerText = `${res.breach_depth_m} m Depth`;
    }

    document.getElementById("res-vol").innerText = `${res.water_released_mcm} MCM`;
    document.getElementById("res-peak").innerText = `${res.peak_discharge_m3s.toLocaleString()} m³/s`;

    // Hydrograph chart
    renderHydrographChart(res.hydrograph);

    // Downstream timeline table
    renderDownstreamTable(res.downstream_impact);
}

function renderHydrographChart(hydro) {
    const ctx = document.getElementById("hydrographChart").getContext("2d");

    if (hydrographChartInstance) {
        hydrographChartInstance.destroy();
    }

    hydrographChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: hydro.time_minutes.map(t => `${t}m`),
            datasets: [{
                label: "Breach Outburst Hydrograph Q (m³/s)",
                data: hydro.discharge_m3s,
                borderColor: "#06b6d4",
                backgroundColor: "rgba(6, 182, 212, 0.2)",
                fill: true,
                tension: 0.35,
                pointRadius: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#9ca3af", maxTicksLimit: 12 },
                    title: { display: true, text: 'Time Elapsed Post-Breach (minutes)', color: '#9ca3af' }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#9ca3af" },
                    title: { display: true, text: 'Discharge Q (m³/s)', color: '#06b6d4' }
                }
            },
            plugins: {
                legend: { labels: { color: "#e5e7eb" } }
            }
        }
    });
}

function renderDownstreamTable(impacts) {
    const tbody = document.getElementById("downstream-table-body");
    tbody.innerHTML = "";

    if (!impacts || impacts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#9ca3af;">No immediate downstream settlements registered.</td></tr>`;
        return;
    }

    impacts.forEach(item => {
        const tr = document.createElement("tr");

        let badgeClass = "badge-green";
        if (item.warning_status.includes("CRITICAL")) badgeClass = "badge-red";
        else if (item.warning_status.includes("ORANGE")) badgeClass = "badge-orange";
        else if (item.warning_status.includes("YELLOW")) badgeClass = "badge-yellow";

        tr.innerHTML = `
            <td><strong>${item.name}</strong><br><small style="color:#9ca3af;">${item.critical_asset || ''}</small></td>
            <td>${item.distance_km} km</td>
            <td style="color:#38bdf8; font-weight:600;">${item.wave_arrival_min} min</td>
            <td>${item.attenuated_peak_q_m3s.toLocaleString()} m³/s</td>
            <td>${item.est_flood_depth_m} m</td>
            <td><span class="badge ${badgeClass}">${item.warning_status}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadHistoricalData() {
    try {
        const res = await fetch("/api/historical");
        const events = await res.json();
        const container = document.getElementById("historical-events-container");
        container.innerHTML = "";

        events.forEach(ev => {
            const card = document.createElement("div");
            card.style.background = "#111827";
            card.style.border = "1px solid #27354f";
            card.style.borderRadius = "8px";
            card.style.padding = "1rem";
            card.style.marginBottom = "0.75rem";

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <h4 style="color:#38bdf8; font-size:1rem; font-weight:700;">${ev.event_name} (${ev.year})</h4>
                    <span style="font-size:0.75rem; color:#9ca3af;">${ev.location} &bull; ${ev.basin}</span>
                </div>
                <p style="font-size:0.8rem; color:#d1d5db; margin-bottom:0.4rem;"><strong>Trigger:</strong> ${ev.trigger}</p>
                <p style="font-size:0.8rem; color:#ef4444; margin-bottom:0.4rem;"><strong>Impact:</strong> ${ev.damage} (Peak Q: ~${ev.estimated_peak_discharge_m3s.toLocaleString()} m³/s)</p>
                <p style="font-size:0.75rem; color:#34d399; background:rgba(16,185,129,0.1); padding:0.4rem 0.6rem; border-radius:4px;">
                    <strong>Glaciological Lesson:</strong> ${ev.key_lesson}
                </p>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load historical events:", err);
    }
}
