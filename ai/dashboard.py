import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from live_data import ANOMALIES_FILE

# Shared with realtime_detector.py; it is the dashboard's live data source.
DATA_FILE = ANOMALIES_FILE
REFRESH_INTERVAL = 2000  # milliseconds



# Page configuration


st.set_page_config(
    page_title="PQ Proxy Analytics",
    page_icon="🔐",
    layout="wide"
)



# AUTO REFRESH


st_autorefresh(
    interval=REFRESH_INTERVAL,
    key="dashboard_refresh"
)



# Title


st.title("Post-Quantum Reverse Proxy Analytics")

st.markdown(
    """
    **TLS 1.3 + X25519MLKEM768 + AI Anomaly Detection**

    This dashboard monitors performance and detects unusual
    traffic patterns associated with the post-quantum proxy.
    """
)



# Load CSV


def load_data():

    try:

        df = pd.read_csv(DATA_FILE)

        
        # Timestamp
        

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            df = df.dropna(
                subset=["timestamp"]
            )

        
        # Numeric columns
        

        numeric_columns = [
            "requests_total",
            "tls_handshakes_total",
            "active_connections",
            "handshake_duration_ms",
            "request_duration_ms",
            "requests_per_interval",
            "handshakes_per_interval",
            "anomaly_score"
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        return df

    except FileNotFoundError:

        return pd.DataFrame()

    except Exception as e:

        st.error(f"Error loading data: {e}")

        return pd.DataFrame()



# READ DATA


df = load_data()



# Check data


if df.empty:

    st.warning(
        "No live anomaly data found. Start realtime_detector.py first."
    )

    st.stop()



# Latest data


latest = df.iloc[-1]



# Basic calculations


total_samples = len(df)

if "status" in df.columns:

    total_anomalies = int(
        (
            df["status"]
            .astype(str)
            .str.upper()
            == "ANOMALY"
        ).sum()
    )

else:

    total_anomalies = 0


anomaly_percentage = (
    total_anomalies / total_samples * 100
    if total_samples > 0
    else 0
)



# Header metrics


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Samples",
        total_samples
    )


with col2:

    requests = latest.get(
        "requests_total",
        0
    )

    st.metric(
        "Requests",
        f"{requests:.0f}"
    )


with col3:

    handshakes = latest.get(
        "tls_handshakes_total",
        0
    )

    st.metric(
        "TLS Handshakes",
        f"{handshakes:.0f}"
    )


with col4:

    st.metric(
        "Anomalies",
        total_anomalies
    )



# Performance


st.subheader("Proxy Performance")


col1, col2, col3, col4 = st.columns(4)


with col1:

    handshake_latency = latest.get(
        "handshake_duration_ms",
        0
    )

    st.metric(
        "PQ Handshake Latency",
        f"{handshake_latency:.3f} ms"
    )


with col2:

    request_latency = latest.get(
        "request_duration_ms",
        0
    )

    st.metric(
        "Request Latency",
        f"{request_latency:.3f} ms"
    )


with col3:

    active_connections = latest.get(
        "active_connections",
        0
    )

    st.metric(
        "Active Connections",
        f"{active_connections:.0f}"
    )


with col4:

    st.metric(
        "Anomaly Rate",
        f"{anomaly_percentage:.2f}%"
    )



# Current AI status


st.subheader("AI Traffic Analysis")


latest_status = str(
    latest.get("status", "NORMAL")
).upper()


if latest_status == "ANOMALY":

    st.error("⚠ ANOMALY DETECTED")

    st.write(
        "The latest observation contains traffic "
        "characteristics that differ from the learned baseline."
    )

else:

    st.success("✓ TRAFFIC NORMAL")

    st.write(
        "The latest observation is consistent with "
        "the learned traffic baseline."
    )



# Last update


st.caption(
    f"Last data timestamp: {latest['timestamp']}"
)

st.caption(
    "Dashboard automatically refreshes every 2 seconds."
)



# Latency charts


st.subheader("Latency Analysis")


latency_columns = [
    "handshake_duration_ms",
    "request_duration_ms"
]


if all(
    column in df.columns
    for column in latency_columns
):

    chart_data = df[
        [
            "timestamp",
            "handshake_duration_ms",
            "request_duration_ms"
        ]
    ].copy()

    # Make absolutely sure chart values are numeric

    chart_data[
        "handshake_duration_ms"
    ] = pd.to_numeric(
        chart_data["handshake_duration_ms"],
        errors="coerce"
    )

    chart_data[
        "request_duration_ms"
    ] = pd.to_numeric(
        chart_data["request_duration_ms"],
        errors="coerce"
    )

    chart_data = chart_data.dropna(
        subset=[
            "handshake_duration_ms",
            "request_duration_ms"
        ]
    )

    chart_data = chart_data.set_index(
        "timestamp"
    )

    st.line_chart(
        chart_data,
        y=[
            "handshake_duration_ms",
            "request_duration_ms"
        ],
        use_container_width=True
    )



# AI anomaly score


st.subheader("AI Anomaly Score")


if "anomaly_score" in df.columns:

    score_data = df[
        [
            "timestamp",
            "anomaly_score"
        ]
    ].copy()

    score_data["anomaly_score"] = pd.to_numeric(
        score_data["anomaly_score"],
        errors="coerce"
    )

    score_data = score_data.dropna(
        subset=["anomaly_score"]
    )

    score_data = score_data.set_index(
        "timestamp"
    )

    st.line_chart(
        score_data,
        y="anomaly_score",
        use_container_width=True
    )



# Traffic rate


st.subheader("Traffic Rate")


rate_columns = [
    "requests_per_interval",
    "handshakes_per_interval"
]


if all(
    column in df.columns
    for column in rate_columns
):

    traffic_data = df[
        [
            "timestamp",
            "requests_per_interval",
            "handshakes_per_interval"
        ]
    ].copy()

    traffic_data[
        "requests_per_interval"
    ] = pd.to_numeric(
        traffic_data["requests_per_interval"],
        errors="coerce"
    )

    traffic_data[
        "handshakes_per_interval"
    ] = pd.to_numeric(
        traffic_data["handshakes_per_interval"],
        errors="coerce"
    )

    traffic_data = traffic_data.dropna(
        subset=rate_columns
    )

    traffic_data = traffic_data.set_index(
        "timestamp"
    )

    st.line_chart(
        traffic_data,
        y=[
            "requests_per_interval",
            "handshakes_per_interval"
        ],
        use_container_width=True
    )



# Detected anomalies


st.subheader("Detected Anomalies")


if "status" in df.columns:

    anomalies = df[
        df["status"]
        .astype(str)
        .str.upper()
        == "ANOMALY"
    ].copy()

else:

    anomalies = pd.DataFrame()


if anomalies.empty:

    st.info(
        "No anomalies detected in the collected dataset."
    )

else:

    display_columns = [
        "timestamp",
        "handshake_duration_ms",
        "request_duration_ms",
        "active_connections",
        "anomaly_score",
        "status"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in anomalies.columns
    ]

    st.dataframe(
        anomalies[
            display_columns
        ]
        .sort_values(
            "timestamp",
            ascending=False
        ),
        use_container_width=True
    )



# Latest observations


st.subheader("Latest Traffic Observations")


latest_columns = [
    "timestamp",
    "requests_total",
    "tls_handshakes_total",
    "active_connections",
    "handshake_duration_ms",
    "request_duration_ms",
    "anomaly_score",
    "status"
]


latest_columns = [
    column
    for column in latest_columns
    if column in df.columns
]


latest_table = (
    df[
        latest_columns
    ]
    .tail(20)
    .sort_values(
        "timestamp",
        ascending=False
    )
)


st.dataframe(
    latest_table,
    use_container_width=True
)



# Footer


st.divider()

st.caption(
    "PQ Proxy Analytics • Live monitoring from realtime_detector.py"
)
