#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <cstring>
#include <iomanip>
#include <algorithm>
#include <mpi.h>

using namespace std;

// Structure for 2D domain decomposition
struct DomainConfig {
    int rank, world_size;
    int image_size;
    int grid_rows, grid_cols;
    int my_row, my_col;
    int local_rows, local_cols;
    int halo_size;
};

int clamp255(int v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

DomainConfig setup_domain(int image_size, int rank, int world_size) {
    DomainConfig config;
    config.rank = rank;
    config.world_size = world_size;
    config.image_size = image_size;
    config.halo_size = 1;
    
    int grid_dim = (int)sqrt(world_size);
    while (world_size % grid_dim != 0) grid_dim--;
    
    config.grid_rows = grid_dim;
    config.grid_cols = world_size / grid_dim;
    
    config.my_row = rank / config.grid_cols;
    config.my_col = rank % config.grid_cols;
    
    config.local_rows = image_size / config.grid_rows;
    config.local_cols = image_size / config.grid_cols;
    
    // Handle uneven division
    if (config.my_row == config.grid_rows - 1)
        config.local_rows = image_size - (config.grid_rows - 1) * config.local_rows;
    if (config.my_col == config.grid_cols - 1)
        config.local_cols = image_size - (config.grid_cols - 1) * config.local_cols;
    
    return config;
}

// Simple scatter: rank 0 sends image blocks to all ranks
void scatter_image(vector<int>& global_img, vector<int>& local_img,
                   const DomainConfig& config, int N) {
    int h = config.halo_size;
    
    if (config.rank == 0) {
        // Rank 0 distributes blocks
        for (int r = 0; r < config.world_size; ++r) {
            int dst_row = r / config.grid_cols;
            int dst_col = r % config.grid_cols;
            
            int start_row = dst_row * (N / config.grid_rows);
            int start_col = dst_col * (N / config.grid_cols);
            int rows = (dst_row == config.grid_rows - 1) ? 
                      (N - start_row) : (N / config.grid_rows);
            int cols = (dst_col == config.grid_cols - 1) ? 
                      (N - start_col) : (N / config.grid_cols);
            
            if (r == 0) {
                // Copy rank 0's portion (skip halo)
                for (int i = 0; i < rows; ++i) {
                    for (int j = 0; j < cols; ++j) {
                        local_img[(i + h) * (cols + 2*h) + (j + h)] = 
                            global_img[(start_row + i) * N + start_col + j];
                    }
                }
            } else {
                // Send to other ranks
                for (int i = 0; i < rows; ++i) {
                    MPI_Send(&global_img[(start_row + i) * N + start_col],
                            cols, MPI_INT, r, 0, MPI_COMM_WORLD);
                }
            }
        }
    } else {
        // Receive data
        for (int i = 0; i < config.local_rows; ++i) {
            int h = config.halo_size;
            MPI_Recv(&local_img[(i + h) * (config.local_cols + 2*h) + h],
                    config.local_cols, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
}

// Simple halo exchange with blocking sends/recvs for reliability
void exchange_halo_blocking(vector<int>& local_img, const DomainConfig& config) {
    int h = config.halo_size;
    int rows = config.local_rows;
    int cols = config.local_cols;
    int pitch = cols + 2*h;
    
    // Neighbors
    int north = (config.my_row > 0) ? config.rank - config.grid_cols : MPI_PROC_NULL;
    int south = (config.my_row < config.grid_rows - 1) ? 
                config.rank + config.grid_cols : MPI_PROC_NULL;
    int west = (config.my_col > 0) ? config.rank - 1 : MPI_PROC_NULL;
    int east = (config.my_col < config.grid_cols - 1) ? 
               config.rank + 1 : MPI_PROC_NULL;
    
    // Exchange North-South
    if (north != MPI_PROC_NULL) {
        MPI_Sendrecv(&local_img[h * pitch + h], cols, MPI_INT, north, 0,
                     &local_img[0 * pitch + h], cols, MPI_INT, north, 1,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    
    if (south != MPI_PROC_NULL) {
        MPI_Sendrecv(&local_img[(rows-1+h) * pitch + h], cols, MPI_INT, south, 1,
                     &local_img[(rows+h) * pitch + h], cols, MPI_INT, south, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    
    // Exchange East-West
    if (west != MPI_PROC_NULL) {
        for (int i = 0; i < rows; ++i) {
            int idx = (i + h) * pitch;
            MPI_Sendrecv(&local_img[idx + h], 1, MPI_INT, west, 2+i,
                        &local_img[idx], 1, MPI_INT, west, 2+rows+i,
                        MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }
    
    if (east != MPI_PROC_NULL) {
        for (int i = 0; i < rows; ++i) {
            int idx = (i + h) * pitch;
            MPI_Sendrecv(&local_img[idx + cols + h - 1], 1, MPI_INT, east, 2+rows+i,
                        &local_img[idx + cols + h], 1, MPI_INT, east, 2+i,
                        MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }
}

// Compute Sobel on local domain
void compute_sobel_local(vector<int>& local_img, vector<int>& output_img,
                         const DomainConfig& config) {
    int h = config.halo_size;
    int rows = config.local_rows;
    int cols = config.local_cols;
    int pitch = cols + 2*h;
    
    // Sobel kernels
    int gx[3][3] = {{-1, 0, 1}, {-2, 0, 2}, {-1, 0, 1}};
    int gy[3][3] = {{-1, -2, -1}, {0, 0, 0}, {1, 2, 1}};
    
    for (int i = h; i < rows + h; ++i) {
        for (int j = h; j < cols + h; ++j) {
            int gx_val = 0, gy_val = 0;
            
            for (int di = -1; di <= 1; ++di) {
                for (int dj = -1; dj <= 1; ++dj) {
                    int pixel = local_img[(i + di) * pitch + (j + dj)];
                    gx_val += gx[di+1][dj+1] * pixel;
                    gy_val += gy[di+1][dj+1] * pixel;
                }
            }
            
            int mag = (int)sqrt(gx_val * gx_val + gy_val * gy_val);
            output_img[(i-h) * cols + (j-h)] = clamp255(mag);
        }
    }
}

// Gather results back to rank 0
void gather_image(vector<int>& local_img, vector<int>& global_img,
                  const DomainConfig& config, int N) {
    if (config.rank == 0) {
        for (int r = 0; r < config.world_size; ++r) {
            int dst_row = r / config.grid_cols;
            int dst_col = r % config.grid_cols;
            
            int start_row = dst_row * (N / config.grid_rows);
            int start_col = dst_col * (N / config.grid_cols);
            int rows = (dst_row == config.grid_rows - 1) ? 
                      (N - start_row) : (N / config.grid_rows);
            int cols = (dst_col == config.grid_cols - 1) ? 
                      (N - start_col) : (N / config.grid_cols);
            
            if (r == 0) {
                // Copy my data
                for (int i = 0; i < rows; ++i) {
                    for (int j = 0; j < cols; ++j) {
                        global_img[(start_row + i) * N + start_col + j] = 
                            local_img[i * cols + j];
                    }
                }
            } else {
                // Receive from other ranks
                for (int i = 0; i < rows; ++i) {
                    MPI_Recv(&global_img[(start_row + i) * N + start_col],
                            cols, MPI_INT, r, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                }
            }
        }
    } else {
        // Send results back
        for (int i = 0; i < config.local_rows; ++i) {
            MPI_Send(&local_img[i * config.local_cols],
                    config.local_cols, MPI_INT, 0, 0, MPI_COMM_WORLD);
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    
    int N = (argc > 1) ? atoi(argv[1]) : 512;
    int num_runs = (argc > 2) ? atoi(argv[2]) : 1;
    
    if (rank == 0) {
        cout << "MPI Sobel Edge Detection\n";
        cout << "Image Size: " << N << "x" << N << "\n";
        cout << "MPI Ranks: " << world_size << "\n";
        cout << "Runs: " << num_runs << "\n\n";
    }
    
    DomainConfig config = setup_domain(N, rank, world_size);
    
    if (rank == 0) {
        cout << "Domain Grid: " << config.grid_rows << "x" << config.grid_cols << "\n";
        cout << "Local size (avg): " << N/config.grid_rows << "x" 
             << N/config.grid_cols << "\n";
        cout << "Halo size: " << config.halo_size << "\n\n";
    }
    
    // Allocate local image with halo
    int h = config.halo_size;
    vector<int> local_img((config.local_rows + 2*h) * (config.local_cols + 2*h), 0);
    vector<int> output_img(config.local_rows * config.local_cols, 0);
    
    // Allocate global image (rank 0 only)
    vector<int> global_img(N * N);
    if (rank == 0) {
        for (int i = 0; i < N * N; ++i) {
            global_img[i] = (i % 256);
        }
    }
    
    double total_time = 0;
    double total_comm_time = 0;
    
    for (int run = 0; run < num_runs; ++run) {
        double start = MPI_Wtime();
        
        // Scatter
        scatter_image(global_img, local_img, config, N);
        
        double comm_start = MPI_Wtime();
        exchange_halo_blocking(local_img, config);
        double comm_end = MPI_Wtime();
        total_comm_time += (comm_end - comm_start);
        
        // Compute
        compute_sobel_local(local_img, output_img, config);
        
        // Gather (only rank 0 needs global result for timing)
        gather_image(output_img, global_img, config, N);
        
        double end = MPI_Wtime();
        total_time += (end - start);
    }
    
    if (rank == 0) {
        double avg_time = (total_time / num_runs) * 1000.0;
        cout << "RANKS=" << world_size << " SIZE=" << N << " RUNS=" << num_runs
             << " AVG_TIME=" << fixed << setprecision(3) << avg_time << " ms\n";
    }
    
    MPI_Finalize();
    return 0;
}
