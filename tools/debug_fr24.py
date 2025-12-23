import requests
import json

# ---------------- CONFIGURATION ----------------
# PASTE YOUR FULL TOKEN HERE
TOKEN = "019ad149-f995-70d9-a6f5-ad165a1853a3|UAbRqScsW2S6Iz9HT3R6yARMjUW0L8tVkx9hYHuae0206acb"
URL = "https://fr24api.flightradar24.com/api/live/flight-positions/full"

# ---------------- HEADERS ----------------
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Accept-Version": "v1"
}

# ---------------- PARAMETERS ----------------
# FIX: Use 'operating_as' instead of 'airlines'
params = {
    "operating_as": "FIN"
}

print(f"--- ✈️  Testing Connection with Finnair (FIN) ---")
print(f"Targeting: {URL}")

try:
    response = requests.get(URL, headers=headers, params=params)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        flight_list = data.get('data', [])
        
        if flight_list:
            count = len(flight_list)
            print(f"✅ SUCCESS: Found {count} active Finnair flights!")
            
            # Print details of the first flight found as an example
            first_flight = flight_list[0]
            print("\n--- Example Flight Data ---")
            print(json.dumps(first_flight, indent=2))
        else:
            print("⚠️ SUCCESS (200 OK), but list is empty.")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"Script Error: {e}")
