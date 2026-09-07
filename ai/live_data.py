"""Shared location for the real-time detector's dashboard data."""

from pathlib import Path

ANOMALIES_FILE = Path(__file__).resolve().parent / "data" / "realtime_anomalies.csv"
