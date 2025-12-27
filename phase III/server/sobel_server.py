#!/usr/bin/env python3
"""
gRPC server for Sobel edge detection service.
Supports replication, health checks, and metrics collection.
"""

import grpc
from concurrent import futures
import time
import argparse
import signal
import sys
import os
from collections import deque
import threading

# Add proto directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sobel_service_pb2
import sobel_service_pb2_grpc
from server.sobel_worker import process_image_bytes


class SobelServicer(sobel_service_pb2_grpc.SobelServiceServicer):
    """Implementation of Sobel edge detection service."""
    
    def __init__(self, server_id: str):
        self.server_id = server_id
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.processing_times = deque(maxlen=1000)  # Keep last 1000
        self.lock = threading.Lock()
        
        print(f"[{self.server_id}] Server initialized")
    
    def ProcessImage(self, request, context):
        """Process an image with Sobel edge detection."""
        start_time = time.time()
        
        try:
            with self.lock:
                self.total_requests += 1
            
            # Process the image
            result_bytes = process_image_bytes(
                request.image_data,
                request.width,
                request.height
            )
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            with self.lock:
                self.successful_requests += 1
                self.processing_times.append(processing_time_ms)
            
            # Create response
            response = sobel_service_pb2.ImageResponse(
                width=request.width,
                height=request.height,
                result_data=result_bytes,
                request_id=request.request_id,
                server_timestamp_ms=int(time.time() * 1000),
                processing_time_ms=processing_time_ms,
                server_id=self.server_id
            )
            
            print(f"[{self.server_id}] Processed request {request.request_id} "
                  f"({request.width}x{request.height}) in {processing_time_ms:.2f}ms")
            
            return response
            
        except Exception as e:
            with self.lock:
                self.failed_requests += 1
            
            print(f"[{self.server_id}] Error processing request: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Processing error: {str(e)}")
            return sobel_service_pb2.ImageResponse()
    
    def HealthCheck(self, request, context):
        """Health check endpoint."""
        uptime = int(time.time() - self.start_time)
        
        return sobel_service_pb2.HealthResponse(
            healthy=True,
            server_id=self.server_id,
            load=self.total_requests - self.successful_requests - self.failed_requests,
            uptime_seconds=uptime
        )
    
    def GetMetrics(self, request, context):
        """Return server metrics."""
        with self.lock:
            avg_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            sorted_times = sorted(self.processing_times)
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        uptime = int(time.time() - self.start_time)
        
        return sobel_service_pb2.MetricsResponse(
            server_id=self.server_id,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            avg_processing_time_ms=avg_time,
            p95_processing_time_ms=p95_time,
            p99_processing_time_ms=p99_time,
            uptime_seconds=uptime
        )


def serve(port: int, server_id: str):
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = SobelServicer(server_id)
    sobel_service_pb2_grpc.add_SobelServiceServicer_to_server(servicer, server)
    
    server_address = f'[::]:{port}'
    server.add_insecure_port(server_address)
    
    def signal_handler(sig, frame):
        print(f"\n[{server_id}] Shutting down gracefully...")
        server.stop(grace=5)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.start()
    print(f"[{server_id}] Server started on port {port}")
    print(f"[{server_id}] Ready to process requests...")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print(f"\n[{server_id}] Interrupted")
        server.stop(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sobel gRPC Server')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--id', type=str, required=True, help='Server ID (e.g., server-1)')
    
    args = parser.parse_args()
    
    serve(args.port, args.id)
