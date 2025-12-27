# Parallel Computing: Edge Detection Image Processing

A comprehensive implementation of Sobel edge detection using three parallel computing paradigms: shared memory (OpenMP), distributed memory (MPI), and fault-tolerant distributed systems (gRPC).

## Project Structure

```
Parallel_Computing_Edge_Detection_Image_Processing/
├── Phase1/                    # OpenMP Shared Memory Parallelization
├── phase II/                  # MPI Distributed Memory Parallelization
└── phase III/                 # gRPC Fault-Tolerant Distributed System
```

## Phase 1: OpenMP Shared Memory Parallelization

**Implementation**: Parallel Sobel edge detection using OpenMP

**Key Features**:
- Multi-threaded shared memory parallelization
- Performance benchmarking (1, 2, 4, 8 threads)
- Speedup and efficiency analysis

**Documentation**: See `Phase1/README.md`

**Quick Start**:
```bash
cd Phase1
make clean && make all
./benchmark.sh
python3 analyze_performance.py
```

## Phase 2: MPI Distributed Memory Parallelization

**Implementation**: Distributed Sobel edge detection using MPI with 2D domain decomposition

**Key Features**:
- 2D Cartesian process grid (√p × √p)
- Halo exchange for stencil computation
- Strong/weak scaling analysis
- Latency and bandwidth benchmarking

**Documentation**: See `phase II/README.md`

**Quick Start**:
```bash
cd "phase II"
make clean && make all
./scripts/strong_scaling.sh
python3 analyze_mpi.py
```

## Phase 3: Resilient Distributed System with gRPC

**Implementation**: Fault-tolerant Sobel service with automatic failover

**Key Features**:
- gRPC service with multiple replicas
- Automatic retry with exponential backoff
- Client-side failover and health tracking
- Failure injection and recovery testing
- Real-time performance monitoring

**Documentation**: See `phase III/README.md`

**Quick Start**:
```bash
cd "phase III"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make compile
./scripts/run_demo.sh
```

## System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Compiler**: GCC 9.0+ with OpenMP support
- **MPI**: LAM/MPI or OpenMPI
- **Python**: 3.7+
- **RAM**: 4 GB minimum, 8 GB recommended

## Performance Summary

### Phase 1 (OpenMP)
- **Speedup**: 1.8x @ 2 threads, 2.6x @ 4 threads
- **Efficiency**: 90% @ 2 threads, 65% @ 4 threads

### Phase 2 (MPI)
- **Strong Scaling**: Up to 4x speedup (on real cluster)
- **Weak Scaling**: 85-95% efficiency (on real cluster)
- **Note**: Localhost testing shows overhead due to LAM/MPI loopback latency

### Phase 3 (gRPC)
- **Availability**: 95-100% success rate with failures
- **Recovery Time**: 2-5 seconds (crash), 10-20 seconds (freeze)
- **Failover**: Automatic, no manual intervention

## Key Concepts Demonstrated

1. **Parallel Programming Models**
   - Shared memory (threads)
   - Distributed memory (message passing)
   - Remote procedure calls (RPC)

2. **Performance Analysis**
   - Speedup and efficiency metrics
   - Strong and weak scaling
   - Amdahl's and Gustafson's laws

3. **Fault Tolerance**
   - Service replication
   - Automatic retry and backoff
   - Health monitoring and failover

4. **System Design**
   - Load balancing strategies
   - Communication patterns (halo exchange, RPC)
   - Resilience patterns (circuit breaker, retry)

## Technologies Used

- **C++**: Core algorithm implementation
- **OpenMP**: Thread-based parallelization
- **MPI**: Process-based distributed computing
- **Python**: Analysis, visualization, gRPC client
- **gRPC/Protocol Buffers**: Service definition and RPC
- **NumPy**: Numerical computing
- **Matplotlib**: Performance visualization

## Educational Objectives

This project demonstrates:
- Progression from shared memory → distributed memory → fault-tolerant systems
- Trade-offs between different parallel computing paradigms
- Real-world considerations: communication overhead, fault tolerance, scalability
- Performance analysis and visualization techniques

## License

Academic project - feel free to use for educational purposes.

## Author

Noureqo Mohamed
- Email: noureqomohamed14@gmail.com
- GitHub: [@Noureqo1](https://github.com/Noureqo1)

## Acknowledgments

- Course: Parallel and Distributed Systems
- Date: December 2025
