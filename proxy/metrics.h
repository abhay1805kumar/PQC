#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include<string>

class Metrics
{
public:

    
    // Counters
    

    std::atomic<uint64_t> requests_total{0};

    std::atomic<uint64_t> request_bytes_total{0};

    std::atomic<uint64_t> response_bytes_total{0};

    std::atomic<uint64_t> active_connections{0};

    
    // Number of successful TLS handshakes
    

    std::atomic<uint64_t> tls_handshakes_total{0};

    
    // Accumulated timings in microseconds
    

    std::atomic<uint64_t> handshake_time_us_total{0};

    std::atomic<uint64_t> request_time_us_total{0};

    
    // Generate Prometheus text format
    

    std::string prometheus() const;
};


// Global metrics object
extern Metrics g_metrics;