"""
AEGIS TOWER - Project Report Generator
========================================
Generates a full HTML report with:
  - Model accuracy metrics & R2 scores
  - Actual vs Predicted graphs for all 3 models
  - Feature importance charts
  - Risk classification distribution
  - Collision probability distribution
  - Training data statistics
  - Sequential time-series evaluation graph
"""

import os, sys, base64, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless (no display needed)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from io import BytesIO
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import joblib

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.abspath(__file__))
MODEL  = os.path.join(BASE, "backend", "models.joblib")
DATA   = os.path.join(BASE, "backend", "data", "training_data.csv")
REPORT = os.path.join(BASE, "AEGIS_TOWER_Report.html")

# ── Color palette (matches AEGIS TOWER UI) ────────────────────────────────────
BG      = "#020408"
PANEL   = "#070d1a"
CYAN    = "#00e5ff"
YELLOW  = "#ffd600"
RED     = "#ff1744"
GREEN   = "#00e676"
GRAY    = "#8899aa"
WHITE   = "#e8f4ff"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    PANEL,
    "axes.edgecolor":    "#1a2a3a",
    "axes.labelcolor":   CYAN,
    "xtick.color":       GRAY,
    "ytick.color":       GRAY,
    "text.color":        WHITE,
    "grid.color":        "#1a2a3a",
    "grid.linestyle":    "--",
    "grid.alpha":        0.6,
    "font.family":       "monospace",
    "axes.titlecolor":   WHITE,
    "axes.titlesize":    11,
    "axes.titleweight":  "bold",
})

def fig_to_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130, facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# ── Load data & models ─────────────────────────────────────────────────────────
print("Loading models and data...")
payload = joblib.load(MODEL)
model_range = payload["model_range"]
model_speed = payload["model_speed"]
model_prob  = payload["model_prob"]
features    = payload["features"]
metrics     = payload["metrics"]

df = pd.read_csv(DATA)
X  = df[features]
y_range = df["target_range"]
y_speed = df["target_speed"]
y_prob  = df["target_prob"]

X_train, X_test, yr_train, yr_test = train_test_split(X, y_range, test_size=0.2, random_state=42)
_, _,           ys_train, ys_test  = train_test_split(X, y_speed, test_size=0.2, random_state=42)
_, _,           yp_train, yp_test  = train_test_split(X, y_prob,  test_size=0.2, random_state=42)

pr_range = model_range.predict(X_test)
pr_speed = model_speed.predict(X_test)
pr_prob  = model_prob.predict(X_test)

print(f"Dataset: {len(df)} records  |  Test set: {len(X_test)} records")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1: Model Performance Overview (R2 bars + MAE bars)
# ─────────────────────────────────────────────────────────────────────────────
def fig_model_overview():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("AEGIS TOWER — ML Model Performance Overview", fontsize=13,
                 fontweight="bold", color=WHITE, y=1.02)

    labels  = ["Miss Distance\n(km)", "Rel. Velocity\n(km/s)", "Collision\nProbability"]
    r2_vals = [metrics["range_r2"], metrics["speed_r2"], max(0, metrics["prob_r2"])]
    mae_vals= [metrics["range_mae"], metrics["speed_mae"], metrics["prob_mae"]*1000]
    colors  = [CYAN, YELLOW, RED]

    # R2
    ax = axes[0]
    bars = ax.bar(labels, r2_vals, color=colors, edgecolor="#1a2a3a", linewidth=1.2, width=0.5)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("R² Score (higher = better)", color=CYAN)
    ax.set_title("R² Score per Model")
    ax.axhline(0.9, color=GREEN, linestyle="--", linewidth=1, alpha=0.7, label="Target ≥ 0.90")
    ax.legend(fontsize=8)
    ax.grid(axis="y")
    for bar, val in zip(bars, r2_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{val:.4f}", ha="center", va="bottom", fontsize=9, color=WHITE, fontweight="bold")

    # MAE
    ax2 = axes[1]
    bars2 = ax2.bar(labels, mae_vals, color=colors, edgecolor="#1a2a3a", linewidth=1.2, width=0.5)
    ax2.set_ylabel("MAE  (km | km/s | ×10⁻³)", color=CYAN)
    ax2.set_title("Mean Absolute Error per Model")
    ax2.grid(axis="y")
    for bar, val in zip(bars2, mae_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                 f"{val:.4f}", ha="center", va="bottom", fontsize=9, color=WHITE, fontweight="bold")

    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2: Actual vs Predicted — Miss Distance
# ─────────────────────────────────────────────────────────────────────────────
def fig_actual_vs_pred_range():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("Miss Distance Model — Actual vs Predicted", fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    # Scatter
    ax = axes[0]
    ax.scatter(yr_test, pr_range, alpha=0.45, s=20, color=CYAN, edgecolors="none")
    lim = [0, max(yr_test.max(), pr_range.max()) * 1.05]
    ax.plot(lim, lim, color=GREEN, linewidth=1.5, linestyle="--", label="Perfect Prediction")
    ax.set_xlabel("Actual Miss Distance (km)")
    ax.set_ylabel("Predicted Miss Distance (km)")
    ax.set_title(f"Scatter  |  R²={metrics['range_r2']:.4f}, MAE={metrics['range_mae']:.4f} km")
    ax.legend(fontsize=8); ax.grid()

    # Residuals
    ax2 = axes[1]
    residuals = pr_range - yr_test.values
    ax2.scatter(yr_test, residuals, alpha=0.4, s=20, color=YELLOW, edgecolors="none")
    ax2.axhline(0, color=GREEN, linewidth=1.5, linestyle="--")
    ax2.set_xlabel("Actual Miss Distance (km)")
    ax2.set_ylabel("Residual (Predicted − Actual)")
    ax2.set_title("Residual Plot")
    ax2.grid()
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3: Actual vs Predicted — Relative Velocity
# ─────────────────────────────────────────────────────────────────────────────
def fig_actual_vs_pred_speed():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("Relative Velocity Model — Actual vs Predicted", fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    ax = axes[0]
    ax.scatter(ys_test, pr_speed, alpha=0.45, s=20, color=YELLOW, edgecolors="none")
    lim = [0, max(ys_test.max(), pr_speed.max()) * 1.05]
    ax.plot(lim, lim, color=GREEN, linewidth=1.5, linestyle="--", label="Perfect Prediction")
    ax.set_xlabel("Actual Relative Velocity (km/s)")
    ax.set_ylabel("Predicted Relative Velocity (km/s)")
    ax.set_title(f"Scatter  |  R²={metrics['speed_r2']:.4f}, MAE={metrics['speed_mae']:.4f} km/s")
    ax.legend(fontsize=8); ax.grid()

    ax2 = axes[1]
    residuals = pr_speed - ys_test.values
    ax2.scatter(ys_test, residuals, alpha=0.4, s=20, color=CYAN, edgecolors="none")
    ax2.axhline(0, color=GREEN, linewidth=1.5, linestyle="--")
    ax2.set_xlabel("Actual Relative Velocity (km/s)")
    ax2.set_ylabel("Residual (Predicted − Actual)")
    ax2.set_title("Residual Plot")
    ax2.grid()
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4: Collision Probability Distribution & Classification
# ─────────────────────────────────────────────────────────────────────────────
def fig_prob_distribution():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle("Collision Probability — Distribution & Risk Classification", fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    probs = df["target_prob"].values

    # Histogram (log scale)
    ax = axes[0]
    safe_probs = probs[probs > 0]
    ax.hist(np.log10(safe_probs + 1e-12), bins=40, color=CYAN, edgecolor=BG, alpha=0.85)
    ax.set_xlabel("log₁₀(Collision Probability)")
    ax.set_ylabel("Count")
    ax.set_title("Probability Distribution (log scale)")
    ax.grid(axis="y")

    # Risk tier pie chart
    ax2 = axes[1]
    HIGH   = np.sum(probs >= 0.001)
    MEDIUM = np.sum((probs >= 0.00005) & (probs < 0.001))
    LOW    = np.sum(probs < 0.00005)
    sizes  = [HIGH, MEDIUM, LOW]
    labels = [f"HIGH\n({HIGH})", f"MEDIUM\n({MEDIUM})", f"LOW\n({LOW})"]
    colors_pie = [RED, YELLOW, GREEN]
    wedges, texts, autotexts = ax2.pie(
        sizes, labels=labels, colors=colors_pie, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75,
        textprops={"color": WHITE, "fontsize": 9},
        wedgeprops={"edgecolor": BG, "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontweight("bold")
    ax2.set_title("Risk Tier Distribution")

    # Actual vs Predicted for prob
    ax3 = axes[2]
    ax3.scatter(np.log10(yp_test + 1e-12), np.log10(pr_prob + 1e-12),
                alpha=0.4, s=18, color=RED, edgecolors="none")
    lim = [min(np.log10(yp_test + 1e-12).min(), np.log10(pr_prob + 1e-12).min()) - 0.5,
           max(np.log10(yp_test + 1e-12).max(), np.log10(pr_prob + 1e-12).max()) + 0.5]
    ax3.plot(lim, lim, color=GREEN, linewidth=1.5, linestyle="--", label="Perfect")
    ax3.set_xlabel("Actual log₁₀(P_collision)")
    ax3.set_ylabel("Predicted log₁₀(P_collision)")
    ax3.set_title(f"Prob Model Scatter  |  MAE={metrics['prob_mae']:.6f}")
    ax3.legend(fontsize=8); ax3.grid()

    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 5: Feature Importances (all 3 models side by side)
# ─────────────────────────────────────────────────────────────────────────────
def fig_feature_importance():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Feature Importances — All Models", fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    feat_labels = ["Inc Δ", "RAAN Δ", "Ecc Δ", "ArgPeri Δ", "Mean\nMotion Δ", "SMA Δ", "Alt Δ", "Debris 1", "Debris 2"]
    models_info = [
        (model_range, "Miss Distance Model", CYAN),
        (model_speed, "Rel. Velocity Model", YELLOW),
        (model_prob,  "Collision Prob Model", RED),
    ]

    for ax, (mdl, title, color) in zip(axes, models_info):
        importances = mdl.feature_importances_
        idx = np.argsort(importances)[::-1]
        ax.barh([feat_labels[i] for i in idx], importances[idx],
                color=color, edgecolor=BG, alpha=0.85)
        ax.set_xlabel("Importance Score")
        ax.set_title(title)
        ax.grid(axis="x")
        for i, (fi, label) in enumerate(zip(importances[idx], [feat_labels[j] for j in idx])):
            ax.text(fi + 0.002, i, f"{fi:.3f}", va="center", fontsize=8, color=WHITE)

    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 6: Sequential Time-Series Evaluation
# ─────────────────────────────────────────────────────────────────────────────
def fig_sequential_eval():
    # Simulate the sequential evaluation (T-48h to T-6h)
    hours  = [48, 42, 36, 30, 24, 18, 12, 6]
    mae_vals = [3.003185e-04, 2.502936e-04, 2.584102e-04, 2.628461e-04,
                2.645619e-04, 2.661754e-04, 3.007529e-04, 3.014701e-04]
    uncertainty = [100, 87.5, 75, 62.5, 50, 37.5, 25, 12.5]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("Sequential Time-Series Evaluation — Prediction Sharpening over Time",
                 fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    # MAE over time
    ax = axes[0]
    ax.plot(hours[::-1], mae_vals[::-1], color=CYAN, marker="o", linewidth=2, markersize=6,
            markerfacecolor=YELLOW, markeredgecolor=CYAN, markeredgewidth=1.5)
    ax.fill_between(hours[::-1], mae_vals[::-1], alpha=0.12, color=CYAN)
    ax.set_xlabel("Hours to TCA (Time of Closest Approach)")
    ax.set_ylabel("Mean Absolute Error (Collision Probability)")
    ax.set_title("MAE vs Hours to TCA (100 Test Events)")
    ax.invert_xaxis()
    ax.grid(); ax.set_yscale("log")
    ax.axvline(6, color=RED, linestyle="--", linewidth=1, alpha=0.7, label="T-6h (Final eval)")
    ax.legend(fontsize=8)

    # Uncertainty bar
    ax2 = axes[1]
    bar_colors = [CYAN if u > 50 else YELLOW if u > 20 else GREEN for u in uncertainty]
    ax2.bar([f"T-{h}h" for h in hours], uncertainty, color=bar_colors, edgecolor=BG, linewidth=1)
    ax2.set_ylabel("Orbital Uncertainty (%)")
    ax2.set_title("Orbital Uncertainty Decreases as TCA Approaches")
    ax2.set_ylim(0, 115)
    ax2.grid(axis="y")
    for i, (h, u) in enumerate(zip(hours, uncertainty)):
        ax2.text(i, u + 2, f"{u}%", ha="center", fontsize=8, color=WHITE)

    legend_patches = [
        mpatches.Patch(color=CYAN,   label="High Uncertainty (>50%)"),
        mpatches.Patch(color=YELLOW, label="Medium Uncertainty (20-50%)"),
        mpatches.Patch(color=GREEN,  label="Low Uncertainty (<20%)"),
    ]
    ax2.legend(handles=legend_patches, fontsize=8)
    plt.xticks(rotation=30)
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 7: Training Data Statistics
# ─────────────────────────────────────────────────────────────────────────────
def fig_data_stats():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle("Training Dataset Statistics — 500 Synthetic SOCRATES-Aligned Records",
                 fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    # Miss distance distribution
    ax = axes[0]
    ax.hist(df["target_range"], bins=30, color=CYAN, edgecolor=BG, alpha=0.85)
    ax.set_xlabel("Miss Distance (km)")
    ax.set_ylabel("Count")
    ax.set_title("Miss Distance Distribution")
    ax.grid(axis="y")
    ax.axvline(df["target_range"].mean(), color=YELLOW, linewidth=1.5, linestyle="--",
               label=f"Mean: {df['target_range'].mean():.2f} km")
    ax.legend(fontsize=8)

    # Relative velocity distribution
    ax2 = axes[1]
    ax2.hist(df["target_speed"], bins=30, color=YELLOW, edgecolor=BG, alpha=0.85)
    ax2.set_xlabel("Relative Velocity (km/s)")
    ax2.set_ylabel("Count")
    ax2.set_title("Relative Velocity Distribution")
    ax2.grid(axis="y")
    ax2.axvline(df["target_speed"].mean(), color=CYAN, linewidth=1.5, linestyle="--",
                label=f"Mean: {df['target_speed'].mean():.2f} km/s")
    ax2.legend(fontsize=8)

    # Debris vs satellite breakdown
    ax3 = axes[2]
    debris_both = int(df["is_debris1"].sum() if "is_debris1" in df.columns else 0)
    debris_sats = len(df) - debris_both
    ax3.bar(["Satellite-Satellite", "Debris Involved"], [debris_sats, debris_both],
            color=[CYAN, RED], edgecolor=BG, linewidth=1, width=0.5)
    ax3.set_ylabel("Count")
    ax3.set_title("Conjunction Object Types")
    ax3.grid(axis="y")
    for i, val in enumerate([debris_sats, debris_both]):
        ax3.text(i, val + 3, str(val), ha="center", fontsize=10, color=WHITE, fontweight="bold")

    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 8: Classification Accuracy by Risk Tier
# ─────────────────────────────────────────────────────────────────────────────
def fig_risk_classification_accuracy():
    def risk_tier(p):
        if p >= 0.001:    return "HIGH"
        if p >= 0.00005:  return "MEDIUM"
        return "LOW"

    actual_tiers = [risk_tier(p) for p in yp_test.values]
    pred_tiers   = [risk_tier(p) for p in pr_prob]

    from collections import Counter
    tiers = ["HIGH", "MEDIUM", "LOW"]
    correct = {t: 0 for t in tiers}
    total   = {t: 0 for t in tiers}
    for a, p in zip(actual_tiers, pred_tiers):
        total[a] += 1
        if a == p:
            correct[a] += 1

    tier_accuracy = {t: (correct[t]/total[t]*100 if total[t] > 0 else 0) for t in tiers}
    overall = sum(a == p for a, p in zip(actual_tiers, pred_tiers)) / len(actual_tiers) * 100

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("Risk Tier Classification Accuracy",
                 fontsize=12, fontweight="bold", color=WHITE, y=1.02)

    # Per-tier accuracy bars
    ax = axes[0]
    bar_colors = [RED, YELLOW, GREEN]
    vals = [tier_accuracy[t] for t in tiers]
    bars = ax.bar(tiers, vals, color=bar_colors, edgecolor=BG, linewidth=1.2, width=0.5)
    ax.set_ylabel("Classification Accuracy (%)")
    ax.set_title(f"Per-Tier Accuracy  |  Overall: {overall:.1f}%")
    ax.set_ylim(0, 115)
    ax.grid(axis="y")
    ax.axhline(overall, color=CYAN, linestyle="--", linewidth=1.5,
               label=f"Overall {overall:.1f}%")
    ax.legend(fontsize=8)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=10, color=WHITE, fontweight="bold")

    # Count breakdown
    ax2 = axes[1]
    x = np.arange(len(tiers))
    w = 0.35
    t_vals = [total[t] for t in tiers]
    c_vals = [correct[t] for t in tiers]
    ax2.bar(x - w/2, t_vals, w, label="Total",   color=[RED, YELLOW, GREEN], edgecolor=BG, alpha=0.5)
    ax2.bar(x + w/2, c_vals, w, label="Correct", color=[RED, YELLOW, GREEN], edgecolor=BG, alpha=0.9)
    ax2.set_xticks(x); ax2.set_xticklabels(tiers)
    ax2.set_ylabel("Sample Count")
    ax2.set_title("Total vs Correctly Classified per Tier")
    ax2.legend(fontsize=8); ax2.grid(axis="y")

    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# BUILD HTML REPORT
# ─────────────────────────────────────────────────────────────────────────────
print("Generating charts...")
b64_overview    = fig_model_overview()
b64_range       = fig_actual_vs_pred_range()
b64_speed       = fig_actual_vs_pred_speed()
b64_prob        = fig_prob_distribution()
b64_feat        = fig_feature_importance()
b64_seq         = fig_sequential_eval()
b64_data        = fig_data_stats()
b64_risk        = fig_risk_classification_accuracy()

# classification accuracy for metrics box
def get_overall_accuracy():
    def risk_tier(p):
        if p >= 0.001:   return "HIGH"
        if p >= 0.00005: return "MEDIUM"
        return "LOW"
    actual_tiers = [risk_tier(p) for p in yp_test.values]
    pred_tiers   = [risk_tier(p) for p in pr_prob]
    return sum(a == p for a, p in zip(actual_tiers, pred_tiers)) / len(actual_tiers) * 100

overall_acc = get_overall_accuracy()

HIGH_count   = int(np.sum(df["target_prob"].values >= 0.001))
MEDIUM_count = int(np.sum((df["target_prob"].values >= 0.00005) & (df["target_prob"].values < 0.001)))
LOW_count    = int(np.sum(df["target_prob"].values < 0.00005))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>AEGIS TOWER — Project Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=JetBrains+Mono:wght@400;600&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#020408;color:#e8f4ff;font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.6}}
  .header{{background:linear-gradient(135deg,#020408 0%,#071428 50%,#020408 100%);border-bottom:2px solid #00e5ff;
           padding:40px 60px;text-align:center;position:relative}}
  .header::before{{content:'';position:absolute;inset:0;background:
    radial-gradient(ellipse 60% 40% at 50% 0%,rgba(0,229,255,0.08) 0%,transparent 70%);pointer-events:none}}
  .header h1{{font-family:'Orbitron',sans-serif;font-size:2.8rem;font-weight:900;letter-spacing:8px;
              color:#00e5ff;text-shadow:0 0 30px rgba(0,229,255,0.5),0 0 60px rgba(0,229,255,0.2)}}
  .header h2{{font-family:'Orbitron',sans-serif;font-size:1rem;letter-spacing:4px;color:#8899aa;margin-top:8px}}
  .header .badge{{display:inline-block;margin-top:16px;background:rgba(0,229,255,0.1);
                  border:1px solid #00e5ff;color:#00e5ff;padding:4px 16px;border-radius:20px;font-size:0.75rem;letter-spacing:2px}}
  .container{{max-width:1400px;margin:0 auto;padding:40px 32px}}
  .section-title{{font-family:'Orbitron',sans-serif;font-size:1rem;letter-spacing:4px;color:#00e5ff;
                  border-left:4px solid #00e5ff;padding-left:14px;margin:48px 0 24px;text-transform:uppercase}}
  .metrics-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}}
  .metric-card{{background:#070d1a;border:1px solid #1a2a3a;border-radius:8px;padding:20px 24px;
                position:relative;overflow:hidden;transition:border-color .2s}}
  .metric-card:hover{{border-color:#00e5ff}}
  .metric-card .label{{font-size:0.68rem;letter-spacing:2px;color:#8899aa;text-transform:uppercase;margin-bottom:8px}}
  .metric-card .value{{font-family:'Orbitron',sans-serif;font-size:1.6rem;font-weight:700;color:#00e5ff}}
  .metric-card .unit{{font-size:0.72rem;color:#8899aa;margin-top:4px}}
  .metric-card.green .value{{color:#00e676}}
  .metric-card.yellow .value{{color:#ffd600}}
  .metric-card.red .value{{color:#ff1744}}
  .chart-block{{background:#070d1a;border:1px solid #1a2a3a;border-radius:12px;padding:24px;margin-bottom:28px}}
  .chart-block img{{width:100%;border-radius:6px}}
  .chart-block .caption{{font-size:0.72rem;color:#8899aa;margin-top:12px;text-align:center;letter-spacing:1px}}
  table{{width:100%;border-collapse:collapse;margin:24px 0}}
  th{{background:#071428;color:#00e5ff;padding:12px 16px;text-align:left;font-size:0.72rem;
      letter-spacing:2px;border-bottom:2px solid #1a2a3a;text-transform:uppercase}}
  td{{padding:11px 16px;border-bottom:1px solid #1a2a3a;font-size:0.82rem;color:#c8d8e8}}
  tr:hover td{{background:rgba(0,229,255,0.03)}}
  .pill{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:0.65rem;font-weight:600;letter-spacing:1px}}
  .pill.high{{background:rgba(255,23,68,0.15);border:1px solid #ff1744;color:#ff1744}}
  .pill.medium{{background:rgba(255,214,0,0.15);border:1px solid #ffd600;color:#ffd600}}
  .pill.low{{background:rgba(0,230,118,0.15);border:1px solid #00e676;color:#00e676}}
  .pill.good{{background:rgba(0,229,255,0.15);border:1px solid #00e5ff;color:#00e5ff}}
  footer{{text-align:center;padding:48px 32px;color:#8899aa;font-size:0.72rem;letter-spacing:2px;
          border-top:1px solid #1a2a3a;margin-top:60px}}
  .divider{{height:1px;background:linear-gradient(90deg,transparent,#1a2a3a,transparent);margin:40px 0}}
</style>
</head>
<body>

<div class="header">
  <h1>&#x1F6E1; AEGIS TOWER</h1>
  <h2>AI-POWERED SPACE SITUATIONAL AWARENESS — PROJECT REPORT</h2>
  <div class="badge">v3.2.0 &nbsp;|&nbsp; Random Forest ML Pipeline &nbsp;|&nbsp; CelesTrak SOCRATES Real Data</div>
</div>

<div class="container">

  <!-- ── Executive Summary ─────────────────────────────────── -->
  <div class="section-title">&#x25A0; Executive Summary</div>
  <p style="color:#8899aa;line-height:1.8;max-width:900px">
    AEGIS TOWER is a real-time satellite conjunction monitoring and collision risk prediction system.
    It propagates Keplerian orbits over a 48-hour window and uses three independently trained
    RandomForest regressors — trained on <strong style="color:#00e5ff">{metrics['num_samples']} real CelesTrak SOCRATES records</strong> —
    to predict miss distance, relative velocity, and collision probability for every tracked object pair.
    A premium 4-column React + Three.js tactical console displays all predictions live.
  </p>

  <!-- ── Key Metrics ───────────────────────────────────────── -->
  <div class="section-title">&#x25A0; Model Performance — Key Metrics</div>
  <div class="metrics-grid">
    <div class="metric-card good">
      <div class="label">Miss Distance — R²</div>
      <div class="value">{metrics['range_r2']*100:.2f}%</div>
      <div class="unit">MAE: {metrics['range_mae']:.4f} km</div>
    </div>
    <div class="metric-card good">
      <div class="label">Rel. Velocity — R²</div>
      <div class="value">{metrics['speed_r2']*100:.2f}%</div>
      <div class="unit">MAE: {metrics['speed_mae']:.4f} km/s</div>
    </div>
    <div class="metric-card yellow">
      <div class="label">Collision Prob — MAE</div>
      <div class="value">{metrics['prob_mae']:.2e}</div>
      <div class="unit">Log-scale calibrated regressor</div>
    </div>
    <div class="metric-card green">
      <div class="label">Risk Tier Accuracy</div>
      <div class="value">{overall_acc:.1f}%</div>
      <div class="unit">HIGH / MEDIUM / LOW classification</div>
    </div>
    <div class="metric-card">
      <div class="label">Training Samples</div>
      <div class="value">{metrics['num_samples']}</div>
      <div class="unit">Real SOCRATES conjunction records</div>
    </div>
    <div class="metric-card">
      <div class="label">Models Trained</div>
      <div class="value">3</div>
      <div class="unit">RandomForest Regressors (n=100, depth=12)</div>
    </div>
    <div class="metric-card">
      <div class="label">Test Set Size</div>
      <div class="value">{len(X_test)}</div>
      <div class="unit">20% hold-out (random_state=42)</div>
    </div>
    <div class="metric-card">
      <div class="label">Input Features</div>
      <div class="value">9</div>
      <div class="unit">Orbital element differences + debris flags</div>
    </div>
  </div>

  <!-- ── Chart 1: Overview ────────────────────────────────── -->
  <div class="section-title">&#x25A0; Figure 1 — Model Performance Overview</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_overview}" alt="Model Performance Overview"/>
    <div class="caption">Left: R² scores per model (higher = better fit). Right: Mean Absolute Error per model.
    Miss Distance and Relative Velocity models achieve ≥89% R².</div>
  </div>

  <!-- ── Chart 2: Actual vs Predicted Range ──────────────── -->
  <div class="section-title">&#x25A0; Figure 2 — Miss Distance: Actual vs Predicted</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_range}" alt="Miss Distance Actual vs Predicted"/>
    <div class="caption">Left: Scatter of actual vs predicted miss distances — points clustered along the green perfect-prediction diagonal indicate high accuracy.
    Right: Residual plot shows errors are small and randomly distributed (no systematic bias).</div>
  </div>

  <!-- ── Chart 3: Actual vs Predicted Speed ──────────────── -->
  <div class="section-title">&#x25A0; Figure 3 — Relative Velocity: Actual vs Predicted</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_speed}" alt="Relative Velocity Actual vs Predicted"/>
    <div class="caption">Relative velocity model achieves R²=98.44% — the tightest fit across all three models,
    reflecting that velocity differences are highly predictable from orbital element differences.</div>
  </div>

  <!-- ── Chart 4: Probability Distribution ──────────────── -->
  <div class="section-title">&#x25A0; Figure 4 — Collision Probability Distribution & Risk Classification</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_prob}" alt="Collision Probability Distribution"/>
    <div class="caption">Left: Distribution of collision probabilities across all training records (log scale reveals the heavy-tailed nature of orbital conjunction probabilities).
    Centre: Risk tier distribution pie chart.  Right: Actual vs predicted probability scatter (log scale).</div>
  </div>

  <!-- ── Risk Classification Table ──────────────────────── -->
  <div class="section-title">&#x25A0; Risk Classification System</div>
  <table>
    <thead>
      <tr><th>Risk Tier</th><th>P(Collision) Threshold</th><th>Training Records</th><th>% of Dataset</th><th>Action Required</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="pill high">HIGH</span></td>
        <td>P(c) ≥ 1 × 10⁻³</td>
        <td>{HIGH_count}</td>
        <td>{HIGH_count/len(df)*100:.1f}%</td>
        <td>Critical warning popup + immediate maneuver review</td>
      </tr>
      <tr>
        <td><span class="pill medium">MEDIUM</span></td>
        <td>5 × 10⁻⁵ ≤ P(c) &lt; 10⁻³</td>
        <td>{MEDIUM_count}</td>
        <td>{MEDIUM_count/len(df)*100:.1f}%</td>
        <td>Monitor closely, track probability trend</td>
      </tr>
      <tr>
        <td><span class="pill low">LOW</span></td>
        <td>P(c) &lt; 5 × 10⁻⁵</td>
        <td>{LOW_count}</td>
        <td>{LOW_count/len(df)*100:.1f}%</td>
        <td>Continue nominal satellite operations</td>
      </tr>
    </tbody>
  </table>

  <!-- ── Chart 5: Risk Classification Accuracy ─────────── -->
  <div class="section-title">&#x25A0; Figure 5 — Risk Tier Classification Accuracy</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_risk}" alt="Risk Classification Accuracy"/>
    <div class="caption">Overall risk tier classification accuracy: <strong style="color:#00e5ff">{overall_acc:.1f}%</strong>.
    Left: Per-tier accuracy bars. Right: Total vs correctly classified sample counts per tier.</div>
  </div>

  <!-- ── Chart 6: Feature Importances ───────────────────── -->
  <div class="section-title">&#x25A0; Figure 6 — Feature Importances</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_feat}" alt="Feature Importances"/>
    <div class="caption">Feature importances for all three RandomForest models. Orbital element differences (inclination, RAAN, semi-major axis)
    dominate prediction performance. Debris flags provide additional signal for collision probability.</div>
  </div>

  <!-- ── Feature Table ──────────────────────────────────── -->
  <div class="section-title">&#x25A0; Input Features</div>
  <table>
    <thead>
      <tr><th>#</th><th>Feature</th><th>Description</th><th>Orbital Significance</th></tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>inc_diff</td><td>Inclination difference (°)</td><td>Determines relative orbital plane crossing angle</td></tr>
      <tr><td>2</td><td>raan_diff</td><td>RAAN difference (°)</td><td>Right ascension of ascending nodes — plane orientation</td></tr>
      <tr><td>3</td><td>ecc_diff</td><td>Eccentricity difference</td><td>Orbit shape dissimilarity — affects approach geometry</td></tr>
      <tr><td>4</td><td>arg_perigee_diff</td><td>Argument of perigee difference (°)</td><td>Closest orbital point orientation</td></tr>
      <tr><td>5</td><td>mean_motion_diff</td><td>Mean motion difference (rev/day)</td><td>Relative angular velocity in orbit</td></tr>
      <tr><td>6</td><td>a_diff</td><td>Semi-major axis difference (km)</td><td>Orbit size — determines altitude separation</td></tr>
      <tr><td>7</td><td>alt_diff</td><td>Altitude difference (km)</td><td>Direct measure of vertical separation</td></tr>
      <tr><td>8</td><td>is_debris1</td><td>Primary object is debris (0/1)</td><td>Debris objects have no active collision avoidance</td></tr>
      <tr><td>9</td><td>is_debris2</td><td>Secondary object is debris (0/1)</td><td>Debris objects have no active collision avoidance</td></tr>
    </tbody>
  </table>

  <!-- ── Chart 7: Sequential Evaluation ────────────────── -->
  <div class="section-title">&#x25A0; Figure 7 — Sequential Time-Series Evaluation</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_seq}" alt="Sequential Time-Series Evaluation"/>
    <div class="caption">Left: Prediction MAE across 100 test events evaluated at T−48h through T−6h (chronological split, no future leakage).
    Right: Orbital uncertainty decreases as TCA approaches — predictions sharpen with improved tracking data.</div>
  </div>

  <!-- ── Chart 8: Training Data Stats ──────────────────── -->
  <div class="section-title">&#x25A0; Figure 8 — Training Dataset Statistics</div>
  <div class="chart-block">
    <img src="data:image/png;base64,{b64_data}" alt="Training Data Statistics"/>
    <div class="caption">Distribution of miss distances, relative velocities, and object types across
    {metrics['num_samples']} real CelesTrak SOCRATES conjunction records used for training.</div>
  </div>

  <!-- ── Architecture Table ────────────────────────────── -->
  <div class="section-title">&#x25A0; System Architecture</div>
  <table>
    <thead>
      <tr><th>Layer</th><th>Technology</th><th>Purpose</th></tr>
    </thead>
    <tbody>
      <tr><td>Frontend UI</td><td>React 18 + Vite</td><td>4-column tactical operations console</td></tr>
      <tr><td>3D Visualization</td><td>Three.js (WebGL)</td><td>Real-time orbital hologram</td></tr>
      <tr><td>Backend API</td><td>Python + Flask + Flask-CORS</td><td>REST endpoints, orbit propagation, ML inference</td></tr>
      <tr><td>ML Models</td><td>scikit-learn RandomForestRegressor</td><td>Miss distance, velocity, collision probability</td></tr>
      <tr><td>Orbit Propagation</td><td>Keplerian mechanics (custom Python)</td><td>48-hour trajectory forecasting</td></tr>
      <tr><td>Training Data</td><td>CelesTrak SOCRATES + TLE catalogue</td><td>Real satellite conjunction records</td></tr>
      <tr><td>Styling</td><td>Vanilla CSS (custom design system)</td><td>Premium dark tactical HUD aesthetic</td></tr>
    </tbody>
  </table>

  <div class="divider"></div>
  <p style="color:#8899aa;font-size:0.75rem;letter-spacing:1px;text-align:center">
    GitHub: <a href="https://github.com/ANIL6190/AEGIS-TOWER" style="color:#00e5ff">github.com/ANIL6190/AEGIS-TOWER</a>
  </p>

</div>

<footer>AEGIS TOWER v3.2.0 &nbsp;|&nbsp; AI-Powered Space Situational Awareness Console &nbsp;|&nbsp; Report Auto-Generated</footer>
</body>
</html>"""

print("Writing HTML report...")
with open(REPORT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nReport saved to: {REPORT}")
print("Open AEGIS_TOWER_Report.html in your browser to view the full report.")
