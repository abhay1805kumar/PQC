"""Generate dashboard-ready traffic samples for the real-time pipeline."""

import csv
import math
import random
import time
from datetime import datetime

from live_data import ANOMALIES_FILE


DATA_FILE = ANOMALIES_FILE
INTERVAL = 1.0

FIELDS = [
    "timestamp", "requests_total", "tls_handshakes_total", "active_connections",
    "request_bytes_total", "response_bytes_total", "handshake_duration_ms",
    "request_duration_ms", "requests_per_interval", "handshakes_per_interval",
    "request_bytes_per_interval", "response_bytes_per_interval",
    "anomaly_prediction", "anomaly_score", "status",
]


def main():
    """Write realistic detector-compatible samples for dashboard demos."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    requests_total = tls_handshakes_total = 0
    request_bytes_total = response_bytes_total = 0


    with DATA_FILE.open("w", newline="", encoding="utf-8") as file:
        csv.DictWriter(file, fieldnames=FIELDS).writeheader()

    print("=" * 70)
    print("POST-QUANTUM REVERSE PROXY - LIVE DASHBOARD TEST")
    print("=" * 70)
    print(f"Writing detector-compatible data to: {DATA_FILE}")
    print("Dashboard should refresh every 2 seconds.")
    print("Anomaly bursts occur periodically. Press Ctrl+C to stop.")
    print("=" * 70)

    start_time = time.time()
    try:
        while True:
            elapsed = time.time() - start_time
            traffic_wave = math.sin(elapsed / 8.0)
            requests_per_interval = int(max(5, 35 + traffic_wave * 15 + random.randint(-8, 8)))
            handshakes_per_interval = int(max(3, requests_per_interval * random.uniform(0.55, 0.9)))
            active_connections = int(max(2, 20 + traffic_wave * 10 + random.randint(-5, 8)))
            request_bytes_per_interval = requests_per_interval * random.randint(700, 1_500)
            response_bytes_per_interval = requests_per_interval * random.randint(1_200, 3_000)
            handshake_latency = max(3, random.gauss(18, 3))
            request_latency = max(8, random.gauss(35, 7))

            
            anomaly_prediction = 1
            anomaly_score = random.uniform(0.03, 0.25)
            status = "NORMAL"

            if 20 <= elapsed % 30 <= 28:
                requests_per_interval = random.randint(180, 450)
                handshakes_per_interval = random.randint(120, 300)
                active_connections = random.randint(100, 280)
                request_bytes_per_interval = requests_per_interval * random.randint(8_000, 20_000)
                response_bytes_per_interval = requests_per_interval * random.randint(15_000, 40_000)
                handshake_latency = random.uniform(55, 120)
                request_latency = random.uniform(120, 400)
                anomaly_prediction = -1
                anomaly_score = random.uniform(-0.50, -0.05)
                status = "ANOMALY"

            requests_total += requests_per_interval
            tls_handshakes_total += handshakes_per_interval
            request_bytes_total += request_bytes_per_interval
            response_bytes_total += response_bytes_per_interval

            row = {
                "timestamp": datetime.now().isoformat(),
                "requests_total": requests_total,
                "tls_handshakes_total": tls_handshakes_total,
                "active_connections": active_connections,
                "request_bytes_total": request_bytes_total,
                "response_bytes_total": response_bytes_total,
                "handshake_duration_ms": round(handshake_latency, 3),
                "request_duration_ms": round(request_latency, 3),
                "requests_per_interval": requests_per_interval,
                "handshakes_per_interval": handshakes_per_interval,
                "request_bytes_per_interval": request_bytes_per_interval,
                "response_bytes_per_interval": response_bytes_per_interval,
                "anomaly_prediction": anomaly_prediction,
                "anomaly_score": round(anomaly_score, 3),
                "status": status,
            }

            with DATA_FILE.open("a", newline="", encoding="utf-8") as file:
                csv.DictWriter(file, fieldnames=FIELDS).writerow(row)

            label = "!!! ANOMALY !!!" if status == "ANOMALY" else "NORMAL"
            print(
                f"[{row['timestamp']}] {label:15} | "
                f"Req: {requests_per_interval:3} | TLS: {handshakes_per_interval:3} | "
                f"Conn: {active_connections:3} | Score: {anomaly_score:.2f}"
            )
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nLive dashboard test stopped.")


if __name__ == "__main__":
    main()
