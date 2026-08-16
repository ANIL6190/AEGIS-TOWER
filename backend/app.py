import os
import re
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

from data_fetcher import parse_tle_line2
from train import train_models, MODEL_PATH

app = Flask(__name__)
CORS(app)

# Load ML Models
models = None
def load_models_lazy():
    global models
    if models is None:
        if not os.path.exists(MODEL_PATH):
            print("Model files not found. Initiating training...")
            train_models()
        try:
            models = joblib.load(MODEL_PATH)
            print("ML models loaded successfully.")
        except Exception as e:
            print("Error loading models:", e)
    return models

# ── Keplerian Propagator ──────────────────────────────────────────────────────
def propagate_kepler(params, epoch_base, target_time):
    """
    Propagates a satellite using simplified Keplerian mechanics.
    params dict expects keys: inclination, raan, eccentricity, arg_perigee,
                              mean_anomaly, mean_motion, a
    """
    mu = 398600.4418  # km^3 / s^2
    n_rad_s = params["mean_motion"] * 2 * np.pi / 86400.0
    a = params["a"]

    dt = (target_time - epoch_base).total_seconds()

    M_0 = np.radians(params["mean_anomaly"])
    M = (M_0 + n_rad_s * dt) % (2 * np.pi)

    # Solve Kepler's Equation (Newton-Raphson)
    e = params["eccentricity"]
    E = M
    for _ in range(10):
        dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= dE
        if abs(dE) < 1e-10:
            break

    x_orbital = a * (np.cos(E) - e)
    y_orbital = a * np.sqrt(max(0, 1 - e**2)) * np.sin(E)

    i = np.radians(params["inclination"])
    Omega = np.radians(params["raan"])
    omega = np.radians(params["arg_perigee"])

    cos_o, sin_o = np.cos(omega), np.sin(omega)
    cos_O, sin_O = np.cos(Omega), np.sin(Omega)
    cos_i, sin_i = np.cos(i), np.sin(i)

    # Rotation matrix from orbital to ECI
    P_x = cos_O * cos_o - sin_O * sin_o * cos_i
    P_y = sin_O * cos_o + cos_O * sin_o * cos_i
    P_z = sin_o * sin_i

    Q_x = -cos_O * sin_o - sin_O * cos_o * cos_i
    Q_y = -sin_O * sin_o + cos_O * cos_o * cos_i
    Q_z = cos_o * sin_i

    x = x_orbital * P_x + y_orbital * Q_x
    y = x_orbital * P_y + y_orbital * Q_y
    z = x_orbital * P_z + y_orbital * Q_z

    return np.array([x, y, z])


# ── Satellite Inventory Loader ────────────────────────────────────────────────
SATELLITES_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "data", "satellites.js"
)

def load_satellites():
    """
    Parses the TLE_DATA array from src/data/satellites.js.
    Falls back to an inline hardcoded list if the JS file can't be parsed.
    """
    try:
        js_path = os.path.abspath(SATELLITES_JS_PATH)
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract the array body between [ and the closing ]; of TLE_DATA
        match = re.search(
            r"export\s+const\s+TLE_DATA\s*=\s*(\[[\s\S]*?\]);",
            content
        )
        if not match:
            raise ValueError("TLE_DATA export not found in satellites.js")

        raw_js = match.group(1)

        # Convert JS object syntax to JSON:
        # 1. Remove trailing commas before ] or }
        raw_js = re.sub(r",\s*([\]}])", r"\1", raw_js)
        # 2. Quote unquoted keys (word characters before colon)
        raw_js = re.sub(r'(?<!["\w])(\w+)\s*:', r'"\1":', raw_js)
        # 3. Remove any remaining single-line JS comments
        raw_js = re.sub(r"//[^\n]*", "", raw_js)

        sats = json.loads(raw_js)
        print(f"Loaded {len(sats)} satellites from satellites.js")
        return sats

    except Exception as e:
        print(f"Warning: could not parse satellites.js ({e}). Using hardcoded fallback.")
        return _FALLBACK_SATELLITES()


def _FALLBACK_SATELLITES():
    return [
        {"id": "25544", "name": "ISS (ZARYA)",        "type": "satellite",
         "tle1": "1 25544U 98067A   26218.25000000  .00016717  00000-0  30276-3 0  9018",
         "tle2": "2 25544  51.6428  21.2062 0001469  78.2714 281.8216 15.49280727260254"},
        {"id": "36123", "name": "COSMOS 2251 DEBRIS",  "type": "debris",
         "tle1": "1 36123U 93036A   26218.25000000  .00001234  00000-0  54321-3 0  9993",
         "tle2": "2 36123  74.0321  15.1234 0012453 180.1234 180.3241 14.23451234567890"},
        {"id": "58214", "name": "SENTINEL-DEMO-SAT-1", "type": "satellite",
         "tle1": "1 58214U 23050A   26218.25000000  .00001021  00000-0  45213-4 0  9999",
         "tle2": "2 58214  51.6442  45.1234 0001421  90.1234 270.3241 15.12453678912345"},
        {"id": "49271", "name": "DEBRIS FRAGMENT-B",   "type": "debris",
         "tle1": "1 49271U 21085C   26218.25000000  .00003412  00000-0  12345-3 0  9990",
         "tle2": "2 49271  51.6450  45.1240 0001430  90.1245 270.3220 15.12461234567890"},
        {"id": "35421", "name": "AEROSAT-9",           "type": "satellite",
         "tle1": "1 35421U 08042A   26218.25000000  .00000156  00000-0  21345-4 0  9991",
         "tle2": "2 35421  74.0456 220.1234 0002345  45.1234 315.1234 14.89123456789012"},
        {"id": "35422", "name": "DEBRIS-C (METEOR)",   "type": "debris",
         "tle1": "1 35422U 08042B   26218.25000000  .00000543  00000-0  54321-4 0  9992",
         "tle2": "2 35422  74.0460 220.1250 0002350  45.1220 315.1210 14.89134512345678"},
        {"id": "48274", "name": "TIANGONG STATION",    "type": "satellite",
         "tle1": "1 48274U 21035A   26218.25000000  .00012341  00000-0  21345-3 0  9996",
         "tle2": "2 48274  41.5823 234.1234 0001423 120.3421 240.2341 15.62134512345678"},
        {"id": "34124", "name": "IRIDIUM 33 DEBRIS",   "type": "debris",
         "tle1": "1 34124U 97051C   26218.25000000  .00002134  00000-0  87654-4 0  9997",
         "tle2": "2 34124  86.4231 150.3214 0001234  60.2341 300.1234 14.32145678901234"},
        {"id": "40697", "name": "SENTINEL-2A",          "type": "satellite",
         "tle1": "1 40697U 15028A   26218.25000000  .00000023  00000-0  23456-4 0  9995",
         "tle2": "2 40697  98.5623 185.3214 0001123  45.1234 315.2341 14.39234102345678"},
        {"id": "27386", "name": "ENVISAT DEBRIS",       "type": "debris",
         "tle1": "1 27386U 02009A   26218.25000000  .00000045  00000-0  34123-4 0  9991",
         "tle2": "2 27386  98.5432 230.1245 0001234  80.4532 280.1234 14.32109876543210"},
    ]


def _parse_epoch(tle1_str):
    """Parse TLE Line 1 epoch to a datetime."""
    try:
        epoch_str = tle1_str[18:32].strip()
        epoch_year2 = int(epoch_str[:2])
        year = 2000 + epoch_year2 if epoch_year2 < 57 else 1900 + epoch_year2
        epoch_day = float(epoch_str[2:])
        return datetime(year, 1, 1) + timedelta(days=epoch_day - 1)
    except Exception:
        return datetime.now()


# ── Conjunction Computation Cache ─────────────────────────────────────────────
conjunctions_cache = None
cache_timestamp = None
CACHE_TTL_SECONDS = 30  # Refresh every 30 seconds


def compute_all_conjunctions():
    global conjunctions_cache, cache_timestamp

    now = datetime.now()
    if conjunctions_cache is not None and cache_timestamp is not None:
        if (now - cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
            return conjunctions_cache

    sats = load_satellites()
    payload = load_models_lazy()
    if not payload:
        print("ML models unavailable — returning empty conjunction list.")
        return []

    model_prob = payload["model_prob"]

    # Parse all satellite TLEs into propagator-ready dicts
    parsed_sats = []
    for s in sats:
        tle_info = parse_tle_line2(s.get("tle2", ""))
        if not tle_info:
            continue
        epoch_base = _parse_epoch(s.get("tle1", ""))
        parsed_sats.append({
            "id":           s["id"],
            "name":         s["name"],
            "type":         s.get("type", "satellite"),
            # Use consistent key names matching propagate_kepler
            "inclination":  tle_info["inc"],
            "raan":         tle_info["raan"],
            "eccentricity": tle_info["ecc"],
            "arg_perigee":  tle_info["arg_perigee"],
            "mean_anomaly": tle_info["mean_anomaly"],
            "mean_motion":  tle_info["mean_motion"],
            "a":            tle_info["a"],
            # Also keep short names for feature computation
            "inc":          tle_info["inc"],
            "ecc":          tle_info["ecc"],
            "epoch_base":   epoch_base,
        })

    conjunctions = []
    search_start = datetime.now()

    for i in range(len(parsed_sats)):
        for j in range(i + 1, len(parsed_sats)):
            s1 = parsed_sats[i]
            s2 = parsed_sats[j]

            # ── Altitude proximity filter ──────────────────────────────────
            alt1 = s1["a"] - 6371.0
            alt2 = s2["a"] - 6371.0
            if abs(alt1 - alt2) > 200:  # km — skip widely separated orbits
                continue

            # ── Coarse scan: 48-hour window at 15-min steps ────────────────
            min_dist = float("inf")
            tca_time = None

            try:
                for step_m in range(0, 2881, 15):
                    t = search_start + timedelta(minutes=step_m)
                    pos1 = propagate_kepler(s1, s1["epoch_base"], t)
                    pos2 = propagate_kepler(s2, s2["epoch_base"], t)
                    d = np.linalg.norm(pos1 - pos2)
                    if d < min_dist:
                        min_dist = d
                        tca_time = t

                # ── Refinement: ±15 min around coarse TCA at 1-min steps ───
                if tca_time:
                    refine_start = tca_time - timedelta(minutes=15)
                    for step_m in range(31):
                        t = refine_start + timedelta(minutes=step_m)
                        pos1 = propagate_kepler(s1, s1["epoch_base"], t)
                        pos2 = propagate_kepler(s2, s2["epoch_base"], t)
                        d = np.linalg.norm(pos1 - pos2)
                        if d < min_dist:
                            min_dist = d
                            tca_time = t

            except Exception as prop_err:
                print(f"Propagation error for {s1['id']}/{s2['id']}: {prop_err}")
                continue

            # ── Only keep conjunctions within 50 km miss distance ──────────
            if min_dist >= 50.0:
                continue

            # ── Relative velocity at TCA ───────────────────────────────────
            try:
                t_plus = tca_time + timedelta(seconds=1)
                p1_tca  = propagate_kepler(s1, s1["epoch_base"], tca_time)
                p1_plus = propagate_kepler(s1, s1["epoch_base"], t_plus)
                p2_tca  = propagate_kepler(s2, s2["epoch_base"], tca_time)
                p2_plus = propagate_kepler(s2, s2["epoch_base"], t_plus)
                rel_v = float(np.linalg.norm((p1_plus - p1_tca) - (p2_plus - p2_tca)))
            except Exception:
                rel_v = 7.5  # Default LEO relative speed (km/s) if computation fails

            # ── ML Feature vector ──────────────────────────────────────────
            inc_diff          = abs(s1["inc"]         - s2["inc"])
            raan_diff         = abs(s1["raan"]        - s2["raan"])
            ecc_diff          = abs(s1["ecc"]         - s2["ecc"])
            arg_perigee_diff  = abs(s1["arg_perigee"] - s2["arg_perigee"])
            mean_motion_diff  = abs(s1["mean_motion"] - s2["mean_motion"])
            a_diff            = abs(s1["a"]           - s2["a"])
            alt_diff          = abs(alt1 - alt2)
            is_deb1 = 1 if s1["type"] == "debris" else 0
            is_deb2 = 1 if s2["type"] == "debris" else 0

            feat_df = pd.DataFrame([{
                "inc_diff":          inc_diff,
                "raan_diff":         raan_diff,
                "ecc_diff":          ecc_diff,
                "arg_perigee_diff":  arg_perigee_diff,
                "mean_motion_diff":  mean_motion_diff,
                "a_diff":            a_diff,
                "alt_diff":          alt_diff,
                "is_debris1":        is_deb1,
                "is_debris2":        is_deb2,
            }])

            # ── Predict collision probability (model outputs log10 probability) ───
            try:
                pred_log_prob = float(model_prob.predict(feat_df)[0])
                pred_prob = float(10 ** pred_log_prob)
            except Exception as ml_err:
                print(f"ML prediction error: {ml_err}")
                pred_prob = 0.0001

            # Blend ML prediction with physical proximity signal
            prob_distance_factor = float(np.exp(-min_dist / 8.0))
            final_prob = float(np.clip(pred_prob * 0.4 + prob_distance_factor * 0.6, 1e-7, 0.9999))

            # ── Risk tier ──────────────────────────────────────────────────
            risk = "LOW"
            if final_prob >= 0.001:
                risk = "HIGH"
            elif final_prob >= 0.00005:
                risk = "MEDIUM"

            lead_time_hours = (tca_time - datetime.now()).total_seconds() / 3600.0

            # Build history from a linear interpolation backwards
            prob_hist = [
                round(final_prob * f, 7)
                for f in [0.4, 0.55, 0.65, 0.75, 0.85, 0.9, 0.95, 1.0]
            ]

            conjunctions.append({
                "id":                           f"CA-{s1['id']}-{s2['id']}",
                "primaryObject":                {"id": s1["id"], "name": s1["name"]},
                "secondaryObject":              {"id": s2["id"], "name": s2["name"]},
                "timeToTcaHours":               float(np.clip(lead_time_hours, 0.1, 200.0)),
                "missDistanceKm":               float(min_dist),
                "relativeVelocityKmS":          float(rel_v),
                "predictedProbabilityOfCollision": final_prob,
                "riskClassification":           risk,
                "trend":                        "increasing" if final_prob > 0.0005 else "stable",
                "confidence":                   float(np.clip(0.75 + 0.25 * (1.0 - final_prob / 0.01), 0.75, 0.99)),
                "history":                      prob_hist,
                "pathTrend":                    "increasing" if final_prob > 0.0001 else "stable",
            })

    # Sort: HIGH → MEDIUM → LOW, then ascending miss distance
    tier_weight = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    conjunctions.sort(
        key=lambda x: (-tier_weight[x["riskClassification"]], x["missDistanceKm"])
    )

    conjunctions_cache = conjunctions
    cache_timestamp = now
    print(f"Computed {len(conjunctions)} conjunction events.")
    return conjunctions


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def get_index_api():
    payload = load_models_lazy()
    model_loaded = payload is not None
    return jsonify({
        "name": "AEGIS TOWER Space Situational Awareness ML API",
        "status": "online",
        "version": "3.2.0",
        "ml_model_loaded": model_loaded,
        "available_endpoints": {
            "GET  /": "This status dashboard",
            "GET  /api/status": "Detailed diagnostics of trained ML models",
            "GET  /api/conjunctions": "Computed active close approaches from live Keplerian propagation",
            "GET  /api/satellites": "Complete catalogue of tracked active satellites & debris catalog",
            "POST /api/predict": "Run collision probability predictions for TLE pairs",
            "POST /api/train": "Manually trigger retraining on raw SOCRATES datasets"
        }
    })


@app.route("/api/satellites", methods=["GET"])
def get_satellites_api():
    sats = load_satellites()
    # Strip TLE strings for the frontend (keep id, name, type, tle1, tle2)
    return jsonify(sats)


@app.route("/api/conjunctions", methods=["GET"])
def get_conjunctions_api():
    try:
        conjs = compute_all_conjunctions()
        return jsonify(conjs)
    except Exception as e:
        print("Error computing conjunctions:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def post_predict_api():
    data = request.json or {}
    tle2_1 = data.get("tle2_1", "")
    tle2_2 = data.get("tle2_2", "")

    tle_info1 = parse_tle_line2(tle2_1)
    tle_info2 = parse_tle_line2(tle2_2)

    if not tle_info1 or not tle_info2:
        return jsonify({"error": "Failed to parse TLE inputs"}), 400

    payload = load_models_lazy()
    if not payload:
        return jsonify({"error": "Model not loaded"}), 500

    model_prob = payload["model_prob"]

    inc_diff         = abs(tle_info1["inc"]         - tle_info2["inc"])
    raan_diff        = abs(tle_info1["raan"]        - tle_info2["raan"])
    ecc_diff         = abs(tle_info1["ecc"]         - tle_info2["ecc"])
    arg_perigee_diff = abs(tle_info1["arg_perigee"] - tle_info2["arg_perigee"])
    mean_motion_diff = abs(tle_info1["mean_motion"] - tle_info2["mean_motion"])
    a_diff           = abs(tle_info1["a"]           - tle_info2["a"])
    alt1 = tle_info1["a"] - 6371.0
    alt2 = tle_info2["a"] - 6371.0
    alt_diff = abs(alt1 - alt2)

    feat_df = pd.DataFrame([{
        "inc_diff":         inc_diff,
        "raan_diff":        raan_diff,
        "ecc_diff":         ecc_diff,
        "arg_perigee_diff": arg_perigee_diff,
        "mean_motion_diff": mean_motion_diff,
        "a_diff":           a_diff,
        "alt_diff":         alt_diff,
        "is_debris1":       data.get("is_debris1", 0),
        "is_debris2":       data.get("is_debris2", 1),
    }])

    pred_log_prob = float(model_prob.predict(feat_df)[0])
    pred_prob = float(10 ** pred_log_prob)

    return jsonify({
        "inc_diff":             inc_diff,
        "raan_diff":            raan_diff,
        "predicted_probability": pred_prob,
        "recommended_risk":     "HIGH" if pred_prob >= 0.001 else "MEDIUM" if pred_prob >= 0.00005 else "LOW",
    })


@app.route("/api/status", methods=["GET"])
def get_status_api():
    payload = load_models_lazy()
    if not payload:
        return jsonify({"status": "Not trained", "model_loaded": False})
    return jsonify({
        "status":       "Model active",
        "model_loaded": True,
        "metrics":      payload.get("metrics", {}),
    })


@app.route("/api/train", methods=["POST"])
def post_train_api():
    try:
        train_models()
        global models
        models = None  # Reset cache so models are reloaded
        return jsonify({"message": "Model trained and reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    load_models_lazy()
    app.run(port=5000, debug=True, use_reloader=False)
