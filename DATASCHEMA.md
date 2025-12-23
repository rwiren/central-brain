# 📡 Central Brain Data Schema
**Generated:** 2025-12-23 20:40
**Database:** `readsb`
**Host:** `192.168.1.134`

> **Note:** This schema reflects the *exact* current state of the database. Descriptions are auto-generated based on the Level 4 Ontology.

---

## 📑 Table of Contents
- [adsb_stats](#adsb_stats)
- [aircraft](#aircraft)
- [cpu](#cpu)
- [disk](#disk)
- [global_aircraft_state](#global_aircraft_state)
- [gps_data](#gps_data)
- [gps_drift](#gps_drift)
- [gps_tpv](#gps_tpv)
- [local_aircraft_state](#local_aircraft_state)
- [local_performance](#local_performance)
- [mem](#mem)
- [physics_alerts](#physics_alerts)
- [rf_battle_stats](#rf_battle_stats)
- [runway_events](#runway_events)
- [security_alerts](#security_alerts)
- [system](#system)
- [system_stats](#system_stats)
- [temp](#temp)
- [weather_local](#weather_local)

---
## `adsb_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `aircraft_total` | `float` | Raw Value |
| `avg_rssi` | `float` | Raw Value |
| `max_range_km` | `float` | Raw Value |
| `message_count` | `float` | Count |

---
## `aircraft`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number / Callsign |
| `icao` | Aircraft Hex ID (Address) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt` | `float` | Raw Value |
| `alt_baro_ft` | `integer` | Barometric Altitude (ft) |
| `gs` | `float` | Raw Value |
| `hex` | `string` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `squawk` | `string` | Raw Value |
| `vert_rate` | `integer` | Vertical Rate (fpm) |

---
## `cpu`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `cpu` | Metadata |
| `fleet_role` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity / Hostname |
| `lat` | Metadata |
| `location` | Metadata |
| `lon` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_id` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `usage_guest` | `float` | Resource Usage Metric |
| `usage_guest_nice` | `float` | Resource Usage Metric |
| `usage_idle` | `float` | Resource Usage Metric |
| `usage_iowait` | `float` | Resource Usage Metric |
| `usage_irq` | `float` | Resource Usage Metric |
| `usage_nice` | `float` | Resource Usage Metric |
| `usage_softirq` | `float` | Resource Usage Metric |
| `usage_steal` | `float` | Resource Usage Metric |
| `usage_system` | `float` | Resource Usage Metric |
| `usage_user` | `float` | Resource Usage Metric |

---
## `disk`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `device` | Metadata |
| `fleet_role` | Metadata |
| `fstype` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity / Hostname |
| `lat` | Metadata |
| `location` | Metadata |
| `lon` | Metadata |
| `mode` | Metadata |
| `path` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_id` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `free` | `integer` | Raw Value |
| `inodes_free` | `integer` | Filesystem Inodes |
| `inodes_total` | `integer` | Filesystem Inodes |
| `inodes_used` | `integer` | Filesystem Inodes |
| `inodes_used_percent` | `float` | Filesystem Inodes |
| `total` | `integer` | Raw Value |
| `used` | `integer` | Raw Value |
| `used_percent` | `float` | Percentage (%) |

---
## `global_aircraft_state`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number / Callsign |
| `data_source_type` | Metadata |
| `icao` | Aircraft Hex ID (Address) |
| `icao24` | Aircraft Hex ID (24-bit) |
| `origin_country` | Metadata |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt_baro_ft` | `float` | Barometric Altitude (ft) |
| `alt_ft` | `integer` | Raw Value |
| `baro_alt_m` | `float` | Raw Value |
| `gs_knots` | `float` | Ground Speed (knots) |
| `gs_mps` | `float` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `origin_data` | `string` | Raw Value |
| `speed_kts` | `integer` | Raw Value |
| `squawk` | `string` | Raw Value |
| `track` | `integer` | Ground Track (deg) |
| `value` | `integer` | Raw Value |
| `vr_mps` | `float` | Raw Value |

---
## `gps_data`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `hdop` | `float` | Raw Value |
| `nSat` | `float` | Raw Value |
| `pdop` | `float` | Raw Value |
| `satellites_used` | `float` | Raw Value |
| `vdop` | `float` | Raw Value |

---
## `gps_drift`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID (Address) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `drift_km` | `float` | GPS vs Reality Drift (km) |

---
## `gps_tpv`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |
| `mode` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt` | `float` | Raw Value |
| `altHAE` | `float` | Raw Value |
| `altMSL` | `float` | Raw Value |
| `climb` | `float` | Raw Value |
| `ecefpAcc` | `float` | Raw Value |
| `ecefvAcc` | `float` | Raw Value |
| `ecefvx` | `float` | Raw Value |
| `ecefvy` | `float` | Raw Value |
| `ecefvz` | `float` | Raw Value |
| `ecefx` | `float` | Raw Value |
| `ecefy` | `float` | Raw Value |
| `ecefz` | `float` | Raw Value |
| `epc` | `float` | Raw Value |
| `epd` | `float` | Raw Value |
| `eph` | `float` | Raw Value |
| `eps` | `float` | Raw Value |
| `ept` | `float` | Raw Value |
| `epv` | `float` | Raw Value |
| `epx` | `float` | Raw Value |
| `epy` | `float` | Raw Value |
| `geoidSep` | `float` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `leapseconds` | `float` | Raw Value |
| `lon` | `float` | Longitude (deg) |
| `magtrack` | `float` | Raw Value |
| `magvar` | `float` | Raw Value |
| `mode` | `float` | Raw Value |
| `sep` | `float` | Raw Value |
| `speed` | `float` | Raw Value |
| `status` | `float` | Raw Value |
| `track` | `float` | Ground Track (deg) |

---
## `local_aircraft_state`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number / Callsign |
| `host` | Sensor Identity / Hostname |
| `icao24` | Aircraft Hex ID (24-bit) |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `adsb_version` | `integer` | Raw Value |
| `alert` | `integer` | Flight Status Alert (Squawk change/Emergency) |
| `alt_baro_ft` | `integer` | Barometric Altitude (ft) |
| `alt_geom_ft` | `integer` | Geometric (GPS) Altitude (ft) |
| `category` | `string` | Raw Value |
| `emergency` | `string` | Raw Value |
| `geom_rate_fpm` | `integer` | Geometric Vertical Rate (fpm) |
| `gs_knots` | `float` | Ground Speed (knots) |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `msg_count` | `integer` | Count |
| `nac_p` | `integer` | Nav Accuracy Category (Position) |
| `nac_v` | `integer` | Nav Accuracy Category (Velocity) |
| `nav_altitude_mcp_ft` | `integer` | Pilot Selected Altitude (MCP) (ft) |
| `nav_heading` | `float` | Pilot Selected Heading (deg) |
| `nav_qnh` | `float` | Pilot Selected Pressure Setting (hPa) |
| `nic` | `integer` | Nav Integrity Category (0-11) |
| `origin_data` | `string` | Raw Value |
| `rc` | `integer` | Radius of Containment (meters) |
| `rssi` | `float` | Signal Strength (dBFS) |
| `seen_seconds` | `float` | Time since last update (s) |
| `sil` | `integer` | Source Integrity Level (0-3) |
| `spi` | `integer` | Special Position Indicator (Ident) |
| `squawk` | `string` | Raw Value |
| `track` | `float` | Ground Track (deg) |
| `v_rate_fpm` | `integer` | Raw Value |
| `vert_rate` | `integer` | Vertical Rate (fpm) |
| `vert_rate_fpm` | `integer` | Vertical Rate (fpm) |

---
## `local_performance`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `airborne_msg` | `integer` | Raw Value |
| `aircraft_with_pos` | `integer` | Raw Value |
| `aircraft_without_pos` | `integer` | Raw Value |
| `cpu_load_ms` | `integer` | System Load Average |
| `cpu_sec` | `float` | Raw Value |
| `max_range_meters` | `float` | Max Reception Range (m) |
| `messages` | `integer` | Total Messages Processed |
| `messages_last1min` | `integer` | Msg Rate (Last 60s) |
| `messages_total_lifetime` | `float` | Raw Value |
| `messages_total_lifetime` | `integer` | Raw Value |
| `positions_last1min` | `integer` | Raw Value |
| `remote_bytes_in` | `integer` | Raw Value |
| `signal_db` | `float` | Signal Strength (dB) |
| `strong_signals` | `float` | Count of Strong Signals (> -3dB) |
| `strong_signals` | `integer` | Count of Strong Signals (> -3dB) |

---
## `mem`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `fleet_role` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity / Hostname |
| `lat` | Metadata |
| `location` | Metadata |
| `lon` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_id` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `active` | `integer` | Raw Value |
| `available` | `integer` | Raw Value |
| `available_percent` | `float` | Percentage (%) |
| `buffered` | `integer` | Raw Value |
| `cached` | `integer` | Raw Value |
| `commit_limit` | `integer` | Raw Value |
| `committed_as` | `integer` | Raw Value |
| `dirty` | `integer` | Raw Value |
| `free` | `integer` | Raw Value |
| `high_free` | `integer` | Raw Value |
| `high_total` | `integer` | Raw Value |
| `huge_page_size` | `integer` | Raw Value |
| `huge_pages_free` | `integer` | Raw Value |
| `huge_pages_total` | `integer` | Raw Value |
| `inactive` | `integer` | Raw Value |
| `low_free` | `integer` | Raw Value |
| `low_total` | `integer` | Raw Value |
| `mapped` | `integer` | Raw Value |
| `page_tables` | `integer` | Raw Value |
| `shared` | `integer` | Raw Value |
| `slab` | `integer` | Raw Value |
| `sreclaimable` | `integer` | Raw Value |
| `sunreclaim` | `integer` | Raw Value |
| `swap_cached` | `integer` | Raw Value |
| `swap_free` | `integer` | Raw Value |
| `swap_total` | `integer` | Raw Value |
| `total` | `integer` | Raw Value |
| `used` | `integer` | Raw Value |
| `used_percent` | `float` | Percentage (%) |
| `vmalloc_chunk` | `integer` | Raw Value |
| `vmalloc_total` | `integer` | Raw Value |
| `vmalloc_used` | `integer` | Raw Value |
| `write_back` | `integer` | Raw Value |
| `write_back_tmp` | `integer` | Raw Value |

---
## `physics_alerts`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID (Address) |
| `icao24` | Aircraft Hex ID (24-bit) |
| `type` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `callsign` | `string` | Raw Value |
| `message` | `string` | Raw Value |
| `severity` | `float` | Raw Value |
| `value` | `float` | Raw Value |
| `violation` | `string` | Raw Value |

---
## `rf_battle_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |
| `role` | Node Role (Anchor/Scout) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `activity_score` | `integer` | Raw Value |
| `alt_high` | `integer` | Raw Value |
| `alt_low` | `integer` | Raw Value |
| `alt_mid` | `integer` | Raw Value |
| `ground_count` | `integer` | Count |
| `max_range_nm` | `float` | Raw Value |
| `msg_rate` | `integer` | Raw Value |
| `rssi_db` | `float` | Raw Value |
| `total_count` | `integer` | Count |

---
## `runway_events`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number / Callsign |
| `event` | Metadata |
| `icao` | Aircraft Hex ID (Address) |
| `runway` | Metadata |
| `squawk` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `altitude` | `float` | Raw Value |
| `callsign` | `string` | Raw Value |
| `speed` | `float` | Raw Value |
| `squawk` | `string` | Raw Value |
| `value` | `float` | Raw Value |

---
## `security_alerts`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID (Address) |
| `type` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alert_val` | `integer` | Raw Value |
| `diff_km` | `float` | Raw Value |
| `fr24_lat` | `float` | Raw Value |
| `fr24_lon` | `float` | Raw Value |
| `local_lat` | `float` | Raw Value |
| `local_lon` | `float` | Raw Value |
| `message` | `string` | Raw Value |

---
## `system`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `fleet_role` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity / Hostname |
| `lat` | Metadata |
| `location` | Metadata |
| `lon` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_id` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `load1` | `float` | System Load Average |
| `load15` | `float` | System Load Average |
| `load5` | `float` | System Load Average |
| `n_cpus` | `integer` | Raw Value |
| `n_physical_cpus` | `integer` | Raw Value |
| `uptime` | `integer` | System Uptime (seconds) |
| `uptime_format` | `string` | Raw Value |

---
## `system_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity / Hostname |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `cpu_temp` | `float` | CPU Temperature (°C) |
| `cpu_usage` | `float` | CPU Load (%) |
| `disk_usage` | `float` | Disk Usage (%) |
| `ram_usage` | `float` | RAM Usage (%) |
| `uptime` | `integer` | System Uptime (seconds) |

---
## `temp`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `fleet_role` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity / Hostname |
| `lat` | Metadata |
| `location` | Metadata |
| `lon` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor` | Metadata |
| `sensor_id` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `temp` | `float` | Raw Value |

---
## `weather_local`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `station` | Weather Station ID (ICAO) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `dewpoint_c` | `float` | Dew Point (°C) |
| `pressure_hpa` | `float` | Barometric Pressure (QNH) (hPa) |
| `raw_metar` | `string` | Raw METAR String |
| `temperature_c` | `float` | Temperature (°C) |
| `visibility_miles` | `float` | Visibility (statute miles) |
| `wind_dir_deg` | `float` | Wind Direction (deg) |
| `wind_speed_kt` | `float` | Wind Speed (knots) |

---
