import requests
import sys

# ==============================================================================
# Script: calc_data_volume.py
# Description: Calculates ingestion rates and projects storage growth.
# ==============================================================================

INFLUX_HOST = "http://192.168.1.134:8086"
DB_NAME = "readsb"

def get_count(duration):
    """Counts total rows in 'local_aircraft_state' for a given duration."""
    q = f'SELECT count("lat") FROM "local_aircraft_state" WHERE time > now() - {duration}'
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params={'db': DB_NAME, 'q': q})
        data = r.json()
        if 'results' in data and 'series' in data['results'][0]:
            return data['results'][0]['series'][0]['values'][0][1]
    except:
        pass
    return 0

def main():
    print("--- 📊 DATA VOLUME REPORT ---")
    print(f"Target: {INFLUX_HOST}")
    
    # 1. Measure Actuals
    print("\nScanning database (this takes a moment)...")
    last_1h = get_count("1h")
    last_24h = get_count("24h")
    
    # 2. Calculate Rates
    msgs_per_sec = last_1h / 3600
    msgs_per_min = last_1h / 60
    
    # 3. Projections
    projected_week = last_24h * 7
    projected_month = last_24h * 30
    
    # 4. Storage Estimation (InfluxDB compresses heavily, ~5-10 bytes per point)
    # This is a rough estimate based on 15 fields per row.
    est_size_gb_week = (projected_week * 15 * 8) / (1024**3) # Uncompressed raw CSV size approx
    
    print("\n--- 🚀 INGESTION VELOCITY ---")
    print(f"Current Speed:    {msgs_per_sec:.1f} msg/sec")
    print(f"Volume (1 Hour):  {last_1h:,} rows")
    print(f"Volume (24 Hours):{last_24h:,} rows")
    
    print("\n--- 🔮 PROJECTIONS ---")
    print(f"Weekly Growth:    {projected_week:,} rows")
    print(f"Monthly Growth:   {projected_month:,} rows")
    
    print("\n--- 💾 TRAINING DATA SIZE (Estimated CSV) ---")
    print(f"A 1-week training dataset will be approx: {est_size_gb_week:.2f} GB (Uncompressed)")
    
    if msgs_per_sec > 50:
        print("\n✅ STATUS: HIGH VELOCITY. Excellent for Deep Learning.")
    elif msgs_per_sec > 10:
        print("\n✅ STATUS: MODERATE. Good for standard ML.")
    else:
        print("\n⚠️ STATUS: LOW. Check antenna position?")

if __name__ == "__main__":
    main()
