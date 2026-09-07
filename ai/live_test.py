import csv
import math
import os
import random
import time
from datetime import datetime

DATA_FILE = "data/anomalies.csv"
INTERVAL = 1.0  # generate data every 1 second

# Make sure data directory exists
os.makedirs("data", exist_ok=True)

FIELDS = [
    "timestamp",
    "requests_total",
    "tls_handshakes_total",
    "active_connections",
    "handshake_duration_ms",
    "request_duration_ms",
    "requests_per_interval",
    "handshakes_per_interval",
    "anomaly_score",
    "status",
]

# Start counters
requests_total = 0
tls_handshakes_total = 0

# Create/replace CSV for a clean demonstration
with open(DATA_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()

print("=" * 70)
print(" POST-QUANTUM REVERSE PROXY - LIVE STRESS TEST")
print("=" * 70)
print(f"Writing live metrics to: {DATA_FILE}")
print("Dashboard should refresh every 2 seconds.")
print("Anomaly bursts occur periodically.")
print("Press Ctrl+C to stop.")
print("=" * 70)

start_time = time.time()

try:
    while True:
        elapsed = time.time() - start_time

        # ---------------------------------------------------------
        # NORMAL TRAFFIC BASELINE
        # ---------------------------------------------------------

        # Smooth traffic variation
        traffic_wave = math.sin(elapsed / 8.0)

        requests_per_interval = int(
            max(
                5,
                35
                + traffic_wave * 15
                + random.randint(-8, 8)
            )
        )

        handshakes_per_interval = int(
            max(
                3,
                requests_per_interval * random.uniform(0.55, 0.9)
            )
        )

        active_connections = int(
            max(
                2,
                20
                + traffic_wave * 10
                + random.randint(-5, 8)
            )
        )

        handshake_latency = max(
            3,
            random.gauss(18, 3)
        )

        request_latency = max(
            8,
            random.gauss(35, 7)
        )

        anomaly_score = random.uniform(0.03, 0.25)
        status = "NORMAL"

        # ---------------------------------------------------------
        # PERIODIC STRESS / ANOMALY BURST
        # ---------------------------------------------------------

        # Every ~30 seconds, create an 8-second abnormal burst
        cycle = elapsed % 30

        if 20 <= cycle <= 28:

            # Traffic spike
            requests_per_interval = random.randint(180, 450)

            # Large number of simultaneous connections
            active_connections = random.randint(100, 280)

            # Large number of TLS handshakes
            handshakes_per_interval = random.randint(120, 300)

            # Increased PQC handshake latency
            handshake_latency = random.uniform(55, 120)

            # Increased request latency
            request_latency = random.uniform(120, 400)

            # High anomaly score
            anomaly_score = random.uniform(0.78, 0.99)

            status = "ANOMALY"

        # ---------------------------------------------------------
        # UPDATE TOTAL COUNTERS
        # ---------------------------------------------------------

        requests_total += requests_per_interval
        tls_handshakes_total += handshakes_per_interval

        # ---------------------------------------------------------
        # WRITE NEW ROW
        # ---------------------------------------------------------

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requests_total": requests_total,
            "tls_handshakes_total": tls_handshakes_total,
            "active_connections": active_connections,
            "handshake_duration_ms": round(handshake_latency, 3),
            "request_duration_ms": round(request_latency, 3),
            "requests_per_interval": requests_per_interval,
            "handshakes_per_interval": handshakes_per_interval,
            "anomaly_score": round(anomaly_score, 3),
            "status": status,
        }

        with open(DATA_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)

        # ---------------------------------------------------------
        # TERMINAL OUTPUT
        # ---------------------------------------------------------

        symbol = "!!! ANOMALY !!!" if status == "ANOMALY" else "NORMAL"

        print(
            f"[{row['timestamp']}] "
            f"{symbol:15} | "
            f"Req/s: {requests_per_interval:3} | "
            f"TLS/s: {handshakes_per_interval:3} | "
            f"Conn: {active_connections:3} | "
            f"PQC: {handshake_latency:6.1f} ms | "
            f"Req: {request_latency:6.1f} ms | "
            f"Score: {anomaly_score:.2f}"
        )

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\n")
    print("=" * 70)
    print("Stress test stopped.")
    print(f"Final requests:       {requests_total}")
    print(f"Final TLS handshakes: {tls_handshakes_total}")
    print("=" * 70)