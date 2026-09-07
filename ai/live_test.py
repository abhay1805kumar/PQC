import csv
import os
import random
import time
from datetime import datetime

DATA_FILE = "data/anomalies.csv"

os.makedirs("data", exist_ok=True)

columns = [
    "timestamp",
    "requests_total",
    "tls_handshakes_total",
    "active_connections",
    "handshake_duration_ms",
    "request_duration_ms",
    "requests_per_interval",
    "handshakes_per_interval",
    "anomaly_score",
    "status"
]

# Create CSV if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()


# Read existing totals
requests_total = 0
tls_handshakes_total = 0

try:
    with open(DATA_FILE, "r", newline="") as f:
        rows = list(csv.DictReader(f))

        if rows:
            requests_total = int(float(rows[-1]["requests_total"]))
            tls_handshakes_total = int(
                float(rows[-1]["tls_handshakes_total"])
            )

except Exception:
    pass


print("Live test data generator started...")
print("Writing new data every 1 second.")
print("Press CTRL+C to stop.\n")


while True:

    # Normal traffic
    requests = random.randint(20, 100)
    handshakes = random.randint(5, 30)

    requests_total += requests
    tls_handshakes_total += handshakes

    active_connections = random.randint(5, 50)

    handshake_latency = random.uniform(1, 8)
    request_latency = random.uniform(5, 30)

    # Generate anomaly approximately 10% of the time
    if random.random() < 0.10:

        handshake_latency *= random.uniform(3, 8)
        request_latency *= random.uniform(3, 6)
        active_connections *= random.randint(3, 6)

        anomaly_score = random.uniform(0.80, 1.00)
        status = "ANOMALY"

    else:

        anomaly_score = random.uniform(0.00, 0.30)
        status = "NORMAL"

    row = {
        "timestamp": datetime.now().isoformat(),
        "requests_total": requests_total,
        "tls_handshakes_total": tls_handshakes_total,
        "active_connections": active_connections,
        "handshake_duration_ms": handshake_latency,
        "request_duration_ms": request_latency,
        "requests_per_interval": requests,
        "handshakes_per_interval": handshakes,
        "anomaly_score": anomaly_score,
        "status": status
    }

    with open(DATA_FILE, "a", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writerow(row)

    print(
        f"{row['timestamp']} | "
        f"{status:7} | "
        f"requests={requests:3} | "
        f"handshakes={handshakes:2} | "
        f"score={anomaly_score:.2f}"
    )

    time.sleep(1)