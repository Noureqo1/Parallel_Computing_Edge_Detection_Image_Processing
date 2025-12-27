#!/bin/bash
# Weak Scaling Benchmark for Phase 2
# Measures how execution time scales when problem size and process count increase together

set -e

# Configuration - problem size per process
# Weak scaling: keep data per rank constant, increase problem size with rank count
PROCESSES=(1 2 4 8)
PROBLEM_PER_RANK=512  # Each rank gets this size per dimension initially
NUM_RUNS=5
OUTPUT_CSV="weak_scaling_results.csv"

echo "==================================================================="
echo "Phase 2 - Weak Scaling Benchmark (MPI Sobel)"
echo "==================================================================="
echo ""

# Verify binary exists
if [ ! -f "./src/sobel_mpi" ]; then
    echo "Error: MPI Sobel binary not found. Run 'make sobel' first."
    exit 1
fi

# Create CSV header
echo "PROCESSES,IMAGE_SIZE,AVG_TIME_MS,MIN_TIME_MS,MAX_TIME_MS,EFFICIENCY" > "$OUTPUT_CSV"

# Benchmark loop
echo "Running weak scaling benchmarks..."
echo "(This tests how time scales when problem size grows with process count)"
echo ""

for procs in "${PROCESSES[@]}"; do
    # Calculate image size: sqrt(procs) * PROBLEM_PER_RANK per dimension
    grid_dim=$(echo "sqrt($procs)" | bc)
    image_size=$((grid_dim * PROBLEM_PER_RANK))
    
    echo "--- $procs processes (Image: ${image_size}x${image_size}) ---"
    
    result=$(mpirun -np "$procs" ./src/sobel_mpi "$image_size" "$NUM_RUNS" 2>&1 | grep "RANKS=")
    
    avg_time=$(echo "$result" | grep -oP 'AVG_TIME=\K[0-9.]+' || echo "0")
    min_time=$(echo "$result" | grep -oP 'MIN=\K[0-9.]+' || echo "0")
    max_time=$(echo "$result" | grep -oP 'MAX=\K[0-9.]+' || echo "0")
    
    # For weak scaling, efficiency is measured relative to 1 process
    # A good weak scaling maintains constant time as problem size increases
    if [ "$procs" -eq 1 ]; then
        baseline_time=$avg_time
        efficiency="1.000"
    else
        efficiency=$(echo "scale=3; $baseline_time / $avg_time" | bc)
    fi
    
    echo "  Time: ${avg_time} ms, Efficiency: ${efficiency}"
    
    echo "$procs,$image_size,$avg_time,$min_time,$max_time,$efficiency" >> "$OUTPUT_CSV"
done

echo ""
echo "==================================================================="
echo "Weak scaling benchmark complete!"
echo "Results saved to: $OUTPUT_CSV"
echo ""
echo "Perfect weak scaling would show constant time as problem size increases."
echo "In practice, communication overhead causes time to increase slightly."
echo ""
