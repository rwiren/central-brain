#!/usr/bin/env python3
# ==============================================================================
# DATA EXPLORER v2.0 (Deep Audit)
# ==============================================================================
# Description: Advanced statistical analysis and visualization for ADS-B data.
# Output: 'analysis/data_quality_report.txt' and advanced PNG charts.
# ==============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import sys

# CONFIGURATION
DATASET_DIR = "datasets"
OUTPUT_DIR = "analysis"

def get_latest_dataset():
    search_paths = [f"{DATASET_DIR}/*.csv", f"../{DATASET_DIR}/*.csv"]
    for path in search_paths:
        files = glob.glob(path)
        if files:
            return max(files, key=os.path.getctime)
    return None

def main():
    print("📊 STARTING DEEP DATA AUDIT...")
    
    # 1. Load Data
    csv_file = get_latest_dataset()
    if not csv_file:
        print("❌ No datasets found!")
        sys.exit(1)

    print(f"📂 Loading: {csv_file}")
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'], format='mixed')
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. GENERATE TEXT REPORT
    report_path = f"{OUTPUT_DIR}/data_quality_report.txt"
    with open(report_path, "w") as f:
        f.write(f"DATA QUALITY REPORT\n")
        f.write(f"===================\n")
        f.write(f"File: {csv_file}\n")
        f.write(f"Total Rows: {len(df):,}\n")
        f.write(f"Unique Aircraft (ICAO): {df['icao'].nunique()}\n")
        f.write(f"Time Range: {df['time'].min()} to {df['time'].max()}\n\n")
        
        f.write("MISSING DATA (Null Counts):\n")
        f.write(df.isnull().sum().to_string())
        f.write("\n\n")
        
        f.write("STATISTICS (Numerical):\n")
        f.write(df.describe().to_string())
    
    print(f"✅ Generated text report: {report_path}")

    # 3. VISUALIZATION: MISSING DATA HEATMAP
    # This shows if gaps happen randomly or in chunks (system outages)
    print("🧩 Generating Missing Data Heatmap...")
    plt.figure(figsize=(12, 6))
    # We sample 10000 rows to keep it fast/readable
    sns.heatmap(df.sample(n=min(10000, len(df))).isnull(), cbar=False, yticklabels=False, cmap='viridis')
    plt.title("Missing Data Patterns (Sample)")
    plt.savefig(f"{OUTPUT_DIR}/04_missing_data_heatmap.png")
    plt.close()

    # 4. VISUALIZATION: CORRELATION MATRIX
    # Do physics make sense? (e.g. Altitude vs Speed)
    print("🔗 Generating Correlation Matrix...")
    plt.figure(figsize=(10, 8))
    # Select only numeric columns for correlation
    numeric_df = df[['alt_baro_ft', 'gs_knots', 'track', 'v_rate_fpm']]
    corr = numeric_df.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Feature Correlation Matrix")
    plt.savefig(f"{OUTPUT_DIR}/05_correlation_matrix.png")
    plt.close()

    # 5. VISUALIZATION: SINGLE FLIGHT TRAJECTORY
    # Pick the aircraft with the most data points to visualize a "perfect" track
    print("✈️  Generating Trajectory Sample...")
    top_icao = df['icao'].value_counts().idxmax()
    flight = df[df['icao'] == top_icao].sort_values('time')
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Altitude (ft)', color=color)
    ax1.plot(flight['time'], flight['alt_baro_ft'], color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis
    color = 'tab:red'
    ax2.set_ylabel('Speed (kts)', color=color)
    ax2.plot(flight['time'], flight['gs_knots'], color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f"Single Flight Profile: {top_icao}")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/06_single_trajectory.png")
    plt.close()

    print("\n✨ Advanced Exploration Complete.")

if __name__ == "__main__":
    main()
