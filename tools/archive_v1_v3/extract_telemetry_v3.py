#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Telemetry Data Extraction Pipeline (ADS-B / RPi Central Brain)
Script: extract_telemetry_v3.py
Description: Robust InfluxDB extractor targeting the RPi5 'central-brain'.
             - Fixes 'Connection Refused' by targeting correct IP.
             - Fixes 'unpack(b)' errors by forcing JSON transport.
             - Fixes 'AttributeError' by using a Type Guard on results.

Version: 1.2.0
Author: RW
Date: 2025-12-17
Revision: 3
"""

import sys
import socket
import datetime
import pandas as pd
import logging
from influxdb import InfluxDBClient

# ==========================================
# Configuration / Constants
# ==========================================
CONF = {
    # [ARCHITECTURAL CHANGE] Target the RPi5 "central-brain"
    'influx_host': '192.168.1.134', 
    'influx_port': 8086,
    'influx_user': 'admin',      # Update if you have enabled auth on Balena
    'influx_pass': 'password',   # Update if you have enabled auth on Balena
    'db_name': 'telemetry_db',   # Ensure this matches your Balena env variable
    
    'chunk_size': 5000,
    
    # Tables requested for extraction
    'target_tables': [
        'adsb_stats', 'aircraft', 'cpu', 'disk', 'global_aircraft_state',
        'gps_data', 'gps_drift', 'gps_tpv', 'local_aircraft_state',
        'local_performance', 'mem', 'physics_alerts', 'rf_battle_stats',
        'runway_events', 'security_alerts', 'system', 'system_stats',
        'temp', 'weather_local'
    ],
    
    # Date Range: 3rd to 7th Dec 2025
    'start_date': '2025-12-03',
    'end_date': '2025-12-07'
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
        
        # 1. Pre-flight Network Check
        self._check_connectivity()
        # 2. Database Connection
        self._connect()

    def _check_connectivity(self):
        """
        Verifies TCP reachability to the RPi5 before attempting heavy operations.
        """
        host = self.config['influx_host']
        port = self.config['influx_port']
        logger.info(f"Checking connectivity to 'central-brain' ({host}:{port})...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3) # 3 second timeout
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info("  [OK] Network path to RPi5 is active.")
            else:
                logger.critical(f"  [FAIL] Unable to reach {host}:{port} (Errno: {result}).")
                logger.critical("  -> Check if BalenaOS device is online and exposing port 8086.")
                logger.critical("  -> If using ZeroTier, ensure both devices are authorized.")
                sys.exit(1)
        except Exception as e:
            logger.critical(f"  [FAIL] Connectivity check error: {e}")
            sys.exit(1)

    def _connect(self):
        """
        Establishes connection to InfluxDB with JSON header enforcement.
        """
        try:
            self.client = InfluxDBClient(
                host=self.config['influx_host'],
                port=self.config['influx_port'],
                username=self.config['influx_user'],
                password=self.config['influx_pass'],
                database=self.config['db_name'],
                timeout=10
            )
            
            # [CRITICAL FIX] 
            # Force the client to request JSON instead of MsgPack.
            # This prevents the 'unpack(b) received extra data' error common 
            # when client/server versions differ (e.g., Python client vs Balena Influx).
            if hasattr(self.client, '_headers'):
                self.client._headers['Accept'] = 'application/json'
            
            logger.info("Connection established to InfluxDB (JSON headers enforced).")
            
        except Exception as e:
            logger.critical(f"Failed to initialize InfluxDB client: {e}")
            sys.exit(1)

    def extract_by_date(self, target_date):
        """
        Extracts data for all configured tables for a specific date.
        """
        logger.info(f"Processing Date: {target_date}")
        
        # Full day window
        start_time = f"{target_date}T00:00:00Z"
        end_time = f"{target_date}T23:59:59Z"

        for measurement in self.config['target_tables']:
            self._query_measurement(measurement, start_time, end_time)

    def _query_measurement(self, measurement, start_time, end_time):
        """
        Queries a specific measurement using chunking to manage RAM usage.
        """
        logger.info(f"  > Extracting table: {measurement}...")
        
        query = (f"SELECT * FROM \"{measurement}\" "
                 f"WHERE time >= '{start_time}' AND time <= '{end_time}'")

        try:
            # Query with chunking
            result = self.client.query(query, chunked=True, chunk_size=self.config['chunk_size'])
            
            points = self._normalize_result(result, measurement)
            
            if points:
                self._save_data(points, measurement, start_time[:10])
            else:
                logger.info(f"    [INFO] No data found for {measurement}.")

        except Exception as e:
            logger.error(f"    [WARN] Chunk query failed for {measurement}: {e}")

    def _normalize_result(self, result, measurement_name):
        """
        [CRITICAL FIX] Type Guard for polymorphic results.
        InfluxDB client sometimes returns a ResultSet, sometimes a List, 
        and sometimes a Dict depending on the error state or data shape.
        """
        try:
            # Case 1: Standard ResultSet (Expected success path)
            if hasattr(result, 'get_points'):
                return list(result.get_points())
            
            # Case 2: Raw List (Fallback for some JSON responses)
            elif isinstance(result, list):
                if len(result) > 0:
                    if isinstance(result[0], dict):
                        return result
                    return result 
                return []
                
            # Case 3: Raw Dict (Single series fallback)
            elif isinstance(result, dict):
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
            
            # Reorder columns to put 'time' first if it exists
            if 'time' in df.columns:
                cols = ['time'] + [c for c in df.columns if c != 'time']
                df = df[cols]
                
            filename = f"export_{measurement}_{date_str}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"    [SUCCESS] Extracted {len(df)} records -> {filename}")
            
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
