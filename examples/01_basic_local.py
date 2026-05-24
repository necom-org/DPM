"""
Example 01: Basic Local Usage

This script demonstrates how to create a DockPlotManager locally and add
some basic plots without using remote networking.
"""

import os
import sys
import numpy as np

# Add project root to path so we can import DPM
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DPM import DockPlotManager
import pyqtgraph as pg

def run_example():
    # 1. Create the manager. This opens the main window with a control dock and console.
    manager = DockPlotManager("Basic Local Example")

    # 2. Prepare some data
    x = np.linspace(0, 10, 1000)
    y1 = np.sin(x)
    y2 = np.cos(x)

    # 3. Add a dock with multiple curves
    # Docks are logical containers for one or more plots.
    manager.add_dock_plot(
        "Trigonometry", 
        curves={
            "Sine": (x, y1),
            "Cosine": (x, y2)
        },
        title="Sine and Cosine Waves"
    )

    # 4. Add another dock with a single curve
    y3 = np.exp(-x/5) * np.sin(2*x)
    manager.add_dock_plot("Damped", curves={"Damped Sine": (x, y3)})

    # 5. You can also add data to existing (or new) docks using add_data
    # If the dock doesn't exist, it will be created automatically.
    x2 = np.linspace(0, 10, 20)
    y4 = np.random.normal(size=20)
    manager.add_data("Random Points", (x2, y4), dock_name="Noise")

    print("DPM is running. You can interact with the plots and use the built-in console.")
    
    # Start the Qt event loop
    manager.app.exec()

if __name__ == "__main__":
    run_example()
