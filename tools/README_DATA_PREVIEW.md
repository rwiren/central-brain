# Secure Skies: Data Preview Package (v1)

**Generated:** 2025-12-18 20:01
**Author:** RW (Lead Solution Architect)
**Project:** ADS-B Integrity & Spoofing Detection (HEL-ARN Corridor)

---

## 1. Executive Summary
This package provides a **"Small Data Preview"** for the AI Neural Networks Cohort. 
It represents a snapshot of the "Secure Skies" ingestion pipeline (Central Brain RPi5) covering the **"Golden Week" (Nov 26 – Dec 03, 2025)**.

**Objective:** Use this data to prototype the *Sequence Modeling (GRU/LSTM)* and *Anomaly Detection* modules defined in the Use Case Matrix.

---

## 2. Package Contents

### A. The Training Data (Processed CSVs)
Cleaned time-series data ready for Pandas/TensorFlow ingestion.

* **`secure_skies_local_v2.csv` (Input Features / X)**
    * *Source:* Local Raspberry Pi 5 (RTL-SDR).
    * *Volume:* ~160,000 flight updates.
    * *Columns:* `Timestamp`, `ICAO24`, `Latitude`, `Longitude`, `Baro_Altitude`, `Velocity`, `Heading`, `Vertical_Rate`.
    * *Note:* Contains the raw physics input for the model.

* **`secure_skies_global_v2.csv` (Ground Truth / Y)**
    * *Source:* OpenSky Network Historical DB.
    * *Usage:* Use this to verify the local sensor's accuracy and detect location spoofing ("Teleportation" events).

* **`secure_skies_alerts_v2.csv` (Labels)**
    * *Content:* 59 confirmed anomaly events (Physics/Security alerts) during this window.

### B. The Evidence (Raw & Visual)
* **`raw_dump_2025-11-30.lp`**: A single-day raw database dump (InfluxDB Line Protocol). Use this to see exactly what the sensor "sees" before any cleaning.
* **`physics_profile_2025-11-30.png`**: A visualization of the "Flight Envelope" (Speed vs Altitude). It proves we have valid clusters of taxiing, climbing, and cruising aircraft—plus some high-altitude 
anomalies.

### C. The Tools
* **`extract_csv_from_dump_v4.py`**: The script used to generate these CSVs. Included for transparency and reproducibility.

---

## 3. Data Maturity & Improvement Notes
* **Preview Status:** This is a preliminary dataset. While sufficient for training level 4 AI models, it is not yet "Production Grade."
* **Synchronization:** Timestamps are synchronized via GNSS/NTP, but minor jitter (<1s) may exist between Local and Global streams. We can refine this collection process in future iterations if precision 
requirements increase.
* **Signal Metrics:** The `Signal_Strength` field is sparsely populated in the CSVs due to early parser configurations. Raw signal data exists in the `.lp` logs if you wish to engineer RSSI features.
* **The "Antenna Event":** On **Dec 03**, the sensor was moved outdoors. You may observe a step-change in data density and message integrity. This is a known "Intervention," not a spoofing anomaly.

---

**Happy Coding!**
