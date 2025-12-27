#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <cstring>
#include <iomanip>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif

using namespace std;

// Performance timing structure
struct PerfMetrics {
    double time_ms;
    int threads;
    int image_size;
    double gflops;  // Estimated computation rate
};

// Function to compute estimated GFLOPs
// Sobel requires ~3 multiplications + 8 additions + 1 sqrt + comparisons per pixel
double computeGFLOPS(int N, double time_ms) {
    long long operations = (long long)N * N * 15;  // Conservative estimate
    if (time_ms == 0) return 0;
    return (operations / 1e9) / (time_ms / 1e3);
}

void make_test_image(vector<int> &img, int N) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            img[i*N + j] = ((i*31 + j*17) % 256);
}

int clamp255(int v){ return v < 0 ? 0 : (v>255?255:v); }

// Sequential Sobel edge detection
// Memory Access Pattern: Row-major traversal with fixed stencil (3x3 neighborhood)
// Cache Locality: Good spatial locality along rows, but row-to-row boundary is cold
// Optimization Note: No cache blocking applied here (baseline version)
double run_sobel_seq(const vector<int> &img, vector<int> &out, int N) {
    auto start = chrono::high_resolution_clock::now();
    
    // Main computation loop: (N-2)^2 pixels, 16 ops/pixel + 1 sqrt ≈ 15 FLOPs per pixel
    for (int i = 1; i < N-1; ++i) {
        for (int j = 1; j < N-1; ++j) {
            // Sobel X-gradient kernel: [-1, 0, 1; -2, 0, 2; -1, 0, 1]
            int Gx = -img[(i-1)*N + (j-1)] - 2*img[i*N + (j-1)] - img[(i+1)*N + (j-1)]
                     + img[(i-1)*N + (j+1)] + 2*img[i*N + (j+1)] + img[(i+1)*N + (j+1)];
            
            // Sobel Y-gradient kernel: [-1, -2, -1; 0, 0, 0; 1, 2, 1]
            int Gy = -img[(i-1)*N + (j-1)] - 2*img[(i-1)*N + j]   - img[(i-1)*N + (j+1)]
                     + img[(i+1)*N + (j-1)] + 2*img[(i+1)*N + j]   + img[(i+1)*N + (j+1)];
            
            // Gradient magnitude: sqrt(Gx^2 + Gy^2)
            int val = (int) std::sqrt((double)Gx*Gx + (double)Gy*Gy);
            out[i*N + j] = clamp255(val);
        }
    }
    auto end = chrono::high_resolution_clock::now();
    return chrono::duration_cast<chrono::milliseconds>(end - start).count();
}

// OpenMP Parallel Sobel edge detection
// Parallelization: Outer loop (i) parallelized with static scheduling
// Schedule Choice: static schedule chosen to minimize synchronization overhead
// Thread Safety: No shared state within parallel region except reads from img (read-only)
// Data Race Prevention: Each thread writes to disjoint output regions (i*N + j)
// Memory Note: False sharing unlikely due to row-major output layout
double run_sobel_omp(const vector<int> &img, vector<int> &out, int N) {
    auto start = chrono::high_resolution_clock::now();
    
    // Static schedule distributes iterations evenly; good for balanced workload
    // Collapse(2) could improve load balance but increases synchronization overhead
    #pragma omp parallel for collapse(2) schedule(static) num_threads(omp_get_max_threads())
    for (int i = 1; i < N-1; ++i) {
        for (int j = 1; j < N-1; ++j) {
            // Each thread computes disjoint pixel locations - no synchronization needed
            int Gx = -img[(i-1)*N + (j-1)] - 2*img[i*N + (j-1)] - img[(i+1)*N + (j-1)]
                     + img[(i-1)*N + (j+1)] + 2*img[i*N + (j+1)] + img[(i+1)*N + (j+1)];
            int Gy = -img[(i-1)*N + (j-1)] - 2*img[(i-1)*N + j]   - img[(i-1)*N + (j+1)]
                     + img[(i+1)*N + (j-1)] + 2*img[(i+1)*N + j]   + img[(i+1)*N + (j+1)];
            int val = (int) std::sqrt((double)Gx*Gx + (double)Gy*Gy);
            out[i*N + j] = clamp255(val);
        }
    }
    auto end = chrono::high_resolution_clock::now();
    return chrono::duration_cast<chrono::milliseconds>(end - start).count();
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cout << "Usage: ./edge_sobel <mode> [N] [threads] [num_runs]\n";
        cout << "  mode: 'seq' or 'omp'\n";
        cout << "  N: image size (default 1024)\n";
        cout << "  threads: number of threads for OMP (default 1)\n";
        cout << "  num_runs: number of runs for averaging (default 5)\n";
        return 1;
    }
    
    string mode = argv[1];
    int N = (argc > 2) ? stoi(argv[2]) : 1024;
    int threads = (argc > 3) ? stoi(argv[3]) : 1;
    int num_runs = (argc > 4) ? stoi(argv[4]) : 5;

    // Validate inputs
    if (N < 3) {
        cerr << "Image size N must be at least 3\n";
        return 1;
    }
    if (threads < 1) {
        cerr << "Threads must be at least 1\n";
        return 1;
    }

    vector<int> img(N*N);
    vector<int> out(N*N);
    make_test_image(img, N);

    // Warm-up run (helps with JIT compilation on some systems)
    if (mode == "seq") {
        run_sobel_seq(img, out, N);
    } else if (mode == "omp") {
#ifdef _OPENMP
        omp_set_num_threads(threads);
        run_sobel_omp(img, out, N);
#endif
    }

    // Performance measurement: multiple runs for statistical significance
    vector<double> times;
    for (int run = 0; run < num_runs; ++run) {
        double ms = 0;
        if (mode == "seq") {
            ms = run_sobel_seq(img, out, N);
        } else if (mode == "omp") {
#ifdef _OPENMP
            omp_set_num_threads(threads);
            ms = run_sobel_omp(img, out, N);
#else
            cerr << "Not compiled with OpenMP support\n";
            return 2;
#endif
        } else {
            cerr << "Unknown mode: " << mode << "\n";
            return 1;
        }
        times.push_back(ms);
    }

    // Compute statistics
    double min_time = *min_element(times.begin(), times.end());
    double max_time = *max_element(times.begin(), times.end());
    double avg_time = 0;
    for (double t : times) avg_time += t;
    avg_time /= times.size();

    // Output in CSV format for easy plotting
    cout << fixed << setprecision(3);
    cout << "MODE=" << mode << " N=" << N;
    if (mode == "omp") cout << " THREADS=" << threads;
    cout << " AVG_TIME=" << avg_time << " MIN=" << min_time 
         << " MAX=" << max_time << " GFLOPS=" << computeGFLOPS(N, avg_time) << "\n";

    // Show a sample for correctness verification
    if (N <= 16) {
        cout << "Output snippet (first 8x8 pixels):\n";
        for (int i=0;i<min(N,8);++i) {
            for (int j=0;j<min(N,8);++j) {
                cout << setw(3) << out[i*N+j] << " ";
            }
            cout << "\n";
        }
    }
    return 0;
}
