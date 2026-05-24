"""
Example 02: Live Updates with Append Mode

This script demonstrates how to update plots in real-time. It uses
'append mode' to keep a rolling buffer of incoming data.
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
    manager = DockPlotManager("Live Updates Example")

    # 1. Create a plot and set it to append mode.
    # We specify a max_samples limit to keep only the most recent data.
    dock = manager.add_dock_plot("Live Stream")
    dock.set_append_mode(max_samples=500)

    # 2. Set up a timer to simulate incoming data chunks
    timer = QtCore.QTimer()
    
    # We'll keep track of our "internal clock" for the simulation
    state = {'t': 0}

    def update():
        t0 = state['t']
        t1 = t0 + 0.1
        x = np.linspace(t0, t1, 10)
        y = np.sin(2 * np.pi * 0.5 * x) + np.random.normal(scale=0.1, size=len(x))
        
        # add_data will find the curve in "Live Stream" and append to it
        manager.add_data("Noisy Sine", (x, y), dock_name="Live Stream")
        
        state['t'] = t1

    timer.timeout.connect(update)
    timer.start(50) # Update every 50ms

    print("Live update simulation started.")
    manager.app.exec()

if __name__ == "__main__":
    run_example()
