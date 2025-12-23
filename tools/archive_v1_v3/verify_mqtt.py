#!/usr/bin/env python3
"""
Script: verify_mqtt.py
Version: 1.1.0 (Paho 2.x Support)
Description: Simple MQTT Pub/Sub test compatible with new Paho library.
"""
import sys
import time
import random
try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    print("❌ Missing library. Run: pip install paho-mqtt")
    sys.exit(1)

# --- CONFIGURATION ---
BROKER = "192.168.1.134"  # Central Brain IP
PORT = 1883
TOPIC = "test/ping"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    print(f"📩 Received: {msg.payload.decode()} on {msg.topic}")
    client.disconnect()

def main():
    client_id = f"tester-{random.randint(0, 1000)}"
    
    # FIX: Explicitly use VERSION2 for Paho 2.x compatibility
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id)
    
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔌 Connecting to {BROKER}:{PORT}...")
    try:
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("   (Is the broker running and listening on 0.0.0.0?)")
        return

    # Start loop in background
    client.loop_start()
    
    # Wait for connection
    time.sleep(1)
    
    # Publish
    msg = f"Hello from Python! Time: {time.time()}"
    print(f"📤 Publishing: {msg}")
    client.publish(TOPIC, msg)
    
    # Wait for receipt
    time.sleep(2)
    client.loop_stop()

if __name__ == "__main__":
    main()
