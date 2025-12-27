#!/bin/bash
# Complete demonstration of Phase 3: Resilient Sobel Service

set -e

# Activate virtual environment if it exists
if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NUM_REPLICAS=2
BASE_PORT=50051
LOAD_DURATION=90  # Run for 90 seconds to demonstrate recovery
REQUEST_RATE=5.0
LOG_DIR="logs"
OUTPUT_DIR="results"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Phase 3: Resilient Distributed Sobel Edge Detection Demo  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Create directories
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# Step 1: Start server replicas
echo -e "${GREEN}[1/5] Starting Server Replicas${NC}"
echo "----------------------------------------"
./scripts/start_replicas.sh $NUM_REPLICAS $BASE_PORT &
SERVER_SCRIPT_PID=$!

# Wait for servers to start
echo "Waiting for servers to initialize..."
sleep 3

# Build server list
SERVERS=""
for i in $(seq 0 $((NUM_REPLICAS-1))); do
    PORT=$((BASE_PORT + i))
    if [ -n "$SERVERS" ]; then
        SERVERS="${SERVERS},localhost:${PORT}"
    else
        SERVERS="localhost:${PORT}"
    fi
done

echo -e "${GREEN}✓ Servers ready: $SERVERS${NC}"
echo

# Step 2: Start load generator in background
echo -e "${GREEN}[2/5] Starting Load Generation${NC}"
echo "----------------------------------------"
echo "Duration: $LOAD_DURATION seconds"
echo "Request rate: $REQUEST_RATE req/sec"
echo

python3 client/load_generator.py \
    --servers "$SERVERS" \
    --duration $LOAD_DURATION \
    --rate $REQUEST_RATE \
    --log "$OUTPUT_DIR/load_test.json" &
LOAD_GEN_PID=$!

# Wait for load generation to ramp up
sleep 5

# Step 3: Inject first failure (crash server-0)
echo
echo -e "${RED}[3/5] Injecting Failure #1: CRASH${NC}"
echo "----------------------------------------"
echo "Target: server-0"
echo "Time: $(date +%T)"
echo

./scripts/inject_failure.sh crash server-0

echo -e "${YELLOW}Server-0 crashed! Client should failover to server-1...${NC}"
sleep 20

# Step 4: Inject second failure (freeze server-1)
echo
echo -e "${RED}[4/5] Injecting Failure #2: FREEZE${NC}"
echo "----------------------------------------"
echo "Target: server-1"
echo "Time: $(date +%T)"
echo

./scripts/inject_failure.sh freeze server-1

echo -e "${YELLOW}Server-1 frozen! Client should experience timeouts...${NC}"
sleep 15

# Resume server-1
echo "Resuming server-1..."
./scripts/inject_failure.sh resume server-1
echo -e "${GREEN}✓ Server-1 resumed${NC}"

# Wait for load test to complete
echo
echo -e "${BLUE}Waiting for load generation to complete...${NC}"
wait $LOAD_GEN_PID

# Step 5: Analyze results
echo
echo -e "${GREEN}[5/5] Analyzing Results${NC}"
echo "----------------------------------------"

if [ -f "$OUTPUT_DIR/load_test.json" ]; then
    python3 monitoring/analyze_metrics.py \
        --log "$OUTPUT_DIR/load_test.json" \
        --output "$OUTPUT_DIR/analysis" \
        --window 1.0
    
    echo
    echo -e "${GREEN}✓ Analysis complete!${NC}"
    echo
    echo "Generated files:"
    ls -lh "$OUTPUT_DIR"/ | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'
else
    echo -e "${RED}Error: Load test log not found${NC}"
fi

# Cleanup
echo
echo -e "${BLUE}Cleaning up...${NC}"
kill -TERM $SERVER_SCRIPT_PID 2>/dev/null || true
wait $SERVER_SCRIPT_PID 2>/dev/null || true

echo
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Demo Complete!                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Review the results:"
echo "  1. Analysis report: $OUTPUT_DIR/analysis_report.txt"
echo "  2. Time-series plots: $OUTPUT_DIR/analysis_*.png"
echo "  3. Raw data: $OUTPUT_DIR/load_test.json"
echo "  4. Server logs: $LOG_DIR/*.log"
echo
echo "Key observations to look for:"
echo "  • Client automatically retries failed requests"
echo "  • Failover to healthy replicas when one crashes"
echo "  • Recovery time after failures"
echo "  • p95 latency degradation during failures"
echo "  • Throughput maintained despite server crashes"
echo
