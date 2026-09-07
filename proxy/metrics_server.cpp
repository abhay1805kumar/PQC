#include <boost/asio.hpp>
#include <boost/beast.hpp>

#include "metrics.h"

#include <iostream>
#include <string>
#include <thread>

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace http  = beast::http;

using tcp = asio::ip::tcp;


// Configuration


constexpr unsigned short METRICS_PORT = 9090;


// Handle one metrics HTTP client


void handle_metrics_client(tcp::socket socket)
{
    try
    {
        beast::tcp_stream stream(
            std::move(socket)
        );

        beast::flat_buffer buffer;

        http::request<http::string_body> request;

        
        // Read HTTP request
        

        http::read(
            stream,
            buffer,
            request
        );

        
        // Only /metrics is supported
        

        if (request.method() != http::verb::get ||
            request.target() != "/metrics")
        {
            http::response<http::string_body> response(
                http::status::not_found,
                request.version()
            );

            response.set(
                http::field::content_type,
                "text/plain"
            );

            response.body() =
                "Not Found\n";

            response.prepare_payload();

            http::write(
                stream,
                response
            );

            return;
        }

        
        // Get Prometheus metrics
        

        std::string metrics =
            g_metrics.prometheus();

        
        // Create HTTP response
        

        http::response<http::string_body> response(
            http::status::ok,
            request.version()
        );

        response.set(
            http::field::content_type,
            "text/plain; version=0.0.4"
        );

        response.set(
            http::field::server,
            "pq-proxy-metrics"
        );

        response.body() = metrics;

        response.prepare_payload();

        
        // Send response
        

        http::write(
            stream,
            response
        );

        
        // Close connection
        

        beast::error_code ec;

        stream.socket().shutdown(
            tcp::socket::shutdown_both,
            ec
        );
    }
    catch (const std::exception& e)
    {
        std::cerr
            << "[Metrics] Client error: "
            << e.what()
            << std::endl;
    }
}


// Metrics server


void run_metrics_server()
{
    try
    {
        asio::io_context io_context;

        tcp::acceptor acceptor(
            io_context,
            tcp::endpoint(
                tcp::v4(),
                METRICS_PORT
            )
        );

        std::cout
            << "[Metrics] Prometheus endpoint listening on :"
            << METRICS_PORT
            << std::endl;

        while (true)
        {
            tcp::socket socket(
                io_context
            );

            acceptor.accept(
                socket
            );

            std::thread(
                handle_metrics_client,
                std::move(socket)
            ).detach();
        }
    }
    catch (const std::exception& e)
    {
        std::cerr
            << "[Metrics] Server error: "
            << e.what()
            << std::endl;
    }
}