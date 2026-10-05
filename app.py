from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent

FORECAST_FILE = (
    PROJECT_ROOT
    / "reports"
    / "live_forecasts"
    / "grid_forecast_72h_latest.csv"
)


st.set_page_config(
    page_title="Grid Forecaster",
    page_icon="🌱",
    layout="wide",
)


@st.cache_data
def load_forecast():
    """Lädt die aktuelle 72-Stunden-Prognose."""

    if not FORECAST_FILE.exists():
        raise FileNotFoundError(
            f"Prognosedatei nicht gefunden: {FORECAST_FILE}"
        )

    data = pd.read_csv(FORECAST_FILE)

    data["timestamp_local"] = pd.to_datetime(
        data["timestamp_local"]
    )

    data = data.sort_values("timestamp_local")

    data["date"] = data["timestamp_local"].dt.date
    data["hour"] = data["timestamp_local"].dt.hour

    return data


def date_label(selected_date):
    """Erstellt eine verständliche Beschriftung."""

    today = date.today()

    if selected_date == today:
        return f"Heute – {selected_date:%d.%m.%Y}"

    if selected_date == today + pd.Timedelta(days=1):
        return f"Morgen – {selected_date:%d.%m.%Y}"

    return selected_date.strftime("%d.%m.%Y")


def green_category(value):
    """Ordnet den vorhergesagten Grünanteil ein."""

    if value >= 70:
        return "🟢 Hoch"

    if value >= 45:
        return "🟡 Mittel"

    return "🔴 Niedrig"


def find_best_window(
    daily_data,
    duration,
    earliest_start,
    latest_end,
):
    """Sucht das grünste zusammenhängende Zeitfenster."""

    candidates = []

    for start_hour in range(
        earliest_start,
        latest_end - duration + 1,
    ):
        end_hour = start_hour + duration

        window = daily_data[
            (daily_data["hour"] >= start_hour)
            & (daily_data["hour"] < end_hour)
        ].copy()

        # Für jede benötigte Stunde muss eine Prognose vorliegen.
        if len(window) != duration:
            continue

        expected_hours = list(
            range(start_hour, end_hour)
        )

        if window["hour"].tolist() != expected_hours:
            continue

        average_share = window[
            "predicted_renewable_share_pct"
        ].mean()

        candidates.append(
            {
                "start_hour": start_hour,
                "end_hour": end_hour,
                "average_share": average_share,
                "window": window,
            }
        )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda candidate: candidate["average_share"],
    )


st.title("🌱 Grid Forecaster")

st.write(
    "Finde das grünste Zeitfenster für einen "
    "verschiebbaren Stromverbraucher oder IT-Job."
)


try:
    forecast = load_forecast()

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()


available_dates = sorted(
    forecast["date"].unique()
)

selected_date = st.selectbox(
    "Datum auswählen",
    options=available_dates,
    format_func=date_label,
)


daily_data = forecast[
    forecast["date"] == selected_date
].copy()


col1, col2, col3 = st.columns(3)

with col1:
    duration = st.selectbox(
        "Wie lange dauert dein Job?",
        options=[1, 2, 3, 4, 6],
        index=2,
        format_func=lambda hours: (
            f"{hours} Stunde"
            if hours == 1
            else f"{hours} Stunden"
        ),
    )

with col2:
    earliest_start = st.selectbox(
        "Frühester Start",
        options=list(range(24)),
        index=8,
        format_func=lambda hour: f"{hour:02d}:00 Uhr",
    )

with col3:
    latest_end = st.selectbox(
        "Spätestes Ende",
        options=list(range(1, 25)),
        index=19,
        format_func=lambda hour: (
            "24:00 Uhr"
            if hour == 24
            else f"{hour:02d}:00 Uhr"
        ),
    )


if latest_end <= earliest_start:
    st.error(
        "Das späteste Ende muss nach dem "
        "frühesten Start liegen."
    )
    st.stop()


if latest_end - earliest_start < duration:
    st.error(
        "Der ausgewählte Zeitraum ist kürzer "
        "als die Jobdauer."
    )
    st.stop()


best_window = find_best_window(
    daily_data=daily_data,
    duration=duration,
    earliest_start=earliest_start,
    latest_end=latest_end,
)


if best_window is None:
    st.warning(
        "Für diesen Zeitraum liegen nicht genügend "
        "zusammenhängende Prognosestunden vor."
    )
    st.stop()


average_share = best_window["average_share"]
start_hour = best_window["start_hour"]
end_hour = best_window["end_hour"]


st.divider()

st.subheader("Empfohlenes grünes Zeitfenster")

result_col1, result_col2, result_col3 = st.columns(3)

with result_col1:
    st.metric(
        "Beste Startzeit",
        f"{start_hour:02d}:00 Uhr",
    )

with result_col2:
    st.metric(
        "Endzeit",
        (
            "24:00 Uhr"
            if end_hour == 24
            else f"{end_hour:02d}:00 Uhr"
        ),
    )

with result_col3:
    st.metric(
        "Durchschnittlicher Grünanteil",
        f"{average_share:.1f} %",
    )


st.success(
    f"{green_category(average_share)} – "
    f"Starte den Job am besten um "
    f"{start_hour:02d}:00 Uhr."
)


st.subheader("Stündliche Prognose")

chart_data = daily_data[
    [
        "timestamp_local",
        "predicted_renewable_share_pct",
    ]
].set_index("timestamp_local")

chart_data = chart_data.rename(
    columns={
        "predicted_renewable_share_pct":
        "Grünanteil in %"
    }
)

st.line_chart(
    chart_data,
    y="Grünanteil in %",
)


st.subheader("Stundenwerte")

table = daily_data[
    [
        "timestamp_local",
        "predicted_renewable_share_pct",
    ]
].copy()

table["Uhrzeit"] = table[
    "timestamp_local"
].dt.strftime("%H:%M")

table["Grünanteil"] = table[
    "predicted_renewable_share_pct"
].map(lambda value: f"{value:.1f} %")

table["Bewertung"] = table[
    "predicted_renewable_share_pct"
].map(green_category)

st.dataframe(
    table[
        [
            "Uhrzeit",
            "Grünanteil",
            "Bewertung",
        ]
    ],
    hide_index=True,
    use_container_width=True,
)


with st.expander("Wie wird die Empfehlung berechnet?"):
    st.write(
        "Das Hauptmodell prognostiziert für jede Stunde "
        "den Anteil erneuerbarer Energien. Die Anwendung "
        "prüft innerhalb des gewählten Zeitraums alle "
        "möglichen zusammenhängenden Zeitfenster und "
        "wählt das Fenster mit dem höchsten "
        "durchschnittlichen Grünanteil aus."
    )