#!/usr/bin/env python3
# ==============================================================================
# CENTRAL BRAIN AI TRAINER v2.0.0
# ==============================================================================
# Author:      RW / Central Brain Project
# Description: Trains LSTM (Trajectory) and Autoencoder (Anomaly) models
#              using the latest flight telemetry dataset.
#              Optimized for Apple Silicon (M-series) GPU acceleration.
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
from tensorflow.keras.layers import LSTM, Dense, Input, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping

__version__ = "2.0.0"

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
DATASET_DIR = "datasets"
MODEL_DIR = "models"
SEQ_LEN = 10  # Lookback window (10 seconds)
EPOCHS = 20   # Training cycles (Increase for better accuracy)
BATCH_SIZE = 256 # Increased for M4 Max (Faster training)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_latest_dataset():
    """Finds the most recent CSV file in the datasets folder."""
    files = glob.glob(f"{DATASET_DIR}/*.csv")
    if not files:
        return None
    return max(files, key=os.path.getctime)

def create_sequences(data, seq_len):
    """Converts a continuous stream of data into sequences for LSTM."""
    X = []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
    return np.array(X)

def main():
    print("="*60)
    print(f"🧠 CENTRAL BRAIN AI TRAINER v{__version__}")
    print(f"⚡ TensorFlow: {tf.__version__}")
    
    # Check for GPU
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"🚀 GPU Acceleration Active: {len(gpus)} device(s) found.")
    else:
        print("⚠️  No GPU found. Training will be slow (CPU Mode).")
    print("="*60)

    # 1. Load Data
    csv_file = get_latest_dataset()
    if not csv_file:
        log("❌ No datasets found! Run fetch_training_data.py first.")
        return

    log(f"📂 Loading Dataset: {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Feature Selection (Physics & Geometry)
    features = ['lat', 'lon', 'alt_baro_ft', 'gs_knots', 'track', 'v_rate_fpm']
    data = df[features].values
    
    log(f"📊 Loaded {len(df)} rows. Features: {features}")

    # 2. Preprocessing (Normalization)
    # Neural Networks require inputs between 0 and 1
    log("🔄 Normalizing data...")
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    # Save Scaler (Critical for RPi5 Inference later)
    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    scaler_path = f"{MODEL_DIR}/scaler_v2.gz"
    joblib.dump(scaler, scaler_path)
    log(f"💾 Scaler saved to {scaler_path}")

    # 3. Sequence Generation
    log(f"🎞️  Generating Sequences (Window: {SEQ_LEN}s)...")
    X_train = create_sequences(data_scaled, SEQ_LEN)
    log(f"✅ Training Shape: {X_train.shape} (Samples, TimeSteps, Features)")

    # ----------------------------------------------------------
    # MODEL A: TRAJECTORY PREDICTOR (LSTM)
    # Goal: Predict the NEXT point (t+1) based on history (t-10...t)
    # Use Case: "Is the plane where physics says it should be?"
    # ----------------------------------------------------------
    log("\n🏋️‍♂️ TRAINING MODEL A: Trajectory Predictor (LSTM)...")
    
    # Target (Y) is the *next* point in the sequence (shifted by 1)
    # For this simplified trainer, we predict the last step of the sequence
    y_train = X_train[:, -1, :] 

    model_lstm = Sequential([
        LSTM(128, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=False),
        Dense(64, activation='relu'),
        Dense(X_train.shape[2]) # Output: 6 features (Lat, Lon, Alt...)
    ])

    model_lstm.compile(optimizer='adam', loss='mse')
    
    # Early Stopping prevents overfitting
    stopper = EarlyStopping(monitor='loss', patience=3)
    
    model_lstm.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=[stopper], verbose=1)
    
    lstm_path = f"{MODEL_DIR}/trajectory_lstm_v2.h5"
    model_lstm.save(lstm_path)
    log(f"✅ Model Saved: {lstm_path}")

    # ----------------------------------------------------------
    # MODEL B: ANOMALY DETECTOR (AUTOENCODER)
    # Goal: Compress and Decompress the flight path.
    # Use Case: "Does this flight path shape look normal?"
    # ----------------------------------------------------------
    log("\n🏋️‍♂️ TRAINING MODEL B: Anomaly Detector (Autoencoder)...")

    inputs = Input(shape=(SEQ_LEN, 6))
    # Encoder
    L1 = LSTM(64, activation='relu', return_sequences=False)(inputs)
    L2 = RepeatVector(SEQ_LEN)(L1)
    # Decoder
    L3 = LSTM(64, activation='relu', return_sequences=True)(L2)
    output = TimeDistributed(Dense(6))(L3)

    autoencoder = Model(inputs, output)
    autoencoder.compile(optimizer='adam', loss='mse')

    # Note: Autoencoder maps Input -> Input (Reconstruction)
    autoencoder.fit(X_train, X_train, epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=[stopper], verbose=1)

    ae_path = f"{MODEL_DIR}/anomaly_autoencoder_v2.h5"
    autoencoder.save(ae_path)
    log(f"✅ Model Saved: {ae_path}")

    log("\n🎉 ALL TRAINING COMPLETE.")
    log(f"📦 Deliverables ready in '{MODEL_DIR}/'")

if __name__ == "__main__":
    main()
