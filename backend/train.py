import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from data_fetcher import build_dataset, TRAINING_DATA_PATH

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "models.joblib")

def train_models():
    # Load dataset
    if not os.path.exists(TRAINING_DATA_PATH) or os.path.getsize(TRAINING_DATA_PATH) < 100:
        print("Training data not found. Compiling...")
        df = build_dataset()
    else:
        df = pd.read_csv(TRAINING_DATA_PATH)
        
    if len(df) < 5:
        print("Not enough training samples. Re-building dataset...")
        df = build_dataset()
        
    print(f"Loaded {len(df)} samples for training.")
    
    # Features & Targets
    features = [
        "inc_diff", "raan_diff", "ecc_diff", 
        "arg_perigee_diff", "mean_motion_diff", 
        "a_diff", "alt_diff", "is_debris1", "is_debris2"
    ]
    
    X = df[features]
    y_range = df["target_range"]
    y_speed = df["target_speed"]
    y_prob = df["target_prob"]
    y_log_prob = np.log10(np.clip(y_prob, 1e-12, 1.0))
    
    # Train test splits
    X_train, X_test, y_train_range, y_test_range = train_test_split(X, y_range, test_size=0.2, random_state=42)
    _, _, y_train_speed, y_test_speed = train_test_split(X, y_speed, test_size=0.2, random_state=42)
    _, _, y_train_prob, y_test_prob = train_test_split(X, y_prob, test_size=0.2, random_state=42)
    _, _, y_train_log_prob, y_test_log_prob = train_test_split(X, y_log_prob, test_size=0.2, random_state=42)
    
    print("Training RandomForest Regressors...")
    
    # 1. Miss Distance Regressor
    model_range = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=12)
    model_range.fit(X_train, y_train_range)
    pred_range = model_range.predict(X_test)
    mae_range = mean_absolute_error(y_test_range, pred_range)
    r2_range = r2_score(y_test_range, pred_range)
    print(f"Miss Distance Model - MAE: {mae_range:.4f} km, R2: {r2_range:.4f}")
    
    # 2. Relative Speed Regressor
    model_speed = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=12)
    model_speed.fit(X_train, y_train_speed)
    pred_speed = model_speed.predict(X_test)
    mae_speed = mean_absolute_error(y_test_speed, pred_speed)
    r2_speed = r2_score(y_test_speed, pred_speed)
    print(f"Relative Velocity Model - MAE: {mae_speed:.4f} km/s, R2: {r2_speed:.4f}")
    
    # 3. Collision Probability Regressor (Trained on log10-space for scale stability)
    model_prob = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=12)
    model_prob.fit(X_train, y_train_log_prob)
    pred_log_prob = model_prob.predict(X_test)
    pred_raw_prob = 10 ** pred_log_prob
    mae_prob = mean_absolute_error(y_test_prob, pred_raw_prob)
    r2_prob_raw = r2_score(y_test_prob, pred_raw_prob)
    r2_prob_log = r2_score(y_test_log_prob, pred_log_prob)
    print(f"Collision Probability Model - MAE: {mae_prob:.6f}, Log10 R2: {r2_prob_log:.4f} (Raw R2: {r2_prob_raw:.4f})")
    
    # Save the bundle
    payload = {
        "model_range": model_range,
        "model_speed": model_speed,
        "model_prob": model_prob,
        "features": features,
        "metrics": {
            "range_mae": float(mae_range),
            "range_r2": float(r2_range),
            "speed_mae": float(mae_speed),
            "speed_r2": float(r2_speed),
            "prob_mae": float(mae_prob),
            "prob_r2": float(r2_prob_raw),
            "prob_log_r2": float(r2_prob_log),
            "num_samples": len(df)
        }
    }
    
    joblib.dump(payload, MODEL_PATH)
    print(f"All models saved successfully to {MODEL_PATH}")
    return payload
    return payload

if __name__ == "__main__":
    train_models()
