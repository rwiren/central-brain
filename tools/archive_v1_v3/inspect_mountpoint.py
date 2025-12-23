import socket

# Target
CASTER = "rtk2go.com"
PORT = 2101
TARGET_MOUNT = "Lintuvaara"  # We know this one connects!

def decode_messages(msg_string):
    """Translates RTCM IDs into human features"""
    codes = msg_string.split(",")
    print(f"\n🔍 Decoding Stream Capabilities for '{TARGET_MOUNT}':")
    
    has_legacy = False
    has_modern = False
    has_position = False
    
    for c in codes:
        mid = c.split("(")[0].strip()
        
        if mid in ["1004", "1012"]:
            print(f"  - [{mid}] Legacy DGPS (L1 Only) -> Status 2 (DGPS)")
            has_legacy = True
        elif mid in ["1074", "1077", "1084", "1087", "1094", "1097"]:
            print(f"  - [{mid}] Modern MSM (High Precision) -> Status 4/5 (RTK)")
            has_modern = True
        elif mid in ["1005", "1006"]:
            print(f"  - [{mid}] Base Station Position -> REQUIRED for RTK")
            has_position = True
        elif mid == "1230":
            print(f"  - [{mid}] GLONASS Biases -> Helps accuracy")
            
    print("-" * 40)
    if has_modern and has_position:
        print("✅ VERDICT: This station SUPPORTS RTK (Status 4/5).")
    elif has_legacy:
        print("⚠️ VERDICT: This is a DGPS-ONLY station (Status 2 max).")
    else:
        print("❌ VERDICT: Unknown/Incomplete message set.")

def inspect():
    print(f"--- Connecting to {CASTER}:{PORT} ---")
    try:
        # Raw socket to bypass "BadStatusLine" errors
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((CASTER, PORT))
        
        # Send NTRIP Source Table Request
        s.sendall(b"GET / HTTP/1.0\r\nUser-Agent: NTRIP Python\r\n\r\n")
        
        buffer = ""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            buffer += chunk.decode('utf-8', errors='ignore')
        
        s.close()
        
        # Parse
        found = False
        for line in buffer.splitlines():
            if f";{TARGET_MOUNT};" in line:
                found = True
                parts = line.split(";")
                print(f"✅ FOUND: {parts[1]}")
                print(f"📍 Location Broadcast: {parts[9]}, {parts[10]}")
                print(f"📡 Stream Format:     {parts[3]}")
                print(f"📨 Message List:      {parts[4]}")
                
                decode_messages(parts[4])
                break
        
        if not found:
            print(f"❌ Mountpoint '{TARGET_MOUNT}' is currently OFFLINE.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
