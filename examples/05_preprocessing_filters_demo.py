"""
Example 05: Real-Time Preprocessing Hooks & Stateful Filtering

This script demonstrates how to utilize DPM's new real-time preprocessing hooks (filters)
to perform live single-channel smoothing, stateful cross-channel subtraction,
and dynamic virtual curve generation.

Run this script to open the DPM visualizer with three live plots showing these pipelines.
"""

import os
import sys
import numpy as np

# Add project root to path so we can import DPM
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DPM import DockPlotManager
import pyqtgraph as pg
from PyQt6 import QtCore

def run_example():
    print("=" * 70)
    print("      Real-Time Preprocessing Hooks & Stateful Filters Demo")
    print("=" * 70)
    print("\nPre-configured pipelines running in this demo:")
    print("1. Multi-Channel State Sharing (Real-Time Subtraction):")
    print("   - 'Composite Noisy Signal' dynamically subtracts the raw 'Reference Noise'!")
    print("   - The resulting differential signal is plotted as 'Subtracted Clean Signal'.")
    print("2. Dynamic Virtual Channel Generation (Moving Average):")
    print("   - The raw noisy signal passes through a 9-point rolling mean filter.")
    print("   - The filtered result is dynamically plotted on the fly as 'Smoothed Waveform'.")
    print("\nOpening the visualizer and starting the simulation...")
    print("-" * 70)

    # 1. Initialize DockPlotManager
    manager = DockPlotManager("Preprocessing Filters Demo")

    # 2. Add an analyzer dock plot and initialize rolling append mode
    dock = manager.add_dock_plot("Signal Processor")
    dock.set_append_mode(max_samples=1000)

    # 3. Define a Stateful Cross-Channel Subtraction Filter
    class CrossChannelFilter:
        def __init__(self):
            self.last_ref_y = None  # Cache for reference noise data

        def process_reference(self, x, y):
            # Cache the latest reference noise chunk
            self.last_ref_y = y
            return x, y

        def process_signal(self, x, y):
            # Subtract the reference noise from the composite signal in real-time
            if self.last_ref_y is not None:
                min_len = min(len(y), len(self.last_ref_y))
                y_clean = y[:min_len] - self.last_ref_y[:min_len]
                
                # Push the derived signal to a new 'Cleaned Signal' curve!
                manager.add_data("Subtracted Clean Signal", (x[:min_len], y_clean), dock_name="Signal Processor")
            return x, y

    cc_filter = CrossChannelFilter()

    # 4. Define a Virtual Moving Average Channel Filter
    def virtual_moving_average_filter(x, y):
        # Apply a 9-point rolling mean smoothing
        window = 9
        y_smooth = np.convolve(y, np.ones(window)/window, mode='same')
        
        # Dynamically push to a virtual curve
        manager.add_data("Smoothed Waveform", (x, y_smooth), dock_name="Signal Processor")
        return x, y

    # 5. Register the filters on the manager
    # 'Composite Noisy Signal' gets both subtraction processing and moving average!
    manager.add_filter("Reference Noise", cc_filter.process_reference)
    manager.add_filter("Composite Noisy Signal", cc_filter.process_signal)
    manager.add_filter("Composite Noisy Signal", virtual_moving_average_filter)

    # 6. Simulation setup: Feed raw signals (10 Hz sine + noise)
    timer = QtCore.QTimer()
    state = {'t': 0.0}
    sample_rate = 250.0  # Hz

    def update():
        t0 = state['t']
        t1 = t0 + 0.1  # 100ms chunk
        num_points = int((t1 - t0) * sample_rate)
        
        x = np.linspace(t0, t1, num_points, endpoint=False)
        
        # Raw reference noise
        y_noise = np.random.normal(scale=0.6, size=len(x))
        
        # Raw noisy composite signal (10 Hz pure sine + reference noise)
        y_sine = 1.5 * np.sin(2 * np.pi * 10 * x)
        y_signal = y_sine + y_noise
        
        # Stream raw data in. The registered filters will intercept and process them.
        manager.add_data("Reference Noise", (x, y_noise), dock_name="Signal Processor")
        manager.add_data("Composite Noisy Signal", (x, y_signal), dock_name="Signal Processor")
        
        state['t'] = t1

    timer.timeout.connect(update)
    timer.start(50)  # Update every 50ms

    # Start event loop
    manager.app.exec()

if __name__ == "__main__":
    run_example()
