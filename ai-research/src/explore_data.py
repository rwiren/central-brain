#!/usr/bin/env python3
# ==============================================================================
# DATA EXPLORER v1.1 (Timestamp Fix)
# ==============================================================================
# Description: Generates visualizations for the ADS-B training dataset.
# Output: Saves PNG charts to 'analysis/' folder.
# ==============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import sys

# CONFIGURATION
DATASET_DIR = "datasets"
OUTPUT_DIR = "analysis"

def get_latest_dataset():
    """Finds the most recent CSV file."""
    # Check current dir and parent dir (in case running from src/)
    search_paths = [f"{DATASET_DIR}/*.csv", f"../{DATASET_DIR}/*.csv"]
    for path in search_paths:
        files = glob.glob(path)
        if files:
            return max(files, key=os.path.getctime)
    return None

def main():
    print("📊 STARTING DATA EXPLORATION...")
    
    # 1. Load Data
    csv_file = get_latest_dataset()
    if not csv_file:
        print("❌ No datasets found! Run fetch_training_data.py first.")
        sys.exit(1)

    print(f"📂 Loading: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # FIX: Use 'mixed' format to handle the specific ISO string from the CSV
    df['time'] = pd.to_datetime(df['time'], format='mixed')
    
    print(f"✅ Loaded {len(df):,} rows.")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. VISUALIZATION A: SPATIAL COVERAGE (Map)
    print("🗺️  Generating Spatial Map...")
    plt.figure(figsize=(10, 8))
    # Plot a random sample (10%) to keep the map readable and fast
    sample = df.sample(frac=0.1)
    plt.scatter(sample['lon'], sample['lat'], alpha=0.1, s=1, c='blue')
    plt.title(f"Sensor Coverage Map (10% Sample of {len(df)} points)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{OUTPUT_DIR}/01_spatial_coverage.png")
    print(f"   -> Saved to {OUTPUT_DIR}/01_spatial_coverage.png")
    plt.close()

    # 3. VISUALIZATION B: FLIGHT ENVELOPE (Alt vs Speed)
    print("✈️  Generating Flight Envelope...")
    plt.figure(figsize=(10, 6))
    sample = df.sample(frac=0.1)
    plt.scatter(sample['gs_knots'], sample['alt_baro_ft'], alpha=0.1, s=1, c='green')
    plt.title("Flight Physics Envelope (Speed vs Altitude)")
    plt.xlabel("Ground Speed (knots)")
    plt.ylabel("Altitude (feet)")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{OUTPUT_DIR}/02_flight_envelope.png")
    print(f"   -> Saved to {OUTPUT_DIR}/02_flight_envelope.png")
    plt.close()

    # 4. VISUALIZATION C: TRAFFIC DENSITY (Time)
    print("📉 Generating Traffic Histogram...")
    plt.figure(figsize=(12, 4))
    df.set_index('time').resample('1h').size().plot(kind='area', alpha=0.6)
    plt.title("Traffic Volume (Messages per Hour)")
    plt.xlabel("Time")
    plt.ylabel("Message Count")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{OUTPUT_DIR}/03_traffic_volume.png")
    print(f"   -> Saved to {OUTPUT_DIR}/03_traffic_volume.png")
    plt.close()

    print("\n✨ Exploration Complete. Open the 'analysis' folder to view charts.")

if __name__ == "__main__":
    main()
