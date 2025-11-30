# Release Notes - v0.9.0-beta (Central Brain)

**Date:** 2025-11-30
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
