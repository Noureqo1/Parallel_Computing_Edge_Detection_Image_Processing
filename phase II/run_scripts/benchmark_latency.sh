#!/bin/bash
# Latency and Bandwidth Benchmark for Phase 2
# Measures point-to-point communication characteristics

set -e

echo "==================================================================="
echo "Phase 2 - Latency and Bandwidth Benchmark"
echo "==================================================================="
echo ""

# Verify binary exists
if [ ! -f "./src/benchmark_latency" ]; then
    echo "Error: Latency benchmark binary not found. Run 'make latency' first."
    exit 1
fi

# Run the benchmark with 2 processes
echo "Running latency/bandwidth benchmark (2 processes)..."
echo ""

mpirun -np 2 ./src/benchmark_latency | tee latency_bandwidth_results.txt

echo ""
echo "Results saved to: latency_bandwidth_results.txt"
echo ""
echo "Key Metrics:"
echo "  - Latency: One-way message latency (lower is better)"
echo "  - Bandwidth: Message throughput (higher is better)"
echo ""
echo "Observations:"
echo "  - Small messages are latency-limited"
echo "  - Large messages are bandwidth-limited"
echo "  - Communication overhead is visible in the results"
echo ""
