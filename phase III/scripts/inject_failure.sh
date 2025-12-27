#!/bin/bash
# Inject failures into running Sobel service replicas

set -e

LOG_DIR="logs"
FAILURE_TYPE="${1:-crash}"
TARGET_SERVER="${2:-server-0}"

echo "Failure Injection Tool"
echo "====================="
echo "Type: $FAILURE_TYPE"
echo "Target: $TARGET_SERVER"
echo

case "$FAILURE_TYPE" in
    crash)
        echo "Injecting CRASH failure (killing process)..."
        PID_FILE="$LOG_DIR/${TARGET_SERVER}.pid"
        
        if [ ! -f "$PID_FILE" ]; then
            echo "Error: PID file not found: $PID_FILE"
            echo "Make sure the server is running."
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "Error: Server process (PID: $PID) is not running"
            exit 1
        fi
        
        echo "Killing $TARGET_SERVER (PID: $PID)"
        kill -9 "$PID"
        
        echo "✓ Server crashed successfully"
        echo
        echo "To restart the server:"
        echo "  Port 5005X where X is the server number (e.g., 50051 for server-0)"
        ;;
    
    delay)
        echo "Injecting NETWORK DELAY failure..."
        # Extract port from server ID (server-0 -> 50051, server-1 -> 50052)
        SERVER_NUM=${TARGET_SERVER##*-}
        PORT=$((50051 + SERVER_NUM))
        
        echo "Adding 2000ms delay to localhost:$PORT traffic"
        echo "Note: Requires root privileges and 'tc' command"
        echo
        echo "Commands to add delay:"
        echo "  sudo tc qdisc add dev lo root netem delay 2000ms"
        echo
        echo "To remove delay:"
        echo "  sudo tc qdisc del dev lo root"
        echo
        echo "Warning: This affects ALL localhost traffic!"
        echo "For production, use iptables with specific ports."
        ;;
    
    freeze)
        echo "Injecting FREEZE failure (SIGSTOP)..."
        PID_FILE="$LOG_DIR/${TARGET_SERVER}.pid"
        
        if [ ! -f "$PID_FILE" ]; then
            echo "Error: PID file not found: $PID_FILE"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "Error: Server process (PID: $PID) is not running"
            exit 1
        fi
        
        echo "Freezing $TARGET_SERVER (PID: $PID)"
        kill -STOP "$PID"
        
        echo "✓ Server frozen"
        echo
        echo "To resume:"
        echo "  kill -CONT $PID"
        ;;
    
    resume)
        echo "Resuming frozen server..."
        PID_FILE="$LOG_DIR/${TARGET_SERVER}.pid"
        
        if [ ! -f "$PID_FILE" ]; then
            echo "Error: PID file not found: $PID_FILE"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "Error: Server process (PID: $PID) is not running"
            exit 1
        fi
        
        echo "Resuming $TARGET_SERVER (PID: $PID)"
        kill -CONT "$PID"
        
        echo "✓ Server resumed"
        ;;
    
    *)
        echo "Error: Unknown failure type: $FAILURE_TYPE"
        echo
        echo "Usage: $0 <failure_type> [target_server]"
        echo
        echo "Failure types:"
        echo "  crash   - Kill server process (SIGKILL)"
        echo "  freeze  - Freeze server (SIGSTOP)"
        echo "  resume  - Resume frozen server (SIGCONT)"
        echo "  delay   - Add network delay (requires tc/root)"
        echo
        echo "Example:"
        echo "  $0 crash server-0"
        echo "  $0 freeze server-1"
        echo "  $0 resume server-1"
        exit 1
        ;;
esac

echo
echo "Failure injected at: $(date)"
echo "Monitor client logs to observe resilience behavior"
