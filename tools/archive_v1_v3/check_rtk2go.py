import requests

MOUNTPOINT = "knummi_kha"
CASTER_URL = "http://rtk2go.com:2101/"

def check_stream():
    print(f"--- Checking RTK2Go for {MOUNTPOINT} ---")
    try:
        r = requests.get(CASTER_URL, timeout=10)
        found = False
        
        for line in r.text.splitlines():
            if line.startswith(f"STR;{MOUNTPOINT};"):
                found = True
                parts = line.split(";")
                # Format: STR;Mount;ID;Format;Details;...
                print(f"✅ FOUND: {parts[1]}")
                print(f"📍 Location: {parts[9]},{parts[10]}") # Lat/Lon
                print(f"📡 Format:   {parts[3]}")
                print(f"📨 Messages: {parts[4]}") 
                
                # Simple decoder for common RTK messages
                msgs = parts[4].split(",")
                print("\n--- Message Decode ---")
                for m in msgs:
                    mid = m.split("(")[0] # remove rate e.g. 1077(1) -> 1077
                    if mid == "1005" or mid == "1006": print(f"  {m:<8} -> Base Station Position (REQUIRED)")
                    elif mid == "1077": print(f"  {m:<8} -> GPS High Precision (MSM7)")
                    elif mid == "1087": print(f"  {m:<8} -> GLONASS High Precision (MSM7)")
                    elif mid == "1097": print(f"  {m:<8} -> Galileo High Precision (MSM7)")
                    elif mid == "1127": print(f"  {m:<8} -> BeiDou High Precision (MSM7)")
                    elif mid == "1230": print(f"  {m:<8} -> GLONASS Biases")
                    else: print(f"  {m:<8} -> Other")
                break
        
        if not found:
            print(f"❌ Mountpoint '{MOUNTPOINT}' not found in sourcetable.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_stream()
