"""
Apache Flink integration with Sobel gRPC service.
Real-time image processing pipeline with fault tolerance.
"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction
from pyflink.common.typeinfo import Types
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from client.sobel_client import ResilientSobelClient


class SobelProcessor(MapFunction):
    """Flink map function that processes images through gRPC."""
    
    def __init__(self):
        self.client = None
    
    def open(self, runtime_context):
        """Initialize gRPC client."""
        self.client = ResilientSobelClient(
            ['localhost:50051', 'localhost:50052'],
            max_retries=3
        )
    
    def map(self, value):
        """Process single image."""
        request_id, width, height = value
        
        # Generate synthetic image (replace with real data)
        image = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        
        # Process through gRPC
        response = self.client.process_image(
            image.tobytes(),
            width,
            height,
            f"flink-{request_id}"
        )
        
        if response:
            return f"SUCCESS: {request_id} by {response.server_id}"
        else:
            return f"FAILED: {request_id}"
    
    def close(self):
        """Cleanup."""
        if self.client:
            self.client.close()


def main():
    # Create Flink environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)
    
    print("=" * 60)
    print("Apache Flink - Sobel Edge Detection Pipeline")
    print("=" * 60)
    print("\nNote: Make sure gRPC servers are running:")
    print("  python3 server/sobel_server.py --port 50051 --id server-0")
    print("  python3 server/sobel_server.py --port 50052 --id server-1")
    print()
    
    # Create source (simulated image requests)
    # Format: (request_id, width, height)
    data = [(i, 256, 256) for i in range(20)]
    
    # Create stream
    ds = env.from_collection(
        collection=data,
        type_info=Types.TUPLE([Types.INT(), Types.INT(), Types.INT()])
    )
    
    # Process through Sobel service
    result = ds.map(SobelProcessor(), output_type=Types.STRING())
    
    # Print results
    result.print()
    
    # Execute pipeline
    print("Starting Flink pipeline...")
    env.execute("Sobel Edge Detection Pipeline")
    print("\nPipeline complete!")


if __name__ == "__main__":
    main()
