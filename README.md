# Secure Skies: ADS-B Integrity & Spoofing Detection

![Status](https://img.shields.io/badge/Status-Data_Ingestion-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-BalenaOS-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-yellow?style=flat-square)

**Location:** HEL-ARN Corridor (Focus: EFHK)
**Author:** RW

## 📖 Project Overview
**Business Problem:** Unencrypted ADS-B signals are vulnerable to spoofing, creating "ghost flights" and polluting data streams used for Integrated Sensing (ISAC).

**Goal:** Train a Sequence Model (LSTM/RNN) to predict flight anomalies by learning the physics of valid trajectories vs. synthetic spoofing attacks.

---

## 📐 System Flow
This architecture treats the RPi4 as a "dumb" sensor (Forward Edge) and the RPi5 as the "intelligent" processor (Central Brain).

```mermaid
graph LR
    %% 1. Sensing Layer
    subgraph SENSOR [RPi4: The Sensor]
        WAVES((Radio Waves)) --> ANT[Antenna]
        ANT --> DECODER[Signal Decoder]
    end

    %% 2. Intelligence Layer
    subgraph BRAIN [RPi5: The Brain]
        DECODER -->|Stream| PHYSICS[Runway Tracker]
        DECODER -->|Stream| DETECT[Spoof Detector]
        
        PHYSICS -->|Label: Landing| DB[(Flight Database)]
        DETECT -->|Alert: Anomaly| ALERT[Alert System]
    end

    %% 3. Validation Layer
    subgraph CLOUD [External Validation]
        DETECT -.->|Cross-Check| OPENSKY[OpenSky Network]
    end

    %% 4. Visualization
    DB --> DASH[Dashboard]

    %% Styling
    style SENSOR fill:#f9f9f9,stroke:#333
    style BRAIN fill:#e1f5fe,stroke:#0277bd
    style CLOUD fill:#fff3e0,stroke:#ef6c00,stroke-dasharray: 5 5
    style ALERT fill:#ffebee,stroke:#c62828
```

---

## 📂 Repository Structure
```text
.
├── docker-compose.yml          # Orchestration
├── physics-guard               # Logic: Detects Mach 2 anomalies
│   ├── Dockerfile
│   ├── guard.py
│   └── requirements.txt
├── runway-tracker              # Logic: Geofencing & ML Labeling
│   ├── Dockerfile
│   └── src
│       └── main.py
└── spoof-detector              # Logic: OpenSky Cross-referencing
    ├── Dockerfile
    ├── requirements.txt
    └── watchdog.py
```

---

## 📔 Project Journal

### [2025-11-23] Phase 1: Infrastructure & Data Engineering
- **Objective:** Establish reliable data collection for HEL flight corridor.
- **Action:** Deployed `readsb` (SDR), `influxdb` (Time-Series DB), and `grafana`.
- **Feature Engineering:** Implemented `runway-tracker` service to calculate distance-to-threshold and vertical rates.
- **Data:** Successfully logging ~10,000 flight events per day to `flight_ops` bucket.

---

## 📚 Acknowledgements & References
This project builds upon open-source research and existing Balena blocks.

* **Base Infrastructure:** [balena-ads-b by ketilmo](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file) - Excellent foundation for containerized SDR.
* **Data Validation:** [OpenSky Network Config](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file#part-6--configure-opensky-network) - We utilize their API for ground-truth verification.
* **Security Research:** [Defeating ADS-B (YouTube)](https://www.youtube.com/watch?v=51zEjso9kZw)

---

## 🛠 Deployment
```bash
balena push <app-name>
```
