import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AQI Dashboard",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ══ KEYFRAME ANIMATIONS ══════════════════════════════════════════ */

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(28px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientShift {
        0%   { background-position: 0%   50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0%   50%; }
    }
    @keyframes shimmerSweep {
        0%   { transform: translateX(-100%) skewX(-15deg); }
        100% { transform: translateX(250%)  skewX(-15deg); }
    }
    @keyframes floatBubble {
        0%, 100% { transform: translateY(0)   scale(1); }
        50%       { transform: translateY(-8px) scale(1.05); }
    }
    @keyframes rowFadeIn {
        from { opacity: 0; transform: translateX(-12px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes pulse-ring {
        0%   { box-shadow: 0 0 0 0   rgba(98,68,216,.35); }
        70%  { box-shadow: 0 0 0 12px rgba(98,68,216,0); }
        100% { box-shadow: 0 0 0 0   rgba(98,68,216,0); }
    }
    @keyframes tabSlideIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ══ BASE ════════════════════════════════════════════════════════ */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background: #f4f5fb !important;
        color: #1a1a2e !important;
    }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container {
        padding: 1.8rem 2.8rem 2rem 2.8rem !important;
        max-width: 1450px !important;
    }
    [data-testid="stAppViewContainer"] { background: #f4f5fb !important; }
    [data-testid="stSidebar"]          { display: none !important; }

    /* ══ FILE BANNER ════════════════════════════════════════════════ */
    .file-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #fff;
        border: 1px solid #e2e3ef;
        border-radius: 12px;
        padding: 11px 20px;
        margin-bottom: 20px;
        font-size: 14px;
        font-weight: 500;
        color: #333;
        box-shadow: 0 1px 5px rgba(0,0,0,.06);
        animation: slideDown .5s ease both;
    }
    .file-size { color: #aaa; font-weight: 400; margin-left: 4px; }

    /* ══ METRIC CARDS ═══════════════════════════════════════════════ */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        margin-bottom: 24px;
    }
    .metric-card {
        border-radius: 18px;
        padding: 24px 26px;
        color: #fff;
        position: relative;
        overflow: hidden;
        background-size: 200% 200%;
        box-shadow: 0 6px 20px rgba(80,40,200,.22);
        transition: transform .25s ease, box-shadow .25s ease;
        cursor: default;
        /* stagger set inline via nth-child */
        animation: fadeInUp .6s ease both;
    }
    .metric-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 16px 36px rgba(80,40,200,.32);
        animation: gradientShift 3s ease infinite, pulse-ring 1.8s ease;
    }
    /* shimmer sweep on hover */
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 50%; height: 100%;
        background: linear-gradient(90deg,
            rgba(255,255,255,0) 0%,
            rgba(255,255,255,.18) 50%,
            rgba(255,255,255,0) 100%);
        transform: translateX(-100%) skewX(-15deg);
        transition: none;
        pointer-events: none;
    }
    .metric-card:hover::before {
        animation: shimmerSweep .7s ease forwards;
    }
    /* decorative bubbles */
    .metric-card .bubble-1 {
        position: absolute;
        top: -35px; right: -35px;
        width: 120px; height: 120px;
        border-radius: 50%;
        background: rgba(255,255,255,.13);
        animation: floatBubble 4s ease-in-out infinite;
    }
    .metric-card .bubble-2 {
        position: absolute;
        bottom: -20px; left: -20px;
        width: 80px; height: 80px;
        border-radius: 50%;
        background: rgba(255,255,255,.08);
        animation: floatBubble 5s ease-in-out infinite reverse;
    }
    .metric-card .label {
        font-size: 13px;
        font-weight: 500;
        opacity: .88;
        letter-spacing: .5px;
        margin-bottom: 10px;
        text-transform: uppercase;
        position: relative; z-index: 1;
    }
    .metric-card .value {
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -1.5px;
        line-height: 1;
        position: relative; z-index: 1;
        transition: transform .2s ease;
    }
    .card-1 {
        background: linear-gradient(135deg, #3d25a8, #6448dc, #4730b8);
        animation-delay: .05s;
    }
    .card-2 {
        background: linear-gradient(135deg, #4a30be, #7258e8, #5438c8);
        animation-delay: .15s;
    }
    .card-3 {
        background: linear-gradient(135deg, #563ad0, #8268f0, #6040d4);
        animation-delay: .25s;
    }
    .card-4 {
        background: linear-gradient(135deg, #6248d8, #9478f8, #6c50e0);
        animation-delay: .35s;
    }


    /* ══ ST.TABS OVERRIDE ══════════════════════════════════════════════ */
    [data-testid="stTabs"]        { background: transparent !important; }
    [data-testid="stTabsContent"] {
        border: none !important; padding: 0 !important;
        background: transparent !important;
        animation: tabSlideIn .35s ease both;
    }
    [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 2px solid #e2e3ef !important;
        gap: 0 !important; padding: 0 !important;
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        padding: 10px 22px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #888 !important;
        margin-bottom: -2px !important;
        transition: color .2s ease, transform .15s ease !important;
        border-radius: 0 !important;
    }
    [data-baseweb="tab"]:hover {
        color: #444 !important;
        background: transparent !important;
        transform: translateY(-1px) !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
        color: #d63031 !important;
        border-bottom-color: #d63031 !important;
        background: transparent !important;
    }
    [data-baseweb="tab-highlight"] { display: none !important; }
    [data-baseweb="tab-border"]    { display: none !important; }

    /* ══ SECTION HEADINGS ═════════════════════════════════════════════ */
    .section-heading {
        font-size: 22px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 16px 0;
        animation: fadeInUp .5s ease both;
    }
    .section-sub {
        font-size: 17px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 20px 0 12px 0;
        animation: fadeInUp .4s ease both;
    }

    /* ══ DATA TABLES ════════════════════════════════════════════════ */
    .table-wrapper {
        background: #fff;
        border-radius: 14px;
        padding: 4px 0;
        box-shadow: 0 1px 6px rgba(0,0,0,.07);
        overflow-x: auto;
        animation: fadeInUp .5s ease .1s both;
    }
    .table-wrapper table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .table-wrapper thead tr { background: #f6f7fc; }
    .table-wrapper th {
        padding: 11px 16px;
        font-weight: 600;
        color: #666;
        text-align: left;
        white-space: nowrap;
        border-bottom: 1px solid #eef0f8;
    }
    .table-wrapper td {
        padding: 10px 16px;
        color: #333;
        border-bottom: 1px solid #f2f3fa;
        white-space: nowrap;
        transition: background .15s ease;
    }
    /* staggered row entrance */
    .table-wrapper tbody tr {
        animation: rowFadeIn .4s ease both;
    }
    .table-wrapper tbody tr:nth-child(1) { animation-delay: .05s; }
    .table-wrapper tbody tr:nth-child(2) { animation-delay: .10s; }
    .table-wrapper tbody tr:nth-child(3) { animation-delay: .15s; }
    .table-wrapper tbody tr:nth-child(4) { animation-delay: .20s; }
    .table-wrapper tbody tr:nth-child(5) { animation-delay: .25s; }
    .table-wrapper tbody tr:nth-child(6) { animation-delay: .30s; }
    .table-wrapper tbody tr:nth-child(7) { animation-delay: .35s; }
    .table-wrapper tbody tr:nth-child(8) { animation-delay: .40s; }
    .table-wrapper tr:last-child td { border-bottom: none; }
    .table-wrapper tr:hover td { background: #f6f6ff; }
    .row-idx { color: #bbb; font-size: 12px; }

    /* ── chart card ── */
    .chart-card {
        background: #fff;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 6px rgba(0,0,0,.07);
    }

    /* ══ UPLOAD PAGE ═════════════════════════════════════════════════ */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 8vh;
        margin-bottom: 2rem;
        animation: fadeInUp 0.8s ease both;
    }
    .upload-icon-container {
        width: 80px;
        height: 80px;
        margin: 0 auto 24px;
        background: linear-gradient(135deg, #4730b8 0%, #7258e8 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 10px 20px rgba(71, 48, 184, 0.3);
        animation: floatBubble 3s ease-in-out infinite;
    }
    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #1a1a2e;
        margin-bottom: 16px;
        letter-spacing: -1px;
        text-align: center;
    }
    .hero-subtitle {
        color: #666;
        font-size: 18px;
        margin-bottom: 40px;
        line-height: 1.6;
        text-align: center;
        max-width: 600px;
    }
    
    /* Enhance Streamlit uploader to look like a massive dropzone */
    [data-testid="stFileUploader"] {
        background: #ffffff !important;
        border: 2px dashed #c0c4d6 !important;
        border-radius: 20px !important;
        padding: 40px 20px !important;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        animation: fadeInUp 0.8s ease 0.2s both;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #6448dc !important;
        background: rgba(100, 72, 220, 0.02) !important;
        box-shadow: 0 15px 35px rgba(100, 72, 220, 0.1);
        transform: translateY(-2px);
    }
    
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 32px 0;
        color: #a0a4b8;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        animation: fadeInUp 0.8s ease 0.3s both;
    }
    .divider::before, .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #d2d4e6;
    }
    .divider:not(:empty)::before {
        margin-right: 1em;
    }
    .divider:not(:empty)::after {
        margin-left: 1em;
    }

    /* Target the built-in dataset button */
    [data-testid="baseButton-primary"] {
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        animation: fadeInUp 0.8s ease 0.4s both;
    }

    /* ── info/warning overrides ── */
    [data-testid="stInfo"] {
        border-radius: 10px !important;
    }

    /* ── remove streamlit's default top padding on tab content ── */
    [data-testid="stTabsContent"] > div {
        padding-top: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constants ────────────────────────────────────────────────────────────────────
DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "data", "stations_geo.csv")
NUMERIC_COLS = ["latitude", "longitude", "pollutant_min", "pollutant_max", "pollutant_avg"]

# ── Helpers ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_df(raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def load_default() -> pd.DataFrame:
    df = pd.read_csv(DEFAULT_CSV)
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def df_to_html(df: pd.DataFrame, show_index: bool = True) -> str:
    cols = list(df.columns)
    header = "".join(f"<th>{c}</th>" for c in ([""] + cols if show_index else cols))
    body = ""
    for idx, row in df.iterrows():
        cells = f"<td class='row-idx'>{idx}</td>" if show_index else ""
        cells += "".join(f"<td>{v}</td>" for v in row)
        body += f"<tr>{cells}</tr>"
    return (
        f"<div class='table-wrapper'>"
        f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
        f"</div>"
    )

def fmt(v, d=2):
    return f"{v:.{d}f}" if pd.notna(v) else "—"

# ── Session state ─────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "file_size" not in st.session_state:
    st.session_state.file_size = None

# ═════════════════════════════════════════════════════════════════════════════════
# UPLOAD SCREEN
# ═════════════════════════════════════════════════════════════════════════════════
if st.session_state.df is None:
    # Use empty columns to center our content nicely without using full width
    col_space1, col_main, col_space2 = st.columns([1, 2, 1])
    
    with col_main:
        st.markdown(
            """
            <div class='hero-container'>
                <div class='upload-icon-container'>
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21.5 12H16c-.7 2-2 3-4 3s-3.3-1-4-3H2.5"/>
                        <path d="M5.5 5.5A5 5 0 0 1 12 3c2.8 0 5 2.2 5 5"/>
                        <path d="M12 12v6"/>
                        <path d="M12 18l-3-3"/>
                        <path d="M12 18l3-3"/>
                    </svg>
                </div>
                <div class='hero-title'>Air Quality Analytics</div>
                <div class='hero-subtitle'>Upload an AQI dataset to instantly generate comprehensive visual insights, map distributions, and predictive models.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        up = st.file_uploader(
            "Upload your CSV",
            type=["csv"],
            help="The file should contain AQI station data.",
            label_visibility="collapsed"
        )
        if up:
            raw = up.read()
            st.session_state.df        = parse_df(raw)
            st.session_state.file_name = up.name
            st.session_state.file_size = f"{len(raw)/1024:.1f}KB"
            st.rerun()

        st.markdown("<div class='divider'>OR</div>", unsafe_allow_html=True)

        if st.button("🚀 Explore Built-in Dataset", use_container_width=True, type="primary"):
            size = os.path.getsize(DEFAULT_CSV)
            st.session_state.df        = load_default()
            st.session_state.file_name = "stations_geo.csv"
            st.session_state.file_size = f"{size/1024:.1f}KB"
            st.rerun()

    st.stop()

# ═════════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════════
df = st.session_state.df

# ── File banner ──────────────────────────────────────────────────────────────────
b_col, x_col = st.columns([8, 1])
with b_col:
    st.markdown(
        f"""
        <div class='file-banner'>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9L13 2z"
                    stroke="#4730b8" stroke-width="1.8" fill="rgba(71,48,184,.10)"/>
              <path d="M13 2v7h7" stroke="#4730b8" stroke-width="1.8" fill="none"/>
            </svg>
            <b>{st.session_state.file_name}</b>
            <span class='file-size'>{st.session_state.file_size}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with x_col:
    if st.button("✕  Close", use_container_width=True):
        st.session_state.df        = None
        st.session_state.file_name = None
        st.session_state.file_size = None
        st.rerun()

# ── Metrics ───────────────────────────────────────────────────────────────────────
avg_aqi = df["pollutant_avg"].mean()     if "pollutant_avg" in df.columns else np.nan
max_aqi = df["pollutant_max"].max()      if "pollutant_max" in df.columns else np.nan
min_aqi = df["pollutant_min"].min()      if "pollutant_min" in df.columns else np.nan
records = len(df)

# raw numeric targets for JS counter
avg_raw = float(avg_aqi)  if pd.notna(avg_aqi) else 0
max_raw = float(max_aqi)  if pd.notna(max_aqi) else 0
min_raw = float(min_aqi)  if pd.notna(min_aqi) else 0
rec_raw = int(records)

st.markdown(
    f"""
    <div class='metric-grid'>
      <div class='metric-card card-1'>
        <div class='bubble-1'></div><div class='bubble-2'></div>
        <div class='label'>Avg AQI</div>
        <div class='value' id='cnt-avg' data-target='{avg_raw:.2f}' data-decimals='2'>{fmt(avg_aqi)}</div>
      </div>
      <div class='metric-card card-2'>
        <div class='bubble-1'></div><div class='bubble-2'></div>
        <div class='label'>Max AQI</div>
        <div class='value' id='cnt-max' data-target='{max_raw:.2f}' data-decimals='2'>{fmt(max_aqi)}</div>
      </div>
      <div class='metric-card card-3'>
        <div class='bubble-1'></div><div class='bubble-2'></div>
        <div class='label'>Min AQI</div>
        <div class='value' id='cnt-min' data-target='{min_raw:.2f}' data-decimals='2'>{fmt(min_aqi)}</div>
      </div>
      <div class='metric-card card-4'>
        <div class='bubble-1'></div><div class='bubble-2'></div>
        <div class='label'>Records</div>
        <div class='value' id='cnt-rec' data-target='{rec_raw}' data-decimals='0'>{records:,}</div>
      </div>
    </div>

    <script>
    (function() {{
      function easeOutQuart(t) {{ return 1 - Math.pow(1 - t, 4); }}
      function animateCounter(el) {{
        var target   = parseFloat(el.getAttribute('data-target'));
        var decimals = parseInt(el.getAttribute('data-decimals'));
        var duration = 1400;
        var start    = null;
        function step(ts) {{
          if (!start) start = ts;
          var progress = Math.min((ts - start) / duration, 1);
          var eased    = easeOutQuart(progress);
          var current  = target * eased;
          if (decimals > 0) {{
            el.textContent = current.toFixed(decimals);
          }} else {{
            el.textContent = Math.round(current).toLocaleString();
          }}
          if (progress < 1) requestAnimationFrame(step);
          else {{
            if (decimals > 0) el.textContent = target.toFixed(decimals);
            else el.textContent = Math.round(target).toLocaleString();
          }}
        }}
        requestAnimationFrame(step);
      }}
      var ids = ['cnt-avg','cnt-max','cnt-min','cnt-rec'];
      ids.forEach(function(id) {{
        var el = document.getElementById(id);
        if (el) animateCounter(el);
      }});
    }})();
    </script>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────────
tab_analysis, tab_viz, tab_pred = st.tabs(["📊  Analysis", "📈  Visualization", "🤖  Prediction"])

# ═══════════════════════════════════════════════════════
# TAB 1 – Analysis
# ═══════════════════════════════════════════════════════
with tab_analysis:
    st.markdown("<div class='section-heading'>Dataset Overview</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.15, 0.85])

    # Head table
    with left_col:
        preview = ["country", "state", "city", "station"]
        preview = [c for c in preview if c in df.columns]
        st.markdown(df_to_html(df[preview].head(5)), unsafe_allow_html=True)

    # Describe table
    with right_col:
        desc_cols = [c for c in NUMERIC_COLS if c in df.columns]
        desc = df[desc_cols].describe().round(4)
        st.markdown(df_to_html(desc), unsafe_allow_html=True)

    # Column info
    st.markdown("<div class='section-sub'>Column Info</div>", unsafe_allow_html=True)
    info_rows = ""
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isna().sum())
        pct   = f"{nulls/len(df)*100:.1f}%"
        non_null = f"{len(df)-nulls:,}"
        null_color = "#e05" if nulls > 0 else "#48bb78"
        info_rows += (
            f"<tr><td><b>{col}</b></td>"
            f"<td style='color:#6244d8'>{dtype}</td>"
            f"<td>{non_null}</td>"
            f"<td style='color:{null_color}'>{pct}</td></tr>"
        )
    st.markdown(
        f"""<div class='table-wrapper'>
          <table>
            <thead><tr>
              <th>Column</th><th>Dtype</th><th>Non-Null Count</th><th>Null %</th>
            </tr></thead>
            <tbody>{info_rows}</tbody>
          </table></div>""",
        unsafe_allow_html=True,
    )

    # Value counts for categorical columns
    cat_cols = [c for c in ["country", "state", "city", "pollutant_id"] if c in df.columns]
    if cat_cols:
        st.markdown("<div class='section-sub'>Top Values (Categorical)</div>", unsafe_allow_html=True)
        vc_cols = st.columns(len(cat_cols))
        for i, col in enumerate(cat_cols):
            with vc_cols[i]:
                vc = df[col].value_counts().head(8).reset_index()
                vc.columns = [col, "count"]
                vc_rows = "".join(
                    f"<tr><td>{r[col]}</td><td style='color:#6244d8;font-weight:600'>{r['count']}</td></tr>"
                    for _, r in vc.iterrows()
                )
                st.markdown(
                    f"""<div class='table-wrapper'>
                      <table>
                        <thead><tr><th>{col}</th><th>Count</th></tr></thead>
                        <tbody>{vc_rows}</tbody>
                      </table></div>""",
                    unsafe_allow_html=True,
                )

# ═══════════════════════════════════════════════════════
# TAB 2 – Visualization
# ═══════════════════════════════════════════════════════
with tab_viz:
    st.markdown("<div class='section-heading'>Visualizations</div>", unsafe_allow_html=True)

    city_col = "city"        if "city"        in df.columns else None
    poll_col = "pollutant_id" if "pollutant_id" in df.columns else None

    f1, f2, _ = st.columns([1.5, 1.5, 3])
    cities = sorted(df[city_col].dropna().unique()) if city_col else []
    polls  = sorted(df[poll_col].dropna().unique()) if poll_col else []

    with f1:
        sel_city = st.selectbox("🏙 City", cities, key="vis_city") if cities else None
    with f2:
        sel_poll = st.selectbox("🧪 Pollutant", polls, key="vis_poll") if polls else None

    filtered = df.copy()
    if sel_city and city_col:
        filtered = filtered[filtered[city_col] == sel_city]
    if sel_poll and poll_col:
        filtered = filtered[filtered[poll_col] == sel_poll]

    if filtered.empty:
        st.info("No data for the selected filters.")
    else:
        CHART_BG = dict(paper_bgcolor="white", plot_bgcolor="white")

        v1, v2 = st.columns(2)

        # ── Bar: top stations by avg AQI ──
        with v1:
            if "pollutant_avg" in filtered.columns and "station" in filtered.columns:
                bar_df = (
                    filtered.dropna(subset=["pollutant_avg"])
                    .nlargest(20, "pollutant_avg")
                )
                fig_bar = go.Figure(go.Bar(
                    x=bar_df["station"],
                    y=bar_df["pollutant_avg"],
                    marker=dict(
                        color=bar_df["pollutant_avg"],
                        colorscale=[[0, "#8268f0"], [1, "#4730b8"]],
                        showscale=False,
                    ),
                ))
                fig_bar.update_layout(
                    **CHART_BG,
                    margin=dict(l=40, r=10, t=40, b=110),
                    xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=10)),
                    yaxis=dict(title="Avg AQI", gridcolor="#f0f0f7"),
                    title=dict(text="Top 20 Stations – Avg AQI", font=dict(size=14, color="#222"), x=0.02),
                    height=390,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # ── Scatter: min/max range ──
        with v2:
            if "pollutant_min" in filtered.columns and "pollutant_max" in filtered.columns:
                sc_df = filtered.dropna(subset=["pollutant_min", "pollutant_max"]).head(40)
                x_axis = sc_df["station"] if "station" in sc_df.columns else sc_df.index
                fig_sc = go.Figure()
                fig_sc.add_trace(go.Scatter(
                    x=x_axis, y=sc_df["pollutant_min"],
                    mode="lines+markers", name="Min",
                    line=dict(color="#7c5cff", width=2),
                    marker=dict(size=5),
                ))
                fig_sc.add_trace(go.Scatter(
                    x=x_axis, y=sc_df["pollutant_max"],
                    mode="lines+markers", name="Max",
                    line=dict(color="#4ea1ff", width=2),
                    marker=dict(size=5),
                ))
                fig_sc.update_layout(
                    **CHART_BG,
                    margin=dict(l=40, r=10, t=40, b=110),
                    xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=10)),
                    yaxis=dict(title="Value", gridcolor="#f0f0f7"),
                    legend=dict(orientation="h", y=1.08),
                    title=dict(text="Min / Max Range per Station", font=dict(size=14, color="#222"), x=0.02),
                    height=390,
                )
                st.plotly_chart(fig_sc, use_container_width=True)

        # ── Histogram ──
        if "pollutant_avg" in filtered.columns:
            h1, h2 = st.columns(2)
            with h1:
                hist_data = filtered["pollutant_avg"].dropna()
                fig_hist = px.histogram(
                    hist_data, x="pollutant_avg", nbins=40,
                    color_discrete_sequence=["#6244d8"],
                )
                fig_hist.update_layout(
                    **CHART_BG,
                    margin=dict(l=40, r=10, t=40, b=40),
                    xaxis=dict(title="Avg AQI", showgrid=False),
                    yaxis=dict(title="Frequency", gridcolor="#f0f0f7"),
                    bargap=0.06,
                    title=dict(text="AQI Distribution", font=dict(size=14, color="#222"), x=0.02),
                    height=300,
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # ── Box plot ──
            with h2:
                if poll_col and "pollutant_avg" in df.columns:
                    box_df = df[df[city_col] == sel_city] if (city_col and sel_city) else df
                    fig_box = px.box(
                        box_df, x=poll_col, y="pollutant_avg",
                        color=poll_col,
                        color_discrete_sequence=px.colors.sequential.Purples_r,
                    )
                    fig_box.update_layout(
                        **CHART_BG,
                        margin=dict(l=40, r=10, t=40, b=60),
                        xaxis=dict(title="Pollutant", showgrid=False),
                        yaxis=dict(title="Avg AQI", gridcolor="#f0f0f7"),
                        showlegend=False,
                        title=dict(text="AQI by Pollutant Type", font=dict(size=14, color="#222"), x=0.02),
                        height=300,
                    )
                    st.plotly_chart(fig_box, use_container_width=True)

        # ── Map ──
        if "latitude" in filtered.columns and "longitude" in filtered.columns:
            map_df = filtered.dropna(subset=["latitude", "longitude"])
            if not map_df.empty:
                st.markdown("<div class='section-sub'>Station Map</div>", unsafe_allow_html=True)
                fig_map = px.scatter_mapbox(
                    map_df,
                    lat="latitude", lon="longitude",
                    hover_name="station" if "station" in map_df.columns else None,
                    color="pollutant_avg" if "pollutant_avg" in map_df.columns else None,
                    color_continuous_scale=[[0, "#8268f0"], [0.5, "#f6ad55"], [1, "#fc8181"]],
                    zoom=4, height=500,
                )
                try:
                    token = st.secrets["MAPBOX_TOKEN"]
                except Exception:
                    token = ""
                map_cfg = dict(
                    style="carto-positron",
                    center=dict(lat=map_df["latitude"].mean(), lon=map_df["longitude"].mean()),
                )
                if token:
                    map_cfg["accesstoken"] = token
                fig_map.update_layout(mapbox=map_cfg, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig_map, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB 3 – Prediction
# ═══════════════════════════════════════════════════════
with tab_pred:
    st.markdown("<div class='section-heading'>AQI Prediction</div>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#888;font-size:14px;margin-top:-10px;margin-bottom:20px;'>"
        "Linear regression model trained on numeric features to predict average AQI.</p>",
        unsafe_allow_html=True,
    )

    feature_cols = [c for c in ["latitude", "longitude", "pollutant_min", "pollutant_max"] if c in df.columns]
    target = "pollutant_avg"

    if target not in df.columns or len(feature_cols) < 2:
        st.warning("Not enough numeric columns to train a model.")
    else:
        pred_df = df[feature_cols + [target]].dropna()

        if len(pred_df) < 30:
            st.warning("Too few complete rows for training.")
        else:
            X = pred_df[feature_cols].values
            y = pred_df[target].values
            split = int(len(pred_df) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            model = LinearRegression().fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2  = model.score(X_test, y_test)
            mae = float(np.mean(np.abs(y_pred - y_test)))
            rmse = float(np.sqrt(np.mean((y_pred - y_test) ** 2)))

            # Score cards
            pm1, pm2, pm3, pm4 = st.columns(4)
            score_cards = [
                ("pm1", "card-1", "R² Score",       f"{r2:.4f}"),
                ("pm2", "card-2", "MAE",             f"{mae:.2f}"),
                ("pm3", "card-3", "RMSE",            f"{rmse:.2f}"),
                ("pm4", "card-4", "Test Samples",    f"{len(y_test):,}"),
            ]
            for col, (var, card, label, val) in zip([pm1, pm2, pm3, pm4], score_cards):
                col.markdown(
                    f"<div class='metric-card {card}' style='padding:18px 22px;'>"
                    f"<div class='label'>{label}</div>"
                    f"<div class='value' style='font-size:26px;'>{val}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            CHART_BG = dict(paper_bgcolor="white", plot_bgcolor="white")
            p1, p2 = st.columns(2)

            # Actual vs Predicted
            with p1:
                min_v = float(min(y_test.min(), y_pred.min()))
                max_v = float(max(y_test.max(), y_pred.max()))
                fig_prd = go.Figure()
                fig_prd.add_trace(go.Scatter(
                    x=y_test, y=y_pred, mode="markers",
                    marker=dict(color="#6244d8", opacity=0.45, size=5),
                    name="Predicted",
                ))
                fig_prd.add_trace(go.Scatter(
                    x=[min_v, max_v], y=[min_v, max_v],
                    mode="lines", line=dict(color="#d63031", dash="dash", width=1.5),
                    name="Perfect fit",
                ))
                fig_prd.update_layout(
                    **CHART_BG,
                    xaxis=dict(title="Actual AQI", showgrid=False),
                    yaxis=dict(title="Predicted AQI", gridcolor="#f0f0f7"),
                    margin=dict(l=50, r=20, t=40, b=40),
                    legend=dict(orientation="h", y=1.1),
                    title=dict(text="Actual vs Predicted AQI", font=dict(size=14, color="#222"), x=0.02),
                    height=380,
                )
                st.plotly_chart(fig_prd, use_container_width=True)

            # Feature coefficients
            with p2:
                coef_df = pd.DataFrame({
                    "Feature": feature_cols,
                    "Coefficient": model.coef_,
                }).sort_values("Coefficient")
                colors = ["#d63031" if v < 0 else "#6244d8" for v in coef_df["Coefficient"]]
                fig_coef = go.Figure(go.Bar(
                    x=coef_df["Coefficient"],
                    y=coef_df["Feature"],
                    orientation="h",
                    marker_color=colors,
                ))
                fig_coef.update_layout(
                    **CHART_BG,
                    xaxis=dict(showgrid=False, title="Coefficient"),
                    yaxis=dict(showgrid=False),
                    margin=dict(l=10, r=20, t=40, b=30),
                    title=dict(text="Feature Coefficients", font=dict(size=14, color="#222"), x=0.02),
                    height=280,
                )
                st.plotly_chart(fig_coef, use_container_width=True)

            # Residuals distribution
            residuals = y_test - y_pred
            fig_res = px.histogram(
                residuals, nbins=40, color_discrete_sequence=["#6244d8"],
            )
            fig_res.update_layout(
                **CHART_BG,
                xaxis=dict(title="Residual (Actual − Predicted)", showgrid=False),
                yaxis=dict(title="Count", gridcolor="#f0f0f7"),
                bargap=0.06,
                margin=dict(l=50, r=20, t=40, b=40),
                title=dict(text="Residuals Distribution", font=dict(size=14, color="#222"), x=0.02),
                height=260,
            )
            st.plotly_chart(fig_res, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <hr style='border:none;border-top:1px solid #e2e3ef;margin:30px 0 10px;'>
    <p style='text-align:center;color:#ccc;font-size:12px;'>
        AQI Dashboard &nbsp;·&nbsp; stations_geo.csv
    </p>
    """,
    unsafe_allow_html=True,
)
