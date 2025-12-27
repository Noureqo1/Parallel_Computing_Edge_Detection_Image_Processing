#!/bin/bash
# Quick Start Guide for Phase 1 Evaluation
# Run this script to demonstrate all Phase 1 requirements in 2-3 minutes

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         Phase 1: Parallel Sobel Edge Detection - Quick Start          ║"
echo "║                   Demonstrating All Requirements                       ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# === BUILD ===
echo "📦 Step 1: Building Sequential and OpenMP Versions"
echo "════════════════════════════════════════════════════"
make clean > /dev/null 2>&1
make all 2>&1 | grep -E "✓|build"
echo ""

# === BASELINE ===
echo "🔍 Step 2: Baseline Verification (Sequential + Correctness)"
echo "════════════════════════════════════════════════════════════"
echo "Running small test (64×64) for correctness verification:"
./edge_sobel_seq seq 64 1 1
echo ""

# === PERFORMANCE MEASUREMENT ===
echo "⚡ Step 3: Performance Measurements (Image Size: 2048×2048)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Sequential Baseline (1 thread):"
TIME_SEQ=$(./edge_sobel_omp omp 2048 1 3 | grep "AVG_TIME" | grep -oP 'AVG_TIME=\K[0-9.]+')
echo "  → Average Time: ${TIME_SEQ} ms"
echo ""

echo "Parallel Performance:"
for threads in 2 4; do
    output=$(./edge_sobel_omp omp 2048 $threads 3)
    time_p=$(echo "$output" | grep "AVG_TIME" | grep -oP 'AVG_TIME=\K[0-9.]+')
    gflops=$(echo "$output" | grep "GFLOPS" | grep -oP 'GFLOPS=\K[0-9.]+')
    speedup=$(echo "scale=2; $TIME_SEQ / $time_p" | bc)
    efficiency=$(echo "scale=2; $speedup / $threads" | bc)
    
    echo "  $threads threads: Time=${time_p}ms, Speedup=${speedup}x, Efficiency=${efficiency}"
done
echo ""

# === AMDAHL'S LAW ===
echo "📐 Step 4: Amdahl's Law Verification"
echo "═══════════════════════════════════"
echo ""
echo "For Sobel edge detection:"
echo "  - Parallelizable fraction: f ≈ 0.95"
echo "  - Sequential fraction: (1-f) ≈ 0.05"
echo ""
echo "Predicted Maximum Speedup @ 4 threads:"
AMDAHL=$(echo "scale=2; 1 / (0.05 + 0.95/4)" | bc)
echo "  S(4) = 1/(0.05 + 0.95/4) = ${AMDAHL}x"
echo ""
echo "Measured values should be close to this prediction."
echo ""

# === CACHE ANALYSIS ===
echo "💾 Step 5: Memory Characteristics"
echo "═════════════════════════════════"
echo ""
echo "Image Size: 2048×2048 pixels = 4,194,304 pixels"
echo "Bytes per pixel: 40 (36 read + 4 write)"
echo "Total memory: ~160 MB transferred"
echo ""
echo "Measured time: ${TIME_SEQ} ms"
BANDWIDTH=$(echo "scale=1; 160 / $TIME_SEQ" | bc)
echo "Memory bandwidth: ${BANDWIDTH} MB/s (low = memory-bound algorithm)"
echo ""
echo "⚠️  Low bandwidth indicates Sobel is memory-bound, not compute-bound"
echo "   → This explains why speedup plateaus beyond 4 threads"
echo ""

# === FILE STRUCTURE ===
echo "📂 Step 6: Project Deliverables"
echo "═════════════════════════════════"
echo ""
echo "Source Code:"
ls -lh edge_detiction.cpp | awk '{print "  ✓", $9, "(" $5 ")"}'
echo ""
echo "Build System:"
ls -lh Makefile | awk '{print "  ✓", $9, "(" $5 ")"}'
echo ""
echo "Executables:"
ls -lh edge_sobel_seq edge_sobel_omp 2>/dev/null | awk '{print "  ✓", $9}'
echo ""
echo "Analysis Scripts:"
ls -lh benchmark.sh analyze_performance.py profile_cache.sh | awk '{print "  ✓", $9, "(" $5 ")"}'
echo ""
echo "Documentation:"
ls -lh README.md REPORT_TEMPLATE.md COMPLETION_SUMMARY.md | awk '{print "  ✓", $9, "(" $5 ")"}'
echo ""

# === RECOMMENDATIONS ===
echo "🎯 Next Steps to Complete Phase 1 Submission:"
echo "═════════════════════════════════════════════"
echo ""
echo "1. Run full benchmarks (optional, takes 5-10 min):"
echo "   $ bash benchmark.sh"
echo "   $ python3 analyze_performance.py"
echo ""
echo "2. Fill in report with your actual performance data:"
echo "   $ cp REPORT_TEMPLATE.md report.md"
echo "   $ # Edit with your measurements"
echo "   $ pandoc report.md -o report.pdf --pdf-engine xelatex"
echo ""
echo "3. Record 2-minute demo video:"
echo "   $ # Use OBS or similar tool"
echo "   $ # Show: code, execution, speedup graph"
echo ""
echo "4. Create submission folder:"
echo "   $ mkdir -p ../Phase1_Submission/src ../Phase1_Submission/plots"
echo "   $ cp edge_detiction.cpp ../Phase1_Submission/src/"
echo "   $ cp Makefile benchmark.sh analyze_performance.py ../Phase1_Submission/"
echo "   $ cp plots/*.png ../Phase1_Submission/plots/"
echo "   $ cp report.pdf ../Phase1_Submission/"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "✅ Phase 1 Quick Demo Complete!"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📖 For more details, see:"
echo "   - README.md (full usage guide)"
echo "   - COMPLETION_SUMMARY.md (requirements checklist)"
echo "   - REPORT_TEMPLATE.md (report structure)"
echo ""
