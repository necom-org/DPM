"""
Example 03: Remote Data Receiver

This script starts a DPM instance that listens for data on ZMQ.
Run this BEFORE starting 03_remote_sender.py.
"""

import os
import sys

# Add project root to path so we can import DPM modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DPM_listener import DPMListener
import pyqtgraph as pg

def run_receiver():
    # 1. Create a listener. 
    # It will automatically create a DockPlotManager if one isn't provided.
    # It subscribes to the 'my_experiment' topic.
    listener = DPMListener(subName="my_experiment")
    
    # 2. Start the update timer (internal to the listener)
    listener.start_updating(50) # check for new data every 50ms

    print("Receiver is active and listening for 'my_experiment'...")
    
    # 3. Start the Qt event loop
    pg.mkQApp().exec()

if __name__ == "__main__":
    run_receiver()
