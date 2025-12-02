#!/usr/bin/env python3
# ==============================================================================
# CENTRAL BRAIN AI TRAINER v2.3.0
# ==============================================================================
# Updates:
# - Added Validation Split (0.2)
# - Increased Batch Size (1024) for M4 Max
# - Added MODEL C: GRU (Optimized for RPi5)
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
from tensorflow.keras.callbacks import EarlyStopping

# === PATH CONFIGURATION ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")

# === HYPERPARAMETERS ===
SEQ_LEN = 10
EPOCHS = 30        
BATCH_SIZE = 1024  

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
    print(f"🧠 CENTRAL BRAIN TRAINER v2.3 (Multi-Model)")
    print(f"📂 Root: {PROJECT_ROOT}")
    print(f"🆔 Run ID: {run_id}")
    print(f"⚙️  Config: Epochs={EPOCHS} | Batch={BATCH_SIZE}")
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

    stopper = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

    # --- MODEL A: LSTM (The Heavyweight) ---
    log("🏋️‍♂️ Training Model A (LSTM)...")
    model_a = Sequential([
        Input(shape=(SEQ_LEN, 6)),
        LSTM(128, return_sequences=False),
        Dense(64, activation='relu'),
        Dense(6)
    ])
    model_a.compile(optimizer='adam', loss='mse')
    model_a.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=[stopper], verbose=1)
    model_a.save(f"{MODEL_DIR}/trajectory_lstm_v2_{run_id}.h5")

    # --- MODEL B: AUTOENCODER (The Anomaly Detector) ---
    log("\n🏋️‍♂️ Training Model B (Autoencoder)...")
    inputs = Input(shape=(SEQ_LEN, 6))
    encoded = LSTM(64, activation='relu', return_sequences=False)(inputs)
    decoded = RepeatVector(SEQ_LEN)(encoded)
    decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
    output = TimeDistributed(Dense(6))(decoded)
    
    model_b = Model(inputs, output)
    model_b.compile(optimizer='adam', loss='mse')
    model_b.fit(X_train, X_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=[stopper], verbose=1)
    model_b.save(f"{MODEL_DIR}/anomaly_autoencoder_v2_{run_id}.h5")

    # --- MODEL C: GRU (The Lightweight Alternative) ---
    log("\n🏋️‍♂️ Training Model C (GRU - RPi Optimized)...")
    model_c = Sequential([
        Input(shape=(SEQ_LEN, 6)),
        GRU(128, return_sequences=False), # GRU instead of LSTM
        Dense(64, activation='relu'),
        Dense(6)
    ])
    model_c.compile(optimizer='adam', loss='mse')
    model_c.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, callbacks=[stopper], verbose=1)
    model_c.save(f"{MODEL_DIR}/trajectory_gru_v2_{run_id}.h5")

    log(f"✅ All Models Trained. Time: {datetime.now() - total_start}")

if __name__ == "__main__":
    main()

