# AEGIS TOWER
### AI-Powered Space Situational Awareness Console

![AEGIS TOWER](https://img.shields.io/badge/AEGIS%20TOWER-v3.2.0-00e5ff?style=for-the-badge&labelColor=020408)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![Flask](https://img.shields.io/badge/Flask-ML%20Backend-000000?style=flat-square&logo=flask)
![ML](https://img.shields.io/badge/ML-Random%20Forest%20Regressor-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

**AEGIS TOWER** is a real-time, AI-assisted satellite conjunction monitoring and collision risk assessment system. It tracks hundreds of active satellites and orbital debris objects simultaneously, propagates their Keplerian orbits forward up to 48 hours, and uses trained **RandomForest ML regressors** built on real CelesTrak SOCRATES conjunction data to predict:

- **Miss Distance** (km) at Time of Closest Approach (TCA)
- **Relative Velocity** (km/s) at TCA
- **Collision Probability** P(c)

The system features a premium 4-column tactical operations console UI with a live 3D orbital hologram, conjunction threat stream, tracked objects catalogue, and ML diagnostics panel.

---

## ML Pipeline Architecture

```
CelesTrak SOCRATES  --►  data_fetcher.py  --►  training_data.csv
        |                                              |
        |                                       train.py (RF Regressors)
        |                                              |
        └--►  TLE Catalogue --►  app.py  --►  models.joblib
                                   |
                    Keplerian Orbit Propagation (48h window)
                                   |
                    ML Inference (Miss Distance, Velocity, P(c))
                                   |
                           /api/conjunctions  --►  React Dashboard
```

### Model Performance (Trained on 500 synthetic SOCRATES-aligned orbital records with live CelesTrak scraper)
| Model | MAE | R² Score | Note |
|---|---|---|---|
| Miss Distance Regressor | 1.23 km | **0.8928** | Linear scale |
| Relative Velocity Regressor | 0.44 km/s | **0.9844** | Linear scale |
| Collision Probability Regressor | 4.45e-04 | **0.5559** | $\log_{10}$ target space |

### Sequential Time-Series Evaluation
Chronological train/test split (no future leakage). Predictions sharpen as TCA approaches:
| TCA Lead Time | Orbital Uncertainty | Mean Abs Error |
|---|---|---|
| T-48h | 100% | 3.00e-04 |
| T-24h | 50%  | 2.65e-04 |
| T-6h  | 12.5%| 3.01e-04 |

---

## Project Structure

```
AEGIS TOWER/
├── backend/
│   ├── app.py              # Flask REST API + Keplerian propagator + ML inference
│   ├── train.py            # RandomForest model training on SOCRATES data
│   ├── data_fetcher.py     # CelesTrak TLE + SOCRATES conjunction data scraper
│   ├── test_backend.py     # Sequential time-series ML evaluation suite
│   └── data/
│       ├── training_data.csv   # Cached SOCRATES conjunction records
│       └── models.joblib       # Trained RF regressor bundle
├── src/
│   ├── App.jsx             # Root application + 4-column layout
│   ├── App.css             # Premium dark tactical CSS design system
│   ├── components/
│   │   ├── OrbitScene.jsx          # 3D orbital hologram (Three.js)
│   │   ├── AlertFeed.jsx           # Live conjunction threat stream
│   │   ├── SatelliteInventory.jsx  # Full tracked objects catalogue
│   │   ├── DetailPanel.jsx         # Event telemetry details panel
│   │   ├── ModelConfidence.jsx     # Live ML diagnostics metrics
│   │   ├── OperatorPanel.jsx       # Maneuver action deck
│   │   └── RiskDashboard.jsx       # Top-level risk KPI bar
│   └── data/
│       └── satellites.js   # Built-in TLE catalogue (offline fallback)
├── index.html
├── vite.config.js
└── package.json
```

---

## Getting Started

### Prerequisites
- Python 3.10+ with pip
- Node.js 18+ with npm

### 1. Clone the Repository
```bash
git clone https://github.com/ANIL6190/AEGIS-TOWER.git
cd AEGIS-TOWER
```

### 2. Install Python Dependencies
```bash
pip install flask flask-cors numpy pandas scikit-learn joblib requests
```

### 3. Install Node Dependencies
```bash
npm install
```

### 4. Train the ML Models
Downloads real SOCRATES data from CelesTrak and trains the RandomForest regressors:
```bash
python backend/train.py
```

### 5. Start the Flask Backend (ML API)
```bash
python backend/app.py
```
Backend runs at http://localhost:5000

### 6. Start the React Frontend
```bash
npm run dev
```
Dashboard opens at http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | API status and endpoint index |
| GET | /api/status | Live ML model diagnostics and accuracy metrics |
| GET | /api/conjunctions | Active conjunction events with ML risk predictions |
| GET | /api/satellites | Full tracked objects catalogue |
| POST | /api/predict | Run collision probability prediction for custom TLE pair |
| POST | /api/train | Manually trigger model retraining |

---

## Running the Sequential Evaluation Suite

```bash
python backend/test_backend.py
```

---

## Risk Classification

| Tier | Collision Probability | Action |
|---|---|---|
| HIGH | P(c) >= 1e-3 | Critical warning popup + immediate maneuver review |
| MEDIUM | P(c) >= 5e-5 | Monitor closely, track trend |
| LOW | P(c) < 5e-5 | Continue nominal operations |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Three.js, Vite, Vanilla CSS |
| Backend | Python, Flask, Flask-CORS |
| ML | scikit-learn RandomForestRegressor, pandas, NumPy |
| Data | CelesTrak SOCRATES real conjunction records |
| 3D | Three.js WebGL orbital scene |

---

## License

MIT License

---

**AEGIS TOWER** - Watching the skies so you don't have to.
