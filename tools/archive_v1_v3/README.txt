Project Platinum: Central Brain Data Archive v3.2
Release Date: Wed Dec 24 01:12:44 EET 2025
Maintainer: Riku

CONTENTS:
1. Data Files
   - raw_dump_*_platinum.parquet: AI-Ready dataset.
     * Features: Sensor Fusion (RSSI Delta), Physics Errors, 1Hz Standardized.
   - raw_dump_*_local_aircraft_state.json: Raw source logs for verification.

2. Scripts
   - daily_injector.sh: Automated pipeline (Google Drive Sync enabled).
   - dump_raw_campaign.py: Data extractor (supports --date for history).
   - process_dataset_platinum_v2.py: The refinery logic.

HOW TO USE:
- Load the Parquet file into Pandas/PyTorch.
- Key Training Columns: 'rssi_delta', 'error_dist_km', 'dist_to_efhk_km'.
