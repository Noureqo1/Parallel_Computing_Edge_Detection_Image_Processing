#!/usr/bin/env python3
"""
Phase 2 Performance Analysis
Analyzes strong scaling, weak scaling, and latency/bandwidth results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

def load_scaling_results(csv_file):
    """Load scaling benchmark results"""
    if not os.path.exists(csv_file):
        print(f"Warning: {csv_file} not found")
        return None
    return pd.read_csv(csv_file)

def plot_strong_scaling(df):
    """Generate strong scaling plot"""
    if df is None or df.empty:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Speedup vs Processes
    for size in df['IMAGE_SIZE'].unique():
        size_data = df[df['IMAGE_SIZE'] == size].sort_values('PROCESSES')
        ax1.plot(size_data['PROCESSES'], size_data['SPEEDUP'], 
                marker='o', linewidth=2, markersize=8, label=f'N={size}')
    
    # Ideal speedup line
    processes = sorted(df['PROCESSES'].unique())
    ax1.plot(processes, processes, 'k--', linewidth=2, label='Ideal', alpha=0.7)
    
    ax1.set_xlabel('Number of Processes', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Speedup', fontsize=11, fontweight='bold')
    ax1.set_title('Strong Scaling: Speedup vs Processes', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_xticks(processes)
    
    # Plot 2: Efficiency vs Processes
    for size in df['IMAGE_SIZE'].unique():
        size_data = df[df['IMAGE_SIZE'] == size].sort_values('PROCESSES')
        ax2.plot(size_data['PROCESSES'], size_data['EFFICIENCY'], 
                marker='s', linewidth=2, markersize=8, label=f'N={size}')
    
    # Ideal efficiency
    ax2.axhline(y=1.0, color='k', linestyle='--', linewidth=2, label='Ideal', alpha=0.7)
    ax2.axhline(y=0.8, color='r', linestyle=':', linewidth=1.5, alpha=0.5)
    
    ax2.set_xlabel('Number of Processes', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Efficiency (Speedup / Processes)', fontsize=11, fontweight='bold')
    ax2.set_title('Strong Scaling: Parallel Efficiency', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_xticks(processes)
    ax2.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig('plots/strong_scaling.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/strong_scaling.png")

def plot_weak_scaling(df):
    """Generate weak scaling plot"""
    if df is None or df.empty:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Prepare data
    df_sorted = df.sort_values('PROCESSES')
    baseline_time = df_sorted.iloc[0]['AVG_TIME_MS']
    
    # Plot 1: Execution time vs Processes
    ax1.plot(df_sorted['PROCESSES'], df_sorted['AVG_TIME_MS'], 
            marker='o', linewidth=2, markersize=10, color='blue', label='Measured')
    ax1.axhline(y=baseline_time, color='k', linestyle='--', linewidth=2, 
                label='Baseline (1 process)', alpha=0.7)
    
    ax1.set_xlabel('Number of Processes', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold')
    ax1.set_title('Weak Scaling: Execution Time vs Processes', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_xticks(sorted(df['PROCESSES'].unique()))
    
    # Plot 2: Efficiency vs Processes
    ax2.plot(df_sorted['PROCESSES'], df_sorted['EFFICIENCY'], 
            marker='s', linewidth=2, markersize=10, color='green', label='Measured')
    ax2.axhline(y=1.0, color='k', linestyle='--', linewidth=2, label='Ideal', alpha=0.7)
    ax2.axhline(y=0.8, color='r', linestyle=':', linewidth=1.5, alpha=0.5)
    
    ax2.set_xlabel('Number of Processes', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Efficiency (Baseline Time / Time)', fontsize=11, fontweight='bold')
    ax2.set_title('Weak Scaling: Parallel Efficiency', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_xticks(sorted(df['PROCESSES'].unique()))
    ax2.set_ylim([0.5, 1.2])
    
    plt.tight_layout()
    plt.savefig('plots/weak_scaling.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/weak_scaling.png")

def analyze_latency_bandwidth():
    """Analyze latency/bandwidth results"""
    if not os.path.exists('latency_bandwidth_results.txt'):
        print("Warning: latency_bandwidth_results.txt not found")
        return
    
    # Parse results manually
    latencies = []
    bandwidths = []
    sizes = []
    
    try:
        with open('latency_bandwidth_results.txt', 'r') as f:
            for line in f:
                # Skip header and separator lines
                if '=' in line or 'Message' in line or 'Benchmark' in line or \
                   'World' in line or line.strip() == '':
                    continue
                
                # Parse numeric lines
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        size = int(parts[0])
                        lat = float(parts[1])
                        bw = float(parts[2])
                        sizes.append(size)
                        latencies.append(lat)
                        bandwidths.append(bw)
                    except ValueError:
                        pass
    except FileNotFoundError:
        return
    
    if not sizes:
        return
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Latency plot
    ax1.loglog(sizes, latencies, 'o-', linewidth=2, markersize=8, color='red')
    ax1.set_xlabel('Message Size (Bytes)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Latency (μs)', fontsize=11, fontweight='bold')
    ax1.set_title('Point-to-Point Latency', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    
    # Bandwidth plot
    ax2.semilogx(sizes, bandwidths, 's-', linewidth=2, markersize=8, color='blue')
    ax2.set_xlabel('Message Size (Bytes)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Bandwidth (MB/s)', fontsize=11, fontweight='bold')
    ax2.set_title('Point-to-Point Bandwidth', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, which='both')
    
    plt.tight_layout()
    plt.savefig('plots/latency_bandwidth.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/latency_bandwidth.png")

def print_analysis_summary():
    """Print summary of analysis"""
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    # Strong scaling analysis
    if os.path.exists('strong_scaling_results.csv'):
        df = pd.read_csv('strong_scaling_results.csv')
        print("\nStrong Scaling Results:")
        print("-" * 80)
        print(df.to_string(index=False))
    
    # Weak scaling analysis
    if os.path.exists('weak_scaling_results.csv'):
        df = pd.read_csv('weak_scaling_results.csv')
        print("\nWeak Scaling Results:")
        print("-" * 80)
        print(df.to_string(index=False))
    
    print("\n" + "="*80)

def main():
    print("Phase 2 Performance Analysis\n")
    
    # Create plots directory
    os.makedirs('plots', exist_ok=True)
    
    # Load and analyze results
    print("Generating visualizations...")
    
    strong_df = load_scaling_results('strong_scaling_results.csv')
    if strong_df is not None:
        plot_strong_scaling(strong_df)
    
    weak_df = load_scaling_results('weak_scaling_results.csv')
    if weak_df is not None:
        plot_weak_scaling(weak_df)
    
    analyze_latency_bandwidth()
    
    print_analysis_summary()
    
    print("\n✓ Analysis complete! Check plots/ directory for visualizations.")

if __name__ == "__main__":
    main()
