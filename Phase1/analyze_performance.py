#!/usr/bin/env python3
"""
Performance Analysis and Visualization for Phase 1
Generates Speedup and Efficiency plots required for the report
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

def load_results(csv_file):
    """Load benchmark results from CSV"""
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Run benchmark.sh first.")
        sys.exit(1)
    return pd.read_csv(csv_file)

def compute_metrics(df):
    """Compute Speedup and Efficiency"""
    results = []
    
    for size in df['IMAGE_SIZE'].unique():
        size_data = df[df['IMAGE_SIZE'] == size].copy()
        
        # Get sequential baseline time
        seq_time = size_data[size_data['MODE'] == 'SEQ']['AVG_TIME_MS'].values[0]
        
        for _, row in size_data[size_data['MODE'] == 'OMP'].iterrows():
            parallel_time = row['AVG_TIME_MS']
            threads = int(row['THREADS'])
            
            speedup = seq_time / parallel_time
            efficiency = speedup / threads
            
            results.append({
                'IMAGE_SIZE': size,
                'THREADS': threads,
                'SEQ_TIME': seq_time,
                'PARALLEL_TIME': parallel_time,
                'SPEEDUP': speedup,
                'EFFICIENCY': efficiency,
                'GFLOPS': row['GFLOPS']
            })
    
    return pd.DataFrame(results)

def plot_speedup(metrics):
    """Generate Speedup vs Threads plot"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for size in metrics['IMAGE_SIZE'].unique():
        size_data = metrics[metrics['IMAGE_SIZE'] == size].sort_values('THREADS')
        ax.plot(size_data['THREADS'], size_data['SPEEDUP'], 
                marker='o', linewidth=2, markersize=8, label=f'N={size}')
    
    # Ideal speedup line (Amdahl limit)
    threads = np.array([1, 2, 4, 8])
    ax.plot(threads, threads, 'k--', linewidth=2, label='Ideal (Linear Scaling)', alpha=0.7)
    
    ax.set_xlabel('Number of Threads', fontsize=12, fontweight='bold')
    ax.set_ylabel('Speedup (S = T_seq / T_parallel)', fontsize=12, fontweight='bold')
    ax.set_title('Speedup vs Number of Threads\n(Parallel Sobel Edge Detection)', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    ax.set_xticks([1, 2, 4, 8])
    
    plt.tight_layout()
    plt.savefig('plots/speedup_vs_threads.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/speedup_vs_threads.png")

def plot_efficiency(metrics):
    """Generate Efficiency vs Threads plot"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for size in metrics['IMAGE_SIZE'].unique():
        size_data = metrics[metrics['IMAGE_SIZE'] == size].sort_values('THREADS')
        ax.plot(size_data['THREADS'], size_data['EFFICIENCY'], 
                marker='s', linewidth=2, markersize=8, label=f'N={size}')
    
    # Ideal efficiency line (100%)
    threads = np.array([1, 2, 4, 8])
    ax.axhline(y=1.0, color='k', linestyle='--', linewidth=2, label='Ideal (100%)', alpha=0.7)
    ax.axhline(y=0.8, color='r', linestyle=':', linewidth=1.5, label='80% threshold', alpha=0.5)
    
    ax.set_xlabel('Number of Threads', fontsize=12, fontweight='bold')
    ax.set_ylabel('Efficiency (E = Speedup / Threads)', fontsize=12, fontweight='bold')
    ax.set_title('Parallel Efficiency vs Number of Threads\n(Parallel Sobel Edge Detection)', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    ax.set_xticks([1, 2, 4, 8])
    ax.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig('plots/efficiency_vs_threads.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/efficiency_vs_threads.png")

def plot_scaling_analysis(metrics):
    """Generate strong and weak scaling plot"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Strong Scaling (fixed image size, varying threads)
    for size in metrics['IMAGE_SIZE'].unique():
        size_data = metrics[metrics['IMAGE_SIZE'] == size].sort_values('THREADS')
        ax1.plot(size_data['THREADS'], size_data['PARALLEL_TIME'], 
                marker='o', linewidth=2, markersize=8, label=f'N={size}')
    
    ax1.set_xlabel('Number of Threads', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('Strong Scaling\n(Fixed Problem Size)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_xticks([1, 2, 4, 8])
    
    # Execution time vs Image size (different thread counts)
    sizes = sorted(metrics['IMAGE_SIZE'].unique())
    for threads in [1, 2, 4, 8]:
        thread_data = metrics[metrics['THREADS'] == threads].sort_values('IMAGE_SIZE')
        if len(thread_data) > 0:
            ax2.plot(thread_data['IMAGE_SIZE'], thread_data['PARALLEL_TIME'],
                    marker='s', linewidth=2, markersize=8, label=f'{threads} threads')
    
    ax2.set_xlabel('Image Size (N x N)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('Execution Time vs Problem Size\n(Various Thread Counts)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('plots/scaling_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/scaling_analysis.png")

def generate_report_table(metrics):
    """Generate performance table for report"""
    print("\n" + "="*80)
    print("Performance Summary Table")
    print("="*80)
    
    for size in sorted(metrics['IMAGE_SIZE'].unique()):
        print(f"\nImage Size: {size}x{size}")
        print("-" * 70)
        size_data = metrics[metrics['IMAGE_SIZE'] == size].sort_values('THREADS')
        
        print(f"{'Threads':<10} {'Time(ms)':<12} {'Speedup':<12} {'Efficiency':<12} {'GFLOPS':<10}")
        print("-" * 70)
        
        for _, row in size_data.iterrows():
            threads = int(row['THREADS'])
            time_ms = row['PARALLEL_TIME']
            speedup = row['SPEEDUP']
            efficiency = row['EFFICIENCY']
            gflops = row['GFLOPS']
            
            print(f"{threads:<10} {time_ms:<12.3f} {speedup:<12.3f} {efficiency:<12.3f} {gflops:<10.2f}")

def main():
    print("Performance Analysis for Phase 1\n")
    
    # Create plots directory if needed
    os.makedirs('plots', exist_ok=True)
    
    # Load and analyze results
    df = load_results('benchmark_results.csv')
    metrics = compute_metrics(df)
    
    # Generate visualizations
    print("Generating plots...")
    plot_speedup(metrics)
    plot_efficiency(metrics)
    plot_scaling_analysis(metrics)
    
    # Generate report table
    generate_report_table(metrics)
    
    # Save metrics to CSV for report
    metrics.to_csv('plots/performance_metrics.csv', index=False)
    print("\n✓ Saved: plots/performance_metrics.csv")
    
    print("\n" + "="*80)
    print("Analysis complete! Check plots/ directory for visualization files.")
    print("="*80)

if __name__ == "__main__":
    main()
