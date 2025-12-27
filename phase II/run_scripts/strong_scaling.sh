#!/bin/bash
# Strong Scaling Benchmark for Phase 2
# Measures how execution time decreases with more processes for fixed problem size

set -e

# Configuration
IMAGE_SIZES=(1024 2048)
PROCESS_COUNTS=(1 2 4 8)
NUM_RUNS=5
OUTPUT_CSV="strong_scaling_results.csv"

echo "==================================================================="
echo "Phase 2 - Strong Scaling Benchmark (MPI Sobel)"
echo "==================================================================="
echo ""

# Verify binary exists
if [ ! -f "./src/sobel_mpi" ]; then
    echo "Error: MPI Sobel binary not found. Run 'make sobel' first."
    exit 1
fi

# Create CSV header
echo "IMAGE_SIZE,PROCESSES,AVG_TIME_MS,MIN_TIME_MS,MAX_TIME_MS,SPEEDUP,EFFICIENCY" > "$OUTPUT_CSV"

# Benchmark loop
echo "Running strong scaling benchmarks..."
echo "(This tests speedup with fixed problem size and increasing processes)"
echo ""

for size in "${IMAGE_SIZES[@]}"; do
    echo "--- Image Size: $size x $size ---"
    
    # Get sequential baseline (1 process)
    echo -n "  1 process: "
    result=$(mpirun -np 1 ./src/sobel_mpi "$size" "$NUM_RUNS" 2>&1 | grep "RANKS=")
    baseline_time=$(echo "$result" | grep -oP 'AVG_TIME=\K[0-9.]+' || echo "0")
    echo "${baseline_time} ms"
    
    echo "$size,1,$baseline_time,$baseline_time,$baseline_time,1.000,1.000" >> "$OUTPUT_CSV"
    
    # Run with multiple processes
    for procs in "${PROCESS_COUNTS[@]}"; do
        if [ $procs -eq 1 ]; then
            continue  # Already measured
        fi
        
        echo -n "  $procs processes: "
        result=$(mpirun -np "$procs" ./src/sobel_mpi "$size" "$NUM_RUNS" 2>&1 | grep "RANKS=")
        
        avg_time=$(echo "$result" | grep -oP 'AVG_TIME=\K[0-9.]+' || echo "0")
        min_time=$(echo "$result" | grep -oP 'MIN=\K[0-9.]+' || echo "0")
        max_time=$(echo "$result" | grep -oP 'MAX=\K[0-9.]+' || echo "0")
        
        # Calculate speedup and efficiency
        speedup=$(echo "scale=3; $baseline_time / $avg_time" | bc)
        efficiency=$(echo "scale=3; $speedup / $procs" | bc)
        
        echo "${avg_time} ms (${speedup}x speedup, ${efficiency} efficiency)"
        
        echo "$size,$procs,$avg_time,$min_time,$max_time,$speedup,$efficiency" >> "$OUTPUT_CSV"
    done
    echo ""
done

echo "==================================================================="
echo "Strong scaling benchmark complete!"
echo "Results saved to: $OUTPUT_CSV"
echo ""
echo "Analyze results:"
echo "  python3 ../Phase1/analyze_performance.py"
echo ""
