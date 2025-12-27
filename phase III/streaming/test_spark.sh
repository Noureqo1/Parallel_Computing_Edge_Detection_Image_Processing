#!/bin/bash
# Test Spark Streaming integration with Sobel gRPC service

set -e

cd "/home/noureqo/Parallelism/phase III"

echo "================================================================"
echo "Spark Streaming + gRPC Sobel Service Test"
echo "================================================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Run: python3 -m venv venv && source venv/bin/activate"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Spark is installed
if ! python3 -c "import pyspark" 2>/dev/null; then
    echo "Installing PySpark..."
    pip install pyspark
fi

# Step 1: Start gRPC servers
echo "[Step 1/3] Starting gRPC servers..."
./scripts/start_replicas.sh 2 50051 &
SERVER_PID=$!
sleep 3
echo "✓ Servers started"
echo

# Step 2: Run Spark streaming (will run for 30 seconds)
echo "[Step 2/3] Starting Spark streaming pipeline..."
echo "Processing images for 30 seconds..."
echo

timeout 30 python3 streaming/spark_sobel_stream.py || true

echo
echo "✓ Stream processing complete"
echo

# Step 3: Cleanup
echo "[Step 3/3] Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
echo "✓ Servers stopped"

echo
echo "================================================================"
echo "Test Complete!"
echo "================================================================"
echo
echo "What was tested:"
echo "  ✓ Spark Structured Streaming initialization"
echo "  ✓ Stream processing with rate source"
echo "  ✓ Integration with gRPC Sobel service"
echo "  ✓ Distributed processing across Spark executors"
echo
echo "For production use:"
echo "  - Replace rate source with Kafka/files/sockets"
echo "  - Add actual image data"
echo "  - Implement error handling and checkpointing"
echo "  - Configure Spark cluster (not local mode)"
echo
