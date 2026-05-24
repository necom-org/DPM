# DPM (Dock Plot Manager)

## Project Overview
DPM is a Python-based tool designed to simplify the management and visualization of live-streaming data. It leverages `pyqtgraph` and its `DockArea` system to provide a flexible, interactive environment where data sources can be dynamically plotted, organized into docks, and updated in real-time.

The project is particularly suited for experimental environments where data is generated continuously and needs to be monitored or analyzed interactively.

### Key Technologies
- **Python**: Core language.
- **PyQt6 / PyQt5**: GUI framework.
- **pyqtgraph**: High-performance plotting and dock management.
- **ZMQ (ZeroMQ)**: Messaging library used for remote data streaming.
- **NumPy**: Data processing.
- **Pickle**: State serialization (saving/restoring dock layouts).

### Core Architecture
- **`DPM.py`**: Contains `DockPlotManager`, the central class for managing the GUI, and `DockPlot`, a container for individual `PlotWidgets`.
- **`streaming_data_item.py`**: Defines `StreamingDataItem`, a specialized `PlotDataItem` that supports `APPEND` and `REPLACE` modes for live updates.
- **`DPM_listener.py` & `DPM_sender.py`**: Provide a ZMQ-based infrastructure for sending data from one process (e.g., an experiment script) to a DPM instance in another process.
- **`JupyterConsoleWidget`**: An integrated Jupyter console within the DPM interface for interactive manipulation of plots and data.

---

## Building and Running

### Prerequisites
Ensure you have the following dependencies installed:
```bash
pip install numpy pyqtgraph pyzmq qtconsole
# And a Qt backend, e.g.:
pip install PyQt6
```

### Installation
You can install the project in editable mode:
```bash
pip install -e .
```

### Running the Project
1.  **Local Usage**: You can run `DPM.py` directly to see a demonstration of its plotting capabilities.
2.  **Remote Streaming**:
    *   Start a listener/manager (e.g., via `DPM_listener.py` or by instantiating `DockPlotManager` in a script).
    *   Run a sender script like `dummy_experiment.py` to push data to the manager.


### Testing
The project uses `pytest` for testing. A `tests/` directory contains unit and integration tests.

To run the tests:
```bash
# Add current directory to PYTHONPATH and run pytest
PYTHONPATH=. pytest tests/
```

Tests cover:
- Data unpacking logic in `streaming_data_item.py`.
- ZMQ topic parsing in `DPM_listener.py`.
- Core GUI-lite functionality in `DPM.py` (addDockPlot, addData, appendMode).
- ZMQ communication between `DPMSender` and `DPMListener`.

### Examples
A collection of documented examples is available in the `examples/` directory:
- `01_basic_local.py`: Shows how to create a manager and add plots locally.
- `02_live_updates.py`: Demonstrates 'append mode' for real-time data streaming.
- `03_remote_receiver.py` & `03_remote_sender.py`: Demonstrate cross-process data visualization via ZMQ.

---

## Development Conventions

### Bug Fixes and Improvements
Recent improvements include:
- Fixed `unpack_data` to correctly handle `(x, y)` tuples and single arrays.
- Fixed `DPMSender.pubPoints` to properly send messages.
- Updated `DPMSender` and `DPMListener` to support configurable ports.
- Enhanced ZMQ topics to include trace names for better categorization and labeling.
- Fully implemented `DPMListener.update` to automatically update the plot manager with incoming data.
