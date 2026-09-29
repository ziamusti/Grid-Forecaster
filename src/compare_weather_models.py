from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


results = [
    {
        "model": "Baseline",
        "mae": 19.143,
        "rmse": 22.410,
        "r2": -0.518,
    },
    {
        "model": "Lineare Regression",
        "mae": 13.796,
        "rmse": 16.225,
        "r2": 0.204,
    },
    {
        "model": "Random Forest",
        "mae": 13.335,
        "rmse": 15.352,
        "r2": 0.288,
    },
    {
        "model": "XGBoost",
        "mae": 13.335,
        "rmse": 15.168,
        "r2": 0.305,
    },
    {
        "model": "HistGradientBoosting",
        "mae": 13.404,
        "rmse": 15.238,
        "r2": 0.298,
    },
]


data = pd.DataFrame(results)

data.to_csv(
    REPORT_DIR / "weather_model_comparison.csv",
    index=False,
)


figure, axes = plt.subplots(
    1,
    2,
    figsize=(15, 6),
)

data.plot(
    x="model",
    y=["mae", "rmse"],
    kind="bar",
    ax=axes[0],
    color=["#2ca02c", "#ff7f0e"],
)

axes[0].set_title("Fehler der Wettermodelle")
axes[0].set_xlabel("")
axes[0].set_ylabel("Fehler in Prozentpunkten")
axes[0].legend(["MAE", "RMSE"])
axes[0].tick_params(axis="x", rotation=30)
axes[0].grid(axis="y", alpha=0.3)


data.plot(
    x="model",
    y="r2",
    kind="bar",
    ax=axes[1],
    color="#1f77b4",
    legend=False,
)

axes[1].set_title("R² der Wettermodelle")
axes[1].set_xlabel("")
axes[1].set_ylabel("R²")
axes[1].tick_params(axis="x", rotation=30)
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].grid(axis="y", alpha=0.3)


plt.tight_layout()

output_file = (
    FIGURE_DIR / "weather_model_comparison.png"
)

plt.savefig(
    output_file,
    dpi=200,
)

print(data.to_string(index=False))
print()
print(f"Erstellt: {output_file}")