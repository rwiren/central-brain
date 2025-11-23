# 📘 Data Dictionary & System Architecture

This document defines the final, operational data schema used by the Central Brain.

## 1. Data Sources (Operational)

### A. Local Sensor Data (The "Reality")
* **Source:** RPi4 Feeder (Direct IP access).
* **Content:** Real-time aircraft telemetry (position, speed, altitude).

### B. External Reference (The "Validation")
* **Source:** OpenSky Network API (OAuth2 Client Credentials Flow).
* **Content:** Global crowd-sourced state vectors for anomaly detection.

---

## 2. Database Schema (InfluxDB)

All time-series data is stored in the **\`readsb\`** database.

### ✈️ Measurement: \`local\_aircraft\_state\`
*Stores real-time, validated aircraft position and kinematic data from the local RPi4 sensor.*

| Field Key | Type | Description |
| :--- | :--- | :--- |
| **\`lat\`**, **\`lon\`** | Float | Aircraft Position (WGS84). |
| **\`alt\_baro\_ft\`** | Integer | Barometric Altitude (Feet). **(0 if on ground, fixed).** |
| **\`gs\_knots\`** | Float | Ground Speed (Knots). |
| **\`v\_rate\_fpm\`** | Integer | Vertical Rate (ft/min). |
| **\`track\`** | Float | True track over ground (degrees). |
| **\`origin\_data\`** | String | Source tag: \`"LocalReadsb"\`. |

### 🌍 Measurement: \`global\_aircraft\_state\`
*Stores external, global truth position data fetched via the OpenSky Network API.*

| Field Key | Type | Description |
| :--- | :--- | :--- |
| **\`lat\`**, **\`lon\`** | Float | Aircraft Position (WGS84). |
| **\`baro\_alt\_m\`** | Float | Barometric Altitude (Meters). |
| **\`gs\_mps\`** | Float | Ground Speed (Meters/sec). |
| **\`vr\_mps\`** | Float | Vertical Rate (Meters/sec). |
| **\`origin\_data\`** | String | Source tag: \`"OpenSky"\`. |

### 📊 Measurement: \`local\_performance\`
*Stores health and performance metrics for the receiver itself.*

| Field Key | Type | Description |
| :--- | :--- | :--- |
| **\`messages\`** | Integer | Messages decoded per second/interval. |
| **\`signal\_db\`** | Float | Average signal strength. |
| **\`cpu\_sec\`** | Float | CPU utilization of the decoder process. |
| **\`strong\_signals\`** | Integer | Number of strong signals processed. |

---

## 3. Alerting Data (MQTT)

Critical security events are published to the \`aviation/alerts\` topic.
