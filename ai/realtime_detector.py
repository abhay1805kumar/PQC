import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from live_data import ANOMALIES_FILE


# Configuration


PROMETHEUS_URL = "http://localhost:9091"

OUTPUT_FILE = ANOMALIES_FILE
MIN_SAMPLES_FOR_TRAINING = 10

# The features our model uses for anomaly detection
FEATURES = [
    "requests_per_interval",
    "handshakes_per_interval",
    "active_connections",
    "request_bytes_per_interval",
    "response_bytes_per_interval",
    "handshake_duration_ms",
    "request_duration_ms",
]


# Helper Functions


def query_prometheus(metric):
    """Fetches a specific metric value from Prometheus."""
    url = f"{PROMETHEUS_URL}/api/v1/query"
    try:
        response = requests.get(url, params={"query": metric}, timeout=5)
        response.raise_for_status()
        results = response.json()["data"]["result"]
        return float(results[0]["value"][1]) if results else 0.0
    except requests.RequestException as e:
        print(f"[PROMETHEUS ERROR] Failed to fetch {metric}: {e}")
        return 0.0

def collect_metrics():
    """Collects current raw snapshot of metrics from Prometheus."""
    return {
        "timestamp": datetime.now(),
        "requests_total": query_prometheus("pq_proxy_requests_total"),
        "tls_handshakes_total": query_prometheus("pq_proxy_tls_handshakes_total"),
        "active_connections": query_prometheus("pq_proxy_active_connections"),
        "request_bytes_total": query_prometheus("pq_proxy_request_bytes_total"),
        "response_bytes_total": query_prometheus("pq_proxy_response_bytes_total"),
        "handshake_duration_ms": query_prometheus("pq_proxy_handshake_duration_ms"),
        "request_duration_ms": query_prometheus("pq_proxy_request_duration_ms"),
    }


# Main Real-Time Loop


def main():
    print("============================================")
    print("PQ Proxy AI - Real-Time Anomaly Detection")
    print(f"Prometheus: {PROMETHEUS_URL}")
    print(f"Output:     {OUTPUT_FILE}")
    print("============================================")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
 
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
    
    history = []
    prev_metrics = None
    
    # Model Components
    scaler = StandardScaler()
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    is_trained = False
    
    while True:
        try:
            current_metrics = collect_metrics()
            
            # We need at least two snapshots to calculate interval rates
            if prev_metrics is None:
                prev_metrics = current_metrics
                print("[INIT] Fetched initial metrics state. Waiting for next interval...")
                time.sleep(5)
                continue
                
            # Calculate interval rates (diff between current and previous)
            processed_metrics = current_metrics.copy()
            processed_metrics["requests_per_interval"] = current_metrics["requests_total"] - prev_metrics["requests_total"]
            processed_metrics["handshakes_per_interval"] = current_metrics["tls_handshakes_total"] - prev_metrics["tls_handshakes_total"]
            processed_metrics["request_bytes_per_interval"] = current_metrics["request_bytes_total"] - prev_metrics["request_bytes_total"]
            processed_metrics["response_bytes_per_interval"] = current_metrics["response_bytes_total"] - prev_metrics["response_bytes_total"]
            
            history.append(processed_metrics)
            prev_metrics = current_metrics
            
            #PHASE 1: WARMUP & TRAINING
            if not is_trained:
                if len(history) < MIN_SAMPLES_FOR_TRAINING:
                    print(f"[WARMUP] Collecting baseline data... ({len(history)}/{MIN_SAMPLES_FOR_TRAINING})")
                    # Keep the dashboard live during baseline collection.
                    processed_metrics["anomaly_prediction"] = 0
                    processed_metrics["anomaly_score"] = np.nan
                    processed_metrics["status"] = "WARMUP"
                    pd.DataFrame([processed_metrics]).to_csv(
                        OUTPUT_FILE,
                        mode="a",
                        header=not OUTPUT_FILE.exists(),
                        index=False,
                    )
                else:
                    print("[TRAINING] Enough baseline data collected. Training Isolation Forest model...")
                    df = pd.DataFrame(history)
                    X = df[FEATURES].copy().replace([np.inf, -np.inf], np.nan).fillna(0)
                    
                    X_scaled = scaler.fit_transform(X)
                    model.fit(X_scaled)
                    is_trained = True
                    print("[TRAINING] Model trained successfully! Switching to real-time inference.")
                    
                    # Process the historical batch to save it
                    df["anomaly_prediction"] = model.predict(X_scaled)
                    df["anomaly_score"] = model.decision_function(X_scaled)
                    df["status"] = np.where(df["anomaly_prediction"] == -1, "ANOMALY", "NORMAL")
                    
                    df.to_csv(OUTPUT_FILE, index=False)
            
            #PHASE 2: REAL-TIME INFERENCE
            else:
                df_current = pd.DataFrame([processed_metrics])
                X_current = df_current[FEATURES].copy().replace([np.inf, -np.inf], np.nan).fillna(0)
                
                # Transform using the pre-fitted scaler and predict
                X_scaled = scaler.transform(X_current)
                prediction = model.predict(X_scaled)[0]
                score = model.decision_function(X_scaled)[0]
                
                processed_metrics["anomaly_prediction"] = prediction
                processed_metrics["anomaly_score"] = score
                processed_metrics["status"] = "ANOMALY" if prediction == -1 else "NORMAL"
                
                status_color = "\033[91m" if prediction == -1 else "\033[92m"
                reset_color = "\033[0m"
                
                print(
                    f"[INFERENCE] requests={processed_metrics['requests_total']} "
                    f"active={processed_metrics['active_connections']} "
                    f"score={score:.3f} status={status_color}{processed_metrics['status']}{reset_color}"
                )
                
                # Append to output CSV
                pd.DataFrame([processed_metrics]).to_csv(
                    OUTPUT_FILE, 
                    mode='a', 
                    header=not OUTPUT_FILE.exists(), 
                    index=False
                )
                
        except Exception as e:
            print("[ERROR]", e)
            
        time.sleep(5)

if __name__ == "__main__":
    main()
