#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/asio/ssl.hpp>

#include <openssl/ssl.h>
#include <openssl/err.h>

#include "metrics.h"

void run_metrics_server();

#include <cstdlib>
#include <chrono>
#include <iostream>
#include <string>
#include <thread>

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace http  = beast::http;
namespace ssl   = asio::ssl;

using tcp = asio::ip::tcp;


// Configuration


constexpr unsigned short PROXY_PORT   = 8443;
constexpr unsigned short BACKEND_PORT = 8080;

const std::string BACKEND_HOST = "127.0.0.1";

const char* CERT_FILE = "../certs/server.crt";
const char* KEY_FILE  = "../certs/server.key";


// Create TLS context


ssl::context create_tls_context()
{
    ssl::context ctx(
        ssl::context::tls_server
    );

    
    // TLS 1.3 only
    

    SSL_CTX_set_min_proto_version(
        ctx.native_handle(),
        TLS1_3_VERSION
    );

    SSL_CTX_set_max_proto_version(
        ctx.native_handle(),
        TLS1_3_VERSION
    );

    
    // Certificate
    

    ctx.use_certificate_chain_file(
        CERT_FILE
    );

    ctx.use_private_key_file(
        KEY_FILE,
        ssl::context::pem
    );

    
    // Configure post-quantum hybrid key exchange
    //
    // X25519 + ML-KEM-768
    //
    // Requires OpenSSL 3.5+
    

    if (SSL_CTX_set1_groups_list(
            ctx.native_handle(),
            "X25519MLKEM768"
        ) != 1)
    {
        std::cerr
            << "[TLS] ERROR: Could not configure "
            << "X25519MLKEM768"
            << std::endl;

        ERR_print_errors_fp(stderr);
    }
    else
    {
        std::cout
            << "[TLS] Successfully configured "
            << "X25519MLKEM768"
            << std::endl;
    }

    return ctx;
}


// Forward decrypted HTTP request to Go backend


void proxy_http_request(
    boost::asio::ssl::stream<beast::tcp_stream>& client_stream
)
{
    // Start measuring complete proxy request time
    auto request_start =
        std::chrono::steady_clock::now();

    try
    {
        beast::flat_buffer buffer;

        http::request<http::string_body> request;

        
        // Read HTTP request AFTER TLS termination
        

        http::read(
            client_stream,
            buffer,
            request
        );

        
        // Record request bytes
        

        g_metrics.request_bytes_total +=
            request.body().size();

        std::cout
            << "[HTTP] "
            << request.method_string()
            << " "
            << request.target()
            << std::endl;

        
        // Connect to Go backend
        

        asio::io_context backend_io;

        tcp::resolver resolver(
            backend_io
        );

        auto endpoints =
            resolver.resolve(
                BACKEND_HOST,
                std::to_string(BACKEND_PORT)
            );

        beast::tcp_stream backend_stream(
            backend_io
        );

        backend_stream.connect(
            endpoints
        );

        
        // Modify request for upstream
        

        request.set(
            http::field::host,
            BACKEND_HOST
        );

        request.set(
            http::field::connection,
            "close"
        );

        
        // Send request to Go backend
        

        http::write(
            backend_stream,
            request
        );

        
        // Read Go backend response
        

        beast::flat_buffer backend_buffer;

        http::response<http::string_body> response;

        http::read(
            backend_stream,
            backend_buffer,
            response
        );

        
        // Record response bytes
        

        g_metrics.response_bytes_total +=
            response.body().size();

        std::cout
            << "[UPSTREAM] HTTP "
            << response.result_int()
            << std::endl;

        
        // Send response back through TLS
        

        http::write(
            client_stream,
            response
        );

        
        // Measure complete request processing time
        

        auto request_end =
            std::chrono::steady_clock::now();

        auto request_time =
            std::chrono::duration_cast<
                std::chrono::microseconds
            >(
                request_end - request_start
            ).count();

        
        // Update request metrics
        

        g_metrics.requests_total++;

        g_metrics.request_time_us_total +=
            request_time;

        
        // Shutdown TLS connection
        

        beast::error_code ec;

        client_stream.shutdown(
            ec
        );
    }
    catch (const std::exception& e)
    {
        std::cerr
            << "[Proxy] Error: "
            << e.what()
            << std::endl;
    }
}


// Handle one TLS client


void handle_client(
    tcp::socket socket,
    ssl::context& tls_context
)
{
    
    // Count active connection
    

    g_metrics.active_connections++;

    try
    {
        boost::asio::ssl::stream<beast::tcp_stream>
            stream(
                std::move(socket),
                tls_context
            );

        
        // TLS handshake timing
        

        std::cout
            << "[TLS] Starting handshake..."
            << std::endl;

        auto handshake_start =
            std::chrono::steady_clock::now();

        stream.handshake(
            ssl::stream_base::server
        );

        auto handshake_end =
            std::chrono::steady_clock::now();

        auto handshake_time =
            std::chrono::duration_cast<
                std::chrono::microseconds
            >(
                handshake_end - handshake_start
            ).count();

        
        // Record TLS handshake metrics
        

        g_metrics.tls_handshakes_total++;

        g_metrics.handshake_time_us_total +=
            handshake_time;

        
        // Print negotiated TLS information
        

        SSL* ssl_handle =
            stream.native_handle();

        const char* version =
            SSL_get_version(
                ssl_handle
            );

        const char* cipher =
            SSL_get_cipher_name(
                ssl_handle
            );

        std::cout
            << "[TLS] Version: "
            << version
            << std::endl;

        std::cout
            << "[TLS] Cipher: "
            << cipher
            << std::endl;

        std::cout
            << "[TLS] Handshake time: "
            << handshake_time
            << " us"
            << std::endl;

        
        // Continue with HTTP proxying
        

        proxy_http_request(
            stream
        );
    }
    catch (const std::exception& e)
    {
        std::cerr
            << "[TLS] Connection error: "
            << e.what()
            << std::endl;
    }

    
    // Connection finished
    

    g_metrics.active_connections--;
}


// Main


int main()
{
    try
    {   
        
        // Start Prometheus metrics server
        

        std::thread metrics_thread(
            run_metrics_server
        );

        metrics_thread.detach();

        
        
        // Create TLS context
        

        ssl::context tls_context =
            create_tls_context();

        
        // TCP listener
        

        asio::io_context io_context;

        tcp::acceptor acceptor(
            io_context,
            tcp::endpoint(
                tcp::v4(),
                PROXY_PORT
            )
        );

        
        // Startup information
        

        std::cout
           
            << std::endl;

        std::cout
            << "PQ Reverse Proxy"
            << std::endl;

        std::cout
            << "Listening on HTTPS port: "
            << PROXY_PORT
            << std::endl;

        std::cout
            << "Upstream Go server: "
            << BACKEND_HOST
            << ":"
            << BACKEND_PORT
            << std::endl;

        std::cout
            << "TLS: 1.3"
            << std::endl;

        std::cout
            << "Key exchange: X25519MLKEM768"
            << std::endl;

        std::cout
            << std::endl;

        
        // Accept clients
        

        while (true)
        {
            tcp::socket socket(
                io_context
            );

            acceptor.accept(
                socket
            );

            std::cout
                << "[TCP] New client connection"
                << std::endl;

            std::thread(
                handle_client,
                std::move(socket),
                std::ref(tls_context)
            ).detach();
        }
    }
    catch (const std::exception& e)
    {
        std::cerr
            << "Fatal error: "
            << e.what()
            << std::endl;

        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
