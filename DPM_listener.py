""" DPM Listener: A server that listens for trace data via ZMQ and forwards it to DPM.
"""

import pickle
from typing import Any, Optional, Tuple, Union
import zmq
import pyqtgraph as pg
from DPM import DockPlotManager

PORT = 5561

class DPMListener:
    """Listens for data sent by DPMSender and updates a DockPlotManager."""
    
    def __init__(
        self, 
        subName: Union[str, bytes] = b"default", 
        dpm: Optional[DockPlotManager] = None, 
        host: str = "localhost",
        port: int = PORT
    ) -> None:
        if isinstance(subName, str):
            subName = subName.encode('utf-8')
            
        self.sock = zmq.Context().socket(zmq.SUB)
        self.sock.set_hwm(10)
        self.sock.connect(f"tcp://{host}:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, subName)
        
        self.dpm = dpm or DockPlotManager(name=subName.decode('utf-8'))
        self.timer: Optional[pg.QtCore.QTimer] = None

    @staticmethod
    def parse_topic(topic_bytes: bytes) -> Tuple[bytes, Optional[bytes]]:
        """Parses a ZMQ topic into (label, category)."""
        category = None
        parts = topic_bytes.split(b":")
        label = parts.pop()
        if parts:
            category = parts.pop()
        return label, category

    def update(self) -> Optional[bool]:
        """Polls for new data and updates the DPM."""
        if self.sock.poll(10):
            try:
                topic, msg = self.sock.recv().split(b' ', 1)
                label, category = self.parse_topic(topic)
                data = pickle.loads(msg)
                
                # Convert bytes to string for DPM methods
                label_str = label.decode('utf-8') if isinstance(label, bytes) else label
                category_str = category.decode('utf-8') if isinstance(category, bytes) else category
                
                plot_data = (data['coords'], data['data']) if data.get('coords') is not None else data['data']
                
                # Expose and forward data to DPM
                self.dpm.add_data(label_str, plot_data, dock_name=category_str)
                
                # Extract and dynamically apply append/replace mode
                mode = data.get('mode')
                if mode is None and data.get('type') == 'points':
                    mode = 'append'
                
                max_samples = data.get('max_samples')
                if mode is not None or max_samples is not None:
                    items = self.dpm.all_data_items.get(label_str)
                    if items:
                        for item in items:
                            if mode == 'append':
                                item.setAppendMode(max_samples)
                            elif mode == 'replace':
                                item.setReplaceMode()
                
                return True
            except Exception as e:
                print(f"Error processing message: {e}")
                return False
        return None

    def start_updating(self, interval: int = 100) -> None:
        """Starts a QTimer to periodically call update()."""
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval)

    def stop(self) -> None:
        """Stops the update timer."""
        if self.timer:
            self.timer.stop()

    def close(self) -> None:
        """Closes the ZMQ socket and stops the timer."""
        self.sock.close()
        self.stop()


if __name__ == "__main__":
    listener = DPMListener("myexperiment")
    listener.start_updating(100)
    # Start the Qt event loop
    pg.mkQApp().exec()

