#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Telemetry Data Extraction Pipeline
Script: extract_telemetry_v1.py
Description: Robust InfluxDB extractor that handles serialization conflicts 
             and response type polymorphism. Enforces JSON transport to 
             avoid msgpack unpacking errors.

Version: 1.0.0
Author: RW
Date: 2025-12-17
Revision: 1
"""

import sys
import datetime
import pandas as pd
import logging
from influxdb import InfluxDBClient
from requests.exceptions import ConnectionError

# ==========================================
# Configuration / Constants
# ==========================================
CONF = {
    'influx_host': 'localhost',
    'influx_port': 8086,
    'influx_user': 'admin',      # Update as necessary
    'influx_pass': 'password',   # Update as necessary
    'db_name': 'telemetry_db',   # Update with your actual DB name
    'chunk_size': 5000,
    # The tables observed in your failure logs
    'target_tables': [
        'adsb_stats', 'aircraft', 'cpu', 'disk', 'global_aircraft_state',
        'gps_data', 'gps_drift', 'gps_tpv', 'local_aircraft_state',
        'local_performance', 'mem', 'physics_alerts', 'rf_battle_stats',
        'runway_events', 'security_alerts', 'system', 'system_stats',
        'temp', 'weather_local'
    ],
    'start_date': '2025-12-03',
    'end_date': '2025-12-07'     # Adjusted based on your log snippet
}

# ==========================================
# Logging Setup
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
# Core Architecture
# ==========================================

class TelemetryExtractor:
    def __init__(self, config):
        self.config = config
        self.client = None
        self._connect()

    def _connect(self):
        """
        Establishes connection to InfluxDB.
        CRITICAL FIX: Forces JSON headers to avoid 'unpack(b)' msgpack errors.
        """
        try:
            self.client = InfluxDBClient(
                host=self.config['influx_host'],
                port=self.config['influx_port'],
                username=self.config['influx_user'],
                password=self.config['influx_pass'],
                database=self.config['db_name']
            )
            
            # ARCHITECTURAL FIX: 
            # Force the client to request JSON instead of MsgPack.
            # This prevents the 'unpack(b) received extra data' error.
            if hasattr(self.client, '_headers'):
                self.client._headers['Accept'] = 'application/json'
            
            logger.info("Connection established to InfluxDB (JSON transport forced).")
            
        except Exception as e:
            logger.critical(f"Failed to connect to InfluxDB: {e}")
            sys.exit(1)

    def extract_by_date(self, target_date):
        """
        Extracts data for all configured tables for a specific date.
        """
        logger.info(f"Processing Date: {target_date}")
        
        # Time window definition (Full Day)
        start_time = f"{target_date}T00:00:00Z"
        end_time = f"{target_date}T23:59:59Z"

        for measurement in self.config['target_tables']:
            self._query_measurement(measurement, start_time, end_time)

    def _query_measurement(self, measurement, start_time, end_time):
        """
        Queries a specific measurement and handles extraction.
        """
        logger.info(f"  > Extracting table: {measurement}...")
        
        query = (f"SELECT * FROM \"{measurement}\" "
                 f"WHERE time >= '{start_time}' AND time <= '{end_time}'")

        try:
            # Query with chunking to handle memory load
            result = self.client.query(query, chunked=True, chunk_size=self.config['chunk_size'])
            
            points = self._normalize_result(result, measurement)
            
            if points:
                self._save_data(points, measurement, start_time[:10])
            else:
                logger.info(f"    [INFO] No data found for {measurement}.")

        except Exception as e:
            logger.error(f"    [WARN] chunk query failed for {measurement}: {e}")

    def _normalize_result(self, result, measurement_name):
        """
        ARCHITECTURAL FIX: Type Guard for result format.
        Handles both ResultSet objects and raw Lists to prevent AttributeError.
        """
        try:
            # Case 1: Standard ResultSet (Expected)
            # We check if the object has the method we need
            if hasattr(result, 'get_points'):
                return list(result.get_points())
            
            # Case 2: Raw List (Polymorphic fallback)
            # Sometimes failures in the client return a list of dicts directly
            elif isinstance(result, list):
                # If it's a list, it might be a list of ResultSets or raw dicts
                # We attempt to iterate.
                if len(result) > 0:
                    # Check structure of first item
                    first_item = result[0]
                    if isinstance(first_item, dict):
                        return result
                    # Should unlikely happen in standard influx client, 
                    # but safeguard against nested lists
                    return result 
                return []
                
            # Case 3: Dictionary (Single series result)
            elif isinstance(result, dict):
                # Older clients might return a dict with 'series' key
                if 'series' in result:
                    return result['series'][0].get('values', [])
                return []

            else:
                logger.warning(f"    [WARN] Unknown result type for {measurement_name}: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"    [ERROR] Normalization failed for {measurement_name}: {e}")
            return []

    def _save_data(self, points, measurement, date_str):
        """
        Saves the extracted points to CSV.
        """
        try:
            df = pd.DataFrame(points)
            filename = f"export_{measurement}_{date_str}.csv"
            # df.to_csv(filename, index=False) # Uncomment to actually write files
            logger.info(f"    [SUCCESS] Extracted {len(df)} records. (Would save to {filename})")
        except Exception as e:
            logger.error(f"    [ERROR] Failed to convert/save data for {measurement}: {e}")


# ==========================================
# Main Execution Flow
# ==========================================
def main():
    extractor = TelemetryExtractor(CONF)
    
    start = datetime.datetime.strptime(CONF['start_date'], "%Y-%m-%d")
    end = datetime.datetime.strptime(CONF['end_date'], "%Y-%m-%d")
    
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime("%Y-%m-%d")
        extractor.extract_by_date(date_str)
        current_date += datetime.timedelta(days=1)

if __name__ == "__main__":
    main()
