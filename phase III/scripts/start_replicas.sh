#!/bin/bash
# Start multiple gRPC server replicas

set -e

# Activate virtual environment if it exists
if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Configuration
NUM_REPLICAS="${1:-2}"
BASE_PORT="${2:-50051}"
LOG_DIR="logs"

# Create log directory
mkdir -p "$LOG_DIR"

echo "Starting $NUM_REPLICAS Sobel service replicas..."
echo "Base port: $BASE_PORT"
echo "Log directory: $LOG_DIR"
echo

# Array to store PIDs
declare -a PIDS

# Function to cleanup on exit
cleanup() {
    echo
    echo "Stopping all servers..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping server (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    wait
    echo "All servers stopped"
}

trap cleanup EXIT INT TERM

# Start replicas
for i in $(seq 0 $((NUM_REPLICAS-1))); do
    PORT=$((BASE_PORT + i))
    SERVER_ID="server-$i"
    LOG_FILE="$LOG_DIR/${SERVER_ID}.log"
    
    echo "Starting $SERVER_ID on port $PORT..."
    python3 server/sobel_server.py --port $PORT --id $SERVER_ID > "$LOG_FILE" 2>&1 &
    PID=$!
    PIDS+=($PID)
    
    echo "  PID: $PID"
    echo "  Log: $LOG_FILE"
    
    # Save PID to file for failure injection
    echo "$PID" > "$LOG_DIR/${SERVER_ID}.pid"
    
    # Small delay to avoid port conflicts
    sleep 0.5
done

echo
echo "All servers started successfully!"
echo
echo "Server endpoints:"
for i in $(seq 0 $((NUM_REPLICAS-1))); do
    PORT=$((BASE_PORT + i))
    echo "  server-$i: localhost:$PORT"
done
echo
echo "Press Ctrl+C to stop all servers"
echo

# Wait for all servers
wait
