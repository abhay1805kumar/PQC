"""Shared location for the real-time detector's dashboard data."""

from pathlib import Path


# Dedicated to the current real-time pipeline.  This avoids mixing legacy CSV
# rows (which used a different schema) with live detector/test output.
ANOMALIES_FILE = Path(__file__).resolve().parent / "data" / "realtime_anomalies.csv"
