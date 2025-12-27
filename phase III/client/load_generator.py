"""
Load generator for continuous Sobel service requests.
Generates synthetic images and sends continuous requests for testing.
"""

import argparse
import time
import numpy as np
import sys
import os
import json
from datetime import datetime

# Add proto directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from client.sobel_client import ResilientSobelClient


class LoadGenerator:
    """Generate continuous load on Sobel service."""
    
    def __init__(self, client: ResilientSobelClient, 
                 image_sizes: list = [(256, 256), (512, 512)],
                 requests_per_second: float = 10.0):
        """
        Initialize load generator.
        
        Args:
            client: ResilientSobelClient instance
            image_sizes: List of (width, height) tuples for test images
            requests_per_second: Target request rate
        """
        self.client = client
        self.image_sizes = image_sizes
        self.requests_per_second = requests_per_second
        self.request_interval = 1.0 / requests_per_second
        
        # Metrics
        self.request_log = []
        self.request_count = 0
    
    def generate_test_image(self, width: int, height: int) -> bytes:
        """
        Generate a synthetic test image.
        
        Uses random patterns to ensure some computation load.
        """
        # Generate image with random patterns
        image = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        
        # Add some structure (gradients, edges)
        x = np.linspace(0, 255, width, dtype=np.uint8)
        y = np.linspace(0, 255, height, dtype=np.uint8)
        xx, yy = np.meshgrid(x, y)
        
        # Blend with gradient
        image = (image * 0.5 + (xx + yy) * 0.25).astype(np.uint8)
        
        return image.tobytes()
    
    def run(self, duration_seconds: int = 60, log_file: str = None):
        """
        Run load generation for specified duration.
        
        Args:
            duration_seconds: How long to run (seconds)
            log_file: Path to save request log (JSON)
        """
        print(f"Starting load generation...")
        print(f"  Duration: {duration_seconds} seconds")
        print(f"  Target rate: {self.requests_per_second} req/sec")
        print(f"  Image sizes: {self.image_sizes}")
        print(f"  Servers: {self.client.server_addresses}")
        print()
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        request_id = 0
        
        try:
            while time.time() < end_time:
                loop_start = time.time()
                
                # Select random image size
                width, height = self.image_sizes[request_id % len(self.image_sizes)]
                
                # Generate image
                image_data = self.generate_test_image(width, height)
                
                # Send request
                req_id = f"req-{request_id:06d}"
                request_timestamp = time.time()
                
                response = self.client.process_image(image_data, width, height, req_id)
                
                response_timestamp = time.time()
                latency_ms = (response_timestamp - request_timestamp) * 1000
                
                # Log result
                log_entry = {
                    'request_id': req_id,
                    'timestamp': request_timestamp,
                    'latency_ms': latency_ms,
                    'success': response is not None,
                    'server_id': response.server_id if response else None,
                    'image_size': f"{width}x{height}",
                    'processing_time_ms': response.processing_time_ms if response else None
                }
                self.request_log.append(log_entry)
                
                request_id += 1
                self.request_count += 1
                
                # Rate limiting
                elapsed = time.time() - loop_start
                sleep_time = max(0, self.request_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Progress update every 10 seconds
                if request_id % (int(self.requests_per_second * 10)) == 0:
                    elapsed_total = time.time() - start_time
                    actual_rate = request_id / elapsed_total
                    success_rate = self.client.successful_requests / request_id if request_id > 0 else 0
                    print(f"[{elapsed_total:.1f}s] Sent {request_id} requests "
                          f"(rate: {actual_rate:.1f} req/s, success: {success_rate*100:.1f}%)")
        
        except KeyboardInterrupt:
            print("\nLoad generation interrupted by user")
        
        # Final statistics
        total_time = time.time() - start_time
        actual_rate = self.request_count / total_time
        
        print(f"\n{'='*60}")
        print("Load Generation Complete")
        print(f"{'='*60}")
        print(f"Duration: {total_time:.2f} seconds")
        print(f"Total requests: {self.request_count}")
        print(f"Actual rate: {actual_rate:.2f} req/sec")
        print()
        
        client_stats = self.client.get_statistics()
        print("Client Statistics:")
        print(f"  Successful: {client_stats['successful_requests']}")
        print(f"  Failed: {client_stats['failed_requests']}")
        print(f"  Success rate: {client_stats['success_rate']*100:.2f}%")
        print(f"  Retries: {client_stats['retries_count']}")
        print(f"  Failovers: {client_stats['failover_count']}")
        
        # Calculate latency percentiles
        successful_latencies = [entry['latency_ms'] for entry in self.request_log 
                                if entry['success']]
        
        if successful_latencies:
            successful_latencies.sort()
            p50 = successful_latencies[int(len(successful_latencies) * 0.50)]
            p95 = successful_latencies[int(len(successful_latencies) * 0.95)]
            p99 = successful_latencies[int(len(successful_latencies) * 0.99)]
            
            print()
            print("Latency Statistics:")
            print(f"  Min: {min(successful_latencies):.2f} ms")
            print(f"  p50: {p50:.2f} ms")
            print(f"  p95: {p95:.2f} ms")
            print(f"  p99: {p99:.2f} ms")
            print(f"  Max: {max(successful_latencies):.2f} ms")
        
        # Save log to file
        if log_file:
            with open(log_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'start_time': start_time,
                        'duration_seconds': total_time,
                        'target_rate': self.requests_per_second,
                        'actual_rate': actual_rate,
                        'total_requests': self.request_count,
                        'servers': self.client.server_addresses
                    },
                    'client_stats': client_stats,
                    'requests': self.request_log
                }, f, indent=2)
            
            print(f"\nLog saved to: {log_file}")


def main():
    parser = argparse.ArgumentParser(description='Sobel Service Load Generator')
    parser.add_argument('--servers', type=str, required=True,
                       help='Comma-separated list of server addresses (e.g., localhost:50051,localhost:50052)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds (default: 60)')
    parser.add_argument('--rate', type=float, default=10.0,
                       help='Target requests per second (default: 10.0)')
    parser.add_argument('--sizes', type=str, default='256x256,512x512',
                       help='Comma-separated image sizes (e.g., 256x256,512x512)')
    parser.add_argument('--log', type=str, default='load_test.json',
                       help='Output log file (default: load_test.json)')
    
    args = parser.parse_args()
    
    # Parse servers
    server_addresses = [s.strip() for s in args.servers.split(',')]
    
    # Parse image sizes
    image_sizes = []
    for size_str in args.sizes.split(','):
        width, height = map(int, size_str.split('x'))
        image_sizes.append((width, height))
    
    # Create client
    client = ResilientSobelClient(
        server_addresses,
        max_retries=3,
        initial_backoff_ms=100,
        max_backoff_ms=5000
    )
    
    # Create load generator
    generator = LoadGenerator(
        client,
        image_sizes=image_sizes,
        requests_per_second=args.rate
    )
    
    # Run load test
    generator.run(duration_seconds=args.duration, log_file=args.log)
    
    # Cleanup
    client.close()


if __name__ == '__main__':
    main()
