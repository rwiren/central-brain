[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# Secure Skies: ADS-B Integrity & Spoofing Detection

![Status](https://img.shields.io/badge/Status-Data_Ingestion-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-BalenaOS-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-yellow?style=flat-square)

**Location:** HEL-ARN Corridor (Focus: EFHK)
**Author:** RW

## 📖 Project Overview
**Business Problem:** Unencrypted ADS-B signals are vulnerable to spoofing, creating "ghost flights" and polluting data streams used for air traffic monitoring and critical safety systems.

**Goal:** Train a Sequence Model (LSTM/RNN) to predict flight anomalies by learning the physics of valid trajectories vs. synthetic spoofing attacks.

---

## 🔭 Hardware Setup
This project uses a distributed "Sensor & Brain" architecture to ensure maximum signal fidelity.

### 📡 Node 1: The Sensor (RPi 4)
* **Role:** Dedicated Signal Capture (SIGINT).
* **Hardware:** Raspberry Pi 4 + [RTL-SDR V3 Dongle](https://www.rtl-sdr.com/about-rtl-sdr/) + 1090MHz Antenna.
* **Placement:** **11th Floor** window facing Helsinki-Vantaa (EFHK).
* **Advantage:** High-altitude placement guarantees direct **Line-of-Sight (LoS)** to aircraft, resulting in high-quality, uninterrupted signal packets essential for training ML models.

### 🧠 Node 2: The Central Brain (RPi 5)
* **Role:** Compute, Logic & Storage.
* **Hardware:** Raspberry Pi 5 (16GB RAM) + 1TB NVMe + PoE + Hailo-8L AI Accelerator.
* **Advantage:** High-speed I/O allows for real-time physics calculations and database writes without dropping RF packets.

---

## 📐 System Data Flow

```mermaid
graph LR
    %% 1. Sensing Layer (RPi 4)
    subgraph SENSOR [Node 1: Forward Sensor]
        AIR((RF Signals)) --> ANT[Antenna]
        ANT --> SDR[RTL-SDR]
        SDR --> READSB[Signal Decoder]
    end

    %% 2. Intelligence Layer (RPi 5)
    subgraph BRAIN [Node 2: Central Brain]
        READSB -->|JSON Stream| TRACKER[Runway Tracker]
        READSB -->|JSON Stream| SPOOF[Spoof Detector]
        READSB -->|JSON Stream| GUARD[Physics Guard]
        
        TRACKER -->|Events| DB[(Flight DB)]
        SPOOF -->|Anomalies| DB
        GUARD -->|Alerts| DB
        
        SPOOF -.->|Trigger| ALERT[Alert System]
    end

    %% 3. Validation Layer (Cloud)
    subgraph CLOUD [External Reference]
        OPENSKY[OpenSky Network]
    end

    %% 4. Viz Layer
    OPENSKY -->|Comparison Data| SPOOF
    DB --> DASH[Grafana Dashboard]

    %% Styling
    style SENSOR fill:#f9f9f9,stroke:#666,stroke-width:2px
    style BRAIN fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style CLOUD fill:#fff3e0,stroke:#ef6c00,stroke-dasharray: 5 5
    style DASH fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style TRACKER fill:#fff,stroke:#333
    style SPOOF fill:#fff,stroke:#333
    style GUARD fill:#fff,stroke:#333
```

---

## ✈️ Runway Logic & Thresholds
The core of the data labeling engine is the **Runway Tracker**. To distinguish a "Landing" from a low-altitude flyover, we define runways as vector pairs (**Start Threshold** $\to$ **End Stop**).

**Reference:** [EFHK Aerodrome Chart (AIS Finland)](https://www.ais.fi/eaip/001-2023_2023_01_26/documents/Root_WePub/ANSFI/Charts/AD/EFHK/EF_AD_2_EFHK_MARK.pdf)

### The Python Logic
A flight is classified based on its kinematic relationship to the specific runway geometry:

1.  **Landing Detection:**
    * **Geofence:** Aircraft is < 10km from the *Start* threshold.
    * **Vector Logic:** Aircraft is closer to *Start* than *End* (approaching).
    * **Vertical Rate:** Descending (> 100 ft/min).
    * **High Confidence:** If distance < 6km, the probability of intent is near 100%.

2.  **Takeoff Detection:**
    * **Geofence:** Aircraft is between *Start* and *End* (on the strip) OR just past *End*.
    * **Vector Logic:** Distance to *End* < Distance to *Start*.
    * **Vertical Rate:** Climbing (> 100 ft/min).

---

## 🌐 Global Coverage & Validation
This sensor node contributes data to global networks, allowing us to validate our local findings against community data.

| Network | Station ID | Status |
| :--- | :--- | :--- |
| **AirNav Radar** | [EXTRPI688862](https://www.airnavradar.com/stations/EXTRPI688862) | 🟢 Active |
| **PlaneFinder** | [Receiver 235846](https://planefinder.net/coverage/receiver/235846) | 🟢 Active |
| **FlightAware** | [User: rwiren2](https://www.flightaware.com/adsb/stats/user/rwiren2) | 🟢 Active |
| **FlightRadar24** | [Feed ID: 72235](https://www.flightradar24.com/account/feed-stats/?id=72235) | 🟢 Active |

---

## 📂 Repository Structure
```text
.
├── docker-compose.yml          # Orchestration
├── physics-guard               # Logic: Detects kinematic anomalies (Impossible Velocity)
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

## 📚 Acknowledgements & References
This project builds upon open-source research and existing Balena blocks.

* **Base Infrastructure:** [balena-ads-b by ketilmo](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file) - Excellent foundation for containerized SDR.
* **Data Validation:** [OpenSky Network Config](https://github.com/ketilmo/balena-ads-b?tab=readme-ov-file#part-6--configure-opensky-network) - We utilize their API for ground-truth verification.
* **Hardware:** [RTL-SDR.com](https://www.rtl-sdr.com/) - The standard for low-cost radio analysis.
* **Security Research:** [Defeating ADS-B (YouTube)](https://www.youtube.com/watch?v=51zEjso9kZw)

---

## 🛠 Deployment
```bash
balena push <app-name>
```
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
