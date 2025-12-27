"""
Resilient gRPC client with automatic retry and failover.
"""

import grpc
import time
import random
import sys
import os
from typing import List, Optional

# Add proto directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sobel_service_pb2
import sobel_service_pb2_grpc


class ResilientSobelClient:
    """
    Client with automatic retry, exponential backoff, and failover.
    """
    
    def __init__(self, server_addresses: List[str], max_retries: int = 3,
                 initial_backoff_ms: int = 100, max_backoff_ms: int = 5000,
                 client_id: str = "client-1"):
        """
        Initialize resilient client.
        
        Args:
            server_addresses: List of "host:port" strings
            max_retries: Maximum retry attempts per request
            initial_backoff_ms: Initial backoff delay in ms
            max_backoff_ms: Maximum backoff delay in ms
            client_id: Client identifier
        """
        self.server_addresses = server_addresses
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.client_id = client_id
        
        # Connection pool
        self.channels = {}
        self.stubs = {}
        self._initialize_connections()
        
        # Server health tracking
        self.server_health = {addr: True for addr in server_addresses}
        self.last_health_check = {addr: 0 for addr in server_addresses}
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.retries_count = 0
        self.failover_count = 0
    
    def _initialize_connections(self):
        """Create connections to all servers."""
        for addr in self.server_addresses:
            try:
                channel = grpc.insecure_channel(addr)
                self.channels[addr] = channel
                self.stubs[addr] = sobel_service_pb2_grpc.SobelServiceStub(channel)
                print(f"[{self.client_id}] Connected to {addr}")
            except Exception as e:
                print(f"[{self.client_id}] Warning: Could not connect to {addr}: {e}")
    
    def _select_server(self) -> Optional[str]:
        """
        Select a healthy server (round-robin with health awareness).
        Returns None if no healthy servers available.
        """
        healthy_servers = [addr for addr in self.server_addresses 
                          if self.server_health[addr]]
        
        if not healthy_servers:
            return None
        
        # Simple round-robin among healthy servers
        return random.choice(healthy_servers)
    
    def _mark_server_unhealthy(self, addr: str):
        """Mark a server as unhealthy."""
        self.server_health[addr] = False
        print(f"[{self.client_id}] Marked {addr} as UNHEALTHY")
    
    def _check_server_health(self, addr: str) -> bool:
        """
        Check if a server is healthy (with caching).
        Only checks every 5 seconds to avoid overhead.
        """
        current_time = time.time()
        
        # Rate limit health checks
        if current_time - self.last_health_check[addr] < 5:
            return self.server_health[addr]
        
        self.last_health_check[addr] = current_time
        
        try:
            stub = self.stubs[addr]
            request = sobel_service_pb2.HealthRequest(client_id=self.client_id)
            response = stub.HealthCheck(request, timeout=2)
            
            if response.healthy:
                if not self.server_health[addr]:
                    print(f"[{self.client_id}] {addr} is now HEALTHY")
                self.server_health[addr] = True
                return True
            else:
                self._mark_server_unhealthy(addr)
                return False
                
        except Exception as e:
            self._mark_server_unhealthy(addr)
            return False
    
    def process_image(self, image_data: bytes, width: int, height: int,
                     request_id: str) -> Optional[sobel_service_pb2.ImageResponse]:
        """
        Process an image with automatic retry and failover.
        
        Returns:
            ImageResponse on success, None on failure after all retries
        """
        self.total_requests += 1
        
        request = sobel_service_pb2.ImageRequest(
            width=width,
            height=height,
            image_data=image_data,
            request_id=request_id,
            timestamp_ms=int(time.time() * 1000)
        )
        
        backoff_ms = self.initial_backoff_ms
        last_exception = None
        
        for attempt in range(self.max_retries):
            # Select a server
            server_addr = self._select_server()
            
            if server_addr is None:
                print(f"[{self.client_id}] No healthy servers available!")
                time.sleep(backoff_ms / 1000.0)
                backoff_ms = min(backoff_ms * 2, self.max_backoff_ms)
                
                # Try to recover by checking all servers
                for addr in self.server_addresses:
                    self._check_server_health(addr)
                
                continue
            
            try:
                stub = self.stubs[server_addr]
                response = stub.ProcessImage(request, timeout=10)
                
                self.successful_requests += 1
                if attempt > 0:
                    self.retries_count += attempt
                
                return response
                
            except grpc.RpcError as e:
                last_exception = e
                status_code = e.code()
                
                print(f"[{self.client_id}] Request {request_id} failed on {server_addr}: "
                      f"{status_code} (attempt {attempt + 1}/{self.max_retries})")
                
                # Mark server unhealthy on certain errors
                if status_code in [grpc.StatusCode.UNAVAILABLE, 
                                  grpc.StatusCode.DEADLINE_EXCEEDED,
                                  grpc.StatusCode.INTERNAL]:
                    self._mark_server_unhealthy(server_addr)
                    self.failover_count += 1
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    time.sleep(backoff_ms / 1000.0)
                    backoff_ms = min(backoff_ms * 2, self.max_backoff_ms)
            
            except Exception as e:
                last_exception = e
                print(f"[{self.client_id}] Unexpected error on {server_addr}: {e}")
                self._mark_server_unhealthy(server_addr)
                
                if attempt < self.max_retries - 1:
                    time.sleep(backoff_ms / 1000.0)
                    backoff_ms = min(backoff_ms * 2, self.max_backoff_ms)
        
        # All retries exhausted
        self.failed_requests += 1
        print(f"[{self.client_id}] Request {request_id} FAILED after {self.max_retries} attempts")
        return None
    
    def get_statistics(self) -> dict:
        """Return client statistics."""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'retries_count': self.retries_count,
            'failover_count': self.failover_count,
            'success_rate': self.successful_requests / self.total_requests if self.total_requests > 0 else 0
        }
    
    def close(self):
        """Close all connections."""
        for addr, channel in self.channels.items():
            try:
                channel.close()
                print(f"[{self.client_id}] Closed connection to {addr}")
            except:
                pass


if __name__ == '__main__':
    # Test client
    import numpy as np
    
    servers = ['localhost:50051', 'localhost:50052']
    client = ResilientSobelClient(servers)
    
    # Create test image
    test_img = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
    image_bytes = test_img.tobytes()
    
    print("Sending test request...")
    response = client.process_image(image_bytes, 128, 128, "test-001")
    
    if response:
        print(f"Success! Processed by {response.server_id} in {response.processing_time_ms:.2f}ms")
    else:
        print("Failed to process image")
    
    print("\nClient statistics:")
    stats = client.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    client.close()
