#!/bin/bash
# Comprehensive benchmarking script for Phase 1 evaluation
# Measures speedup and efficiency for varying image sizes and thread counts

set -e

# Configuration
SIZES=(512 1024 2048)
THREADS=(1 2 4 8)
NUM_RUNS=5
OUTPUT_CSV="benchmark_results.csv"

echo "==================================================================="
echo "Phase 1 - Parallel Sobel Edge Detection Benchmark"
echo "==================================================================="
echo ""

# Verify binaries exist
if [ ! -f "./edge_sobel_seq" ] || [ ! -f "./edge_sobel_omp" ]; then
    echo "Error: Binaries not found. Run 'make all' first."
    exit 1
fi

# Create CSV header
echo "IMAGE_SIZE,MODE,THREADS,AVG_TIME_MS,MIN_TIME_MS,MAX_TIME_MS,GFLOPS" > "$OUTPUT_CSV"

# Benchmark loop
echo "Running benchmarks (this may take several minutes)..."
echo ""

for size in "${SIZES[@]}"; do
    echo "--- Image Size: $size x $size ---"
    
    # Sequential baseline
    echo -n "  Sequential: "
    result=$(./edge_sobel_seq seq "$size" 1 "$NUM_RUNS")
    echo "$result" | grep -o "AVG_TIME=[0-9.]*" | cut -d= -f2
    
    # Extract metrics for CSV
    avg_time=$(echo "$result" | grep -oP '(?<=AVG_TIME=)\d+\.\d+' || echo "0")
    min_time=$(echo "$result" | grep -oP '(?<=MIN=)\d+\.\d+' || echo "0")
    max_time=$(echo "$result" | grep -oP '(?<=MAX=)\d+\.\d+' || echo "0")
    gflops=$(echo "$result" | grep -oP '(?<=GFLOPS=)\d+\.\d+' || echo "0")
    
    echo "$size,SEQ,1,$avg_time,$min_time,$max_time,$gflops" >> "$OUTPUT_CSV"
    
    # OpenMP parallel tests
    for thread_count in "${THREADS[@]}"; do
        echo -n "  OpenMP ($thread_count threads): "
        result=$(./edge_sobel_omp omp "$size" "$thread_count" "$NUM_RUNS")
        echo "$result" | grep -o "AVG_TIME=[0-9.]*" | cut -d= -f2
        
        # Extract metrics for CSV
        avg_time=$(echo "$result" | grep -oP '(?<=AVG_TIME=)\d+\.\d+' || echo "0")
        min_time=$(echo "$result" | grep -oP '(?<=MIN=)\d+\.\d+' || echo "0")
        max_time=$(echo "$result" | grep -oP '(?<=MAX=)\d+\.\d+' || echo "0")
        gflops=$(echo "$result" | grep -oP '(?<=GFLOPS=)\d+\.\d+' || echo "0")
        
        echo "$size,OMP,$thread_count,$avg_time,$min_time,$max_time,$gflops" >> "$OUTPUT_CSV"
    done
    echo ""
done

echo "==================================================================="
echo "Benchmark complete!"
echo "Results saved to: $OUTPUT_CSV"
echo ""
echo "To analyze results:"
echo "  python3 analyze_performance.py"
echo ""
