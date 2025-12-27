#!/bin/bash
# Cache profiling and memory analysis utility
# Requires: perf (Linux Performance Events), builds with gprof support

set -e

PROGRAM_SEQ="./edge_sobel_seq"
PROGRAM_OMP="./edge_sobel_omp"
IMAGE_SIZE=${1:-2048}
THREADS=${2:-4}

# Check if perf is available
if ! command -v perf &> /dev/null; then
    echo "WARNING: 'perf' tool not found. Install with: sudo apt-get install linux-tools-generic"
    echo "Attempting cache analysis anyway (may have limited output)..."
fi

echo "=========================================="
echo "Cache & Memory Profiling Analysis"
echo "=========================================="
echo ""

# Check if binaries are built
if [ ! -f "$PROGRAM_OMP" ]; then
    echo "Building binaries..."
    make omp
fi

echo "Configuration: Image Size = ${IMAGE_SIZE}x${IMAGE_SIZE}, Threads = ${THREADS}"
echo ""

# ============ L1/L2/L3 Cache Analysis ============
echo "1. CACHE HIERARCHY ANALYSIS"
echo "-------------------------------------------"

if command -v perf &> /dev/null; then
    echo "Measuring cache performance with perf..."
    perf stat -e \
        L1-dcache-loads,\
        L1-dcache-load-misses,\
        LLC-loads,\
        LLC-load-misses,\
        cache-references,\
        cache-misses,\
        cycles,\
        instructions \
        -r 3 \
        "$PROGRAM_OMP" omp "$IMAGE_SIZE" "$THREADS" 1 2>&1 | tee cache_profile.txt
    
    echo ""
    echo "✓ Full cache profile saved to cache_profile.txt"
else
    echo "Skipping perf measurements (tool not available)"
fi

# ============ Memory Bandwidth Analysis ============
echo ""
echo "2. MEMORY BANDWIDTH ANALYSIS"
echo "-------------------------------------------"

# Theoretical calculations
TOTAL_PIXELS=$((IMAGE_SIZE * IMAGE_SIZE))
BYTES_PER_PIXEL=40  # 9 reads * 4 bytes + 1 write * 4 bytes
TOTAL_BYTES=$((TOTAL_PIXELS * BYTES_PER_PIXEL))

echo "Image Size: ${IMAGE_SIZE}x${IMAGE_SIZE} (${TOTAL_PIXELS} pixels)"
echo "Memory access per pixel: 40 bytes (36 bytes read + 4 bytes write)"
echo "Total memory movement: $(echo "scale=2; $TOTAL_BYTES / 1024 / 1024" | bc) MB"
echo ""

# Run and measure execution time
EXEC_TIME=$("$PROGRAM_OMP" omp "$IMAGE_SIZE" "$THREADS" 1 | grep -oP 'AVG_TIME=\K[0-9.]+')
BANDWIDTH=$(echo "scale=2; ($TOTAL_BYTES / 1024 / 1024) / ($EXEC_TIME / 1000)" | bc)

echo "Execution Time: ${EXEC_TIME} ms"
echo "Bandwidth Required: ${BANDWIDTH} MB/s"
echo ""

# Typical CPU bandwidth for reference
echo "Reference Bandwidth Values (varies by CPU):"
echo "  - Intel Core i5/i7 (Skylake): 17-25 GB/s"
echo "  - Intel Core i9 (Cascade Lake): 30-50 GB/s"
echo "  - AMD Ryzen 5: 25-30 GB/s"
echo "  - AMD Ryzen 9: 35-50 GB/s"
echo ""

if (( $(echo "$BANDWIDTH < 5000" | bc -l) )); then
    echo "STATUS: Memory bandwidth utilization appears NORMAL (< 5 GB/s)"
    echo "        (Problem is memory-bound but not saturating system memory)"
else
    echo "STATUS: High memory bandwidth utilization detected"
fi

# ============ Arithmetic Intensity ============
echo ""
echo "3. ARITHMETIC INTENSITY ANALYSIS"
echo "-------------------------------------------"

FLOPS_PER_PIXEL=15  # Conservative estimate
TOTAL_FLOPS=$((TOTAL_PIXELS * FLOPS_PER_PIXEL))
ARITHMETIC_INTENSITY=$(echo "scale=4; ($TOTAL_FLOPS / 1e9) / ($TOTAL_BYTES / 1e9)" | bc)

echo "Floating-point operations per pixel: ~${FLOPS_PER_PIXEL}"
echo "Total FLOPs: $(echo "scale=2; $TOTAL_FLOPS / 1e9" | bc) billion"
echo "Arithmetic Intensity: ${ARITHMETIC_INTENSITY} FLOP/byte"
echo ""
echo "Interpretation:"
echo "  - Roofline Model: Kernel is MEMORY-BOUND (AI < 1.0)"
echo "  - Memory bandwidth is the limiting factor, not compute"
echo "  - Scaling to more cores won't help without data locality improvements"

# ============ Memory Layout ============
echo ""
echo "4. MEMORY LAYOUT ANALYSIS"
echo "-------------------------------------------"
echo "Storage: Row-major 1D array (good for row iteration)"
echo "Cache line size: 64 bytes (typically)"
echo "Integers per cache line: 16"
echo ""
echo "Access Pattern Efficiency:"
echo "  ✓ Sequential row access: High spatial locality"
echo "  ✗ Row-to-row jumps: Cold cache misses (stride = N × 4 bytes)"
echo ""
echo "Expected L1 Cache Misses:"
CACHE_LINE_PIXELS=16
MISSES_PER_ROW=$(echo "scale=1; $IMAGE_SIZE / $CACHE_LINE_PIXELS" | bc)
MISSES_PER_IMAGE=$(echo "scale=0; $IMAGE_SIZE * $MISSES_PER_ROW" | bc)

echo "  - Per row: ~${MISSES_PER_ROW} (one per cache line)"
echo "  - Per image: ~${MISSES_PER_IMAGE} cache line fills"
echo "  - Cold misses between rows: High"

# ============ Optimization Suggestions ============
echo ""
echo "5. OPTIMIZATION RECOMMENDATIONS"
echo "-------------------------------------------"
echo ""
echo "Current Status: Memory-bound Sobel detector"
echo ""
echo "To Improve Performance:"
echo ""
echo "A. ALGORITHM LEVEL (Easy)"
echo "   ☐ Use approximate Sobel (reduced precision)"
echo "   ☐ Skip edge pixels (narrower processing)"
echo "   ☐ Cache blocking / tiling (improve temporal locality)"
echo ""
echo "B. IMPLEMENTATION LEVEL (Medium)"
echo "   ☐ SIMD vectorization (SSE, AVX, AVX-512)"
echo "   ☐ Data prefetching hints (#pragma omp simd)"
echo "   ☐ Cache-oblivious algorithms"
echo ""
echo "C. SYSTEM LEVEL (Hard)"
echo "   ☐ GPU acceleration (Phase 2 - CUDA)"
echo "   ☐ Distributed memory (Phase 2 - MPI)"
echo "   ☐ Specialized hardware (FPGA, TPU)"
echo ""
echo "==========================================="
echo "Profiling complete! Check cache_profile.txt for details."
echo ""
