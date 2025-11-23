# Secure Skies: ADS-B Integrity & Spoofing Detection

![Status](https://img.shields.io/badge/Status-Active_Monitoring-green?style=flat-square)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
![Platform](https://img.shields.io/badge/Platform-BalenaOS-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-yellow?style=flat-square)
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

### 📡 Node 1: The Sensor (RPi 4 @ 192.168.1.152)
* **Role:** Dedicated Signal Capture and JSON Server.
* **Hardware:** Raspberry Pi 4 + [RTL-SDR V3 Dongle](https://www.rtl-sdr.com/about-rtl-sdr/) + 1090MHz Antenna.
* **Placement:** **11th Floor** window facing Helsinki-Vantaa (EFHK).
* **Function:** Decodes raw 1090MHz RF signals, generates the `aircraft.json` web data, and serves the data over the network.

### 🧠 Node 2: The Central Brain (RPi 5)
* **Role:** Aggregation, Logic, Analytics & OAuth2 Handler.
* **Hardware:** Raspberry Pi 5 (16GB RAM) + 1TB NVMe.
* **Function:**
    * Ingests Beast stream from Node 1 (via RPi5's `readsb` service).
    * Runs **Watchdog 2.0** (Anomaly Detection).
    * Hosts InfluxDB (Time-series data) and Grafana (Visualization).
    * **OAuth2 Integration:** Implements the OAuth2 Client Credentials Flow to reliably fetch global truth data from OpenSky.

---

## 📐 System Data Flow (Operational Architecture)

The final architecture uses the RPi4 as the stable JSON source and implements the mandatory **OAuth2 Client Credentials Flow** for OpenSky.

| Data Stream | Source | Target Database/Service | Status |
| :--- | :--- | :--- | :--- |
| **Local Aircraft Position** | `http://192.168.1.152:8080/data/aircraft.json` | InfluxDB (`local_aircraft_state`) | 🟢 **Stable** |
| **Local Receiver Stats** | `http://192.168.1.152:8080/data/stats.json` | InfluxDB (`local_performance`) | 🟢 **Stable** |
| **Global Truth Data** | OpenSky OAuth2 API | InfluxDB (`global_aircraft_state`) | 🟢 **Stable (Token Flow)** |

---

## 🛡️ Security Modules (Watchdog 2.0)

The core logic is handled by the `spoof-detector` container, which compares local kinematic data against the global truth stream.

1.  **Go-Around/Physics:** Continuously monitors local data for sudden, impossible shifts in altitude and vertical rate.
2.  **Spoof Detection:** Compares the `local\_aircraft\_state` position against the `global\_aircraft\_state` position (both filtered by ICAO24 address).
    * **Threshold:** If the physical distance between the two sources exceeds 2.0 km, an alert is triggered.

---

## 📘 Data Dictionary & Schema

The definitive, current database schema is defined in [DATA_DICTIONARY.md](DATA_DICTIONARY.md). The three primary time-series measurements written by the `adsb-feeders` service are: `local\_performance`, `local\_aircraft\_state`, and `global\_aircraft\_state`.

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

## 🛠 Deployment

1.  **Set Environment Variables (.env file and Balena Dashboard):** You must define these variables for the deployment process.
    * `LAT`, `LON`, `INFLUX\_USER`, `INFLUX\_PASSWORD`, `GRAFANA\_PASSWORD`
    * **OAuth2 Credentials:** `OPENSKY\_CLIENT\_ID` and `OPENSKY\_CLIENT\_SECRET` (Mandatory for API access).

2.  **Deployment:** Push the current repository to your Balena application.
    ```bash
balena push central
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
