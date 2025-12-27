# Phase 3: Resilience & High-Availability Integration

## Overview

Phase 3 transforms the Sobel edge detection algorithm into a **fault-tolerant distributed system** with automatic failover, retry logic, and comprehensive monitoring. This implementation demonstrates production-grade resilience patterns including:

- **Service Replication**: Multiple gRPC server instances
- **Client-Side Resilience**: Automatic retry with exponential backoff
- **Load Balancing**: Round-robin with health-aware selection
- **Failure Recovery**: Graceful degradation and recovery
- **Performance Monitoring**: Real-time metrics collection and analysis

## Architecture

```
┌─────────────┐
│   Client    │
│ (Resilient) │──────┐
└─────────────┘      │
                     ├──→ ┌──────────────┐
┌─────────────┐      │    │  Server-0    │
│    Load     │──────┼───→│  :50051      │
│  Generator  │      │    └──────────────┘
└─────────────┘      │
                     ├──→ ┌──────────────┐
┌─────────────┐      │    │  Server-1    │
│  Metrics    │      └───→│  :50052      │
│  Analyzer   │           └──────────────┘
└─────────────┘
       │
       ├──→ Time-series plots
       └──→ Performance report
```

### Components

1. **gRPC Service** (`proto/sobel_service.proto`)
   - `ProcessImage`: Main edge detection RPC
   - `HealthCheck`: Server health monitoring
   - `GetMetrics`: Performance metrics collection

2. **Server** (`server/`)
   - `sobel_server.py`: gRPC service implementation
   - `sobel_worker.py`: Sobel algorithm (Python/NumPy)
   - Multi-threaded request handling
   - Built-in metrics tracking

3. **Resilient Client** (`client/sobel_client.py`)
   - Automatic retry with exponential backoff
   - Health-aware server selection
   - Failover on connection errors
   - Connection pooling

4. **Load Generator** (`client/load_generator.py`)
   - Synthetic image generation
   - Configurable request rate
   - Continuous load for 60+ seconds
   - Detailed request logging (JSON)

5. **Failure Injection** (`scripts/inject_failure.sh`)
   - Process crash (SIGKILL)
   - Process freeze (SIGSTOP/SIGCONT)
   - Network delay simulation (tc)

6. **Metrics Analysis** (`monitoring/analyze_metrics.py`)
   - Time-series throughput/latency graphs
   - Automatic failure event detection
   - Recovery time calculation
   - Comprehensive performance report

## Quick Start

### 1. Install Dependencies

```bash
cd "phase III"

# Install Python packages in virtual environment (recommended for Python 3.11+)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Or use system packages (if available)
sudo apt-get install python3-grpcio python3-grpcio-tools python3-numpy python3-matplotlib
```

**Note**: On newer Python systems (3.11+), you may get an "externally-managed-environment" error with pip. Use the virtual environment method shown above.

### 2. Compile Protocol Buffers

```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

chmod +x scripts/*.sh
./scripts/compile_proto.sh
```

This generates:
- `sobel_service_pb2.py` (message classes)
- `sobel_service_pb2_grpc.py` (gRPC stubs)

### 3. Run Complete Demo

```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

./scripts/run_demo.sh
```

This automated demo:
1. Starts 2 server replicas (ports 50051-50052)
2. Launches load generator (90 seconds, 5 req/sec)
3. Injects failure #1: Crashes server-0 at ~25s
4. Injects failure #2: Freezes server-1 at ~45s, then resumes
5. Analyzes results and generates plots

### 4. View Results

```bash
# Analysis report
cat results/analysis_report.txt

# Time-series graphs
ls results/*.png

# Raw data
jq . results/load_test.json | less
```

## Manual Usage

### Start Servers

```bash
# Terminal 1: Start replica 1
python3 server/sobel_server.py --port 50051 --id server-0

# Terminal 2: Start replica 2
python3 server/sobel_server.py --port 50052 --id server-1
```

Or use the startup script:

```bash
./scripts/start_replicas.sh 2 50051  # 2 replicas starting at port 50051
```

### Run Load Test

```bash
python3 client/load_generator.py \
    --servers localhost:50051,localhost:50052 \
    --duration 60 \
    --rate 10.0 \
    --sizes 256x256,512x512 \
    --log results/test.json
```

Parameters:
- `--servers`: Comma-separated server addresses
- `--duration`: Test duration in seconds (default: 60)
- `--rate`: Target requests per second (default: 10.0)
- `--sizes`: Image dimensions to test (e.g., 256x256,512x512)
- `--log`: Output JSON log file

### Inject Failures

**Crash a server:**
```bash
./scripts/inject_failure.sh crash server-0
```

**Freeze a server:**
```bash
./scripts/inject_failure.sh freeze server-1

# Later, resume it:
./scripts/inject_failure.sh resume server-1
```

**Network delay (requires root):**
```bash
sudo tc qdisc add dev lo root netem delay 2000ms
# ... run tests ...
sudo tc qdisc del dev lo root
```

### Analyze Results

```bash
python3 monitoring/analyze_metrics.py \
    --log results/test.json \
    --output results/analysis \
    --window 1.0
```

Generates:
- `analysis_report.txt`: Summary statistics
- `analysis_timeseries.png`: Combined throughput + latency plots
- `analysis_throughput.png`: Throughput with failure annotations

## Key Metrics

### Resilience Metrics

1. **Success Rate**: Percentage of successful requests after retries
   - Target: >99% with 2+ replicas
   
2. **Failover Count**: Number of times client switched servers
   - Indicates replica failures detected

3. **Retry Count**: Total retries across all requests
   - Lower is better (indicates fewer failures)

4. **Recovery Time**: Time to return to baseline after failure
   - Measured in seconds
   - Target: <5 seconds

### Performance Metrics

1. **Throughput**: Requests per second
   - Before failure: Baseline throughput
   - During failure: Degraded throughput
   - After recovery: Return to baseline

2. **Latency (p95)**: 95th percentile request latency
   - Normal: <100ms (depends on image size)
   - During failure: May spike to 1000ms+ (timeout scenarios)
   - After recovery: Return to normal

3. **Latency (p99)**: 99th percentile (tail latency)
   - Indicates worst-case user experience

## Failure Scenarios

### Scenario 1: Single Server Crash

**Setup**: 2 replicas running, steady load

**Failure**: Kill server-0 (`./scripts/inject_failure.sh crash server-0`)

**Expected Behavior**:
- Client detects connection failure
- Marks server-0 as unhealthy
- Automatic failover to server-1
- Retries succeed on server-1
- Throughput briefly drops, then recovers
- p95 latency spike during failover (~100-500ms)
- Recovery time: 1-3 seconds

**Metrics to Observe**:
- Success rate remains >95%
- Failover count increments
- Server-1 handles all requests after failure

### Scenario 2: Server Freeze (Partial Failure)

**Setup**: 2 replicas running, steady load

**Failure**: Freeze server-1 (`./scripts/inject_failure.sh freeze server-1`)

**Expected Behavior**:
- Requests to server-1 timeout (10s timeout)
- Client experiences high latency (10,000ms)
- After timeout, marks server-1 unhealthy
- Failover to server-0
- When resumed, server-1 becomes healthy again

**Metrics to Observe**:
- Latency spike to ~10,000ms for affected requests
- Throughput drops significantly during timeout period
- Recovery after freeze is lifted

### Scenario 3: Network Partition

**Setup**: Use tc to add network delay

**Failure**: `sudo tc qdisc add dev lo root netem delay 2000ms`

**Expected Behavior**:
- All requests experience +2000ms latency
- No failures (just slow)
- Client continues normal operation
- Throughput limited by latency

**Metrics to Observe**:
- Throughput drops proportionally to latency increase
- p95 latency increases by delay amount
- No failures or retries

## Expected Results

### Baseline (No Failures)

- **Success Rate**: 100%
- **Throughput**: 8-12 req/sec (depending on image size and system)
- **p95 Latency**: 50-150ms
- **Failovers**: 0
- **Retries**: 0

### With Failures (Single Crash)

- **Success Rate**: 98-100%
- **Throughput**: Brief dip to 50-70% during failover
- **p95 Latency**: Spike to 200-500ms during failover
- **Recovery Time**: 2-5 seconds
- **Failovers**: 1 per crash event
- **Retries**: 5-15 (depends on timing)

### With Failures (Freeze + Resume)

- **Success Rate**: 90-98%
- **Throughput**: Drops to 10-20% during freeze
- **p95 Latency**: Spike to 10,000ms (timeout)
- **Recovery Time**: 10-15 seconds
- **Failovers**: 1 during freeze, potentially 1 on resume
- **Retries**: 20-50 (higher due to timeouts)

## Implementation Details

### Retry Logic

```python
backoff_ms = 100  # Initial backoff
max_backoff_ms = 5000
max_retries = 3

for attempt in range(max_retries):
    try:
        response = stub.ProcessImage(request, timeout=10)
        return response
    except grpc.RpcError:
        if attempt < max_retries - 1:
            time.sleep(backoff_ms / 1000.0)
            backoff_ms = min(backoff_ms * 2, max_backoff_ms)
```

### Health Tracking

- Health checks cached for 5 seconds
- Server marked unhealthy on: UNAVAILABLE, DEADLINE_EXCEEDED, INTERNAL
- Automatic health recovery via periodic checks

### Metrics Collection

All requests logged with:
- Timestamp (milliseconds)
- Request ID
- Latency (milliseconds)
- Success/failure status
- Server ID that processed request
- Image size

## Troubleshooting

### Issue: "grpcio not found"

```bash
pip3 install grpcio grpcio-tools
```

### Issue: "Permission denied" on scripts

```bash
chmod +x scripts/*.sh
```

### Issue: "Port already in use"

```bash
# Find process using port
lsof -i :50051

# Kill it
kill -9 <PID>
```

### Issue: Servers not starting

Check logs:
```bash
cat logs/server-0.log
cat logs/server-1.log
```

### Issue: No plot output

Install matplotlib:
```bash
pip3 install matplotlib
# or
sudo apt-get install python3-matplotlib
```

## Performance Tips

1. **Request Rate**: Start with 5-10 req/sec, increase gradually
2. **Image Size**: Larger images (1024x1024) = more computation time
3. **Number of Replicas**: 2-3 is optimal for testing
4. **Timeout**: 10s default, reduce to 5s for faster failover
5. **Backoff**: Tune initial_backoff_ms based on typical latency

## File Structure

```
phase III/
├── proto/
│   └── sobel_service.proto          # gRPC service definition
├── server/
│   ├── sobel_server.py              # gRPC server
│   └── sobel_worker.py              # Sobel algorithm
├── client/
│   ├── sobel_client.py              # Resilient client
│   └── load_generator.py            # Load testing tool
├── monitoring/
│   └── analyze_metrics.py           # Metrics analysis
├── scripts/
│   ├── compile_proto.sh             # Proto compilation
│   ├── start_replicas.sh            # Start servers
│   ├── inject_failure.sh            # Failure injection
│   └── run_demo.sh                  # Complete demo
├── results/                         # Output directory
│   ├── load_test.json              # Request logs
│   ├── analysis_report.txt         # Summary
│   └── *.png                       # Plots
├── logs/                            # Server logs
│   ├── server-*.log
│   └── server-*.pid
├── requirements.txt                 # Python dependencies
├── sobel_service_pb2.py            # Generated (proto)
├── sobel_service_pb2_grpc.py       # Generated (gRPC stubs)
└── README.md                        # This file
```

## Next Steps

1. **Experiment with Failure Scenarios**
   - Multiple simultaneous crashes
   - Cascading failures
   - Network partitions

2. **Extend Monitoring**
   - Add Prometheus metrics export
   - Real-time dashboard (Grafana)
   - Alert on SLA violations

3. **Optimize Performance**
   - Implement client-side caching
   - Use async/streaming RPCs
   - Add load-aware routing

4. **Advanced Resilience**
   - Circuit breaker pattern
   - Bulkhead isolation
   - Rate limiting

5. **Integration (Bonus)**
   - Spark Structured Streaming
   - Apache Flink
   - Kafka for event streaming

## References

- [gRPC Python Guide](https://grpc.io/docs/languages/python/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [Retry Patterns](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
