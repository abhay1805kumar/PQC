import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


INPUT_FILE = "data/metrics.csv"

OUTPUT_FILE = "data/anomalies.csv"



# Load data


df = pd.read_csv(INPUT_FILE)


if len(df) < 10:

    raise RuntimeError(
        "Not enough data. Collect at least 10 samples first."
    )



# Convert cumulative counters into rates


df["requests_per_interval"] = (
    df["requests_total"].diff()
)

df["handshakes_per_interval"] = (
    df["tls_handshakes_total"].diff()
)

df["request_bytes_per_interval"] = (
    df["request_bytes_total"].diff()
)

df["response_bytes_per_interval"] = (
    df["response_bytes_total"].diff()
)



# First row has no previous sample


df = df.dropna()



# AI features


features = [
    "requests_per_interval",
    "handshakes_per_interval",
    "active_connections",
    "request_bytes_per_interval",
    "response_bytes_per_interval",
    "handshake_duration_ms",
    "request_duration_ms",
]


X = df[features].copy()



# Handle invalid values


X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

X = X.fillna(0)



# Standardize features


scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)



# Isolation Forest


model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)


model.fit(X_scaled)



# Predict anomalies


df["anomaly_prediction"] = model.predict(
    X_scaled
)



# Anomaly score


df["anomaly_score"] = model.decision_function(
    X_scaled
)



# Human-readable label


df["status"] = np.where(
    df["anomaly_prediction"] == -1,
    "ANOMALY",
    "NORMAL"
)



# Save results


df.to_csv(
    OUTPUT_FILE,
    index=False
)



# Display results


print("====================================")
print("PQ Proxy AI Anomaly Detection")
print("====================================")

print()

print(
    "Total samples:",
    len(df)
)

print(
    "Anomalies detected:",
    (df["status"] == "ANOMALY").sum()
)

print()

print(
    df[
        [
            "timestamp",
            "handshake_duration_ms",
            "request_duration_ms",
            "active_connections",
            "anomaly_score",
            "status",
        ]
    ].tail(20)
)

print()

print(
    "Saved:",
    OUTPUT_FILE
)