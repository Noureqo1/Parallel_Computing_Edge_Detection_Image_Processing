# Phase 1: Parallel Sobel Edge Detection
## Parallelism Project - Shared-Memory Parallel Foundations

**Deadline**: Week 6 (25 October 2025)  
**Status**: Ready for Evaluation ✓

---

## 📋 Project Overview

This phase implements and evaluates a **parallel image processing system** using Sobel edge detection as the benchmark application. We progress from a sequential baseline to an OpenMP-parallelized version, measuring performance improvements across various thread counts.

### Learning Objectives

✓ Parallelize sequential code using OpenMP directives  
✓ Measure and analyze speedup and efficiency  
✓ Apply Amdahl's Law to predict parallelization limits  
✓ Analyze cache behavior and memory hierarchy effects  
✓ Produce professional performance reports with visualizations  

---

## 📂 Project Structure

```
Phase1/
├── edge_detiction.cpp          # Source code (sequential + OpenMP)
├── Makefile                     # Build system with profiling targets
├── benchmark.sh                 # Automated benchmarking script
├── analyze_performance.py       # Performance analysis & plot generation
├── profile_cache.sh             # Cache and memory profiling tool
├── REPORT_TEMPLATE.md          # Comprehensive Phase 1 report template
├── README.md                    # This file
├── plots/                       # Generated performance plots
│   ├── speedup_vs_threads.png
│   ├── efficiency_vs_threads.png
│   └── scaling_analysis.png
└── data/                        # Test data (generated at runtime)
```

---

## 🚀 Quick Start

### 1. Build the Project

```bash
cd Phase1
make clean && make all
```

This creates two executables:
- `edge_sobel_seq` - Sequential baseline
- `edge_sobel_omp` - OpenMP parallel version

### 2. Run Quick Benchmark

```bash
make benchmark
```

Sample output:
```
Sequential (N=2048):     103.5 ms
OpenMP 1 thread:         105.2 ms
OpenMP 2 threads:         54.8 ms (1.92x speedup)
OpenMP 4 threads:         28.3 ms (3.66x speedup)
OpenMP 8 threads:         16.5 ms (6.27x speedup)
```

### 3. Full Performance Analysis

```bash
bash benchmark.sh          # Run comprehensive benchmarks (5-10 minutes)
python3 analyze_performance.py  # Generate plots
```

This produces:
- `benchmark_results.csv` - Raw performance data
- `plots/speedup_vs_threads.png` - Speedup plot
- `plots/efficiency_vs_threads.png` - Efficiency plot
- `plots/scaling_analysis.png` - Strong/weak scaling analysis
- `plots/performance_metrics.csv` - Detailed metrics for report

### 4. Cache Profiling

```bash
bash profile_cache.sh 2048 4    # Profile 2048×2048 image with 4 threads
```

Requires `perf` tool. On Ubuntu/Debian:
```bash
sudo apt-get install linux-tools-generic
```

---

## 📊 Understanding the Code

### Sequential Implementation

```cpp
double run_sobel_seq(const vector<int> &img, vector<int> &out, int N) {
    auto start = chrono::high_resolution_clock::now();
    
    for (int i = 1; i < N-1; ++i) {
        for (int j = 1; j < N-1; ++j) {
            // Apply Sobel kernels to 3×3 neighborhood
            int Gx = /* horizontal gradient */;
            int Gy = /* vertical gradient */;
            int val = (int) std::sqrt((double)Gx*Gx + (double)Gy*Gy);
            out[i*N + j] = clamp255(val);
        }
    }
    
    auto end = chrono::high_resolution_clock::now();
    return chrono::duration_cast<chrono::milliseconds>(end - start).count();
}
```

**Characteristics:**
- Time complexity: $O(N^2)$ for $N \times N$ image
- Space complexity: $O(N^2)$ for input and output
- Stencil computation: Each pixel depends on 9-element neighborhood
- Data races: None (different pixels write to different memory locations)

### OpenMP Parallelization

```cpp
#pragma omp parallel for collapse(2) schedule(static)
for (int i = 1; i < N-1; ++i) {
    for (int j = 1; j < N-1; ++j) {
        // Same computation as sequential version
        // Each iteration executed by available thread
    }
}
```

**Why this parallelization works:**
1. **Loop-level parallelism**: Outer loop iterations are independent
2. **No data races**: Each thread writes to unique output locations
3. **Minimal synchronization**: Only implicit barrier at loop end
4. **Good load balancing**: `schedule(static)` distributes iterations evenly

---

## 📈 Performance Expectations

### Speedup Analysis

**Amdahl's Law** predicts maximum speedup:
$$S(p) = \frac{1}{(1-f) + \frac{f}{p}}$$

For Sobel:
- Parallelizable fraction: $f \approx 0.95$ (main loop)
- Predicted speedup at 8 threads: $S(8) = 1/(0.05 + 0.95/8) \approx 5.85$

**Expected Results:**

| Threads | Expected Speedup | Expected Efficiency |
|---------|-----------------|-------------------|
| 1 | 1.00 | 100% |
| 2 | 1.90 | 95% |
| 4 | 3.60 | 90% |
| 8 | 5.85 | 73% |

### Why Speedup < Linear?

1. **Memory Bandwidth**: Sobel is memory-bound (low arithmetic intensity)
2. **Synchronization**: OpenMP barrier cost increases with thread count
3. **Cache Contention**: More threads competing for cache resources
4. **NUMA Effects**: Latency on non-uniform memory access (for >8 threads)

---

## 🔧 Detailed Usage

### Individual Runs

```bash
# Sequential baseline
./edge_sobel_seq seq 1024 1 10

# OpenMP with N threads
./edge_sobel_omp omp 1024 4 10

# Parameters:
# - mode: "seq" or "omp"
# - N: Image size (e.g., 1024 for 1024×1024)
# - threads: Number of threads (for OMP only)
# - num_runs: Number of repetitions for averaging
```

### Output Format

```
MODE=OPENMP N=2048 THREADS=4 AVG_TIME=29.456 MIN=28.123 MAX=30.789 GFLOPS=3.21
```

**Fields:**
- `AVG_TIME`: Average execution time across runs (ms)
- `MIN`/`MAX`: Range of execution times (for stability assessment)
- `GFLOPS`: Estimated floating-point operations per second

### Makefile Targets

```bash
make seq               # Build sequential only
make omp               # Build OpenMP only
make all               # Build both
make clean             # Remove binaries
make benchmark         # Quick performance test
make perf_cache        # Cache profiling with perf
make help              # Show all targets
```

---

## 📊 Performance Profiling & Analysis

### 1. Run Benchmarks

```bash
bash benchmark.sh
```

This script:
- Tests image sizes: 512, 1024, 2048 pixels
- Tests thread counts: 1, 2, 4, 8
- Performs 5 runs per configuration
- Outputs CSV file `benchmark_results.csv`

### 2. Analyze Results

```bash
python3 analyze_performance.py
```

Generates three plots:

#### Speedup vs Threads Plot
Shows how speedup increases with thread count for different image sizes.
- X-axis: Number of threads (1, 2, 4, 8)
- Y-axis: Speedup ($T_S / T_P$)
- Ideal line: Represents linear scaling

#### Efficiency vs Threads Plot
Shows percentage of peak parallelism achieved.
- X-axis: Number of threads
- Y-axis: Efficiency ($Speedup / Threads$)
- Red dashed line: 80% efficiency threshold

#### Scaling Analysis
- **Left panel**: Strong scaling (fixed problem, varying threads)
- **Right panel**: Execution time vs problem size

### 3. Cache Analysis

```bash
bash profile_cache.sh 2048 4
```

Provides:
- L1/L2/L3 cache miss rates
- Memory bandwidth utilization
- Arithmetic intensity analysis
- Optimization recommendations

---

## 💾 Compiler Flags Explanation

```makefile
CXXFLAGS := -Wall -Wextra -O3 -march=native
OPENMP_FLAGS := -fopenmp
```

| Flag | Purpose |
|------|---------|
| `-Wall -Wextra` | Enable compiler warnings |
| `-O3` | Aggressive optimizations (loops, inlining, vectorization) |
| `-march=native` | Compile for local CPU (uses SIMD: SSE, AVX) |
| `-fopenmp` | Enable OpenMP support |

---

## 🧪 Correctness Verification

The code automatically verifies correctness for small images:

```bash
./edge_sobel_seq seq 8 1 1
```

Output shows pixel-by-pixel results for manual verification. For larger images, results are identical whether computed sequentially or in parallel (same algorithm, just different execution order).

---

## 📝 Report Generation

### Using the Template

1. Copy `REPORT_TEMPLATE.md` to `report.pdf` (convert with Pandoc):

```bash
pandoc REPORT_TEMPLATE.md -o report.pdf \
  --from markdown --to pdf \
  --pdf-engine xelatex
```

2. Fill in your actual performance data:
   - Hardware configuration
   - Measured performance tables
   - Your interpretation of results

3. Ensure plots are included:
   - `plots/speedup_vs_threads.png`
   - `plots/efficiency_vs_threads.png`
   - `plots/scaling_analysis.png`

### Report Checklist

✓ Problem statement and Sobel algorithm explanation  
✓ Sequential baseline implementation  
✓ OpenMP parallelization approach (with pragma analysis)  
✓ Performance measurements (table with T_S, T_P, speedup, efficiency)  
✓ Amdahl's Law analysis and interpretation  
✓ Memory hierarchy / cache analysis  
✓ Discussion of bottlenecks (memory bandwidth, synchronization)  
✓ 3 performance plots (well-labeled, readable)  
✓ Conclusion and recommendations for Phase 2  

---

## 🎯 Evaluation Criteria (Phase 1 Rubric)

### 1. Problem Definition & Baseline (15%)
- ✓ Clear Sobel algorithm description
- ✓ Working sequential implementation
- ✓ Verified correctness

### 2. Parallel Design & Implementation (25%)
- ✓ Proper OpenMP directives (`#pragma omp parallel for`)
- ✓ Thread safety analysis (no data races)
- ✓ Synchronization overhead minimized

### 3. Performance Analysis (25%)
- ✓ Accurate timing measurements
- ✓ Speedup calculated correctly ($S = T_S / T_P$)
- ✓ Efficiency computed ($E = S / p$)
- ✓ Amdahl's Law discussion

### 4. Profiling & Memory Analysis (10%)
- ✓ Cache profiling results
- ✓ Evidence of `perf` or `gprof` measurements
- ✓ Memory bandwidth analysis

### 5. Report Clarity (15%)
- ✓ Well-organized sections
- ✓ Clear mathematical notation
- ✓ Professional plots with labels
- ✓ Proper citations / references

### 6. Demo Video (10%)
- ✓ Demonstrates problem definition
- ✓ Shows execution and speedup
- ✓ 2-minute concise presentation

---

## 🐛 Troubleshooting

### Build Issues

**Error: "omp.h not found"**
```bash
# Install OpenMP development headers
sudo apt-get install libomp-dev   # For Clang
sudo apt-get install libgomp1      # For GCC (usually included)
```

**Error: "march=native" not recognized**
```bash
# Use more conservative target
# Edit Makefile: change "-march=native" to "-march=haswell"
```

### Runtime Issues

**All threads show same performance as sequential**
```bash
# Check if OpenMP is actually enabled
./edge_sobel_omp omp 100 4 1
# Should show "THREADS=4" in output
```

**Segmentation fault on large images**
```bash
# Increase stack size for large allocations
export OMP_STACKSIZE=128M
./edge_sobel_omp omp 4096 4 1
```

### Profiling Issues

**perf: Permission denied**
```bash
# Run with elevated privileges or configure perf
sudo perf stat -e ...

# Or enable for your user (Linux-specific)
echo 0 | sudo tee /proc/sys/kernel/perf_event_paranoid
```

---

## 📚 References & Learning Resources

### Concepts
- **Amdahl's Law**: Computing achievable speedup from parallelization
- **Memory Hierarchy**: Cache organization and temporal/spatial locality
- **Stencil Computation**: Common pattern in scientific computing

### OpenMP
- [OpenMP 5.2 Specification](https://www.openmp.org/spec-html/5.2/)
- [OpenMP Quick Reference](https://www.openmp.org/spec-html/5.2/openmpsu2.html)
- Loop parallelism: `#pragma omp parallel for`
- Task parallelism: `#pragma omp task`
- Reductions: `#pragma omp reduction`

### Performance Analysis Tools
- **perf**: Linux performance counter interface
- **gprof**: GNU Profiler
- **Cachegrind**: Part of Valgrind
- **Intel VTune**: Commercial profiler

### Edge Detection References
- Sobel Operator: Wikipedia article on Sobel operator
- Image Processing: Gonzalez & Woods, "Digital Image Processing"

---

## ✅ Checklist Before Submission

- [ ] Code compiles with `make all` without warnings
- [ ] `./edge_sobel_seq` and `./edge_sobel_omp` executables work
- [ ] `benchmark.sh` completes successfully
- [ ] `analyze_performance.py` generates plots
- [ ] Performance plots show sensible results (speedup increases with threads)
- [ ] Report filled with actual performance data
- [ ] Report includes at least 3 labeled plots
- [ ] Amdahl's Law analysis compares predicted vs measured
- [ ] Cache analysis discusses memory bandwidth bottleneck
- [ ] Demo video recorded (2 minutes max)
- [ ] Code repository clean (no temporary files)

---

## 📞 Support & Questions

For issues or questions:
1. Check the Troubleshooting section above
2. Review comments in source code (`edge_detiction.cpp`)
3. Refer to the report template for detailed explanations
4. Consult OpenMP documentation for parallel directives

---

**Project Status**: ✓ Phase 1 Complete  
**Next Phase**: Phase 2 - Distributed Memory (MPI + CUDA)  
**Last Updated**: December 2025

