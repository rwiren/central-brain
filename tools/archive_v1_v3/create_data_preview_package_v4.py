#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Secure Skies - Data Package Manager
Script: create_data_preview_package_v4.py
Description: Final assembly tool for the AI Cohort "Data Preview".
             1. Auto-generates a context-aware README with specific notes on 
                data maturity and future improvements.
             2. Bundles the existing CSVs, Raw Dumps, and Visualization into a 
                single distributable zip file.
             3. Includes the extraction utility so the team can verify the process.

Version: 4.0.0
Author: RW (Lead Solution Architect)
Date: 2025-12-18
"""

import sys
import os
import datetime
import zipfile

# ================= Configuration =================
OUTPUT_ZIP = 'Secure_Skies_Data_Preview_v1.zip'

# Files to include (Must exist in the current folder)
REQUIRED_FILES = [
    'secure_skies_local_v2.csv',
    'secure_skies_global_v2.csv',
    'secure_skies_alerts_v2.csv',
    'raw_dump_2025-11-30.lp',
    'physics_profile_2025-11-30.png',
    'extract_csv_from_dump_v4.py'
]

# ================= Helper Functions =================

def generate_readme():
    """
    Creates the README.md with specific "Preview" language and improvement notes.
    """
    content = f"""# Secure Skies: Data Preview Package (v1)

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
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
"""
    with open('README_DATA_PREVIEW.md', 'w') as f:
        f.write(content)
    print("[INFO] Generated README_DATA_PREVIEW.md")

# ================= Main Execution =================

def main():
    print("="*60)
    print(f" SECURE SKIES: PACKAGE ASSEMBLER (v4.0)")
    print("="*60)

    # 1. Check for files
    print("[STEP 1] Verifying Files...")
    missing = []
    for f_name in REQUIRED_FILES:
        if os.path.exists(f_name):
            print(f"  [OK] Found {f_name}")
        else:
            print(f"  [FAIL] Missing {f_name}")
            missing.append(f_name)
    
    if missing:
        print(f"\n[ERROR] Cannot build package. Missing {len(missing)} files.")
        print("Please ensure all CSVs, LP dumps, and PNGs are in this folder.")
        sys.exit(1)

    # 2. Generate README
    print("\n[STEP 2] Generating Documentation...")
    generate_readme()
    REQUIRED_FILES.append('README_DATA_PREVIEW.md')

    # 3. Create Zip
    print(f"\n[STEP 3] Zipping Package: {OUTPUT_ZIP}...")
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f_name in REQUIRED_FILES:
            print(f"  > Archiving {f_name}...")
            zipf.write(f_name)

    print(f"\n[SUCCESS] Package Ready: {OUTPUT_ZIP}")
    print("Action: Distribute this file to the AI Cohort.")

if __name__ == "__main__":
    main()
