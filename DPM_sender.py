""" DPM Sender: A client for sending trace data to a DPM instance via ZMQ.
"""

import pickle
from typing import Any, Optional, Union
import zmq

PORT = 5561

class DPMSender:
    """Sends trace data to DPM via ZMQ PUB/SUB."""
    
    def __init__(self, pubName: Union[str, bytes] = b"default", port: int = PORT) -> None:
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PUB)
        self.sock.set_hwm(10)
        self.sock.bind(f"tcp://*:{port}")
        
        # Ensure pubName is bytes
        if isinstance(pubName, str):
            pubName = pubName.encode('utf-8')
        self.pubName = pubName

    def _send_data(
        self, 
        name: Union[str, bytes], 
        data: Any, 
        coords: Any = None, 
        data_type: str = 'traces',
        mode: Optional[str] = None,
        max_samples: Optional[int] = None
    ) -> None:
        """Internal method to send formatted data."""
        if isinstance(name, str):
            name = name.encode('utf-8')
            
        payload = {
            "name": name,
            "data": data,
            "coords": coords,
            "type": data_type,
            "mode": mode,
            "max_samples": max_samples
        }
        
        # Topic format: "category:label"
        topic = b"%s:%s " % (self.pubName, name)
        msg = topic + pickle.dumps(payload)
        self.sock.send(msg)

    def pub_points(
        self, 
        name: Union[str, bytes], 
        y: Any, 
        x: Any = None, 
        mode: str = 'append', 
        max_samples: int = 1000
    ) -> None:
        """Sends data points to be plotted, defaulting to append mode."""
        self._send_data(name, y, coords=x, data_type='points', mode=mode, max_samples=max_samples)

    def pub_traces(
        self, 
        name: Union[str, bytes], 
        y: Any, 
        x: Any = None, 
        mode: str = 'replace', 
        max_samples: Optional[int] = None
    ) -> None:
        """Sends trace data to be plotted as curves, defaulting to replace mode."""
        self._send_data(name, y, coords=x, data_type='traces', mode=mode, max_samples=max_samples)

    def pub_arb_data(self, name: Union[str, bytes], data: Any, data_type: str = 'arb') -> None:
        """Sends arbitrary data."""
        self._send_data(name, data, data_type=data_type)

    def close(self) -> None:
        """Closes the ZMQ socket."""
        self.sock.close()
        self.context.term()


if __name__ == "__main__":
    import time
    import numpy as np
    sender = DPMSender(pubName="myexperiment")
    x = np.linspace(0, 1, 1000)
    k = 0
    while True:
        r = np.random.uniform()
        y1 = np.sin(2 * np.pi * 10 * x**2 + 0.1 * k) + r
        y2 = np.sin(2 * np.pi * 10 * x**2 * (0.2 * (k % 10))) + r
        
        sender.pub_traces("test1", y1, x=x)
        sender.pub_traces("test2", y2, x=x)
        
        print(f"Sent iteration {k}")
        k += 1
        time.sleep(0.5)

