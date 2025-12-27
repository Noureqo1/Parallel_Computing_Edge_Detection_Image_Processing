#include <iostream>
#include <vector>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <mpi.h>

using namespace std;

struct LatencyBandwidth {
    int message_size;
    double latency_us;      // One-way latency in microseconds
    double bandwidth_mbps;  // Bandwidth in MB/s
};

// Measure latency and bandwidth between two processes
LatencyBandwidth measure_pair(int rank, int peer_rank, int message_size, int iterations) {
    LatencyBandwidth result;
    result.message_size = message_size;
    
    vector<char> buffer(message_size, 'A');
    double total_time = 0;
    
    MPI_Barrier(MPI_COMM_WORLD);
    
    if (rank == 0 && peer_rank == 1) {
        // Rank 0 initiates: send, receive (measures round-trip)
        auto start = chrono::high_resolution_clock::now();
        
        for (int i = 0; i < iterations; ++i) {
            MPI_Send(buffer.data(), message_size, MPI_CHAR, 1, 0, MPI_COMM_WORLD);
            MPI_Recv(buffer.data(), message_size, MPI_CHAR, 1, 0, MPI_COMM_WORLD, 
                    MPI_STATUS_IGNORE);
        }
        
        auto end = chrono::high_resolution_clock::now();
        total_time = chrono::duration<double, micro>(end - start).count();
        
        // One-way latency is half the round-trip time
        result.latency_us = total_time / (2.0 * iterations);
        result.bandwidth_mbps = (message_size / (result.latency_us / 1e6)) / 1e6;
        
    } else if (rank == 1 && peer_rank == 0) {
        // Rank 1 responds
        for (int i = 0; i < iterations; ++i) {
            MPI_Recv(buffer.data(), message_size, MPI_CHAR, 0, 0, MPI_COMM_WORLD,
                    MPI_STATUS_IGNORE);
            MPI_Send(buffer.data(), message_size, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
        }
    }
    
    return result;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    
    if (world_size < 2) {
        if (rank == 0) {
            cerr << "This benchmark requires at least 2 MPI ranks\n";
        }
        MPI_Finalize();
        return 1;
    }
    
    if (rank == 0) {
        cout << "MPI Latency and Bandwidth Benchmark\n";
        cout << "===================================\n";
        cout << "World size: " << world_size << "\n\n";
    }
    
    // Benchmark message sizes: from 1 byte to 1 MB
    vector<int> sizes = {1, 10, 100, 1000, 10000, 100000, 1000000};
    
    if (rank == 0) {
        cout << fixed << setprecision(3);
        cout << "Message Size (B)\tLatency (μs)\tBandwidth (MB/s)\n";
        cout << "================================================\n";
    }
    
    for (int size : sizes) {
        int iterations = (size <= 100) ? 10000 : (size <= 10000) ? 1000 : 100;
        
        LatencyBandwidth result;
        if (rank <= 1) {
            result = measure_pair(rank, (rank + 1) % 2, size, iterations);
        }
        
        MPI_Barrier(MPI_COMM_WORLD);
        
        if (rank == 0) {
            cout << size << "\t\t" 
                 << result.latency_us << "\t\t" 
                 << result.bandwidth_mbps << "\n";
        }
    }
    
    if (rank == 0) {
        cout << "\n================================================\n";
        cout << "Benchmark complete\n";
    }
    
    MPI_Finalize();
    return 0;
}
