""" DPM: Dock Plot Manager

A tool for managing and visualizing live-streaming data using pyqtgraph docks.
"""

import os
import pickle
from collections import defaultdict, namedtuple
from collections.abc import Mapping

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from streaming_data_item import StreamingDataItem, MODE_APPEND, MODE_REPLACE, unpack_data

# Named tuple for structured curve data
Curve = namedtuple("Curve", ["x", "y", "label", "category"])

def random_word():
    """Returns a random word from the 'words' file."""
    if random_word.words is None:
        dir_name = os.path.dirname(__file__)
        fname = os.path.join(dir_name, 'words')
        with open(fname) as f:
            random_word.words = [line.strip() for line in f]
    word_num = int(np.random.uniform() * len(random_word.words))
    return random_word.words[word_num]

random_word.words = None

# Default pens for plotting
PEN_LIST = [pg.mkPen(s) for s in 'wrgbcmyk']

try:
    from qtconsole import inprocess
except ImportError:
    print("This requires `qtconsole` to run. Install with `pip install qtconsole`.")


class JupyterConsoleWidget(inprocess.QtInProcessRichJupyterWidget):
    """Integrated Jupyter console for interactive data manipulation."""
    def __init__(self):
        super().__init__()
        self.kernel_manager = inprocess.QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

    def shutdown_kernel(self):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()


class DockPlot(Dock):
    """Container for a pyqtgraph PlotWidget within a Dock, including toolbar controls."""
    def __init__(self, name, curves=None, title=None, size=(400, 200), default_plot_kwargs=None):
        super().__init__(name, size=size)
        self.default_plot_kwargs = default_plot_kwargs or {}
        self.data_items = {}  # Map of curve_name -> StreamingDataItem
        
        # Main layout container to host controls and plot
        self.main_widget = pg.QtWidgets.QWidget()
        self.main_layout = pg.QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)
        
        # Toolbar layout
        self.controls_layout = pg.QtWidgets.QHBoxLayout()
        self.controls_layout.setContentsMargins(5, 2, 5, 2)
        
        # 1. PSD Toggle checkbox
        self.psd_cb = pg.QtWidgets.QCheckBox("PSD View")
        self.psd_cb.toggled.connect(self.toggle_psd)
        self.controls_layout.addWidget(self.psd_cb)
        
        # 1b. Plot Mode combobox (Replace/Append)
        self.controls_layout.addWidget(pg.QtWidgets.QLabel("Mode:"))
        self.mode_combo = pg.QtWidgets.QComboBox()
        self.mode_combo.addItems(["Replace", "Append"])
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        self.controls_layout.addWidget(self.mode_combo)
        
        # 2. nperseg window size spinbox
        self.controls_layout.addWidget(pg.QtWidgets.QLabel("FFT Window (nperseg):"))
        self.nperseg_sb = pg.QtWidgets.QSpinBox()
        self.nperseg_sb.setRange(8, 65536)
        self.nperseg_sb.setValue(256)
        self.nperseg_sb.setSingleStep(64)
        self.nperseg_sb.valueChanged.connect(self.change_nperseg)
        self.controls_layout.addWidget(self.nperseg_sb)
        
        # 3. max_samples history spinbox
        self.controls_layout.addWidget(pg.QtWidgets.QLabel("History (max_samples):"))
        self.history_sb = pg.QtWidgets.QSpinBox()
        self.history_sb.setRange(10, 1000000)
        self.history_sb.setValue(1000)
        self.history_sb.setSingleStep(100)
        self.history_sb.valueChanged.connect(self.change_history)
        self.controls_layout.addWidget(self.history_sb)
        
        self.controls_layout.addStretch()
        self.main_layout.addLayout(self.controls_layout)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget(title=title or name)
        self.plot_item = self.plot_widget.plotItem
        self.main_layout.addWidget(self.plot_widget)
        
        self.addWidget(self.main_widget)
        self.plot_item.addLegend()

        if curves:
            for curve_name, data in curves.items():
                self.add_new_item(curve_name, data)

    def add_new_item(self, name, data):
        """Creates and adds a new StreamingDataItem to the plot."""
        # Select a pen that isn't currently in use if possible
        pen = PEN_LIST[0]
        if self.data_items:
            in_use_pens = [item.opts['pen'] for item in self.data_items.values()]
            for p in PEN_LIST:
                if p not in in_use_pens:
                    pen = p
                    break

        item = StreamingDataItem(data, cv_name=name, pen=pen, **self.default_plot_kwargs)
        
        # Sync values from toolbar GUI controls
        item.psd_mode = self.psd_cb.isChecked()
        item.nperseg = self.nperseg_sb.value()
        item.max_samples = self.history_sb.value()
        
        # Sync mode
        if self.mode_combo.currentIndex() == 1:
            item.setAppendMode(item.max_samples)
        else:
            item.setReplaceMode()
        
        self.data_items[name] = item
        self.plot_item.addItem(item, name=name)
        
        if item.psd_mode:
            item._update_psd_view()
        return item

    def remove_item(self, name):
        """Removes a curve by name."""
        if name in self.data_items:
            item = self.data_items.pop(name)
            self.plot_widget.removeItem(item)

    def add_data(self, name, data):
        """Updates an existing curve or creates a new one with the given data."""
        if name not in self.data_items:
            if name is None:
                name = random_word()
            self.add_new_item(name, data)
        else:
            self.data_items[name].addData(data)

    def set_append_mode(self, max_samples=None):
        """Sets all curves in this dock to append mode."""
        for name, item in self.data_items.items():
            item.setAppendMode(max_samples)
            
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(1)  # Index 1 is Append
        self.mode_combo.blockSignals(False)
        
        if max_samples is not None:
            self.history_sb.blockSignals(True)
            self.history_sb.setValue(max_samples)
            self.history_sb.blockSignals(False)

    def set_replace_mode(self):
        """Sets all curves in this dock to replace mode."""
        for item in self.data_items.values():
            item.setReplaceMode()
            
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(0)  # Index 0 is Replace
        self.mode_combo.blockSignals(False)

    def change_mode(self, index):
        """Changes the plotting mode (Replace or Append) for all curves in the dock."""
        if index == 1:  # Append
            max_samples = self.history_sb.value()
            for item in self.data_items.values():
                item.setAppendMode(max_samples)
        else:  # Replace
            for item in self.data_items.values():
                item.setReplaceMode()

    def toggle_psd(self, checked):
        """Toggles PSD view mode for all curves in the dock."""
        for item in self.data_items.values():
            item.psd_mode = checked
            if checked:
                item._update_psd_view()
            else:
                item.setData(item.x, item.y)

    def change_nperseg(self, value):
        """Updates the segment length for all curves in the dock."""
        for item in self.data_items.values():
            item.nperseg = value
            if item.psd_mode:
                item._update_psd_view()

    def change_history(self, value):
        """Updates the history maximum samples for all curves in the dock."""
        for item in self.data_items.values():
            item.max_samples = value
            if len(item.x) > value:
                item.x = item.x[-value:]
                item.y = item.y[-value:]
                if item.psd_mode:
                    item._update_psd_view()
                else:
                    item.setData(item.x, item.y)


class DockPlotManager:
    """Manages a collection of DockPlots and their layouts."""
    def __init__(self, name='DPM Window', default_plot_kwargs=None):
        self.name = name
        self.default_plot_kwargs = default_plot_kwargs or {}
        self.app = pg.mkQApp("DPM App")
        
        self.win = pg.QtWidgets.QMainWindow()
        self.win.setWindowTitle(name)
        
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        
        self.docks = {}  # dock_name -> DockPlot
        self.all_data_items = defaultdict(list)  # curve_name -> list of StreamingDataItems
        
        self.save_file = f"dockManager_{self.name}.pkl"
        self.filters = defaultdict(list)  # curve_name -> list of Callable filters
        self._init_controls()
        self._init_jupyter()
        
        # Automatically restore layout and states on startup if they exist
        if os.path.exists(self.save_file):
            self.load()
            
        self.win.show()

    def _init_controls(self):
        """Initializes the control dock for save/restore functionality."""
        self.control_dock = Dock("Controls", size=(100, 100))
        layout = pg.LayoutWidget()
        
        self.save_btn = pg.QtWidgets.QPushButton('Save Layout')
        self.restore_btn = pg.QtWidgets.QPushButton('Restore Layout')
        self.restore_btn.setEnabled(os.path.exists(self.save_file))
        
        self.save_btn.clicked.connect(self.save)
        self.restore_btn.clicked.connect(self.load)
        
        layout.addWidget(pg.QtWidgets.QLabel("Dock Management:"), row=0, col=0)
        layout.addWidget(self.save_btn, row=1, col=0)
        layout.addWidget(self.restore_btn, row=2, col=0)
        self.control_dock.addWidget(layout)
        self.area.addDock(self.control_dock, 'left')

    def _init_jupyter(self):
        """Initializes the integrated Jupyter console."""
        self.jupyter_widget = JupyterConsoleWidget()
        self.jupyter_dock = Dock("Console", size=(1, 1))
        self.jupyter_dock.addWidget(self.jupyter_widget)
        
        # Expose useful objects to the console
        kernel = self.jupyter_widget.kernel_manager.kernel
        kernel.shell.push({'np': np, 'dpm': self, 'pg': pg})
        
        self.area.addDock(self.jupyter_dock, 'bottom')

    def save(self):
        """Saves the current dock layout and plot states to a file."""
        layout_state = self.area.saveState()
        
        # Capture metadata for all active docks and their curves
        docks_meta = {}
        for dock_name, dock in self.docks.items():
            curves_meta = {}
            for curve_name, item in dock.data_items.items():
                curves_meta[curve_name] = {
                    "mode": item.mode,
                    "max_samples": item.max_samples,
                    "x": item.x,
                    "y": item.y,
                    "psd_mode": item.psd_mode,
                    "nperseg": item.nperseg
                }
            docks_meta[dock_name] = {
                "psd_view": dock.psd_cb.isChecked(),
                "nperseg": dock.nperseg_sb.value(),
                "history_limit": dock.history_sb.value(),
                "plot_mode": dock.mode_combo.currentIndex(),
                "curves": curves_meta
            }
            
        state = {
            "layout": layout_state,
            "docks": docks_meta
        }
        
        with open(self.save_file, 'wb') as f:
            pickle.dump(state, f)
            
        self.restore_btn.setEnabled(True)
        print(f"Layout and plot states saved to {self.save_file}")

    def load(self):
        """Loads and restores the dock layout and plot states from a file."""
        if not os.path.exists(self.save_file):
            print("No saved state found.")
            return

        try:
            with open(self.save_file, 'rb') as f:
                state = pickle.load(f)
                
            # If the state uses the new structured dictionary format
            if isinstance(state, dict) and "layout" in state and "docks" in state:
                # 1. First reconstruct any missing docks/curves and restore their curve states/modes
                for dock_name, dock_meta in state["docks"].items():
                    curves_data = {}
                    for curve_name, curve_meta in dock_meta["curves"].items():
                        # Extract saved x and y data arrays
                        x = curve_meta.get("x", np.array([], dtype=float))
                        y = curve_meta.get("y", np.array([], dtype=float))
                        curves_data[curve_name] = (x, y)
                    
                    if dock_name not in self.docks:
                        # Dynamically reconstruct the dock and its curves
                        dp = self.add_dock_plot(dock_name, curves=curves_data)
                    else:
                        dp = self.docks[dock_name]
                        # For existing docks, make sure any missing curves are added
                        for curve_name, (x, y) in curves_data.items():
                            if curve_name not in dp.data_items:
                                new_item = dp.add_new_item(curve_name, (x, y))
                                self.all_data_items[curve_name].append(new_item)
                            else:
                                dp.data_items[curve_name]._replace_data(x, y)
                                
                    # 2. Restore GUI control values
                    dp.psd_cb.blockSignals(True)
                    dp.psd_cb.setChecked(dock_meta.get("psd_view", False))
                    dp.psd_cb.blockSignals(False)
                    
                    dp.nperseg_sb.blockSignals(True)
                    dp.nperseg_sb.setValue(dock_meta.get("nperseg", 256))
                    dp.nperseg_sb.blockSignals(False)
                    
                    dp.history_sb.blockSignals(True)
                    dp.history_sb.setValue(dock_meta.get("history_limit", 1000))
                    dp.history_sb.blockSignals(False)
                    
                    dp.mode_combo.blockSignals(True)
                    dp.mode_combo.setCurrentIndex(dock_meta.get("plot_mode", 0))
                    dp.mode_combo.blockSignals(False)
                    
                    # 3. Restore mode and max_samples for the reconstructed curves
                    for curve_name, curve_meta in dock_meta["curves"].items():
                        item = dp.data_items.get(curve_name)
                        if item:
                            # Use individual curve mode if present; fallback to dock plot_mode
                            mode = curve_meta.get("mode")
                            if mode is None:
                                saved_plot_mode = dock_meta.get("plot_mode")
                                if saved_plot_mode is not None:
                                    mode = MODE_APPEND if saved_plot_mode == 1 else MODE_REPLACE
                                else:
                                    mode = MODE_REPLACE
                                
                            max_samples = curve_meta.get("max_samples", 1000)
                            item.psd_mode = curve_meta.get("psd_mode", dock_meta.get("psd_view", False))
                            item.nperseg = curve_meta.get("nperseg", dock_meta.get("nperseg", 256))
                            item.max_samples = max_samples
                            
                            if mode == MODE_APPEND:
                                item.setAppendMode(max_samples)
                            else:
                                item.setReplaceMode()
                                
                            if item.psd_mode:
                                item._update_psd_view()
                            else:
                                item.setData(item.x, item.y)
                                
                # 4. Restore the panel geometry layout
                self.area.restoreState(state["layout"], missing='ignore')
            else:
                # Legacy fallback to restoring layout structure directly
                self.area.restoreState(state, missing='ignore')
                
            print("Layout and plots restored.")
        except Exception as e:
            print(f"Error restoring state: {e}")

    def add_filter(self, curve_name, func):
        """Appends a callable filter function to the filter chain of a curve."""
        self.filters[curve_name].append(func)

    def clear_filters(self, curve_name=None):
        """Clears registered filters for a curve (or all curves if curve_name is None)."""
        if curve_name is not None:
            if curve_name in self.filters:
                self.filters[curve_name] = []
        else:
            self.filters.clear()

    def add_dock_plot(self, name, curves=None, title=None, **kwargs):
        """Creates and adds a new DockPlot to the manager."""
        plot_kwargs = self.default_plot_kwargs.copy()
        plot_kwargs.update(kwargs)
        
        dp = DockPlot(name, curves=curves, title=title, default_plot_kwargs=plot_kwargs)
        self.area.addDock(dp)
        self.docks[name] = dp
        
        for curve_name, item in dp.data_items.items():
            self.all_data_items[curve_name].append(item)
        return dp

    def add_data(self, curve_name, data, dock_name=None):
        """Adds data to a curve, creating the curve and dock if necessary."""
        # Unpack coordinates
        x_unpacked, y_unpacked = unpack_data(data)
        
        # Apply any registered curve-specific filters in sequence
        if curve_name in self.filters:
            for filter_func in self.filters[curve_name]:
                try:
                    x_unpacked, y_unpacked = filter_func(x_unpacked, y_unpacked)
                except Exception as e:
                    print(f"Error in filter '{getattr(filter_func, '__name__', 'unknown')}' for curve '{curve_name}': {e}")
                    
        data = (x_unpacked, y_unpacked)
        
        items = self.all_data_items.get(curve_name)
        
        if not items:
            # Create a new dock if it doesn't exist
            if dock_name is None:
                dock_name = list(self.docks.keys())[0] if self.docks else random_word()
            
            if dock_name not in self.docks:
                dp = self.add_dock_plot(dock_name, curves={curve_name: data})
            else:
                dp = self.docks[dock_name]
                new_item = dp.add_new_item(curve_name, data)
                self.all_data_items[curve_name].append(new_item)
        else:
            for item in items:
                item.addData(data)

    def get_plot_item(self, dock_name):
        """Returns the pyqtgraph PlotItem for the specified dock."""
        if dock_name in self.docks:
            return self.docks[dock_name].plot_item
        return None


if __name__ == "__main__":
    # Example usage for interactive testing
    import numpy as np
    from PyQt6 import QtTest
    
    x = np.linspace(0, 1, 1000)
    y = np.sin(2 * np.pi * 30 * x)
    
    dpm = DockPlotManager("Interactive Demo")
    
    # Add a dock with two curves
    dpm.add_dock_plot(
        "Waveforms", 
        curves={
            "Sine": (x, y), 
            "Squared": (x**2, y)
        }, 
        title="Frequency Demo"
    )
    
    # Add another dock with different data types
    dpm.add_dock_plot(
        "Exp", 
        curves={
            "Exponential": (x, np.exp(x)), 
            "Linear": (x**2, x)
        }
    )

    # Set one dock to append mode
    dpm.docks['Exp'].set_append_mode(max_samples=100)

    # Simulate incoming data
    for k in range(1, 10):
        x_chunk = np.linspace(0, 0.1, 5) + k * 0.1
        y_chunk = np.sin(2 * np.pi * x_chunk)
        dpm.add_data("Linear", (x_chunk, y_chunk))
        QtTest.QTest.qWait(200)
