import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


st.set_page_config(
    page_title="AQI Explorer (Streamlit)",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at top, #0b1b3a 0%, #050a14 60%); color: #e8eefc; }
    .sidebar .sidebar-content { background: rgba(10,18,35,.6); border-right: 1px solid rgba(255,255,255,.08); }
    .metric-card { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 14px; padding: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("AQI.csv")

    keep = [
        "country",
        "state",
        "city",
        "station",
        "last_update",
        "latitude",
        "longitude",
        "pollutant_id",
        "pollutant_min",
        "pollutant_max",
        "pollutant_avg",
    ]
    df = df[keep].copy()

    # Normalize numeric columns; treat NA/NaN/blank as missing
    for c in ["latitude", "longitude", "pollutant_min", "pollutant_max", "pollutant_avg"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Some rows may have missing geo
    df = df.dropna(subset=["latitude", "longitude"], how="any")

    # Keep strings
    for c in ["country", "state", "city", "station", "pollutant_id", "last_update"]:
        df[c] = df[c].astype(str)

    return df


def pollutant_description(pid: str) -> str:
    pid = str(pid)
    mapping = {
        "PM2.5": "Fine particulate matter (≤2.5µm)",
        "PM10": "Coarse particulate matter (≤10µm)",
        "SO2": "Sulfur dioxide",
        "NO2": "Nitrogen dioxide",
        "CO": "Carbon monoxide",
        "OZONE": "Ozone",
        "NH3": "Ammonia",
    }
    return mapping.get(pid, "Pollutant signal")


df = load_data()

with st.sidebar:
    st.markdown("## 🌿 AQI Explorer")
    st.markdown("Filter station data by city & pollutant, and visualize trends.")

    cities = sorted(df["city"].unique())
    pollutants = sorted(df["pollutant_id"].unique())

    city = st.selectbox("City", cities, index=0)
    pollutant_id = st.selectbox("Pollutant", pollutants, index=0)

    view_mode = st.radio(
        "Chart view",
        options=["Avg by station", "Min/Max by station"],
        index=0,
        horizontal=True,
    )

    top_n = st.slider("Limit stations on chart", min_value=10, max_value=200, value=60, step=10)

filtered = df[(df["city"] == city) & (df["pollutant_id"] == pollutant_id)].copy()

last_update = filtered["last_update"].unique()
last_update_text = last_update[0] if len(last_update) else "—"

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"<div class='metric-card'><div style='color:#a9b4d6;font-size:12px'>Stations</div><div style='font-size:22px;font-weight:700'>{len(filtered)}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card'><div style='color:#a9b4d6;font-size:12px'>Last update</div><div style='font-size:14px'>{last_update_text}</div></div>", unsafe_allow_html=True)

avg_val = pd.to_numeric(filtered["pollutant_avg"], errors="coerce").mean(skipna=True)
col3.markdown(f"<div class='metric-card'><div style='color:#a9b4d6;font-size:12px'>Mean Avg</div><div style='font-size:20px;font-weight:700'>{avg_val:.2f}'</div></div>", unsafe_allow_html=True) if np.isfinite(avg_val) else col3.markdown("<div class='metric-card'><div style='color:#a9b4d6;font-size:12px'>Mean Avg</div><div style='font-size:14px'>NA</div></div>", unsafe_allow_html=True)

col4.markdown(
    f"<div class='metric-card'><div style='color:#a9b4d6;font-size:12px'>Pollutant</div><div style='font-size:18px;font-weight:700'>{pollutant_id}</div><div style='color:#a9b4d6;font-size:12px'>{pollutant_description(pollutant_id)}</div></div>",
    unsafe_allow_html=True,
)

st.markdown("---")

left, right = st.columns([1.05, 0.95])

with left:
    st.markdown("## 📍 Stations Map")

    if len(filtered) == 0:
        st.info("No records for selected filters.")
    else:
        # Use scatter_mapbox; requires a Mapbox token for high fidelity.
        # We'll use an open style that works best; token optional for some environments.
        # If it doesn't render without a token, user can provide their token in Streamlit secrets.
        # Streamlit secrets are optional. Avoid crashing when no secrets.toml exists.
        try:
            mapbox_token = st.secrets.get("MAPBOX_TOKEN", "")
        except Exception:
            mapbox_token = ""


        fig_map = px.scatter_mapbox(
            filtered,
            lat="latitude",
            lon="longitude",
            hover_name="station",
            hover_data={
                "pollutant_min": True,
                "pollutant_max": True,
                "pollutant_avg": True,
                "last_update": True,
                "state": True,
            },
            color="pollutant_avg" if view_mode == "Avg by station" else "pollutant_avg",
            zoom=5,
            height=520,
            title=None,
        )

        # Center map to selected city by averaging coordinates
        lat_center = float(filtered["latitude"].mean())
        lon_center = float(filtered["longitude"].mean())
        # Only set accesstoken if provided; plotly requires non-empty string.
        mapbox_cfg = {
            "style": "carto-positron",
            "center": {"lat": lat_center, "lon": lon_center},
        }
        if isinstance(mapbox_token, str) and mapbox_token.strip():
            mapbox_cfg["accesstoken"] = mapbox_token

        fig_map.update_layout(
            mapbox=mapbox_cfg,
            margin=dict(l=0, r=0, t=0, b=0),
            legend_title_text="Avg",
        )


        st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.markdown("## 📊 Charts")
    if len(filtered) == 0:
        st.info("No data to chart.")
    else:
        # For charts: best to rank stations by pollutant_avg (or avg where available)
        chart_df = filtered.copy()
        chart_df["pollutant_avg"] = pd.to_numeric(chart_df["pollutant_avg"], errors="coerce")
        chart_df["pollutant_min"] = pd.to_numeric(chart_df["pollutant_min"], errors="coerce")
        chart_df["pollutant_max"] = pd.to_numeric(chart_df["pollutant_max"], errors="coerce")

        # Drop NA for the relevant metric
        if view_mode == "Avg by station":
            chart_df = chart_df.dropna(subset=["pollutant_avg"])
            chart_df = chart_df.sort_values("pollutant_avg", ascending=False).head(top_n)

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=chart_df["station"],
                    y=chart_df["pollutant_avg"],
                    marker_color="rgba(78,161,255,.95)",
                )
            )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8eefc"),
                margin=dict(l=40, r=15, t=30, b=110),
                xaxis=dict(tickangle=-45),
                yaxis_title="Pollutant Avg",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            # Min/Max
            chart_df2 = chart_df.dropna(subset=["pollutant_min", "pollutant_max"], how="all")
            # Use avg as ranking if available; otherwise by max
            if chart_df2["pollutant_avg"].notna().any():
                chart_df2 = chart_df2.sort_values("pollutant_avg", ascending=False)
            else:
                chart_df2 = chart_df2.sort_values("pollutant_max", ascending=False)
            chart_df2 = chart_df2.head(top_n)

            x = chart_df2["station"]
            y_min = chart_df2["pollutant_min"]
            y_max = chart_df2["pollutant_max"]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y_min, mode="lines+markers", name="Min", line=dict(color="rgba(124,92,255,.95)")))
            fig.add_trace(go.Scatter(x=x, y=y_max, mode="lines+markers", name="Max", line=dict(color="rgba(78,161,255,.95)")))

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8eefc"),
                margin=dict(l=40, r=15, t=30, b=110),
                xaxis=dict(tickangle=-45),
                yaxis_title="Pollutant value",
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <div style="color:#a9b4d6;font-size:12px;line-height:1.5">
    <b>Tip:</b> Provide your preferred <i>City</i> and <i>Pollutant</i> using the sidebar. Charts ignore missing values (NA).
    </div>
    """,
    unsafe_allow_html=True,
)

