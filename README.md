\# PQC - Post-Quantum Reverse Proxy Analytics



A Post-Quantum Cryptography reverse proxy analytics project using TLS 1.3,

X25519MLKEM768, Prometheus monitoring, AI-based anomaly detection,

and a Streamlit dashboard.



\## Project Structure



\- `proxy/` - Reverse proxy

\- `backend/` - Backend components

\- `prometheus/` - Prometheus configuration

\- `ai/` - AI analytics, anomaly detection, data collection, and dashboard



\## AI Dashboard



The dashboard monitors:



\- Request traffic

\- TLS handshakes

\- Active connections

\- Handshake latency

\- Request latency

\- Anomaly scores

\- Detected anomalies



\## Running the Dashboard



```powershell

cd ai

python -m streamlit run dashboard.py

