# Release Notes

## v1.4.0 (Runway Intelligence Upgrade)
**Date:** 2025-12-01
**Status:** Production / Stable

### 🏆 Milestone Achievement
This release marks the transition to a fully autonomous Air Traffic Intelligence system. The **Runway Tracker** now operates with "Human-Like" logic, distinguishing between landing, takeoff, taxiing, and 
aborted maneuvers using physics-based filtering.

### 🚀 Core Features
* **Runway Tracker v2.7.2:**
    * **Vector Logic:** Automatically assigns Runway IDs (15, 22, 04, 33) based on aircraft magnetic heading.
    * **Ground Clamp:** Physics filter that prevents false "Landing" alerts for aircraft taxiing at < 60kts.
    * **Global Data Fusion:** "Deep Search" capability looks back 15 minutes in local and global databases to recover missing Squawk codes and Callsigns.
* **Dynamic Configuration:** Airport geometry is now fetched dynamically from the local `airports.geojson` gazetteer.

### 🐛 Bug Fixes
* **Data Sanitization:** Fixed `NoneType` crashes caused by partial ADS-B packets.
* **Tag Awareness:** Solved database query mismatches between Tags (Indexed) and Fields (Data), ensuring Callsigns appear correctly in tables.

---


# Release Notes

## v1.4.0 (The Runway Intelligence Update)
**Date:** 2025-12-01
**Status:** Stable / Production

### 🚀 New Features
* **Runway Tracker v2.0:** Complete rewrite of the tracking engine.
    * **Database-Driven:** Now queries InfluxDB directly instead of polling HTTP (eliminates networking sync issues).
    * **Calculated Physics:** Automatically calculates Vertical Speed (VSI) based on altitude history if the aircraft transponder reports 0 (fixes "Invisible Landing" bug).
    * **Taxiing Detection:** Now detects and logs aircraft moving on the ground (5-40 kts).
    * **Vector Logic:** Uses aircraft heading to determine specific runways (15 vs 22R).
* **Runway Simulator:** Added `tools/runway_test.py` to inject synthetic landing events for dashboard testing.

### 🐛 Bug Fixes
* **Null-Safety:** Fixed critical crash loop in `runway-tracker` when receiving partial ADS-B frames.
* **Dependencies:** Added `geopy` to runway-tracker requirements.

---


# Release Notes

## v1.3.0 (The "Red Team" Release)
**Date:** 2025-11-30
**Status:** Stable / Production

### 🚀 New Features
* **Physics Guard Engine:** New microservice (`physics-guard`) that monitors live telemetry for kinematic anomalies (e.g., Mach > 0.95, VSI > 6000 fpm).
* **Red Team Suite:** Added `spoof_simulator.py` and `physics_test.py` for system validation.
* **Central Brain Dashboard:** Complete integration of live runway logic and security alerts.
* **Architecture Diagram:** Updated Wiki documentation with v0.9 data flow logic.

### 🐛 Bug Fixes
* **MQTT Compatibility:** Downgraded `paho-mqtt` to `<2.0.0` in `physics-guard` to resolve callback API errors.
* **Build System:** Added `.dockerignore` to prevent uploading heavy data volumes during Balena builds.
* **Configuration:** Fixed `docker-compose.yml` to correctly expose the Physics Guard service.

---

# Release Notes - v0.9.0-beta (Central Brain)

**Date:** 2025-11-29
**Status:** Beta / Pre-Production
**Device:** Raspberry Pi 5 (BalenaOS) + macOS Client

## 🚀 Key Features
* **Unified Dashboard:** "Central Brain" dashboard integrating live maps, system health (RPi4 + RPi5), and operational logic.
* **Red Team Capabilities:** Added `tools/spoof_simulator.py` to inject fake GPS data for security testing.
* **Spoof Detection Engine:** `spoof-detector` service now logs drift data and specific security alerts to InfluxDB for historical analysis.
* **Live Runway Logic:** FIDS (Flight Information Display System) table showing landing/takeoff events with visual icons.
* **Cross-Platform Networking:** Fixed `network_mode: host` issues for macOS development environment, enabling seamless local testing.

## 🔧 Component Updates
* **Spoof Detector (v2.1):** * Added InfluxDB logging for `gps_drift` (continuous graphing).
    * Added detailed coordinate logging for `security_alerts` (for table visualization).
    * Drift threshold set to **2.0 km**.
* **FR24 Poller:** Configured to fetch "Truth" data for the Helsinki area (Bounds: 60.6, 59.9, 24.3, 25.5).
* **Grafana:** * Added "SPOOF DETECTOR" panel with dynamic red/green threshold coloring.
    * Added "Live Runway" table with symbol mapping (🛬/🛫).

## ⚠️ Known Issues / TODO
* **Secrets:** API tokens currently passed via environment variables; move to secrets manager for production.
* **Data Persistence:** InfluxDB volume is local; consider backup strategy.
