# ==============================================================================
# TOOL: Fleet Health Verification (Authenticated)
# DATE: 2025-12-22
# ==============================================================================

import requests
import base64
from datetime import datetime

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"

# --- CREDENTIALS (MUST MATCH DASHBOARD VARIABLES) ---
# If you used INFLUX_TOKEN in dashboard, put it here as password, user can be anything.
# If you used INFLUX_USER/PASS, put them here.
DB_USER = "admin"      # Change if you set a specific user
DB_PASS = "admin"      # Change to your Password or Token

# Define what "Alive" means for each node type
NODES = {
    "keimola-office":  {"measure": "gpsd_tpv", "field": "lat", "type": "GPS"},
    "keimola-balcony": {"measure": "gpsd_tpv", "field": "lat", "type": "GPS"},
    "central-brain":   {"measure": "cpu",      "field": "usage_idle", "type": "System"}
}

def check_influx(query):
    url = f"http://{INFLUX_HOST}:{INFLUX_PORT}/query"
    params = {'db': DB_NAME, 'q': query}
    
    # Basic Auth setup
    auth = None
    if DB_USER and DB_PASS:
        auth = (DB_USER, DB_PASS)

    try:
        r = requests.get(url, params=params, auth=auth, timeout=5)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 403:
            return "AUTH_FAIL"
        else:
            return f"HTTP_{r.status_code}"
    except Exception as e:
        return "CONN_FAIL"

print(f"\n=== FLEET STATUS: {datetime.now().strftime('%H:%M:%S')} ===")
print(f"Target: {INFLUX_HOST}")

for node, cfg in NODES.items():
    # Query for the last data point
    q = f"SELECT last(\"{cfg['field']}\") FROM \"{cfg['measure']}\" WHERE \"sensor_id\" = '{node}'"
    res = check_influx(q)

    status = "UNKNOWN"
    details = ""

    if res == "AUTH_FAIL":
        status = "🔒 LOCKED"
        details = "(Script needs correct DB_USER/DB_PASS)"
    elif res == "CONN_FAIL":
        status = "🚫 DOWN"
        details = "(Cannot reach Central Brain)"
    elif isinstance(res, dict):
        if 'results' in res and 'series' in res['results'][0]:
            # Data found!
            val = res['results'][0]['series'][0]['values'][0][1] # Value
            time_str = res['results'][0]['series'][0]['values'][0][0] # Time
            
            # Parse time to check recency
            # Influx returns: 2025-12-22T14:00:00Z
            last_seen = datetime.strptime(time_str[:19], '%Y-%m-%dT%H:%M:%S')
            diff = (datetime.utcnow() - last_seen).total_seconds()
            
            if diff < 300: # Seen in last 5 mins
                status = "✅ ONLINE"
                details = f"({cfg['type']} Active | Lag: {int(diff)}s)"
            else:
                status = "⚠️ STALE"
                details = f"(Last seen: {int(diff/60)} mins ago)"
        else:
            status = "❌ NO DATA"
            details = "(Telegraf not writing yet)"
    
    print(f"{node:<20} {status} {details}")

print("-" * 60)
