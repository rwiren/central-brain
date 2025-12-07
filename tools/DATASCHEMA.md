# 📡 Central Brain Data Schema
**Generated:** 2025-12-07 15:30
**Database:** `readsb`
**Host:** `192.168.1.134`

> **Note:** This schema reflects the *exact* current state of the database, including any legacy or test measurements.

---

## 📑 Table of Contents
- [adsb_stats](#adsb_stats)
- [aircraft](#aircraft)
- [cpu](#cpu)
- [disk](#disk)
- [flight_ops](#flight_ops)
- [global_aircraft_state](#global_aircraft_state)
- [global_truth](#global_truth)
- [gps_data](#gps_data)
- [gps_drift](#gps_drift)
- [gps_tpv](#gps_tpv)
- [integrity_check](#integrity_check)
- [local_aircraft_state](#local_aircraft_state)
- [local_performance](#local_performance)
- [mem](#mem)
- [physics_alerts](#physics_alerts)
- [readsb](#readsb)
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
| `host` | Sensor Identity |

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
| `Call` | Metadata |
| `Gnd` | Metadata |
| `Icao` | Metadata |
| `Mlat` | Metadata |
| `SpdTyp` | Metadata |
| `Sqk` | Metadata |
| `Tisb` | Metadata |
| `TrkH` | Metadata |
| `VsiT` | Metadata |
| `callsign` | Flight Number |
| `host` | Sensor Identity |
| `icao` | Aircraft Hex ID |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `Alt` | `float` | Raw Value |
| `Cmsgs` | `float` | Raw Value |
| `GAlt` | `float` | Raw Value |
| `InHg` | `float` | Raw Value |
| `Lat` | `float` | Raw Value |
| `Long` | `float` | Raw Value |
| `PosTime` | `float` | Raw Value |
| `Sig` | `float` | Raw Value |
| `Spd` | `float` | Raw Value |
| `TAlt` | `float` | Raw Value |
| `TTrk` | `float` | Raw Value |
| `Trak` | `float` | Raw Value |
| `Trt` | `float` | Raw Value |
| `Vsi` | `float` | Raw Value |
| `alt` | `float` | Altitude (Geometric/Ellipsoid) |
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
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `usage_guest` | `float` | Usage Metric |
| `usage_guest_nice` | `float` | Usage Metric |
| `usage_idle` | `float` | Usage Metric |
| `usage_iowait` | `float` | Usage Metric |
| `usage_irq` | `float` | Usage Metric |
| `usage_nice` | `float` | Usage Metric |
| `usage_softirq` | `float` | Usage Metric |
| `usage_steal` | `float` | Usage Metric |
| `usage_system` | `float` | Usage Metric |
| `usage_user` | `float` | Usage Metric |

---
## `disk`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `device` | Metadata |
| `fstype` | Metadata |
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `mode` | Metadata |
| `path` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `free` | `integer` | Free Bytes |
| `inodes_free` | `integer` | Filesystem Inodes |
| `inodes_total` | `integer` | Filesystem Inodes |
| `inodes_used` | `integer` | Filesystem Inodes |
| `inodes_used_percent` | `float` | Filesystem Inodes |
| `total` | `integer` | Total Bytes |
| `used` | `integer` | Used Bytes |
| `used_percent` | `float` | Raw Value |

---
## `flight_ops`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `event_type` | Metadata |
| `hour` | Metadata |
| `icao` | Aircraft Hex ID |
| `runway_guess` | Metadata |
| `source` | Metadata |
| `weekday` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt_ft` | `integer` | Raw Value |
| `bearing_deg` | `float` | Bearing to Aircraft (deg) |
| `distance_km` | `float` | Distance to Aircraft (km) |
| `event_score` | `integer` | Raw Value |
| `is_spoofed` | `integer` | Spoofing Flag (0=OK, 1=WARN) |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `speed_kts` | `integer` | Raw Value |
| `vertical_rate` | `integer` | Raw Value |

---
## `global_aircraft_state`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number |
| `data_source_type` | Metadata |
| `icao` | Aircraft Hex ID |
| `icao24` | Metadata |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt_ft` | `integer` | Raw Value |
| `baro_alt_m` | `float` | Raw Value |
| `gs_mps` | `float` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `origin_data` | `string` | Raw Value |
| `speed_kts` | `integer` | Raw Value |
| `squawk` | `string` | Raw Value |
| `track` | `integer` | Heading/Track (deg) |
| `value` | `integer` | Raw Value |
| `vr_mps` | `float` | Raw Value |

---
## `global_truth`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `aircraft_count` | `integer` | Active Aircraft Count |

---
## `gps_data`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `hdop` | `float` | Horizontal Dilution of Precision |
| `nSat` | `float` | Raw Value |
| `pdop` | `float` | Positional Dilution of Precision |
| `satellites_used` | `float` | Satellites Used for Fix |
| `vdop` | `float` | Vertical Dilution of Precision |

---
## `gps_drift`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `drift_km` | `float` | Raw Value |

---
## `gps_tpv`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt` | `float` | Altitude (Geometric/Ellipsoid) |
| `altHAE` | `float` | Height Above Ellipsoid (m) |
| `altMSL` | `float` | Height Above Mean Sea Level (m) |
| `climb` | `float` | Climb Rate (m/s) |
| `ecefpAcc` | `float` | Raw Value |
| `ecefvAcc` | `float` | Raw Value |
| `ecefvx` | `float` | ECEF X Velocity (m/s) |
| `ecefvy` | `float` | ECEF Y Velocity (m/s) |
| `ecefvz` | `float` | ECEF Z Velocity (m/s) |
| `ecefx` | `float` | ECEF X Coordinate (m) |
| `ecefy` | `float` | ECEF Y Coordinate (m) |
| `ecefz` | `float` | ECEF Z Coordinate (m) |
| `epc` | `float` | Raw Value |
| `epd` | `float` | Raw Value |
| `eph` | `float` | Raw Value |
| `eps` | `float` | Raw Value |
| `ept` | `float` | Raw Value |
| `epv` | `float` | Vertical Precision Error (m) |
| `epx` | `float` | Horizontal Precision Error (m) |
| `epy` | `float` | Vertical Precision Error (m) |
| `geoidSep` | `float` | Geoid Separation (m) |
| `lat` | `float` | Latitude (deg) |
| `leapseconds` | `float` | Raw Value |
| `lon` | `float` | Longitude (deg) |
| `magtrack` | `float` | Raw Value |
| `magvar` | `float` | Raw Value |
| `mode` | `float` | GNSS Fix Type (2=2D, 3=3D) |
| `sep` | `float` | Spherical Error Probability (m) |
| `speed` | `float` | Speed (m/s or kts) |
| `status` | `float` | Raw Value |
| `track` | `float` | Heading/Track (deg) |

---
## `integrity_check`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `is_spoofed` | `integer` | Spoofing Flag (0=OK, 1=WARN) |
| `lat_error` | `float` | Raw Value |
| `lon_error` | `float` | Raw Value |

---
## `local_aircraft_state`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number |
| `host` | Sensor Identity |
| `icao24` | Metadata |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt_baro_ft` | `integer` | Barometric Altitude (ft) |
| `gs_knots` | `float` | Ground Speed (knots) |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `origin_data` | `string` | Raw Value |
| `track` | `float` | Heading/Track (deg) |
| `v_rate_fpm` | `integer` | Raw Value |

---
## `local_performance`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |
| `lat` | Metadata |
| `lon` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `airborne_msg` | `integer` | Raw Value |
| `cpu_sec` | `float` | Raw Value |
| `messages` | `integer` | Total Messages Processed |
| `messages_total_lifetime` | `integer` | Raw Value |
| `signal_db` | `float` | Signal Strength (dB) |
| `strong_signals` | `integer` | Count of Strong Signals (> -3dB) |

---
## `mem`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `role` | Node Role (Anchor/Scout) |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `active` | `integer` | Raw Value |
| `available` | `integer` | Raw Value |
| `available_percent` | `float` | Raw Value |
| `buffered` | `integer` | Raw Value |
| `cached` | `integer` | Raw Value |
| `commit_limit` | `integer` | Raw Value |
| `committed_as` | `integer` | Raw Value |
| `dirty` | `integer` | Raw Value |
| `free` | `integer` | Free Bytes |
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
| `total` | `integer` | Total Bytes |
| `used` | `integer` | Used Bytes |
| `used_percent` | `float` | Raw Value |
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
| `icao` | Aircraft Hex ID |
| `icao24` | Metadata |
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
## `readsb`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `cpr_airborne` | `float` | CPR Airborne Pos Messages |
| `cpr_global_bad` | `float` | Raw Value |
| `cpr_global_ok` | `float` | Global CPR Decodes (Success) |
| `cpr_global_skipped` | `float` | Raw Value |
| `cpr_global_speed` | `float` | Raw Value |
| `cpr_local_aircraft_relative` | `float` | Raw Value |
| `cpr_local_ok` | `float` | Local CPR Decodes (Success) |
| `cpr_local_range` | `float` | Raw Value |
| `cpr_local_skipped` | `float` | Raw Value |
| `cpr_local_speed` | `float` | Raw Value |
| `cpr_surface` | `float` | CPR Surface Pos Messages |
| `cpu_background` | `float` | Demodulator CPU Usage (%) |
| `messages` | `float` | Total Messages Processed |
| `remote_accepted` | `float` | Messages Accepted from Net |
| `remote_modeac` | `float` | Raw Value |
| `remote_modes` | `float` | Raw Value |
| `remote_unknown_icao` | `float` | Raw Value |
| `tracks_new` | `float` | New Tracks Created |
| `tracks_single_message` | `float` | Raw Value |
| `tracks_with_position` | `float` | Tracks with Valid Position |

---
## `rf_battle_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |
| `role` | Node Role (Anchor/Scout) |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `activity_score` | `integer` | RF Activity Index |
| `alt_high` | `integer` | Raw Value |
| `alt_low` | `integer` | Raw Value |
| `alt_mid` | `integer` | Raw Value |
| `ground_count` | `integer` | Count |
| `max_range_nm` | `float` | Max Range (Nautical Miles) |
| `msg_rate` | `integer` | Message Rate (msg/s) |
| `rssi_db` | `float` | Signal Strength (dB) |
| `total_count` | `integer` | Count |

---
## `runway_events`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `callsign` | Flight Number |
| `event` | Metadata |
| `icao` | Aircraft Hex ID |
| `runway` | Metadata |
| `squawk` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `altitude` | `float` | Raw Value |
| `callsign` | `string` | Raw Value |
| `speed` | `float` | Speed (m/s or kts) |
| `squawk` | `string` | Raw Value |
| `value` | `float` | Raw Value |

---
## `security_alerts`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID |
| `type` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alert_val` | `integer` | Alert Level (0-5) |
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
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `load1` | `float` | System Load (1 min avg) |
| `load15` | `float` | System Load (15 min avg) |
| `load5` | `float` | System Load (5 min avg) |
| `n_cpus` | `integer` | Raw Value |
| `uptime` | `integer` | System Uptime (seconds) |
| `uptime_format` | `string` | Raw Value |

---
## `system_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `cpu_model` | Metadata |
| `host` | Sensor Identity |
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
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `sensor` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `temp` | `float` | Temperature (°C) |

---
## `weather_local`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `station` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `dewpoint_c` | `float` | Raw Value |
| `pressure_hpa` | `float` | Raw Value |
| `raw_metar` | `string` | Raw Value |
| `temperature_c` | `float` | Raw Value |
| `visibility_miles` | `float` | Raw Value |
| `wind_dir_deg` | `float` | Raw Value |
| `wind_speed_kt` | `float` | Raw Value |

---
