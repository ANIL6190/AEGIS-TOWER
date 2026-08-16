import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
TRAINING_DATA_PATH = os.path.join(DATA_DIR, "training_data.csv")

def generate_rich_dataset(n_samples=500):
    print(f"Generating {n_samples} physically-consistent conjunction records for training...")
    np.random.seed(42)
    
    # 1. Inputs: Orbital differences
    inc_diff = np.random.uniform(0.0, 90.0, n_samples)
    raan_diff = np.random.uniform(0.0, 180.0, n_samples)
    ecc_diff = np.random.uniform(0.0, 0.02, n_samples)
    arg_perigee_diff = np.random.uniform(0.0, 180.0, n_samples)
    mean_motion_diff = np.random.uniform(0.0, 3.0, n_samples)
    
    # a_diff and alt_diff are highly correlated (semi-major axis diff and altitude diff)
    a_diff = np.random.uniform(0.05, 45.0, n_samples)
    alt_diff = a_diff * (1.0 + np.random.normal(0, 0.1, n_samples))
    alt_diff = np.clip(alt_diff, 0.01, 100.0)
    
    is_debris1 = np.random.binomial(1, 0.35, n_samples)
    is_debris2 = np.random.binomial(1, 0.40, n_samples)
    
    # 2. Outputs: Conjunction metrics based on orbital mechanics
    # Miss distance: strongly related to altitude difference and semi-major axis difference
    target_range = 0.01 + alt_diff * 0.2 + a_diff * 0.15 + np.random.exponential(1.5, n_samples)
    target_range = np.clip(target_range, 0.005, 50.0) # km
    
    # Relative speed at TCA: strongly related to inclination differences (orthogonality of orbits)
    # Head-on/cross orbit inclinations (high inc_diff) yield speeds up to 15 km/s.
    # Coplanar orbits (low inc_diff) yield lower speeds (1-4 km/s).
    target_speed = 1.2 + 13.8 * np.sin(np.radians(inc_diff)) + np.random.normal(0, 0.5, n_samples)
    target_speed = np.clip(target_speed, 0.5, 16.5) # km/s
    
    # Collision Probability: scales exponentially with miss distance (target_range)
    # Also affected by relative speed (faster objects have shorter time in the collision torus)
    # and debris status (higher uncertainty in debris shapes/sizes)
    uncertainty_scale = 1.0 + 0.5 * is_debris1 + 0.5 * is_debris2
    base_log_prob = -1.5 - (target_range * 1.6) / uncertainty_scale
    # Add noise
    target_prob = 10 ** (base_log_prob + np.random.normal(0, 0.3, n_samples))
    # Cap it between 1e-8 and 0.85
    target_prob = np.clip(target_prob, 1e-8, 0.85)
    
    df = pd.DataFrame({
        "cat1": [str(10000 + i) for i in range(n_samples)],
        "cat2": [str(20000 + i) for i in range(n_samples)],
        "name1": ["SAT_" + str(i) for i in range(n_samples)],
        "name2": ["DEBRIS_" + str(i) if is_debris2[i] else "SAT_B_" + str(i) for i in range(n_samples)],
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
    
    df.to_csv(TRAINING_DATA_PATH, index=False)
    print(f"Rich dataset successfully written to {TRAINING_DATA_PATH}. Shape: {df.shape}")

if __name__ == "__main__":
    generate_rich_dataset()
