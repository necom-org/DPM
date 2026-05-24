"""
Example 03: Remote Data Sender

This script simulates an experiment generating data in a separate process.
It sends this data over ZMQ to a DPM Listener.

Run this AFTER starting 03_remote_receiver.py.
"""

import os
import sys
import time
import numpy as np

# Add project root to path so we can import DPM modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DPM_sender import DPMSender

def run_sender():
    # 1. Create a sender. 
    # 'my_experiment' is the category/topic prefix we'll use.
    sender = DPMSender(pubName="my_experiment")
    
    print("Sender started. Publishing data...")
    
    x = np.linspace(0, 10, 100)
    k = 0
    try:
        while True:
            # Generate some dummy data
            y = np.sin(x + k*0.1) + np.random.normal(scale=0.05, size=len(x))
            
            # 2. Publish traces. 
            # In the receiver, this will show up in a dock named 'my_experiment'
            # under the curve label 'oscillator_1'.
            sender.pub_traces("oscillator_1", y, x=x)
            
            # Send another curve periodically
            if k % 10 == 0:
                sender.pub_points("status_val", [np.random.random()], x=[time.time()])
            
            k += 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Sender stopped.")
    finally:
        sender.close()

if __name__ == "__main__":
    run_sender()
