import pytest
import numpy as np
import pyqtgraph as pg
from streaming_data_item import StreamingDataItem, MODE_APPEND, MODE_REPLACE

@pytest.fixture
def qt_app():
    return pg.mkQApp()

def test_sdi_replace_mode(qt_app):
    item = StreamingDataItem(mode=MODE_REPLACE)
    
    # Initial data
    item.addData(np.array([1, 2, 3]))
    assert np.array_equal(item.y, [1, 2, 3])
    
    # Replace
    item.addData(np.array([4, 5]))
    assert np.array_equal(item.y, [4, 5])

def test_sdi_append_mode(qt_app):
    item = StreamingDataItem(mode=MODE_APPEND, max_samples=5)
    
    # Initial data
    item.addData(np.array([1, 2]))
    assert np.array_equal(item.y, [1, 2])
    
    # Append
    item.addData(np.array([3, 4]))
    assert np.array_equal(item.y, [1, 2, 3, 4])
    
    # Append more, exceeding max_samples
    item.addData(np.array([5, 6]))
    # Buffer should be [1, 2, 3, 4, 5, 6] then clipped to [2, 3, 4, 5, 6]
    assert np.array_equal(item.y, [2, 3, 4, 5, 6])
    assert len(item.x) == 5

def test_sdi_append_with_x(qt_app):
    # Test passing (x, y) explicitly
    item = StreamingDataItem(mode=MODE_APPEND)
    item.addData((np.array([0, 1]), np.array([10, 20])))
    assert np.array_equal(item.x, [0, 1])
    
    item.addData((np.array([2, 3]), np.array([30, 40])))
    assert np.array_equal(item.x, [0, 1, 2, 3])
    assert np.array_equal(item.y, [10, 20, 30, 40])

def test_sdi_2element_list_as_y(qt_app):
    # Test that [v1, v2] is treated as y data, not (x, y)
    item = StreamingDataItem()
    item.addData([10.0, 20.0])
    assert np.array_equal(item.y, [10.0, 20.0])
    assert np.array_equal(item.x, [0, 1])
    win = pg.GraphicsLayoutWidget()
    plot = win.addPlot()
    item = StreamingDataItem()
    plot.addItem(item)
    
    # Test finding the plot item
    assert item.get_holding_plot_item() == plot
    
def test_sdi_set_modes(qt_app):
    item = StreamingDataItem(mode=MODE_REPLACE)
    assert item.mode == MODE_REPLACE
    
    item.setAppendMode(max_samples=100)
    assert item.mode == MODE_APPEND
    assert item.max_samples == 100
    
    item.setReplaceMode()
    assert item.mode == MODE_REPLACE

def test_sdi_clear(qt_app):
    item = StreamingDataItem(mode=MODE_APPEND)
    item.addData(np.array([1, 2, 3]))
    assert len(item.x) == 3
    assert len(item.y) == 3
    
    item.clear()
    assert len(item.x) == 0
    assert len(item.y) == 0

