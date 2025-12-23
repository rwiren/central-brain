import requests
import math

# Keimola Tower Coordinates
MY_LAT = 60.3195
MY_LON = 24.8310

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def scan_rtk2go():
    print("--- Scanning RTK2Go for Active Finland Stations ---")
    try:
        r = requests.get("http://rtk2go.com:2101/", timeout=10)
        streams = []
        
        for line in r.text.splitlines():
            if line.startswith("STR;"):
                parts = line.split(";")
                mount = parts[1]
                try:
                    lat = float(parts[9])
                    lon = float(parts[10])
                    dist = haversine(MY_LAT, MY_LON, lat, lon)
                    
                    # Filter for Finland/Nearby (< 100km)
                    if dist < 100:
                        streams.append((dist, mount, parts[3], parts[4]))
                except ValueError:
                    continue # Skip invalid coords

        # Sort by distance
        streams.sort(key=lambda x: x[0])

        print(f"\n{'DISTANCE':<10} {'MOUNTPOINT':<20} {'FORMAT'}")
        print("-" * 60)
        
        if not streams:
            print("❌ No active base stations found within 100km!")
            return

        for s in streams[:10]:
            print(f"{s[0]:.1f} km     {s[1]:<20} {s[2]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_rtk2go()
