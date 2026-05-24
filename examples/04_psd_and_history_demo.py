"""
Example 04: Power Spectral Density (PSD) & History Controls Demo

This script demonstrates how to utilize the new real-time PSD View (Welch method)
and history buffer controls, both interactively through the GUI and programmatically.
It simulates an experimental data acquisition stream containing mixed sine waves and noise.
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
    print("      Power Spectral Density (PSD) & History Buffer Controls Demo")
    print("=" * 70)
    print("\nHow to use this demo:")
    print("1. Toggle 'PSD View' Checkbox:")
    print("   - Switches the view between the raw time domain and frequency spectrum.")
    print("   - In PSD View, you will clearly resolve two sharp frequency peaks at 10 Hz and 35 Hz!")
    print("2. Adjust 'FFT Window (nperseg)':")
    print("   - Change the segment window length to see its impact on frequency resolution.")
    print("   - Larger windows provide sharper peaks but require larger history sizes.")
    print("3. Adjust 'History (max_samples)':")
    print("   - Dynamically control the size of the rolling memory buffer kept on screen.")
    print("4. Persist States:")
    print("   - Change settings, click 'Save Layout' in the left Controls panel.")
    print("   - Close the app, restart it, and click 'Restore Layout' to restore the full UI state!")
    print("\nStarting the visualizer...")
    print("-" * 70)

    # 1. Initialize DockPlotManager
    manager = DockPlotManager("PSD and History Demo")

    # 2. Add an analyzer dock plot and initialize rolling append mode
    dock = manager.add_dock_plot("Signal Analyzer")
    dock.set_append_mode(max_samples=1000)

    # We can also configure these programmatically on initialization if we want:
    # dock.psd_cb.setChecked(False)
    # dock.nperseg_sb.setValue(256)
    # dock.history_sb.setValue(1000)

    # 3. Simulation setup: Feed composite signals (10 Hz + 35 Hz sines + white noise)
    timer = QtCore.QTimer()
    state = {'t': 0.0}
    sample_rate = 250.0  # Hz
    dt = 1.0 / sample_rate

    def update():
        t0 = state['t']
        t1 = t0 + 0.1  # 100ms chunk size
        num_points = int((t1 - t0) * sample_rate)
        
        # Time coordinates for the incoming chunk
        x = np.linspace(t0, t1, num_points, endpoint=False)
        
        # Composite signal: 10 Hz sine + 35 Hz sine + Gaussian noise
        y_signal = (
            1.5 * np.sin(2 * np.pi * 10 * x) + 
            1.0 * np.sin(2 * np.pi * 35 * x) + 
            np.random.normal(scale=0.8, size=len(x))
        )
        
        # Reference noise signal
        y_noise = np.random.normal(scale=0.8, size=len(x))
        
        # Stream both signals into our analyzer dock
        manager.add_data("Composite Signal (10Hz + 35Hz)", (x, y_signal), dock_name="Signal Analyzer")
        manager.add_data("Noise Floor", (x, y_noise), dock_name="Signal Analyzer")
        
        state['t'] = t1

    timer.timeout.connect(update)
    timer.start(50)  # Update every 50ms

    # Run the Qt event loop
    manager.app.exec()

if __name__ == "__main__":
    run_example()
