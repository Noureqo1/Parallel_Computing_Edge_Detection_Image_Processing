# Makefile for Phase 1 - Parallel Sobel Edge Detection
# Supports sequential and OpenMP parallel versions
# Includes performance profiling targets

CXX := g++
CXXFLAGS := -Wall -Wextra -O3 -march=native
OPENMP_FLAGS := -fopenmp
PROFILE_FLAGS := -pg -fno-omit-frame-pointer
PERF_FLAGS := $(CXXFLAGS) -O3 -march=native -fopenmp

# Targets
EXEC_SEQ := edge_sobel_seq
EXEC_OMP := edge_sobel_omp
EXEC_PROFILE := edge_sobel_profile

SOURCES := edge_detiction.cpp
HEADERS :=

.PHONY: all clean seq omp profile help benchmark

all: $(EXEC_SEQ) $(EXEC_OMP)

# Sequential version
$(EXEC_SEQ): $(SOURCES)
	$(CXX) $(CXXFLAGS) -o $@ $^ 
	@echo "✓ Sequential build complete: $(EXEC_SEQ)"

# OpenMP parallel version
$(EXEC_OMP): $(SOURCES)
	$(CXX) $(CXXFLAGS) $(OPENMP_FLAGS) -o $@ $^
	@echo "✓ OpenMP build complete: $(EXEC_OMP)"

# Profile version (for gprof/perf analysis)
$(EXEC_PROFILE): $(SOURCES)
	$(CXX) $(CXXFLAGS) $(OPENMP_FLAGS) $(PROFILE_FLAGS) -o $@ $^
	@echo "✓ Profile build complete: $(EXEC_PROFILE)"

seq: $(EXEC_SEQ)
omp: $(EXEC_OMP)
profile: $(EXEC_PROFILE)

# Quick benchmark on single test case
benchmark: all
	@echo "=== Quick Benchmark (N=2048, 5 runs) ==="
	@echo "Sequential:"
	@./$(EXEC_SEQ) seq 2048 1 5
	@echo "\nOpenMP 1 thread:"
	@./$(EXEC_OMP) omp 2048 1 5
	@echo "\nOpenMP 2 threads:"
	@./$(EXEC_OMP) omp 2048 2 5
	@echo "\nOpenMP 4 threads:"
	@./$(EXEC_OMP) omp 2048 4 5
	@echo "\nOpenMP 8 threads:"
	@./$(EXEC_OMP) omp 2048 8 5

# Cache profiling with perf
perf_cache: $(EXEC_OMP)
	@echo "=== Cache Analysis (requires perf tool) ==="
	@perf stat -e cache-references,cache-misses,LLC-loads,LLC-load-misses \
		./$(EXEC_OMP) omp 2048 4 1

# Clean
clean:
	rm -f $(EXEC_SEQ) $(EXEC_OMP) $(EXEC_PROFILE) *.o gmon.out perf.data perf.data.old
	@echo "✓ Cleaned build artifacts"

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build both sequential and OpenMP versions"
	@echo "  seq          - Build sequential version only"
	@echo "  omp          - Build OpenMP version only"
	@echo "  profile      - Build with profiling support (gprof)"
	@echo "  benchmark    - Run quick performance benchmark"
	@echo "  perf_cache   - Run cache profiling (requires perf)"
	@echo "  clean        - Remove build artifacts"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Example usage:"
	@echo "  make omp"
	@echo "  ./edge_sobel_omp omp 2048 4 5"
