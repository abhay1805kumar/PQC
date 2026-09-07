#include "metrics.h"

#include <sstream>

Metrics g_metrics;



// Generate Prometheus exposition format


std::string Metrics::prometheus() const
{
    std::ostringstream out;

    
    // Requests
    

    out << "# TYPE pq_proxy_requests_total counter\n";

    out << "pq_proxy_requests_total "
        << requests_total.load()
        << "\n\n";


    
    // TLS handshakes
    

    out << "# TYPE pq_proxy_tls_handshakes_total counter\n";

    out << "pq_proxy_tls_handshakes_total "
        << tls_handshakes_total.load()
        << "\n\n";


    
    // Active connections
    

    out << "# TYPE pq_proxy_active_connections gauge\n";

    out << "pq_proxy_active_connections "
        << active_connections.load()
        << "\n\n";


    
    // Request bytes
    

    out << "# TYPE pq_proxy_request_bytes_total counter\n";

    out << "pq_proxy_request_bytes_total "
        << request_bytes_total.load()
        << "\n\n";


    
    // Response bytes
    

    out << "# TYPE pq_proxy_response_bytes_total counter\n";

    out << "pq_proxy_response_bytes_total "
        << response_bytes_total.load()
        << "\n\n";


    
    // Average handshake time
    

    uint64_t handshakes =
        tls_handshakes_total.load();

    double avg_handshake_ms = 0.0;

    if (handshakes > 0)
    {
        avg_handshake_ms =
            static_cast<double>(
                handshake_time_us_total.load()
            ) /
            static_cast<double>(handshakes) /
            1000.0;
    }

    out << "# TYPE pq_proxy_handshake_duration_ms gauge\n";

    out << "pq_proxy_handshake_duration_ms "
        << avg_handshake_ms
        << "\n\n";


    
    // Average request time
    

    uint64_t requests =
        requests_total.load();

    double avg_request_ms = 0.0;

    if (requests > 0)
    {
        avg_request_ms =
            static_cast<double>(
                request_time_us_total.load()
            ) /
            static_cast<double>(requests) /
            1000.0;
    }

    out << "# TYPE pq_proxy_request_duration_ms gauge\n";

    out << "pq_proxy_request_duration_ms "
        << avg_request_ms
        << "\n\n";


    return out.str();
}