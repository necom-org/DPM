""" StreamingDataItem: A specialized pyqtgraph PlotDataItem for live updates.
"""

from collections.abc import Mapping
from typing import Any, Tuple, Union

import numpy as np
import pyqtgraph as pg

def is_collection(obj: Any) -> bool:
    """Check if an object is a collection (list, tuple, or ndarray)."""
    return isinstance(obj, (list, tuple, np.ndarray))

def unpack_data(data: Any) -> Tuple[np.ndarray, np.ndarray]:
    """Unpacks data into (x, y) arrays for plotting."""
    if isinstance(data, Mapping):
        y = np.atleast_1d(data['y'])
        x = np.atleast_1d(data.get('x', np.arange(len(y))))
    elif isinstance(data, (tuple, list)) and len(data) == 2:
        # Distinguish (x, y) from a 2-element list/tuple [y1, y2]
        if is_collection(data[0]) and is_collection(data[1]):
            x, y = np.atleast_1d(data[0]), np.atleast_1d(data[1])
        else:
            y = np.atleast_1d(data)
            x = np.arange(len(y))
    else:
        y = np.atleast_1d(data)
        x = np.arange(len(y))
    return x, y

MODE_REPLACE = 0
MODE_APPEND = 1

class StreamingDataItem(pg.PlotDataItem):
    """A PlotDataItem that supports real-time appending and replacing of data."""
    
    def __init__(self, *args: Any, mode: int = MODE_REPLACE, max_samples: int = 1000, **kwargs: Any) -> None:
        if 'cv_name' in kwargs:
            name = kwargs.pop('cv_name')
            kwargs["name"] = name
        else:
            name = None
            
        # Unpack data if provided as a single argument (e.g. (x, y) tuple from DPM)
        if len(args) == 1:
            x_init, y_init = unpack_data(args[0])
            super().__init__(x_init, y_init, **kwargs)
        else:
            super().__init__(*args, **kwargs)
        
        self.mode = mode
        self.max_samples = max_samples
        self.cv_name = name
        
        # Initialize internal cache from PlotDataItem's data
        if self.xData is not None:
            self.x = np.atleast_1d(self.xData)
            self.y = np.atleast_1d(self.yData)
        else:
            self.x = np.array([], dtype=float)
            self.y = np.array([], dtype=float)
            
        self.psd_mode = False
        self.nperseg = 256

    def setAppendMode(self, max_samples: Union[int, None] = None) -> None:
        """Switches the curve to append mode."""
        self.mode = MODE_APPEND
        if max_samples is not None:
            self.max_samples = max_samples

    def setReplaceMode(self) -> None:
        """Switches the curve to replace mode (default)."""
        self.mode = MODE_REPLACE

    def clear(self) -> None:
        """Clears the cached data and the display."""
        self.x = np.array([], dtype=float)
        self.y = np.array([], dtype=float)
        super().clear()

    def addData(self, data: Any) -> None:
        """Main interface to update the curve's data."""
        if data is None:
            return
            
        x_new, y_new = unpack_data(data)
        
        if self.mode == MODE_APPEND:
            self._append_data(x_new, y_new)
        else:
            self._replace_data(x_new, y_new)

    add_data = addData


    def _update_psd_view(self) -> None:
        """Computes the Power Spectral Density (PSD) using scipy.signal.welch."""
        if len(self.y) > 2:
            try:
                dxs = np.diff(self.x)
                dt = np.mean(dxs) if len(dxs) > 0 else 1.0
                fs = 1.0 / dt if dt > 0 else 1.0
                
                nperseg_actual = min(self.nperseg, len(self.y))
                if nperseg_actual >= 2:
                    from scipy.signal import welch
                    f, Pxx = welch(self.y, fs=fs, nperseg=nperseg_actual)
                    super().setData(f, Pxx)
                    return
            except Exception as e:
                print(f"Error computing PSD in StreamingDataItem: {e}")
        super().setData(self.x, self.y)

    def _replace_data(self, x: np.ndarray, y: np.ndarray) -> None:
        """Replaces the entire trace with new data."""
        self.x, self.y = x, y
        if self.psd_mode:
            self._update_psd_view()
        else:
            self.setData(self.x, self.y)

    def _append_data(self, x: np.ndarray, y: np.ndarray) -> None:
        """Appends new data to the existing trace."""
        # Use np.concatenate instead of np.append for better efficiency
        self.x = np.concatenate((self.x, x))
        self.y = np.concatenate((self.y, y))
        
        # Limit buffer size
        if len(self.x) > self.max_samples:
            self.x = self.x[-self.max_samples:]
            self.y = self.y[-self.max_samples:]
            
        if self.psd_mode:
            self._update_psd_view()
        else:
            self.setData(self.x, self.y)

    def get_holding_plot_item(self) -> Union[pg.PlotItem, None]:
        """Finds the PlotItem that contains this data item."""
        parent = self.parentItem()
        while parent is not None:
            if isinstance(parent, pg.PlotItem):
                return parent
            if hasattr(parent, 'plotItem'):
                return parent.plotItem
            parent = parent.parentItem()
        return None

