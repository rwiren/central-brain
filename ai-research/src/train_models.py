#!/usr/bin/env python3
# ==============================================================================
# CENTRAL BRAIN AI TRAINER v3.0.0 (Overnight Deep Learning)
# ==============================================================================
# Configuration:
# - EPOCHS: 2000 (Deep Convergence)
# - PATIENCE: 50 (Allow for long plateaus)
# - BATCH: 4096 (Max Saturation for Apple Silicon)
# ==============================================================================

import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
import glob
import os
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, GRU, Dense, Input, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# === PATH CONFIGURATION ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")

# === OVERNIGHT HYPERPARAMETERS ===
SEQ_LEN = 10
EPOCHS = 2000      # Let it run as long as it needs
BATCH_SIZE = 4096  # Maximize M4 Max throughput
PATIENCE = 50      # Don't give up easily

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_latest_dataset():
    files = glob.glob(f"{DATASET_DIR}/*.csv")
    if not files: return None
    return max(files, key=os.path.getctime)

def create_sequences(data, seq_len):
    X = []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
    return np.array(X)

def main():
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    total_start = datetime.now()

    print("="*60)
    print(f"🧠 CENTRAL BRAIN TRAINER v3.0 (Overnight Edition)")
    print(f"🌙 Strategy: Deep Convergence")
    print(f"🆔 Run ID: {run_id}")
    print(f"⚙️  Config: Epochs={EPOCHS} | Patience={PATIENCE} | Batch={BATCH_SIZE}")
    print("="*60)

    csv_file = get_latest_dataset()
    if not csv_file:
        log(f"❌ No datasets found in {DATASET_DIR}")
        return

    log(f"📂 Loading: {os.path.basename(csv_file)}")
    df = pd.read_csv(csv_file)
    
    features = ['lat', 'lon', 'alt_baro_ft', 'gs_knots', 'track', 'v_rate_fpm']
    data = df[features].values

    log("🔄 Normalizing...")
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    joblib.dump(scaler, f"{MODEL_DIR}/scaler_v2_{run_id}.gz")

    log("🎞️  Sequencing...")
    X_train = create_sequences(data_scaled, SEQ_LEN)
    y_train = X_train[:, -1, :] 

    # 1. Stop if no improvement for 50 epochs
    stopper = EarlyStopping(monitor='val_loss', patience=PATIENCE, restore_best_weights=True, verbose=1)
    
    # 2. If stuck, lower the learning rate to find the absolute bottom of the curve
    reducer = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=0.000001, verbose=1)

    callbacks_list = [stopper, reducer]
    rmse_metric = tf.keras.metrics.RootMeanSquaredError()

    # --- MODEL A: LSTM ---
    log("🏋️‍♂️ Training Model A (LSTM)...")
    model_a = Sequential([
        Input(shape=(SEQ_LEN, 6)),
        LSTM(128, return_sequences=False),
        Dense(128, activation='relu'), # Added extra layer depth
        Dense(64, activation='relu'),
        Dense(6)
    ])
    model_a.compile(optimizer='adam', loss='mse', metrics=['mae', rmse_metric])
    model_a.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=callbacks_list, verbose=1)
    model_a.save(f"{MODEL_DIR}/trajectory_lstm_v2_{run_id}.h5")

    # --- MODEL B: AUTOENCODER ---
    log("\n🏋️‍♂️ Training Model B (Autoencoder)...")
    inputs = Input(shape=(SEQ_LEN, 6))
    encoded = LSTM(128, activation='relu', return_sequences=False)(inputs) # Increased Width
    decoded = RepeatVector(SEQ_LEN)(encoded)
    decoded = LSTM(128, activation='relu', return_sequences=True)(decoded) # Increased Width
    output = TimeDistributed(Dense(6))(decoded)
    
    model_b = Model(inputs, output)
    model_b.compile(optimizer='adam', loss='mse', metrics=['mae', rmse_metric])
    model_b.fit(X_train, X_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=callbacks_list, verbose=1)
    model_b.save(f"{MODEL_DIR}/anomaly_autoencoder_v2_{run_id}.h5")

    # --- MODEL C: GRU (The Champion) ---
    log("\n🏋️‍♂️ Training Model C (GRU - Deep Training)...")
    model_c = Sequential([
        Input(shape=(SEQ_LEN, 6)),
        GRU(128, return_sequences=False), 
        Dense(128, activation='relu'), # Added extra layer depth
        Dense(64, activation='relu'),
        Dense(6)
    ])
    model_c.compile(optimizer='adam', loss='mse', metrics=['mae', rmse_metric])
    model_c.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=callbacks_list, verbose=1)
    model_c.save(f"{MODEL_DIR}/trajectory_gru_v2_{run_id}.h5")

    log(f"✅ Overnight Training Complete. Total time: {datetime.now() - total_start}")

if __name__ == "__main__":
    main()

