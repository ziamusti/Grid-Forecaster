from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from xgboost import XGBRegressor


HISTORICAL_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2015_2025.csv"
)

DATA_2026_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2026.csv"
)

REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "renewable_share_of_generation_pct"


WEATHER_FEATURES = [
    "temperature_2m_land_mean_c",
    "cloud_cover_land_mean_pct",
    "wind_speed_100m_land_mean_ms",
    "shortwave_radiation_land_mean_wm2",
    "wind_speed_100m_offshore_mean_ms",
]


CALENDAR_FEATURES = [
    "hour_local",
    "weekday",
    "month",
    "is_weekend",
    "is_public_holiday",
    "daylight_hours",
]


ENERGY_COLUMNS = [
    "renewable_share_of_generation_pct",
    "renewable_generation_mwh",
    "total_generation_mwh",
    "grid_load_mwh",
    "wind_onshore_mwh",
    "wind_offshore_mwh",
    "solar_mwh",
    "natural_gas_mwh",
    "hard_coal_mwh",
    "lignite_mwh",
]

LAGS = [168]

ENERGY_FEATURES = [
    f"{column}_lag_{lag}h"
    for lag in LAGS
    for column in ENERGY_COLUMNS
]


FEATURES = (
    WEATHER_FEATURES
    + ENERGY_FEATURES
    + CALENDAR_FEATURES
)


print("Lade Daten 2015–2026 ...")

historical = pd.read_csv(HISTORICAL_FILE)
data_2026 = pd.read_csv(DATA_2026_FILE)

data = pd.concat(
    [historical, data_2026],
    ignore_index=True,
)

data["timestamp_utc"] = pd.to_datetime(
    data["timestamp_utc"],
    utc=True,
)

data = data.sort_values("timestamp_utc")
data["year"] = data["timestamp_utc"].dt.year


TEST_YEARS = [
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
]

results = []


for test_year in TEST_YEARS:
    print()
    print(
        f"Training bis {test_year - 1}, "
        f"Test {test_year} ..."
    )

    train = data[
        data["year"] < test_year
    ].copy()

    test = data[
        data["year"] == test_year
    ].copy()

    x_train = train[FEATURES]
    y_train = train[TARGET]

    x_test = test[FEATURES]
    y_test = test[TARGET]

    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )

    model.fit(
        x_train,
        y_train,
        verbose=False,
    )

    predictions = model.predict(x_test)
    predictions = np.clip(predictions, 0, 100)

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = mean_squared_error(
        y_test,
        predictions,
    ) ** 0.5

    r2 = r2_score(
        y_test,
        predictions,
    )

    results.append(
        {
            "test_year": test_year,
            "training_end_year": test_year - 1,
            "training_hours": len(train),
            "test_hours": len(test),
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        }
    )

    print(f"MAE: {mae:.3f}")
    print(f"RMSE: {rmse:.3f}")
    print(f"R2: {r2:.3f}")


results_data = pd.DataFrame(results)

results_data.to_csv(
    REPORT_DIR / "walk_forward_operational_168h_results.csv",
    index=False,
)


mean_mae = results_data["mae"].mean()
mean_rmse = results_data["rmse"].mean()
mean_r2 = results_data["r2"].mean()


with (
    REPORT_DIR / "walk_forward_operational_168h_summary.txt"
).open("w", encoding="utf-8") as file:
    file.write(
        f"Durchschnittlicher MAE: "
        f"{mean_mae:.3f} Prozentpunkte\n"
    )
    file.write(
        f"Durchschnittlicher RMSE: "
        f"{mean_rmse:.3f} Prozentpunkte\n"
    )
    file.write(
        f"Durchschnittliches R2: {mean_r2:.3f}\n"
    )


figure, axes = plt.subplots(
    1,
    2,
    figsize=(14, 6),
)

axes[0].plot(
    results_data["test_year"],
    results_data["mae"],
    marker="o",
    label="MAE",
)

axes[0].plot(
    results_data["test_year"],
    results_data["rmse"],
    marker="o",
    label="RMSE",
)

axes[0].set_title("Fehler nach Testjahr")
axes[0].set_xlabel("Testjahr")
axes[0].set_ylabel("Fehler in Prozentpunkten")
axes[0].legend()
axes[0].grid(alpha=0.3)


axes[1].plot(
    results_data["test_year"],
    results_data["r2"],
    marker="o",
    color="#1f77b4",
)

axes[1].axhline(
    0,
    color="black",
    linewidth=0.8,
)

axes[1].set_title("R² nach Testjahr")
axes[1].set_xlabel("Testjahr")
axes[1].set_ylabel("R²")
axes[1].grid(alpha=0.3)


plt.tight_layout()

figure_file = (
    FIGURE_DIR / "walk_forward_operational_168h.png"
)

plt.savefig(
    figure_file,
    dpi=200,
)


print()
print("Durchschnitt über alle Testjahre:")
print(f"MAE: {mean_mae:.3f} Prozentpunkte")
print(f"RMSE: {mean_rmse:.3f} Prozentpunkte")
print(f"R2: {mean_r2:.3f}")
print()
print(f"Erstellt: {figure_file}")