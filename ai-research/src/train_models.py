#!/usr/bin/env python3
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
import glob
import os
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Input, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping

# === PATH CONFIGURATION ===
# Get path to 'ai-research' folder (parent of 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")

SEQ_LEN = 10
EPOCHS = 20
BATCH_SIZE = 256

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
    print(f"🧠 CENTRAL BRAIN TRAINER (Relative Paths)")
    print(f"📂 Root: {PROJECT_ROOT}")
    print(f"🆔 Run ID: {run_id}")
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

    stopper = EarlyStopping(monitor='loss', patience=3)

    # --- MODEL A ---
    log("🏋️‍♂️ Training Model A (LSTM)...")
    model_a = Sequential([
        LSTM(128, input_shape=(10, 6), return_sequences=False),
        Dense(64, activation='relu'),
        Dense(6)
    ])
    model_a.compile(optimizer='adam', loss='mse')
    model_a.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=[stopper], verbose=1)
    model_a.save(f"{MODEL_DIR}/trajectory_lstm_v2_{run_id}.h5")

    # --- MODEL B ---
    log("🏋️‍♂️ Training Model B (Autoencoder)...")
    inputs = Input(shape=(10, 6))
    encoded = LSTM(64, activation='relu', return_sequences=False)(inputs)
    decoded = RepeatVector(10)(encoded)
    decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
    output = TimeDistributed(Dense(6))(decoded)
    
    model_b = Model(inputs, output)
    model_b.compile(optimizer='adam', loss='mse')
    model_b.fit(X_train, X_train, epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=[stopper], verbose=1)
    model_b.save(f"{MODEL_DIR}/anomaly_autoencoder_v2_{run_id}.h5")

    log(f"✅ Done. Total time: {datetime.now() - total_start}")

if __name__ == "__main__":
    main()

