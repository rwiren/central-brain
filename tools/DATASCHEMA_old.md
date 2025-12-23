# 📡 Central Brain Data Schema
**Generated:** 2025-12-07 14:52
**Database:** `readsb`
**Host:** `192.168.1.134`

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
- [local_stats](#local_stats)
- [mem](#mem)
- [physics_alerts](#physics_alerts)
- [readsb](#readsb)
- [rf_battle_stats](#rf_battle_stats)
- [runway_events](#runway_events)
- [security_alerts](#security_alerts)
- [system](#system)
- [system_stats](#system_stats)
- [telegraf_test](#telegraf_test)
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
| `avg_rssi` | `float` | Signal Strength (dB) |
| `max_range_km` | `float` | Raw Value |
| `message_count` | `float` | Raw Value |

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
| `Alt` | `float` | Altitude (ft/m) |
| `Cmsgs` | `float` | Ground Speed (kts) |
| `GAlt` | `float` | Altitude (ft/m) |
| `InHg` | `float` | Raw Value |
| `Lat` | `float` | Latitude (deg) |
| `Long` | `float` | Longitude (deg) |
| `PosTime` | `float` | Raw Value |
| `Sig` | `float` | Raw Value |
| `Spd` | `float` | Raw Value |
| `TAlt` | `float` | Altitude (ft/m) |
| `TTrk` | `float` | Raw Value |
| `Trak` | `float` | Raw Value |
| `Trt` | `float` | Raw Value |
| `Vsi` | `float` | Raw Value |
| `alt` | `float` | Altitude (ft/m) |
| `alt_baro_ft` | `integer` | Altitude (ft/m) |
| `gs` | `float` | Ground Speed (kts) |
| `hex` | `string` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `squawk` | `string` | Raw Value |
| `vert_rate` | `integer` | Raw Value |

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
| `role` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `usage_guest` | `float` | Raw Value |
| `usage_guest_nice` | `float` | Raw Value |
| `usage_idle` | `float` | Raw Value |
| `usage_iowait` | `float` | Raw Value |
| `usage_irq` | `float` | Raw Value |
| `usage_nice` | `float` | Raw Value |
| `usage_softirq` | `float` | Raw Value |
| `usage_steal` | `float` | Raw Value |
| `usage_system` | `float` | Raw Value |
| `usage_user` | `float` | Raw Value |

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
| `role` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `free` | `integer` | Raw Value |
| `inodes_free` | `integer` | Raw Value |
| `inodes_total` | `integer` | Raw Value |
| `inodes_used` | `integer` | Raw Value |
| `inodes_used_percent` | `float` | Raw Value |
| `total` | `integer` | Raw Value |
| `used` | `integer` | Raw Value |
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
| `alt_ft` | `integer` | Altitude (ft/m) |
| `bearing_deg` | `float` | Raw Value |
| `distance_km` | `float` | Raw Value |
| `event_score` | `integer` | Raw Value |
| `is_spoofed` | `integer` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `speed_kts` | `integer` | Ground Speed (kts) |
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
| `alt_ft` | `integer` | Altitude (ft/m) |
| `baro_alt_m` | `float` | Altitude (ft/m) |
| `gs_mps` | `float` | Ground Speed (kts) |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `origin_data` | `string` | Raw Value |
| `speed_kts` | `integer` | Ground Speed (kts) |
| `squawk` | `string` | Raw Value |
| `track` | `integer` | Heading (deg) |
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
| `aircraft_count` | `integer` | Raw Value |

---
## `gps_data`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `alt` | `float` | Altitude (ft/m) |
| `altHAE` | `float` | Altitude (ft/m) |
| `altMSL` | `float` | Altitude (ft/m) |
| `altitude` | `float` | Altitude (ft/m) |
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
| `epx` | `float` | Horizontal Precision (m) |
| `epy` | `float` | Vertical Precision (m) |
| `gdop` | `float` | Raw Value |
| `geoidSep` | `float` | Raw Value |
| `hdop` | `float` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `latitude` | `float` | Latitude (deg) |
| `leapseconds` | `float` | Raw Value |
| `lon` | `float` | Longitude (deg) |
| `longitude` | `float` | Longitude (deg) |
| `magtrack` | `float` | Heading (deg) |
| `magvar` | `float` | Raw Value |
| `mode` | `float` | Raw Value |
| `nSat` | `float` | Raw Value |
| `pdop` | `float` | Raw Value |
| `satellites_0_PRN` | `float` | Satellite Count |
| `satellites_0_az` | `float` | Satellite Count |
| `satellites_0_el` | `float` | Satellite Count |
| `satellites_0_gnssid` | `float` | Satellite Count |
| `satellites_0_ss` | `float` | Satellite Count |
| `satellites_0_svid` | `float` | Satellite Count |
| `satellites_10_PRN` | `float` | Satellite Count |
| `satellites_10_az` | `float` | Satellite Count |
| `satellites_10_el` | `float` | Satellite Count |
| `satellites_10_gnssid` | `float` | Satellite Count |
| `satellites_10_sigid` | `float` | Satellite Count |
| `satellites_10_ss` | `float` | Satellite Count |
| `satellites_10_svid` | `float` | Satellite Count |
| `satellites_11_PRN` | `float` | Satellite Count |
| `satellites_11_az` | `float` | Satellite Count |
| `satellites_11_el` | `float` | Satellite Count |
| `satellites_11_gnssid` | `float` | Satellite Count |
| `satellites_11_sigid` | `float` | Satellite Count |
| `satellites_11_ss` | `float` | Satellite Count |
| `satellites_11_svid` | `float` | Satellite Count |
| `satellites_12_PRN` | `float` | Satellite Count |
| `satellites_12_az` | `float` | Satellite Count |
| `satellites_12_el` | `float` | Satellite Count |
| `satellites_12_gnssid` | `float` | Satellite Count |
| `satellites_12_sigid` | `float` | Satellite Count |
| `satellites_12_ss` | `float` | Satellite Count |
| `satellites_12_svid` | `float` | Satellite Count |
| `satellites_13_PRN` | `float` | Satellite Count |
| `satellites_13_az` | `float` | Satellite Count |
| `satellites_13_el` | `float` | Satellite Count |
| `satellites_13_gnssid` | `float` | Satellite Count |
| `satellites_13_sigid` | `float` | Satellite Count |
| `satellites_13_ss` | `float` | Satellite Count |
| `satellites_13_svid` | `float` | Satellite Count |
| `satellites_14_PRN` | `float` | Satellite Count |
| `satellites_14_az` | `float` | Satellite Count |
| `satellites_14_el` | `float` | Satellite Count |
| `satellites_14_gnssid` | `float` | Satellite Count |
| `satellites_14_sigid` | `float` | Satellite Count |
| `satellites_14_ss` | `float` | Satellite Count |
| `satellites_14_svid` | `float` | Satellite Count |
| `satellites_15_PRN` | `float` | Satellite Count |
| `satellites_15_az` | `float` | Satellite Count |
| `satellites_15_el` | `float` | Satellite Count |
| `satellites_15_gnssid` | `float` | Satellite Count |
| `satellites_15_sigid` | `float` | Satellite Count |
| `satellites_15_ss` | `float` | Satellite Count |
| `satellites_15_svid` | `float` | Satellite Count |
| `satellites_16_PRN` | `float` | Satellite Count |
| `satellites_16_az` | `float` | Satellite Count |
| `satellites_16_el` | `float` | Satellite Count |
| `satellites_16_gnssid` | `float` | Satellite Count |
| `satellites_16_sigid` | `float` | Satellite Count |
| `satellites_16_ss` | `float` | Satellite Count |
| `satellites_16_svid` | `float` | Satellite Count |
| `satellites_17_PRN` | `float` | Satellite Count |
| `satellites_17_az` | `float` | Satellite Count |
| `satellites_17_el` | `float` | Satellite Count |
| `satellites_17_gnssid` | `float` | Satellite Count |
| `satellites_17_sigid` | `float` | Satellite Count |
| `satellites_17_ss` | `float` | Satellite Count |
| `satellites_17_svid` | `float` | Satellite Count |
| `satellites_18_PRN` | `float` | Satellite Count |
| `satellites_18_az` | `float` | Satellite Count |
| `satellites_18_el` | `float` | Satellite Count |
| `satellites_18_gnssid` | `float` | Satellite Count |
| `satellites_18_sigid` | `float` | Satellite Count |
| `satellites_18_ss` | `float` | Satellite Count |
| `satellites_18_svid` | `float` | Satellite Count |
| `satellites_19_PRN` | `float` | Satellite Count |
| `satellites_19_az` | `float` | Satellite Count |
| `satellites_19_el` | `float` | Satellite Count |
| `satellites_19_gnssid` | `float` | Satellite Count |
| `satellites_19_sigid` | `float` | Satellite Count |
| `satellites_19_ss` | `float` | Satellite Count |
| `satellites_19_svid` | `float` | Satellite Count |
| `satellites_1_PRN` | `float` | Satellite Count |
| `satellites_1_az` | `float` | Satellite Count |
| `satellites_1_el` | `float` | Satellite Count |
| `satellites_1_gnssid` | `float` | Satellite Count |
| `satellites_1_ss` | `float` | Satellite Count |
| `satellites_1_svid` | `float` | Satellite Count |
| `satellites_20_PRN` | `float` | Satellite Count |
| `satellites_20_az` | `float` | Satellite Count |
| `satellites_20_el` | `float` | Satellite Count |
| `satellites_20_gnssid` | `float` | Satellite Count |
| `satellites_20_sigid` | `float` | Satellite Count |
| `satellites_20_ss` | `float` | Satellite Count |
| `satellites_20_svid` | `float` | Satellite Count |
| `satellites_21_PRN` | `float` | Satellite Count |
| `satellites_21_az` | `float` | Satellite Count |
| `satellites_21_el` | `float` | Satellite Count |
| `satellites_21_gnssid` | `float` | Satellite Count |
| `satellites_21_sigid` | `float` | Satellite Count |
| `satellites_21_ss` | `float` | Satellite Count |
| `satellites_21_svid` | `float` | Satellite Count |
| `satellites_22_PRN` | `float` | Satellite Count |
| `satellites_22_az` | `float` | Satellite Count |
| `satellites_22_el` | `float` | Satellite Count |
| `satellites_22_gnssid` | `float` | Satellite Count |
| `satellites_22_sigid` | `float` | Satellite Count |
| `satellites_22_ss` | `float` | Satellite Count |
| `satellites_22_svid` | `float` | Satellite Count |
| `satellites_23_PRN` | `float` | Satellite Count |
| `satellites_23_az` | `float` | Satellite Count |
| `satellites_23_el` | `float` | Satellite Count |
| `satellites_23_gnssid` | `float` | Satellite Count |
| `satellites_23_ss` | `float` | Satellite Count |
| `satellites_23_svid` | `float` | Satellite Count |
| `satellites_24_PRN` | `float` | Satellite Count |
| `satellites_24_az` | `float` | Satellite Count |
| `satellites_24_el` | `float` | Satellite Count |
| `satellites_24_gnssid` | `float` | Satellite Count |
| `satellites_24_sigid` | `float` | Satellite Count |
| `satellites_24_ss` | `float` | Satellite Count |
| `satellites_24_svid` | `float` | Satellite Count |
| `satellites_25_PRN` | `float` | Satellite Count |
| `satellites_25_az` | `float` | Satellite Count |
| `satellites_25_el` | `float` | Satellite Count |
| `satellites_25_gnssid` | `float` | Satellite Count |
| `satellites_25_sigid` | `float` | Satellite Count |
| `satellites_25_ss` | `float` | Satellite Count |
| `satellites_25_svid` | `float` | Satellite Count |
| `satellites_26_PRN` | `float` | Satellite Count |
| `satellites_26_az` | `float` | Satellite Count |
| `satellites_26_el` | `float` | Satellite Count |
| `satellites_26_gnssid` | `float` | Satellite Count |
| `satellites_26_sigid` | `float` | Satellite Count |
| `satellites_26_ss` | `float` | Satellite Count |
| `satellites_26_svid` | `float` | Satellite Count |
| `satellites_27_PRN` | `float` | Satellite Count |
| `satellites_27_az` | `float` | Satellite Count |
| `satellites_27_el` | `float` | Satellite Count |
| `satellites_27_gnssid` | `float` | Satellite Count |
| `satellites_27_sigid` | `float` | Satellite Count |
| `satellites_27_ss` | `float` | Satellite Count |
| `satellites_27_svid` | `float` | Satellite Count |
| `satellites_28_PRN` | `float` | Satellite Count |
| `satellites_28_az` | `float` | Satellite Count |
| `satellites_28_el` | `float` | Satellite Count |
| `satellites_28_gnssid` | `float` | Satellite Count |
| `satellites_28_sigid` | `float` | Satellite Count |
| `satellites_28_ss` | `float` | Satellite Count |
| `satellites_28_svid` | `float` | Satellite Count |
| `satellites_29_PRN` | `float` | Satellite Count |
| `satellites_29_az` | `float` | Satellite Count |
| `satellites_29_el` | `float` | Satellite Count |
| `satellites_29_gnssid` | `float` | Satellite Count |
| `satellites_29_ss` | `float` | Satellite Count |
| `satellites_29_svid` | `float` | Satellite Count |
| `satellites_2_PRN` | `float` | Satellite Count |
| `satellites_2_az` | `float` | Satellite Count |
| `satellites_2_el` | `float` | Satellite Count |
| `satellites_2_gnssid` | `float` | Satellite Count |
| `satellites_2_sigid` | `float` | Satellite Count |
| `satellites_2_ss` | `float` | Satellite Count |
| `satellites_2_svid` | `float` | Satellite Count |
| `satellites_30_PRN` | `float` | Satellite Count |
| `satellites_30_az` | `float` | Satellite Count |
| `satellites_30_el` | `float` | Satellite Count |
| `satellites_30_gnssid` | `float` | Satellite Count |
| `satellites_30_ss` | `float` | Satellite Count |
| `satellites_30_svid` | `float` | Satellite Count |
| `satellites_31_PRN` | `float` | Satellite Count |
| `satellites_31_az` | `float` | Satellite Count |
| `satellites_31_el` | `float` | Satellite Count |
| `satellites_31_gnssid` | `float` | Satellite Count |
| `satellites_31_ss` | `float` | Satellite Count |
| `satellites_31_svid` | `float` | Satellite Count |
| `satellites_3_PRN` | `float` | Satellite Count |
| `satellites_3_az` | `float` | Satellite Count |
| `satellites_3_el` | `float` | Satellite Count |
| `satellites_3_gnssid` | `float` | Satellite Count |
| `satellites_3_sigid` | `float` | Satellite Count |
| `satellites_3_ss` | `float` | Satellite Count |
| `satellites_3_svid` | `float` | Satellite Count |
| `satellites_4_PRN` | `float` | Satellite Count |
| `satellites_4_az` | `float` | Satellite Count |
| `satellites_4_el` | `float` | Satellite Count |
| `satellites_4_gnssid` | `float` | Satellite Count |
| `satellites_4_sigid` | `float` | Satellite Count |
| `satellites_4_ss` | `float` | Satellite Count |
| `satellites_4_svid` | `float` | Satellite Count |
| `satellites_5_PRN` | `float` | Satellite Count |
| `satellites_5_az` | `float` | Satellite Count |
| `satellites_5_el` | `float` | Satellite Count |
| `satellites_5_gnssid` | `float` | Satellite Count |
| `satellites_5_sigid` | `float` | Satellite Count |
| `satellites_5_ss` | `float` | Satellite Count |
| `satellites_5_svid` | `float` | Satellite Count |
| `satellites_6_PRN` | `float` | Satellite Count |
| `satellites_6_az` | `float` | Satellite Count |
| `satellites_6_el` | `float` | Satellite Count |
| `satellites_6_gnssid` | `float` | Satellite Count |
| `satellites_6_sigid` | `float` | Satellite Count |
| `satellites_6_ss` | `float` | Satellite Count |
| `satellites_6_svid` | `float` | Satellite Count |
| `satellites_7_PRN` | `float` | Satellite Count |
| `satellites_7_az` | `float` | Satellite Count |
| `satellites_7_el` | `float` | Satellite Count |
| `satellites_7_gnssid` | `float` | Satellite Count |
| `satellites_7_sigid` | `float` | Satellite Count |
| `satellites_7_ss` | `float` | Satellite Count |
| `satellites_7_svid` | `float` | Satellite Count |
| `satellites_8_PRN` | `float` | Satellite Count |
| `satellites_8_az` | `float` | Satellite Count |
| `satellites_8_el` | `float` | Satellite Count |
| `satellites_8_gnssid` | `float` | Satellite Count |
| `satellites_8_sigid` | `float` | Satellite Count |
| `satellites_8_ss` | `float` | Satellite Count |
| `satellites_8_svid` | `float` | Satellite Count |
| `satellites_9_PRN` | `float` | Satellite Count |
| `satellites_9_az` | `float` | Satellite Count |
| `satellites_9_el` | `float` | Satellite Count |
| `satellites_9_gnssid` | `float` | Satellite Count |
| `satellites_9_sigid` | `float` | Satellite Count |
| `satellites_9_ss` | `float` | Satellite Count |
| `satellites_9_svid` | `float` | Satellite Count |
| `satellites_used` | `float` | Satellite Count |
| `satellites_visible` | `float` | Satellite Count |
| `sep` | `float` | Raw Value |
| `speed` | `float` | Ground Speed (kts) |
| `status` | `float` | Raw Value |
| `tdop` | `float` | Raw Value |
| `track` | `float` | Heading (deg) |
| `uSat` | `float` | Raw Value |
| `vdop` | `float` | Raw Value |
| `xdop` | `float` | Raw Value |
| `ydop` | `float` | Raw Value |

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
| `alt` | `float` | Altitude (ft/m) |
| `altHAE` | `float` | Altitude (ft/m) |
| `altMSL` | `float` | Altitude (ft/m) |
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
| `epx` | `float` | Horizontal Precision (m) |
| `epy` | `float` | Vertical Precision (m) |
| `geoidSep` | `float` | Raw Value |
| `lat` | `float` | Latitude (deg) |
| `leapseconds` | `float` | Raw Value |
| `lon` | `float` | Longitude (deg) |
| `magtrack` | `float` | Heading (deg) |
| `magvar` | `float` | Raw Value |
| `mode` | `float` | Raw Value |
| `sep` | `float` | Raw Value |
| `speed` | `float` | Ground Speed (kts) |
| `status` | `float` | Raw Value |
| `track` | `float` | Heading (deg) |

---
## `integrity_check`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `icao` | Aircraft Hex ID |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `is_spoofed` | `integer` | Raw Value |
| `lat_error` | `float` | Latitude (deg) |
| `lon_error` | `float` | Longitude (deg) |

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
| `alt_baro_ft` | `integer` | Altitude (ft/m) |
| `gs_knots` | `float` | Ground Speed (kts) |
| `lat` | `float` | Latitude (deg) |
| `lon` | `float` | Longitude (deg) |
| `origin_data` | `string` | Raw Value |
| `track` | `float` | Heading (deg) |
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
| `airborne_msg` | `integer` | Message Count |
| `cpu_sec` | `float` | CPU Usage (%) |
| `messages` | `integer` | Raw Value |
| `messages_total_lifetime` | `integer` | Raw Value |
| `signal_db` | `float` | Signal Strength (dB) |
| `strong_signals` | `integer` | Signal Strength (dB) |

---
## `local_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `source` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `aircraft_count` | `integer` | Raw Value |

---
## `mem`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `role` | Metadata |
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
| `violation` | `string` | Latitude (deg) |

---
## `readsb`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `cpr_airborne` | `float` | Raw Value |
| `cpr_global_bad` | `float` | Raw Value |
| `cpr_global_ok` | `float` | Raw Value |
| `cpr_global_skipped` | `float` | Raw Value |
| `cpr_global_speed` | `float` | Ground Speed (kts) |
| `cpr_local_aircraft_relative` | `float` | Latitude (deg) |
| `cpr_local_ok` | `float` | Raw Value |
| `cpr_local_range` | `float` | Raw Value |
| `cpr_local_skipped` | `float` | Raw Value |
| `cpr_local_speed` | `float` | Ground Speed (kts) |
| `cpr_surface` | `float` | Raw Value |
| `cpu_background` | `float` | CPU Usage (%) |
| `messages` | `float` | Raw Value |
| `remote_accepted` | `float` | Raw Value |
| `remote_modeac` | `float` | Raw Value |
| `remote_modes` | `float` | Raw Value |
| `remote_unknown_icao` | `float` | Raw Value |
| `tracks_new` | `float` | Heading (deg) |
| `tracks_single_message` | `float` | Heading (deg) |
| `tracks_with_position` | `float` | Heading (deg) |

---
## `rf_battle_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |
| `role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `activity_score` | `integer` | Raw Value |
| `alt_high` | `integer` | Altitude (ft/m) |
| `alt_low` | `integer` | Altitude (ft/m) |
| `alt_mid` | `integer` | Altitude (ft/m) |
| `ground_count` | `integer` | Raw Value |
| `max_range_nm` | `float` | Raw Value |
| `msg_rate` | `integer` | Message Count |
| `rssi_db` | `float` | Signal Strength (dB) |
| `total_count` | `integer` | Raw Value |

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
| `altitude` | `float` | Altitude (ft/m) |
| `callsign` | `string` | Raw Value |
| `speed` | `float` | Ground Speed (kts) |
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
| `alert_val` | `integer` | Raw Value |
| `diff_km` | `float` | Raw Value |
| `fr24_lat` | `float` | Latitude (deg) |
| `fr24_lon` | `float` | Longitude (deg) |
| `local_lat` | `float` | Latitude (deg) |
| `local_lon` | `float` | Longitude (deg) |
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
| `load1` | `float` | Raw Value |
| `load15` | `float` | Raw Value |
| `load5` | `float` | Raw Value |
| `n_cpus` | `integer` | CPU Usage (%) |
| `uptime` | `integer` | Raw Value |
| `uptime_format` | `string` | Raw Value |

---
## `system_stats`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `cpu_model` | Metadata |
| `host` | Sensor Identity |
| `placement` | Metadata |
| `role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `cpu_temp` | `float` | Temperature (C) |
| `cpu_usage` | `float` | CPU Usage (%) |
| `disk_usage` | `float` | Raw Value |
| `ram_usage` | `float` | Raw Value |
| `uptime` | `integer` | Raw Value |

---
## `telegraf_test`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `host` | Sensor Identity |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `value` | `float` | Raw Value |

---
## `temp`
### 🏷️ Tags (Indexed)
| Tag Key | Description |
| :--- | :--- |
| `gnss_type` | Metadata |
| `host` | Sensor Identity |
| `location` | Metadata |
| `placement` | Metadata |
| `role` | Metadata |
| `sensor` | Metadata |
| `sensor_role` | Metadata |

### 🔢 Fields (Metrics)
| Field Key | Type | Description |
| :--- | :--- | :--- |
| `temp` | `float` | Temperature (C) |

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
| `temperature_c` | `float` | Temperature (C) |
| `visibility_miles` | `float` | Raw Value |
| `wind_dir_deg` | `float` | Raw Value |
| `wind_speed_kt` | `float` | Ground Speed (kts) |

---
