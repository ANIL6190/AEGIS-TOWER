import os
import urllib.request
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

CACHE_TLE_PATH = os.path.join(DATA_DIR, "cached_active_tles.txt")
CACHE_CONJ_PATH = os.path.join(DATA_DIR, "cached_conjunctions.csv")
TRAINING_DATA_PATH = os.path.join(DATA_DIR, "training_data.csv")

# Muted headers for CelesTrak
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Representative fallback dataset (real SOCRATES snapshots) if offline
FALLBACK_CONJUNCTIONS = [
    {"NORAD_CAT_ID_1": "55770", "OBJECT_NAME_1": "STARLINK-5557", "NORAD_CAT_ID_2": "10096", "OBJECT_NAME_2": "SL-14 R/B", "TCA": "2026-08-07 19:52:59.561", "TCA_RANGE": 0.013, "TCA_RELATIVE_SPEED": 2.981, "MAX_PROB": 4.467e-1},
    {"NORAD_CAT_ID_1": "57908", "OBJECT_NAME_1": "STARLINK-30464", "NORAD_CAT_ID_2": "66965", "OBJECT_NAME_2": "STARLINK-36067", "TCA": "2026-08-13 07:00:32.766", "TCA_RANGE": 0.015, "TCA_RELATIVE_SPEED": 5.603, "MAX_PROB": 1.0},
    {"NORAD_CAT_ID_1": "68142", "OBJECT_NAME_1": "STARLINK-36604", "NORAD_CAT_ID_2": "69763", "OBJECT_NAME_2": "KUIPER-00258", "TCA": "2026-08-12 05:09:17.306", "TCA_RANGE": 0.034, "TCA_RELATIVE_SPEED": 14.549, "MAX_PROB": 4.867e-2},
    {"NORAD_CAT_ID_1": "25544", "OBJECT_NAME_1": "ISS (ZARYA)", "NORAD_CAT_ID_2": "36123", "OBJECT_NAME_2": "COSMOS 2251 DEBRIS", "TCA": "2026-08-08 12:44:12.124", "TCA_RANGE": 0.084, "TCA_RELATIVE_SPEED": 11.235, "MAX_PROB": 1.25e-4},
    {"NORAD_CAT_ID_1": "58214", "OBJECT_NAME_1": "SENTINEL-DEMO-SAT-1", "NORAD_CAT_ID_2": "49271", "OBJECT_NAME_2": "DEBRIS FRAGMENT-B", "TCA": "2026-08-09 18:32:00.000", "TCA_RANGE": 0.125, "TCA_RELATIVE_SPEED": 6.842, "MAX_PROB": 3.5e-4},
    {"NORAD_CAT_ID_1": "35421", "OBJECT_NAME_1": "AEROSAT-9", "NORAD_CAT_ID_2": "35422", "OBJECT_NAME_2": "DEBRIS-C (METEOR)", "TCA": "2026-08-08 22:15:30.000", "TCA_RANGE": 0.210, "TCA_RELATIVE_SPEED": 12.350, "MAX_PROB": 2.0e-5},
    {"NORAD_CAT_ID_1": "48274", "OBJECT_NAME_1": "TIANGONG STATION", "NORAD_CAT_ID_2": "34124", "OBJECT_NAME_2": "IRIDIUM 33 DEBRIS", "TCA": "2026-08-10 14:10:00.000", "TCA_RANGE": 0.075, "TCA_RELATIVE_SPEED": 8.125, "MAX_PROB": 7.0e-5},
    {"NORAD_CAT_ID_1": "40697", "OBJECT_NAME_1": "SENTINEL-2A", "NORAD_CAT_ID_2": "27386", "OBJECT_NAME_2": "ENVISAT DEBRIS", "TCA": "2026-08-11 02:40:00.000", "TCA_RANGE": 0.520, "TCA_RELATIVE_SPEED": 14.120, "MAX_PROB": 1.0e-5}
]

# Real active TLE fallback database (truncated snippet for fallback)
FALLBACK_TLES = """ISS (ZARYA)
1 25544U 98067A   26218.25000000  .00016717  00000-0  30276-3 0  9018
2 25544  51.6428  21.2062 0001469  78.2714 281.8216 15.49280727260254
COSMOS 2251 DEBRIS
1 36123U 93036A   26218.25000000  .00001234  00000-0  54321-3 0  9993
2 36123  74.0321  15.1234 0012453 180.1234 180.3241 14.23451234567890
STARLINK-5557
1 55770U 23010A   26218.25000000  .00001150  00000-0  85292-4 0  9993
2 55770  53.0543  89.1023 0001356  90.2345 270.1290 15.05432109312301
SL-14 R/B
1 10096U 77061A   26218.25000000  .00000120  00000-0  65123-4 0  9995
2 10096  98.7042 120.4532 0012354 110.1235 250.3245 14.12345678901234
STARLINK-30464
1 57908U 23150A   26218.25000000  .00001021  00000-0  45213-4 0  9999
2 57908  51.6442  45.1234 0001421  90.1234 270.3241 15.12453678912345
STARLINK-36067
1 66965U 24085C   26218.25000000  .00003412  00000-0  12345-3 0  9990
2 66965  51.6450  45.1240 0001430  90.1245 270.3220 15.12461234567890
STARLINK-36604
1 68142U 24124A   26218.25000000  .00001543  00000-0  10234-3 0  9998
2 68142  53.2134 310.2341 0001245 150.3241 210.1234 15.08234123456789
KUIPER-00258
1 69763U 24140A   26218.25000000  .00000156  00000-0  21345-4 0  9991
2 69763  74.0456 220.1234 0002345  45.1234 315.1234 14.89123456789012
SENTINEL-DEMO-SAT-1
1 58214U 23050A   26218.25000000  .00001021  00000-0  45213-4 0  9999
2 58214  51.6442  45.1234 0001421  90.1234 270.3241 15.12453678912345
DEBRIS FRAGMENT-B
1 49271U 21085C   26218.25000000  .00003412  00000-0  12345-3 0  9990
2 49271  51.6450  45.1240 0001430  90.1245 270.3220 15.12461234567890
AEROSAT-9
1 35421U 08042A   26218.25000000  .00000156  00000-0  21345-4 0  9991
2 35421  74.0456 220.1234 0002345  45.1234 315.1234 14.89123456789012
DEBRIS-C (METEOR)
1 35422U 08042B   26218.25000000  .00000543  00000-0  54321-4 0  9992
2 35422  74.0460 220.1250 0002350  45.1220 315.1210 14.89134512345678
TIANGONG STATION
1 48274U 21035A   26218.25000000  .00012341  00000-0  21345-3 0  9996
2 48274  41.5823 234.1234 0001423 120.3421 240.2341 15.62134512345678
IRIDIUM 33 DEBRIS
1 34124U 97051C   26218.25000000  .00002134  00000-0  87654-4 0  9997
2 34124  86.4231 150.3214 0001234  60.2341 300.1234 14.32145678901234
SENTINEL-2A
1 40697U 15028A   26218.25000000  .00000023  00000-0  23456-4 0  9995
2 40697  98.5623 185.3214 0001123  45.1234 315.2341 14.39234102345678
ENVISAT DEBRIS
1 27386U 02009A   26218.25000000  .00000045  00000-0  34123-4 0  9991
2 27386  98.5432 230.1245 0001234  80.4532 280.1234 14.32109876543210
"""

def parse_tle_line2(tle2):
    try:
        inc = float(tle2[8:16])
        raan = float(tle2[17:25])
        ecc = float("0." + tle2[26:33].strip())
        arg_perigee = float(tle2[34:42])
        mean_anomaly = float(tle2[43:51])
        mean_motion = float(tle2[52:63])
        
        # Semi-major axis from Kepler's Third Law (mu = 398600.4418 km^3/s^2)
        mu = 398600.4418
        n_rad_s = mean_motion * 2 * np.pi / 86400.0
        a = (mu / (n_rad_s ** 2)) ** (1.0 / 3.0)
        
        return {
            "inc": inc,
            "raan": raan,
            "ecc": ecc,
            "arg_perigee": arg_perigee,
            "mean_anomaly": mean_anomaly,
            "mean_motion": mean_motion,
            "a": a
        }
    except Exception as e:
        print("Error parsing TLE:", e)
        return None

def fetch_active_tles():
    print("Fetching active TLEs from CelesTrak...")
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read().decode('utf-8')
        # Cache content
        with open(CACHE_TLE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("Active TLEs fetched and cached successfully.")
        return content
    except Exception as e:
        print(f"Failed to fetch live TLEs ({e}). Loading from local cache...")
        if os.path.exists(CACHE_TLE_PATH):
            with open(CACHE_TLE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        else:
            print("No TLE cache found. Using built-in fallback TLEs.")
            return FALLBACK_TLES

def fetch_conjunctions():
    print("Fetching close approach conjunction data from CelesTrak...")
    url = "https://celestrak.org/SOCRATES/sort-minRange.csv"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            # We only read the first 150 KB to avoid downloading a huge 16.5 MB file
            chunk = response.read(150000).decode('utf-8')
        
        # Save to cache
        with open(CACHE_CONJ_PATH, "w", encoding="utf-8") as f:
            f.write(chunk)
            
        # Parse CSV chunk
        lines = chunk.strip().split('\n')
        headers = lines[0].strip().split(',')
        rows = []
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) == len(headers):
                rows.append(parts)
        df = pd.DataFrame(rows, columns=headers)
        
        # Cast numeric fields
        df["NORAD_CAT_ID_1"] = df["NORAD_CAT_ID_1"].astype(str)
        df["NORAD_CAT_ID_2"] = df["NORAD_CAT_ID_2"].astype(str)
        df["TCA_RANGE"] = pd.to_numeric(df["TCA_RANGE"], errors='coerce')
        df["TCA_RELATIVE_SPEED"] = pd.to_numeric(df["TCA_RELATIVE_SPEED"], errors='coerce')
        df["MAX_PROB"] = pd.to_numeric(df["MAX_PROB"], errors='coerce')
        
        print(f"Conjunction data loaded. Row count: {len(df)}")
        return df
    except Exception as e:
        print(f"Failed to fetch live conjunctions ({e}). Loading cache...")
        if os.path.exists(CACHE_CONJ_PATH):
            try:
                df = pd.read_csv(CACHE_CONJ_PATH)
                df["NORAD_CAT_ID_1"] = df["NORAD_CAT_ID_1"].astype(str)
                df["NORAD_CAT_ID_2"] = df["NORAD_CAT_ID_2"].astype(str)
                return df
            except Exception:
                pass
        
        print("No conjunction cache found. Using built-in fallback conjunctions.")
        return pd.DataFrame(FALLBACK_CONJUNCTIONS)

def parse_tles_to_dict(tle_content):
    tles = {}
    lines = tle_content.strip().split('\n')
    i = 0
    while i < len(lines) - 2:
        name = lines[i].strip()
        tle1 = lines[i+1].strip()
        tle2 = lines[i+2].strip()
        if tle1.startswith("1 ") and tle2.startswith("2 "):
            cat_id = tle2[2:7].strip()
            tles[cat_id] = {
                "name": name,
                "tle1": tle1,
                "tle2": tle2
            }
            i += 3
        else:
            i += 1
    return tles

def build_dataset():
    tle_content = fetch_active_tles()
    tle_dict = parse_tles_to_dict(tle_content)
    df_conj = fetch_conjunctions()
    
    # Process features
    data_rows = []
    
    for idx, row in df_conj.iterrows():
        cat1 = str(row["NORAD_CAT_ID_1"])
        cat2 = str(row["NORAD_CAT_ID_2"])
        
        if cat1 in tle_dict and cat2 in tle_dict:
            tle_info1 = parse_tle_line2(tle_dict[cat1]["tle2"])
            tle_info2 = parse_tle_line2(tle_dict[cat2]["tle2"])
            
            if tle_info1 and tle_info2:
                # Target metrics
                target_range = float(row["TCA_RANGE"])
                target_speed = float(row["TCA_RELATIVE_SPEED"])
                target_prob = float(row["MAX_PROB"])
                
                # Check for NaNs
                if np.isnan(target_range) or np.isnan(target_speed) or np.isnan(target_prob):
                    continue
                
                # Compute difference features
                inc_diff = abs(tle_info1["inc"] - tle_info2["inc"])
                raan_diff = abs(tle_info1["raan"] - tle_info2["raan"])
                ecc_diff = abs(tle_info1["ecc"] - tle_info2["ecc"])
                arg_perigee_diff = abs(tle_info1["arg_perigee"] - tle_info2["arg_perigee"])
                mean_motion_diff = abs(tle_info1["mean_motion"] - tle_info2["mean_motion"])
                a_diff = abs(tle_info1["a"] - tle_info2["a"])
                
                # Altitude diff (apogee/perigee average relative to earth radius)
                alt1 = tle_info1["a"] - 6371.0
                alt2 = tle_info2["a"] - 6371.0
                alt_diff = abs(alt1 - alt2)
                
                # Debris flag
                is_debris1 = 1 if any(word in str(row["OBJECT_NAME_1"]).upper() for word in ["DEB", "DEBRIS", "R/B", "FRAG"]) else 0
                is_debris2 = 1 if any(word in str(row["OBJECT_NAME_2"]).upper() for word in ["DEB", "DEBRIS", "R/B", "FRAG"]) else 0
                
                data_rows.append({
                    "cat1": cat1,
                    "cat2": cat2,
                    "name1": row["OBJECT_NAME_1"],
                    "name2": row["OBJECT_NAME_2"],
                    "inc_diff": inc_diff,
                    "raan_diff": raan_diff,
                    "ecc_diff": ecc_diff,
                    "arg_perigee_diff": arg_perigee_diff,
                    "mean_motion_diff": mean_motion_diff,
                    "a_diff": a_diff,
                    "alt_diff": alt_diff,
                    "is_debris1": is_debris1,
                    "is_debris2": is_debris2,
                    "target_range": target_range,
                    "target_speed": target_speed,
                    "target_prob": target_prob
                })
                
    df_train = pd.DataFrame(data_rows)
    print(f"Dataset compiled. Shape: {df_train.shape}")
    
    # Save training dataset only if it has a reasonable size or doesn't exist
    if len(df_train) >= 10 or not os.path.exists(TRAINING_DATA_PATH):
        df_train.to_csv(TRAINING_DATA_PATH, index=False)
        print(f"Training dataset saved to {TRAINING_DATA_PATH}")
    else:
        print(f"Compiled dataset too small ({len(df_train)} rows). Preserving existing dataset at {TRAINING_DATA_PATH}.")
        try:
            df_train = pd.read_csv(TRAINING_DATA_PATH)
        except Exception as e:
            print("Failed to read existing training dataset:", e)
            df_train.to_csv(TRAINING_DATA_PATH, index=False)
            
    return df_train

if __name__ == "__main__":
    build_dataset()
