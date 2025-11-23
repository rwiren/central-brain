# Secure Skies: ADS-B Integrity & Spoofing Detection

**Project Status:** 🟢 Data Ingestion Phase
**Location:** HEL-ARN Corridor (Focus: EFHK)
**Author:** Riku Wirén

## 📖 Project Overview
*As part of the AI Neural Networks Cohort 2 Capstone.*

**Business Problem:** Unencrypted ADS-B signals are vulnerable to spoofing, creating "ghost flights" and polluting data streams used for Integrated Sensing (ISAC).
**Goal:** Train a Sequence Model (LSTM/RNN) to predict flight anomalies by learning the physics of valid trajectories vs. synthetic spoofing attacks.

---

## 🏗 Architecture
This system runs on BalenaOS (Edge) and performs three distinct functions:

1.  **Ingestion (SIGINT):** Captures raw 1090MHz RF data via `readsb`.
2.  **Labeling (Runway Tracker):** A physics engine that tags flights as "Landing" or "Takeoff" based on precise runway threshold logic. This generates the **Ground Truth** labels for the ML model.
3.  **Validation (Spoof Detector):** Compares local RF data against global OpenSky Network data to detect inconsistencies.

---

## 📔 Project Journal

### [2025-11-23] Phase 1: Infrastructure & Data Engineering
- **Objective:** Establish reliable data collection for HEL flight corridor.
- **Action:** Deployed `readsb` (SDR), `influxdb` (Time-Series DB), and `grafana`.
- **Feature Engineering:** Implemented `runway-tracker` service to calculate distance-to-threshold and vertical rates.
- **Data:** Successfully logging ~10,000 flight events per day to `flight_ops` bucket.

---

## 🛠 Deployment
This project is designed for BalenaOS.

```bash
balena push <app-name>
```

### Services
* **readsb:** Software Defined Radio interface.
* **runway-tracker:** Python logic for geometric runway analysis.
* **influxdb (1.8):** Storage for flight telemetry.
* **grafana:** Visualization of flight paths and anomalies.
