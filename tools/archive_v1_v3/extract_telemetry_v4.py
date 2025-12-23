#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Telemetry Data Extraction Pipeline (ADS-B / RPi Central Brain)
Script: extract_telemetry_v4.py
Description: Robust InfluxDB extractor targeting the RPi5 'central-brain'.
             - Handles 'Connection Refused' (Fixed in v3).
             - Handles 'unpack(b)' serialization errors (Fixed in v3).
             - Handles 'generator' objects from chunked queries (Fixed in v4).

Version: 1.3.0
Author: RW
Date: 2025-12-17
Revision: 4
"""

import sys
import socket
import datetime
import types  # Required to identify generator objects
import pandas as pd
import logging
from influxdb import InfluxDBClient

# ==========================================
# Configuration / Constants
# ==========================================
CONF = {
    # Target the RPi5 "central-brain"
    'influx_host': '192.168.1.134', 
    'influx_port': 8086,
    'influx_user': 'admin',
    'influx_pass': 'password',
    'db_name': 'telemetry_db',
    
    # Chunking is good for memory, but returns a Generator
    'chunk_size': 5000,
    
    'target_tables': [
        'adsb_stats', 'aircraft', 'cpu', 'disk', 'global_aircraft_state',
        'gps_data', 'gps_drift', 'gps_tpv', 'local_aircraft_state',
        'local_performance', 'mem', 'physics_alerts', 'rf_battle_stats',
        'runway_events', 'security_alerts', 'system', 'system_stats',
        'temp', 'weather_local'
    ],
    
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
        
        self._check_connectivity()
        self._connect()

    def _check_connectivity(self):
        """
        Verifies TCP reachability to the RPi5.
        """
        host = self.config['influx_host']
        port = self.config['influx_port']
        logger.info(f"Checking connectivity to 'central-brain' ({host}:{port})...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info("  [OK] Network path to RPi5 is active.")
            else:
                logger.critical(f"  [FAIL] Unable to reach {host}:{port} (Errno: {result}).")
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
            
            # Force JSON to avoid msgpack errors
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
        
        start_time = f"{target_date}T00:00:00Z"
        end_time = f"{target_date}T23:59:59Z"

        for measurement in self.config['target_tables']:
            self._query_measurement(measurement, start_time, end_time)

    def _query_measurement(self, measurement, start_time, end_time):
        """
        Queries a specific measurement.
        """
        logger.info(f"  > Extracting table: {measurement}...")
        
        query = (f"SELECT * FROM \"{measurement}\" "
                 f"WHERE time >= '{start_time}' AND time <= '{end_time}'")

        try:
            # Result will be a Generator because chunked=True
            result = self.client.query(query, chunked=True, chunk_size=self.config['chunk_size'])
            
            points = self._normalize_result(result, measurement)
            
            if points:
                self._save_data(points, measurement, start_time[:10])
            else:
                logger.info(f"    [INFO] No data found for {measurement}.")

        except Exception as e:
            logger.error(f"    [WARN] Query failed for {measurement}: {e}")

    def _normalize_result(self, result, measurement_name):
        """
        [CRITICAL FIX] Type Guard handling Generators.
        """
        all_points = []
        
        try:
            # Case 1: Generator (Chunked Response) [NEW FIX]
            if isinstance(result, types.GeneratorType):
                # We must iterate through the generator to get the actual data
                for chunk in result:
                    # Each chunk is usually a ResultSet or Dict
                    if hasattr(chunk, 'get_points'):
                        all_points.extend(list(chunk.get_points()))
                    elif isinstance(chunk, dict):
                        # Fallback for raw dict chunks
                        if 'series' in chunk:
                            all_points.extend(chunk['series'][0].get('values', []))
                return all_points

            # Case 2: Standard ResultSet
            elif hasattr(result, 'get_points'):
                return list(result.get_points())
            
            # Case 3: Raw List
            elif isinstance(result, list):
                if len(result) > 0:
                    if isinstance(result[0], dict):
                        return result
                    return result 
                return []
                
            # Case 4: Raw Dict
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
