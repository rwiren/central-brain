# Secure Skies: ADS-B Integrity & Spoofing Detection

![Status](https://img.shields.io/badge/Status-Active_Monitoring-green?style=flat-square)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
![Platform](https://img.shields.io/badge/Platform-BalenaOS-blue?style=flat-square)
![Python](https://imgles.io/badge/Python-3.11-yellow?style=flat-square)
![Last Updated](https://img.shields.io/badge/Last%20Updated-2025--11--24-orange?style=flat-square)

**Location:** HEL-ARN Corridor (Focus: EFHK)  
**Author:** RW

---

### 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Hardware Architecture](#-hardware-architecture)
- [System Data Flow](#-system-data-flow)
- [Security Modules](#-security-modules-watchdog-20)
- [Receiver Coverage](#-receiver-coverage)
- [Data Dictionary & Schema](#-data-dictionary--system-architecture)
- [Deployment](#-deployment)

---

## 📖 Project Overview
**Business Problem:** Unencrypted ADS-B signals are vulnerable to spoofing, creating "ghost flights" and polluting data streams used for air traffic monitoring and critical safety systems.

**Goal:** Detect flight anomalies in real-time by comparing local RF data against global reference networks (OpenSky) and analyzing kinematic physics (e.g., impossible turns, fake go-arounds).

---

## 🔭 Hardware Architecture
This project uses a distributed **"Sensor & Brain"** topology to isolate sensitive RF reception from heavy AI processing.

### 📡 Node 1: The Sensor (RPi 4 @ 192.168.1.xxx:8080)
* **Role:** Dedicated Signal Capture and JSON Server.
* **Hardware:** Raspberry Pi 4 + [RTL-SDR V3 Dongle](https://www.rtl-sdr.com/about-rtl-sdr/) + 1090MHz Antenna.
* **Placement:** **11th Floor** window facing Helsinki-Vantaa (EFHK).
* **Function:** Decodes raw 1090MHz RF signals into Beast binary format and serves the processed data via HTTP.

### 🧠 Node 2: The Central Brain (RPi 5)
* **Role:** Aggregation, Logic, Analytics & OAuth2 Handler.
* **Hardware:** Raspberry Pi 5 (16GB RAM) + 1TB NVMe.
* **Function:**
    * Ingests Beast stream from Node 1.
    * Runs **Watchdog 2.0** (Anomaly Detection).
    * Hosts InfluxDB (Time-series data) and Grafana (Visualization).
    * **OAuth2 Integration:** Implements the OAuth2 Client Credentials Flow to reliably fetch global truth data from OpenSky.

---

## 📐 System Data Flow

```mermaid

graph LR
    %% 1. Sensing Layer
    subgraph SENSOR [Node 1: Sensor]
        AIR((RF Signals)) --> ANT[Antenna]
        ANT --> SDR[RTL-SDR]
        SDR --> FEEDER[Readsb Feeder]
    end

    %% 2. Intelligence Layer
    subgraph BRAIN [Node 2: Central Brain]
        FEEDER -->|TCP Stream| AGG[Readsb Aggregator]
        AGG -->|JSON API| WD[Watchdog Script]
        
        %% Logic Flow
        subgraph LOGIC [Logic Engines]
            WD -.-> TRACK[Runway Tracker]
            WD -.-> PHYS[Physics Guard]
            WD -.-> SPOOF[Spoof Detector]
        end

        %% Actions / Outputs
        TRACK -->|Events| DB[(InfluxDB)]
        PHYS -->|Alerts| MQTT[MQTT Broker]
        SPOOF -->|Alerts| MQTT
        SPOOF -->|Metrics| DB
    end

    %% 3. Reference Layer
    subgraph REF [External Reference]
        OS[OpenSky Network (OAuth2)]
    end

    %% 4. Visualization
    OS -.->|Bearer Token| SPOOF
    DB --> DASH[Grafana Dashboard]

    %% Styling
    style SENSOR fill:#f9f9f9,stroke:#666
    style BRAIN fill:#e3f2fd,stroke:#1565c0
    style REF fill:#fff3e0,stroke:#ef6c00,stroke-dasharray: 5 5
    style DASH fill:#e8f5e9,stroke:#2e7d32
    style LOGIC fill:#ffffff,stroke:#333,stroke-dasharray: 2 2

```

---

## 🛡️ Security Modules (Watchdog 2.0)

The core logic is handled by the ```spoof-detector``` container, which runs the following checks using data ingested by the ```adsb-feeders``` service:

1.  **Runway Logic:** Detects alignment with known runways (EFHK).
2.  **Spoof Detection (Primary):** Compares local RPi4 signal position (`local\_aircraft\_state`) against OpenSky Network global position (`global\_aircraft\_state`).
    * **Threshold:** If discrepancy > 2.0 km, an alert is triggered.
3.  **Physics Guard:** Filters out synthetic data (impossible Mach numbers, vertical rates).

---

## 🗺️ Receiver Coverage

![Receiver Coverage Map](assets/coverage-map.jpg)

*Source: [PlaneFinder Receiver 235846](https://planefinder.net/coverage/receiver/235846)*

The dotted lines represent the theoretical maximum distance the receiver should be able to spot aircraft flying at 10k and 40k feet taking into account obstructions from terrain.

### 🌐 Global Validation
This sensor node contributes data to global networks, allowing us to validate our local findings against community data.

| Network | Station ID | Status |
| :--- | :--- | :--- |
| **AirNav Radar** | [EXTRPI688862](https://www.airnavradar.com/stations/EXTRPI688862) | 🟢 Active |
| **PlaneFinder** | [Receiver 235846](https://planefinder.net/coverage/receiver/235846) | 🟢 Active |
| **FlightAware** | [User: rwiren2](https://www.flightaware.com/adsb/stats/user/rwiren2) | 🟢 Active |
| **FlightRadar24** | [Feed ID: 72235](https://www.flightradar24.com/account/feed-stats/?id=72235) | 🟢 Active |

---

## 📘 Data Dictionary & System Architecture

This section defines the final data sources and storage schemas used in the Central Brain. The detailed schema is in [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

### 1. Data Sources (Inputs)
| Source | Function | Current Data Flow Status |
| :--- | :--- | :--- |
| **RPi4 Feeder (Local)** | Provides `aircraft.json` and `stats.json`. | 🟢 Stable |
| **OpenSky Network (External)** | Provides `/states/all` via OAuth2 Bearer Token. | 🟢 Stable |

### 2. Database Schema (InfluxDB)
All analytical time-series data is stored in the `readsb` database.

| Measurement Name | Data Source | Key Fields | Status |
| :--- | :--- | :--- | :--- |
| **`local\_aircraft\_state`** | RPi4 Feeder | `lat`, `lon`, `alt\_baro\_ft` | **Stable (Fixed 'ground' altitude)** |
| **`global\_aircraft\_state`** | OpenSky OAuth2 | `lat`, `lon`, `baro\_alt\_m` | **Stable (Fixed 401 Auth Error)** |
| **`local\_performance`** | RPi4 Feeder Stats | `signal\_db`, `messages` | **Stable** |

---

## 📂 Repository Structure

```text
.
├── DATA_DICTIONARY.md
├── LICENSE
├── README.md
├── adsb-feeders/          # NEW: Handles data ingestion to InfluxDB (Local & OpenSky)
│   ├── Dockerfile
│   ├── opensky_feeder.py
│   ├── readsb_feeder.py
│   └── readsb_position_feeder.py
├── assets/
├── docker-compose.yml
├── physics-guard/         # Original Logic (now integrated into spoof-detector)
├── runway-tracker/        # Original Logic (now integrated into spoof-detector)
└── spoof-detector/        # Watchdog 2.0 (Main Analyzer)
```

---

## 📚 Acknowledgements & References
* **Base Infrastructure:** [balena-ads-b by ketilmo](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file)
* **Data Validation:** [OpenSky Network Config](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file#part-6--configure-opensky-network)
* **Hardware:** [RTL-SDR.com](https://www.rtl-sdr.com/)
* **Security Research:** [Defeating ADS-B (YouTube)](https://www.youtube.com/watch?v=51zEjso9kZw)

---

## 🛠 Deployment

1.  **Set Environment Variables (.env file and Balena Dashboard):** You must define these variables for the deployment process.
    * **Variables:** `LAT`, `LON`, `INFLUX\_USER`, `INFLUX\_PASSWORD`, `GRAFANA\_PASSWORD`
    * **OAuth2 Credentials:** `OPENSKY\_CLIENT\_ID` and `OPENSKY\_CLIENT\_SECRET` (Mandatory for API access).

2.  **Deployment:** Push the current repository to your Balena application.
    ```bash
balena push central
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
