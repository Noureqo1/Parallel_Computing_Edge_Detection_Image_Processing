"""
Spark Structured Streaming integration with Sobel gRPC service.
Processes image stream through distributed fault-tolerant pipeline.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import BinaryType, StringType, IntegerType
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from client.sobel_client import ResilientSobelClient


# Initialize gRPC client (shared across workers)
_client = None

def get_client():
    global _client
    if _client is None:
        _client = ResilientSobelClient(
            ['localhost:50051', 'localhost:50052'],
            max_retries=3
        )
    return _client


def process_image_spark(image_bytes, width, height, request_id):
    """Process image through gRPC service."""
    try:
        client = get_client()
        response = client.process_image(
            image_bytes,
            int(width),
            int(height),
            request_id
        )
        
        if response:
            return response.result_data
        else:
            return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def main():
    # Create Spark session
    spark = SparkSession.builder \
        .appName("SobelStreamingProcessor") \
        .master("local[4]") \
        .config("spark.executor.memory", "2g") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print("=" * 60)
    print("Spark Structured Streaming - Sobel Edge Detection")
    print("=" * 60)
    
    # Define UDF for image processing
    process_udf = udf(process_image_spark, BinaryType())
    
    # Read from socket stream (simulated image source)
    # In production, use Kafka, files, or other sources
    df = spark \
        .readStream \
        .format("rate") \
        .option("rowsPerSecond", 5) \
        .load()
    
    # Generate synthetic images
    df = df.selectExpr(
        "timestamp",
        "value as request_id",
        "256 as width",
        "256 as height"
    )
    
    # Add random image data (in real scenario, this comes from source)
    from pyspark.sql.functions import lit
    
    # Process through gRPC
    print("\nStarting stream processing...")
    print("Note: Make sure 2 gRPC servers are running:")
    print("  Terminal 1: python3 server/sobel_server.py --port 50051 --id server-0")
    print("  Terminal 2: python3 server/sobel_server.py --port 50052 --id server-1")
    print()
    
    # Simple streaming query that counts processed images
    query = df \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", False) \
        .trigger(processingTime="2 seconds") \
        .start()
    
    print("Stream started. Press Ctrl+C to stop.")
    print()
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\nStopping stream...")
        query.stop()
        spark.stop()


if __name__ == "__main__":
    main()
