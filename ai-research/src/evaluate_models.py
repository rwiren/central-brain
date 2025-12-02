#!/usr/bin/env python3
# ==============================================================================
# CENTRAL BRAIN AI EVALUATOR v1.5.0
# ==============================================================================
# Updates:
# - Added MODEL C: GRU Evaluation
# - Added "Architecture Battle" (LSTM vs GRU) comparison
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

def evaluate(y_true, y_pred, name):
    mse = mean_squared_error(y_true.flatten(), y_pred.flatten())
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true.flatten(), y_pred.flatten())
    print(f"   🔹 {name.ljust(12)} -> MSE: {mse:.6f} | RMSE: {rmse:.6f} | MAE: {mae:.6f}")
    return mse

# --- PLOTTING FUNCTIONS ---

def plot_autoencoder_performance(y_true, y_pred, run_id):
    mae_per_sample = np.mean(np.abs(y_true - y_pred), axis=(1, 2))
    plt.figure(figsize=(10, 6))
    plt.hist(mae_per_sample, bins=50, color='purple', alpha=0.7, label='Reconstruction Error')
    threshold = np.percentile(mae_per_sample, 95)
    plt.axvline(threshold, color='red', linestyle='dashed', linewidth=2, label=f'95% Threshold')
    plt.title(f"Autoencoder Anomaly Distribution (Run: {run_id})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{EVAL_DIR}/autoencoder_distribution_{run_id}.png")
    plt.close()

def plot_architecture_battle(y_true, pred_lstm, pred_gru, run_id, scaler):
    """
    Compares LSTM vs GRU vs Reality.
    This decides which model goes to the Raspberry Pi.
    """
    y_true_inv = scaler.inverse_transform(y_true)
    pred_lstm_inv = scaler.inverse_transform(pred_lstm)
    pred_gru_inv = scaler.inverse_transform(pred_gru)
    
    limit = 200 # Zoom in

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # 1. Altitude
    ax1.plot(y_true_inv[:limit, 2], 'k-', linewidth=2, label='Actual')
    ax1.plot(pred_lstm_inv[:limit, 2], 'r--', label='LSTM (Big Model)')
    ax1.plot(pred_gru_inv[:limit, 2], 'b:', linewidth=2, label='GRU (RPi Model)')
    ax1.set_title(f"Architecture Battle: Altitude (LSTM vs GRU) - {run_id}")
    ax1.set_ylabel("Altitude (ft)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Speed
    ax2.plot(y_true_inv[:limit, 3], 'k-', linewidth=2, label='Actual')
    ax2.plot(pred_lstm_inv[:limit, 3], 'r--', label='LSTM')
    ax2.plot(pred_gru_inv[:limit, 3], 'b:', linewidth=2, label='GRU')
    ax2.set_title(f"Architecture Battle: Speed (LSTM vs GRU) - {run_id}")
    ax2.set_ylabel("Speed (knots)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    path = f"{EVAL_DIR}/battle_lstm_vs_gru_{run_id}.png"
    plt.savefig(path)
    plt.close()
    return path

def main():
    print(f"📊 EVALUATOR v1.5 | Root: {PROJECT_ROOT}")
    
    csv_file = get_latest_dataset()
    if not csv_file: return print("❌ No data found.")
    
    df = pd.read_csv(csv_file)
    data = df[FEATURE_NAMES].values
    
    run_ids = get_run_ids()
    if not run_ids: return print("❌ No models found.")

    for run_id in run_ids:
        print(f"\n🆔 RUN: {run_id}")
        
        # Paths
        suffix = "" if run_id == "LEGACY" else f"_{run_id}"
        s_p = f"{MODEL_DIR}/scaler_v2{suffix}.gz"
        l_p = f"{MODEL_DIR}/trajectory_lstm_v2{suffix}.h5"
        a_p = f"{MODEL_DIR}/anomaly_autoencoder_v2{suffix}.h5"
        g_p = f"{MODEL_DIR}/trajectory_gru_v2{suffix}.h5" # NEW

        if not os.path.exists(s_p): continue

        scaler = joblib.load(s_p)
        data_scaled = scaler.transform(data)
        X_all = create_sequences(data_scaled, SEQ_LEN)
        X_test = X_all[int(len(X_all) * (1 - TEST_SPLIT)):]
        
        # Hold predictions for comparison
        pred_lstm = None
        pred_gru = None

        # 1. Evaluate LSTM
        if os.path.exists(l_p):
            try:
                model = tf.keras.models.load_model(l_p, compile=False)
                pred_lstm = model.predict(X_test, verbose=0)
                evaluate(X_test[:, -1, :], pred_lstm, "LSTM")
            except: pass

        # 2. Evaluate GRU (NEW)
        if os.path.exists(g_p):
            try:
                model = tf.keras.models.load_model(g_p, compile=False)
                pred_gru = model.predict(X_test, verbose=0)
                evaluate(X_test[:, -1, :], pred_gru, "GRU")
            except Exception as e: print(f"   ❌ GRU Error: {e}")

        # 3. Evaluate Autoencoder
        if os.path.exists(a_p):
            try:
                model = tf.keras.models.load_model(a_p, compile=False)
                pred_ae = model.predict(X_test, verbose=0)
                evaluate(X_test, pred_ae, "Autoencoder")
                plot_autoencoder_performance(X_test, pred_ae, run_id)
            except: pass

        # 4. Visual Battle (LSTM vs GRU)
        if pred_lstm is not None and pred_gru is not None:
            f_battle = plot_architecture_battle(X_test[:, -1, :], pred_lstm, pred_gru, run_id, scaler)
            print(f"      ⚔️  Architecture Battle Saved: {os.path.basename(f_battle)}")

if __name__ == "__main__":
    main()

