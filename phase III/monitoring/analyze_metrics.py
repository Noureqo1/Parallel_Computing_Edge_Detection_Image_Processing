"""
Analyze load test results and generate time-series visualizations.
"""

import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict


def load_test_results(log_file: str) -> dict:
    """Load test results from JSON log file."""
    with open(log_file, 'r') as f:
        return json.load(f)


def calculate_windowed_metrics(requests: List[dict], window_size: float = 1.0):
    """
    Calculate metrics in time windows.
    
    Args:
        requests: List of request log entries
        window_size: Window size in seconds
    
    Returns:
        Dictionary with time-series metrics
    """
    if not requests:
        return {}
    
    # Get start time
    start_time = requests[0]['timestamp']
    end_time = requests[-1]['timestamp']
    duration = end_time - start_time
    
    # Create time windows
    num_windows = int(duration / window_size) + 1
    windows = []
    
    for i in range(num_windows):
        window_start = start_time + i * window_size
        window_end = window_start + window_size
        
        # Filter requests in this window
        window_requests = [r for r in requests 
                          if window_start <= r['timestamp'] < window_end]
        
        if not window_requests:
            windows.append({
                'time': window_start - start_time,
                'throughput': 0,
                'latency_avg': 0,
                'latency_p95': 0,
                'success_count': 0,
                'failure_count': 0
            })
            continue
        
        # Calculate metrics
        successful = [r for r in window_requests if r['success']]
        failed = [r for r in window_requests if not r['success']]
        
        latencies = [r['latency_ms'] for r in successful]
        latencies.sort()
        
        windows.append({
            'time': window_start - start_time,
            'throughput': len(window_requests) / window_size,
            'latency_avg': np.mean(latencies) if latencies else 0,
            'latency_p95': latencies[int(len(latencies) * 0.95)] if latencies else 0,
            'success_count': len(successful),
            'failure_count': len(failed)
        })
    
    return windows


def detect_failure_events(requests: List[dict], window_size: float = 2.0) -> List[dict]:
    """
    Detect failure events (spikes in errors or latency).
    
    Returns:
        List of detected events with timestamps
    """
    windows = calculate_windowed_metrics(requests, window_size)
    events = []
    
    for i, window in enumerate(windows):
        # Detect error spike
        if window['failure_count'] > 5:
            events.append({
                'time': window['time'],
                'type': 'error_spike',
                'description': f"{window['failure_count']} failures"
            })
        
        # Detect latency spike (compare to baseline)
        if i > 5:
            baseline_latencies = [w['latency_p95'] for w in windows[max(0,i-5):i] 
                                 if w['latency_p95'] > 0]
            if baseline_latencies:
                baseline_avg = np.mean(baseline_latencies)
                if window['latency_p95'] > baseline_avg * 2 and window['latency_p95'] > 100:
                    events.append({
                        'time': window['time'],
                        'type': 'latency_spike',
                        'description': f"p95 latency: {window['latency_p95']:.1f}ms"
                    })
    
    return events


def plot_time_series(windows: List[dict], events: List[dict], output_prefix: str):
    """Generate time-series plots with failure annotations."""
    
    times = [w['time'] for w in windows]
    throughputs = [w['throughput'] for w in windows]
    latency_avgs = [w['latency_avg'] for w in windows]
    latency_p95s = [w['latency_p95'] for w in windows]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Throughput over time
    ax1.plot(times, throughputs, 'b-', linewidth=2, label='Throughput')
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Throughput (req/sec)', fontsize=12)
    ax1.set_title('System Throughput Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add failure annotations to throughput plot
    for event in events:
        ax1.axvline(x=event['time'], color='red', linestyle='--', alpha=0.6)
        ax1.text(event['time'], max(throughputs) * 0.9, 
                event['type'].replace('_', ' ').title(),
                rotation=90, verticalalignment='bottom',
                fontsize=9, color='red')
    
    # Plot 2: Latency over time
    ax2.plot(times, latency_avgs, 'g-', linewidth=2, label='Average Latency', alpha=0.7)
    ax2.plot(times, latency_p95s, 'r-', linewidth=2, label='p95 Latency')
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Latency (ms)', fontsize=12)
    ax2.set_title('Request Latency Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add failure annotations to latency plot
    for event in events:
        ax2.axvline(x=event['time'], color='red', linestyle='--', alpha=0.6)
        ax2.text(event['time'], max(latency_p95s) * 0.9,
                event['description'],
                rotation=90, verticalalignment='bottom',
                fontsize=9, color='red')
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_timeseries.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_prefix}_timeseries.png")
    plt.close()
    
    # Create separate focused plots
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(times, throughputs, 'b-', linewidth=2.5)
    ax.set_xlabel('Time (seconds)', fontsize=13)
    ax.set_ylabel('Throughput (requests/second)', fontsize=13)
    ax.set_title('System Throughput with Failure Events', fontsize=15, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    for event in events:
        ax.axvline(x=event['time'], color='red', linestyle='--', linewidth=2, alpha=0.7)
        ax.annotate(f"Failure: {event['type']}", 
                   xy=(event['time'], max(throughputs) * 0.8),
                   xytext=(event['time'] + 2, max(throughputs) * 0.85),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                   fontsize=10, color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_throughput.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_prefix}_throughput.png")
    plt.close()


def calculate_recovery_time(windows: List[dict], failure_event_time: float,
                            metric: str = 'throughput') -> float:
    """
    Calculate time to recover after a failure.
    
    Args:
        windows: Windowed metrics
        failure_event_time: Time of failure event
        metric: Metric to track for recovery ('throughput' or 'latency_p95')
    
    Returns:
        Recovery time in seconds
    """
    # Find baseline before failure (average of last 10 windows before failure)
    baseline_windows = [w for w in windows if w['time'] < failure_event_time - 10]
    if not baseline_windows:
        return 0
    
    baseline_windows = baseline_windows[-10:]
    baseline_value = np.mean([w[metric] for w in baseline_windows])
    
    # Find when metric returns to within 10% of baseline
    recovery_threshold = baseline_value * 0.9 if metric == 'throughput' else baseline_value * 1.1
    
    post_failure_windows = [w for w in windows if w['time'] > failure_event_time]
    
    for window in post_failure_windows:
        if metric == 'throughput' and window[metric] >= recovery_threshold:
            return window['time'] - failure_event_time
        elif metric == 'latency_p95' and window[metric] <= recovery_threshold:
            return window['time'] - failure_event_time
    
    return -1  # Did not recover


def generate_summary_report(data: dict, windows: List[dict], events: List[dict],
                           output_file: str):
    """Generate a text summary report."""
    with open(output_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("LOAD TEST ANALYSIS REPORT\n")
        f.write("="*70 + "\n\n")
        
        # Metadata
        metadata = data['metadata']
        f.write("Test Configuration:\n")
        f.write(f"  Duration: {metadata['duration_seconds']:.2f} seconds\n")
        f.write(f"  Target Rate: {metadata['target_rate']:.2f} req/sec\n")
        f.write(f"  Actual Rate: {metadata['actual_rate']:.2f} req/sec\n")
        f.write(f"  Total Requests: {metadata['total_requests']}\n")
        f.write(f"  Servers: {', '.join(metadata['servers'])}\n\n")
        
        # Client stats
        stats = data['client_stats']
        f.write("Overall Statistics:\n")
        f.write(f"  Successful Requests: {stats['successful_requests']}\n")
        f.write(f"  Failed Requests: {stats['failed_requests']}\n")
        f.write(f"  Success Rate: {stats['success_rate']*100:.2f}%\n")
        f.write(f"  Total Retries: {stats['retries_count']}\n")
        f.write(f"  Failover Count: {stats['failover_count']}\n\n")
        
        # Latency analysis
        successful_requests = [r for r in data['requests'] if r['success']]
        latencies = [r['latency_ms'] for r in successful_requests]
        latencies.sort()
        
        if latencies:
            f.write("Latency Distribution:\n")
            f.write(f"  Min: {min(latencies):.2f} ms\n")
            f.write(f"  p50 (Median): {latencies[int(len(latencies)*0.50)]:.2f} ms\n")
            f.write(f"  p95: {latencies[int(len(latencies)*0.95)]:.2f} ms\n")
            f.write(f"  p99: {latencies[int(len(latencies)*0.99)]:.2f} ms\n")
            f.write(f"  Max: {max(latencies):.2f} ms\n")
            f.write(f"  Average: {np.mean(latencies):.2f} ms\n\n")
        
        # Detected events
        f.write(f"Detected Failure Events: {len(events)}\n")
        for i, event in enumerate(events, 1):
            f.write(f"  {i}. Time: {event['time']:.1f}s - "
                   f"{event['type']}: {event['description']}\n")
        f.write("\n")
        
        # Recovery analysis
        if events:
            f.write("Recovery Time Analysis:\n")
            for event in events[:3]:  # Analyze first 3 events
                recovery_time = calculate_recovery_time(windows, event['time'], 'throughput')
                if recovery_time > 0:
                    f.write(f"  Event at {event['time']:.1f}s: "
                           f"Recovered in {recovery_time:.2f} seconds\n")
                else:
                    f.write(f"  Event at {event['time']:.1f}s: "
                           f"Did not fully recover\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"Saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze Sobel Service Load Test Results')
    parser.add_argument('--log', type=str, required=True,
                       help='Path to load test JSON log file')
    parser.add_argument('--output', type=str, default='analysis',
                       help='Output file prefix (default: analysis)')
    parser.add_argument('--window', type=float, default=1.0,
                       help='Time window for metrics (seconds, default: 1.0)')
    
    args = parser.parse_args()
    
    print(f"Loading results from: {args.log}")
    data = load_test_results(args.log)
    
    print("Calculating windowed metrics...")
    windows = calculate_windowed_metrics(data['requests'], args.window)
    
    print("Detecting failure events...")
    events = detect_failure_events(data['requests'], window_size=2.0)
    print(f"  Found {len(events)} failure events")
    
    print("Generating plots...")
    plot_time_series(windows, events, args.output)
    
    print("Generating summary report...")
    generate_summary_report(data, windows, events, f'{args.output}_report.txt')
    
    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()
