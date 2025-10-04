How to use:

Install Pandas 

Put this script into your export folder where all your Apple Health CSVs live.

Run it in IDLE or with:python convert_to_googlefit.py

A new converted/ folder will appear with cleaned CSVs.

Each file will have only three columns:

timestamp,value,unit
2025-09-30T23:12:00+00:00,75,bpm

This version:

Reads tab-delimited Apple CSVs.

Computes midpoint between startDate and endDate as the timestamp.

Outputs timestamp,value,unit.

Handles workouts separately with richer fields.

################################################################## Script below save as python convert_to_googlefit.py

import pandas as pd
import os
from datetime import datetime

# === CONFIG ===
INPUT_DIR = "."
OUTPUT_DIR = "converted"

FILE_UNITS = {
    "heart_rate.csv": "bpm",
    "resting_hr.csv": "bpm",
    "hrv.csv": "ms",
    "steps.csv": "count",
    "active_energy.csv": "kcal",
    "cardio_fitness.csv": "ml/kg/min",
    "sleep.csv": "minutes",
    "workouts.csv": "workout",  # special
}

def parse_ts(ts):
    """Parse Apple-style timestamp into datetime object."""
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S %z")
    except Exception:
        return None

def convert_file(filename, unit):
    filepath = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"⚠️ Skipping {filename} (not found)")
        return

    try:
        df = pd.read_csv(filepath, sep="\t")
        if not {"startDate", "endDate", "value"}.issubset(df.columns):
            print(f"⚠️ {filename}: missing expected columns")
            return

        # Compute midpoint timestamp
        df["start_dt"] = df["startDate"].apply(parse_ts)
        df["end_dt"] = df["endDate"].apply(parse_ts)
        df["timestamp"] = df.apply(
            lambda row: (row["start_dt"] + (row["end_dt"] - row["start_dt"]) / 2).isoformat() 
            if row["start_dt"] and row["end_dt"] else row["startDate"], axis=1
        )

        df["unit"] = unit

        df_out = df[["timestamp", "value", "unit"]]
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        outpath = os.path.join(OUTPUT_DIR, filename)
        df_out.to_csv(outpath, index=False)
        print(f"✅ Converted {filename} -> {outpath}")

    except Exception as e:
        print(f"❌ Failed {filename}: {e}")

def convert_workouts(filename):
    filepath = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"⚠️ Skipping {filename} (not found)")
        return

    try:
        df = pd.read_csv(filepath, sep="\t")

        cols = {c.lower(): c for c in df.columns}
        out = pd.DataFrame()

        if "startdate" in cols:
            out["start_time"] = df[cols["startdate"]].apply(lambda x: parse_ts(str(x)).isoformat() if parse_ts(str(x)) else x)
        if "enddate" in cols:
            out["end_time"] = df[cols["enddate"]].apply(lambda x: parse_ts(str(x)).isoformat() if parse_ts(str(x)) else x)
        if "duration" in cols:
            out["duration_min"] = df[cols["duration"]]
        if "workouttype" in cols:
            out["activity_type"] = df[cols["workouttype"]]
        if "totalenergyburned" in cols:
            out["energy_kcal"] = df[cols["totalenergyburned"]]
        if "totaldistance" in cols:
            out["distance_km"] = df[cols["totaldistance"]]

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        outpath = os.path.join(OUTPUT_DIR, filename)
        out.to_csv(outpath, index=False)
        print(f"✅ Converted workouts -> {outpath}")

    except Exception as e:
        print(f"❌ Failed workouts: {e}")

def main():
    print("🔄 Converting Apple Health exports...")
    for fname, unit in FILE_UNITS.items():
        if unit == "workout":
            convert_workouts(fname)
        else:
            convert_file(fname, unit)
    print("🎉 All done. Check the 'converted' folder.")

if __name__ == "__main__":
    main()
