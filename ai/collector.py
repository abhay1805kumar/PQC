import time
import requests
import pandas as pd
from datetime import datetime


PROMETHEUS_URL = "http://localhost:9091"

OUTPUT_FILE = "data/metrics.csv"



# Prometheus query


def query_prometheus(metric):
    url = f"{PROMETHEUS_URL}/api/v1/query"

    params = {
        "query": metric
    }

    response = requests.get(
        url,
        params=params,
        timeout=5
    )

    response.raise_for_status()

    data = response.json()

    results = data["data"]["result"]

    if not results:
        return 0.0

    return float(results[0]["value"][1])



# Collect metrics


def collect_metrics():

    timestamp = datetime.utcnow().isoformat()

    metrics = {
        "timestamp": timestamp,

        "requests_total":
            query_prometheus(
                "pq_proxy_requests_total"
            ),

        "tls_handshakes_total":
            query_prometheus(
                "pq_proxy_tls_handshakes_total"
            ),

        "active_connections":
            query_prometheus(
                "pq_proxy_active_connections"
            ),

        "request_bytes_total":
            query_prometheus(
                "pq_proxy_request_bytes_total"
            ),

        "response_bytes_total":
            query_prometheus(
                "pq_proxy_response_bytes_total"
            ),

        "handshake_duration_ms":
            query_prometheus(
                "pq_proxy_handshake_duration_ms"
            ),

        "request_duration_ms":
            query_prometheus(
                "pq_proxy_request_duration_ms"
            ),
    }

    return metrics



# Save metrics


def save_metrics(metrics):

    df = pd.DataFrame([metrics])

    try:
        existing = pd.read_csv(OUTPUT_FILE)

        df = pd.concat(
            [existing, df],
            ignore_index=True
        )

    except FileNotFoundError:
        pass

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )



# Main collector loop


def main():

    print("====================================")
    print("PQ Proxy AI Metrics Collector")
    print("Prometheus:", PROMETHEUS_URL)
    print("Output:", OUTPUT_FILE)
    print("====================================")

    while True:

        try:

            metrics = collect_metrics()

            save_metrics(metrics)

            print(
                f"[COLLECTOR] "
                f"requests={metrics['requests_total']} "
                f"handshakes={metrics['tls_handshakes_total']} "
                f"active={metrics['active_connections']} "
                f"handshake_ms={metrics['handshake_duration_ms']:.3f} "
                f"request_ms={metrics['request_duration_ms']:.3f}"
            )

        except Exception as e:

            print(
                "[COLLECTOR] Error:",
                e
            )

        time.sleep(5)


if __name__ == "__main__":
    main()