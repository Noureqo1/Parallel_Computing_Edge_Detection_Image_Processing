# Makefile for Phase 2 - MPI Sobel Edge Detection
# Implements distributed memory parallelism with 2D domain decomposition

MPICC := /usr/bin/mpic++
CXXFLAGS := -Wall -Wextra -O3 -march=native
PROFILE_FLAGS := -pg -fno-omit-frame-pointer

# Targets
EXEC_SOBEL := sobel_mpi
EXEC_LATENCY := benchmark_latency

SOURCES_SOBEL := sobel_mpi.cpp
SOURCES_LATENCY := benchmark_latency.cpp

.PHONY: all clean sobel latency profile help benchmark

all: $(EXEC_SOBEL) $(EXEC_LATENCY)

# MPI Sobel implementation
$(EXEC_SOBEL): src/$(SOURCES_SOBEL)
	$(MPICC) $(CXXFLAGS) -o src/$@ $^
	@echo "✓ MPI Sobel build complete: src/$(EXEC_SOBEL)"

# Latency/Bandwidth benchmark
$(EXEC_LATENCY): src/$(SOURCES_LATENCY)
	$(MPICC) $(CXXFLAGS) -o src/$@ $^
	@echo "✓ Latency benchmark build complete: src/$(EXEC_LATENCY)"

sobel: $(EXEC_SOBEL)
latency: $(EXEC_LATENCY)

# Quick benchmark (single-node)
benchmark-single:
	@echo "=== Single Node Strong Scaling Benchmark ==="
	@echo "Testing with 1, 2, 4 processes on localhost"
	@for p in 1 2 4; do \
		echo "Processes: $$p"; \
		mpirun -np $$p src/$(EXEC_SOBEL) 2048 3; \
		echo ""; \
	done

# Latency/bandwidth benchmark (requires 2+ ranks)
benchmark-latency:
	@echo "=== Latency and Bandwidth Benchmark ==="
	mpirun -np 2 src/$(EXEC_LATENCY)

# Profile version
profile: src/$(SOURCES_SOBEL)
	$(MPICC) $(CXXFLAGS) $(PROFILE_FLAGS) -o src/sobel_mpi_profile $^
	@echo "✓ Profile build complete"

# Clean
clean:
	rm -f src/$(EXEC_SOBEL) src/$(EXEC_LATENCY) src/sobel_mpi_profile *.o gmon.out
	@echo "✓ Cleaned build artifacts"

help:
	@echo "Phase 2 MPI Sobel Edge Detection - Makefile Targets"
	@echo ""
	@echo "Build targets:"
	@echo "  make all              - Build all programs"
	@echo "  make sobel            - Build MPI Sobel only"
	@echo "  make latency          - Build latency benchmark only"
	@echo "  make clean            - Remove build artifacts"
	@echo ""
	@echo "Benchmark targets:"
	@echo "  make benchmark-single - Run strong scaling (1,2,4 processes)"
	@echo "  make benchmark-latency- Run latency/bandwidth test (2 processes)"
	@echo ""
	@echo "Usage examples:"
	@echo "  mpirun -np 2 src/sobel_mpi 1024 5"
	@echo "  mpirun -np 4 src/benchmark_latency"
