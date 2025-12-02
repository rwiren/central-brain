#!/usr/bin/env python3
# ==============================================================================
# CENTRAL BRAIN AI EVALUATOR v1.4.0
# ==============================================================================
# Description:  Evaluates models and generates visual performance reports.
#               Now includes DIRECT COMPARISON between LSTM and Autoencoder.
# ==============================================================================

import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
import glob
import os
import re
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error

# === PATH CONFIGURATION ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
EVAL_DIR = os.path.join(PROJECT_ROOT, "evaluations")

if not os.path.exists(EVAL_DIR):
    os.makedirs(EVAL_DIR)

SEQ_LEN = 10
TEST_SPLIT = 0.2
FEATURE_NAMES = ['lat', 'lon', 'alt_baro_ft', 'gs_knots', 'track', 'v_rate_fpm']

def get_latest_dataset():
    files = glob.glob(f"{DATASET_DIR}/*.csv")
    return max(files, key=os.path.getctime) if files else None

def get_run_ids():
    ids = []
    files = glob.glob(f"{MODEL_DIR}/scaler_v2_*.gz")
    for f in files:
        match = re.search(r"scaler_v2_(.*)\.gz", f)
        if match: ids.append(match.group(1))
    if os.path.exists(os.path.join(MODEL_DIR, "scaler_v2.gz")):
        ids.append("LEGACY")
    return sorted(ids)

def create_sequences(data, seq_len):
    X = []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
    return np.array(X)

# --- INDIVIDUAL PLOTS ---
def plot_lstm_performance(y_true, y_pred, run_id, scaler):
    y_true_inv = scaler.inverse_transform(y_true)
    y_pred_inv = scaler.inverse_transform(y_pred)

    plt.figure(figsize=(10, 6))
    limit = 500 
    plt.plot(y_true_inv[:limit, 1], y_true_inv[:limit, 0], 'b-', label='Actual Path', alpha=0.6)
    plt.plot(y_pred_inv[:limit, 1], y_pred_inv[:limit, 0], 'r--', label='LSTM Prediction', alpha=0.8)
    plt.title(f"LSTM Trajectory Prediction (Run: {run_id})")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{EVAL_DIR}/lstm_trajectory_{run_id}.png")
    plt.close()

def plot_autoencoder_performance(y_true, y_pred, run_id):
    mae_per_sample = np.mean(np.abs(y_true - y_pred), axis=(1, 2))

    plt.figure(figsize=(10, 6))
    plt.hist(mae_per_sample, bins=50, color='purple', alpha=0.7, label='Reconstruction Error')
    threshold = np.percentile(mae_per_sample, 95)
    plt.axvline(threshold, color='red', linestyle='dashed', linewidth=2, label=f'95% Threshold')
    plt.title(f"Autoencoder Anomaly Distribution (Run: {run_id})")
    plt.xlabel("Error (MAE)")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{EVAL_DIR}/autoencoder_distribution_{run_id}.png")
    plt.close()

# --- COMPARISON PLOT ---
def plot_model_comparison(y_true, pred_lstm, pred_ae, run_id, scaler):
    """
    Overlays Actual vs LSTM Prediction vs Autoencoder Reconstruction
    for Altitude and Speed.
    """
    # Inverse transform all 3
    y_true_inv = scaler.inverse_transform(y_true)
    pred_lstm_inv = scaler.inverse_transform(pred_lstm)
    pred_ae_inv = scaler.inverse_transform(pred_ae)

    # We look at the first 200 steps for clarity
    limit = 200
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Altitude Comparison (Index 2)
    ax1.plot(y_true_inv[:limit, 2], 'k-', linewidth=2, label='Actual (Physics)')
    ax1.plot(pred_lstm_inv[:limit, 2], 'r--', label='LSTM (Future Prediction)')
    ax1.plot(pred_ae_inv[:limit, 2], 'g:', linewidth=2, label='Autoencoder (Reconstruction)')
    ax1.set_title(f"Model Battle: Altitude (Feet) - {run_id}")
    ax1.set_ylabel("Altitude (ft)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Ground Speed Comparison (Index 3)
    ax2.plot(y_true_inv[:limit, 3], 'k-', linewidth=2, label='Actual')
    ax2.plot(pred_lstm_inv[:limit, 3], 'r--', label='LSTM')
    ax2.plot(pred_ae_inv[:limit, 3], 'g:', linewidth=2, label='Autoencoder')
    ax2.set_title(f"Model Battle: Ground Speed (Knots) - {run_id}")
    ax2.set_ylabel("Speed (knots)")
    ax2.set_xlabel("Time Steps")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    path = f"{EVAL_DIR}/comparison_models_{run_id}.png"
    plt.savefig(path)
    plt.close()
    return path

def main():
    print(f"📊 EVALUATOR v1.4 | Root: {PROJECT_ROOT}")
    
    csv_file = get_latest_dataset()
    if not csv_file: return print("❌ No data found.")
    
    print(f"📂 Loading Data: {os.path.basename(csv_file)}")
    df = pd.read_csv(csv_file)
    data = df[FEATURE_NAMES].values
    
    run_ids = get_run_ids()
    if not run_ids: return print("❌ No models found.")

    for run_id in run_ids:
        print(f"\n🆔 RUN: {run_id}")
        
        # Define Paths
        if run_id == "LEGACY":
            s_p = f"{MODEL_DIR}/scaler_v2.gz"
            l_p = f"{MODEL_DIR}/trajectory_lstm_v2.h5"
            a_p = f"{MODEL_DIR}/anomaly_autoencoder_v2.h5"
        else:
            s_p = f"{MODEL_DIR}/scaler_v2_{run_id}.gz"
            l_p = f"{MODEL_DIR}/trajectory_lstm_v2_{run_id}.h5"
            a_p = f"{MODEL_DIR}/anomaly_autoencoder_v2_{run_id}.h5"

        if not os.path.exists(s_p): continue

        # Prepare Data
        scaler = joblib.load(s_p)
        data_scaled = scaler.transform(data)
        X_all = create_sequences(data_scaled, SEQ_LEN)
        X_test = X_all[int(len(X_all) * (1 - TEST_SPLIT)):]
        
        # Prepare Variables for Comparison
        pred_lstm = None
        pred_ae_reconstructed = None
        
        # 1. Run LSTM
        if os.path.exists(l_p):
            try:
                model_a = tf.keras.models.load_model(l_p, compile=False)
                pred_lstm = model_a.predict(X_test, verbose=0)
                plot_lstm_performance(X_test[:, -1, :], pred_lstm, run_id, scaler)
                print("      ✅ LSTM Evaluated")
            except Exception as e: print(f"      ❌ LSTM Error: {e}")

        # 2. Run Autoencoder
        if os.path.exists(a_p):
            try:
                model_b = tf.keras.models.load_model(a_p, compile=False)
                pred_ae = model_b.predict(X_test, verbose=0)
                plot_autoencoder_performance(X_test, pred_ae, run_id)
                
                # Extract the LAST step of reconstruction to compare with LSTM
                pred_ae_reconstructed = pred_ae[:, -1, :]
                print("      ✅ Autoencoder Evaluated")
            except Exception as e: print(f"      ❌ AE Error: {e}")

        # 3. Generate Comparison (If both exist)
        if pred_lstm is not None and pred_ae_reconstructed is not None:
            f_comp = plot_model_comparison(X_test[:, -1, :], pred_lstm, pred_ae_reconstructed, run_id, scaler)
            print(f"      ⚔️  Comparison Plot Saved: {os.path.basename(f_comp)}")

if __name__ == "__main__":
    main()

