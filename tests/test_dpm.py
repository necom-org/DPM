import pytest
import pyqtgraph as pg
from DPM import DockPlotManager
import numpy as np
import os

@pytest.fixture
def dpm():
    app = pg.mkQApp("TestApp")
    m = DockPlotManager("TestExperiment")
    yield m
    # Clean up
    if os.path.exists(m.save_file):
        os.remove(m.save_file)

def test_add_dock_plot(dpm):
    name = "test_dock"
    dp = dpm.add_dock_plot(name)
    assert name in dpm.docks
    assert dp.name() == name

def test_add_data_new_dock(dpm):
    name = "data1"
    y = np.array([1, 2, 3])
    dpm.add_data(name, y, dock_name="new_dock")
    assert "new_dock" in dpm.docks
    assert name in dpm.all_data_items
    # Check if the data item was created
    items = dpm.all_data_items[name]
    assert len(items) == 1
    assert np.array_equal(items[0].yData, y)

def test_add_data_existing_dock(dpm):
    dpm.add_dock_plot("dock1")
    y = np.array([4, 5, 6])
    dpm.add_data("data2", y, dock_name="dock1")
    assert "data2" in dpm.all_data_items
    assert len(dpm.all_data_items["data2"]) == 1

def test_append_mode(dpm):
    dpm.add_dock_plot("dock1")
    y1 = np.array([1, 2])
    dpm.add_data("data_append", y1, dock_name="dock1")
    
    dp = dpm.docks["dock1"]
    dp.set_append_mode(max_samples=5)
    
    y2 = np.array([3, 4])
    dpm.add_data("data_append", y2)
    
    item = dpm.all_data_items["data_append"][0]
    # In append mode, it should have [1, 2, 3, 4]
    assert np.array_equal(item.yData, [1, 2, 3, 4])
    
    y3 = np.array([5, 6])
    dpm.add_data("data_append", y3)
    # Should be limited to 5 samples: [2, 3, 4, 5, 6]
    assert np.array_equal(item.yData, [2, 3, 4, 5, 6])

def test_save_restore(dpm):
    dpm.add_dock_plot("dock1")
    dpm.save()
    assert os.path.exists(dpm.save_file)
    assert dpm.restore_btn.isEnabled()
    
    # Modify state
    dpm.load()

def test_save_restore_full_state(dpm):
    from streaming_data_item import MODE_REPLACE, MODE_APPEND
    
    # Add dock and curves
    dpm.add_dock_plot("dock1")
    
    # 1. Add some data in REPLACE mode
    y_replace = np.array([10.0, 20.0, 30.0])
    dpm.add_data("curve_replace", y_replace, dock_name="dock1")
    
    # 2. Add some data in APPEND mode
    y_append = np.array([1.0, 2.0])
    dpm.add_data("curve_append", y_append, dock_name="dock1")
    dpm.docks["dock1"].data_items["curve_append"].setAppendMode(max_samples=5)
    
    # Save the current state
    dpm.save()
    assert os.path.exists(dpm.save_file)
    
    # Create a fresh DockPlotManager instance (simulate later run)
    fresh_dpm = DockPlotManager("TestExperiment")
    try:
        # Load from saved pickle file
        fresh_dpm.load()
        
        # Verify dock and curves were dynamically re-created
        assert "dock1" in fresh_dpm.docks
        dp = fresh_dpm.docks["dock1"]
        
        assert "curve_replace" in dp.data_items
        assert "curve_append" in dp.data_items
        
        # Verify plotting modes are restored correctly
        assert dp.data_items["curve_replace"].mode == MODE_REPLACE
        assert dp.data_items["curve_append"].mode == MODE_APPEND
        assert dp.data_items["curve_append"].max_samples == 5
        
        # Verify plotted data coordinates are restored precisely
        assert np.array_equal(dp.data_items["curve_replace"].y, y_replace)
        assert np.array_equal(dp.data_items["curve_append"].y, y_append)
    finally:
        # Cleanup
        if os.path.exists(fresh_dpm.save_file):
            os.remove(fresh_dpm.save_file)

def test_psd_and_history_gui_integration(dpm):
    from streaming_data_item import MODE_REPLACE, MODE_APPEND
    # Add a dock and curve with coordinate data
    dpm.add_dock_plot("dock1")
    t = np.linspace(0, 1.0, 100)
    # 10 Hz sine wave
    y = np.sin(2 * np.pi * 10 * t)
    dpm.add_data("curve1", (t, y), dock_name="dock1")
    
    dp = dpm.docks["dock1"]
    item = dp.data_items["curve1"]
    
    # 1. Verify initial GUI values
    assert dp.psd_cb.isChecked() is False
    assert dp.mode_combo.currentIndex() == 0  # Replace Mode
    assert dp.nperseg_sb.value() == 256
    assert dp.history_sb.value() == 1000
    assert item.psd_mode is False
    assert item.mode == MODE_REPLACE
    assert item.nperseg == 256
    assert item.max_samples == 1000
    
    # 2. Toggle PSD View
    dp.psd_cb.setChecked(True)
    assert item.psd_mode is True
    # The rendered output (xData) should contain frequencies from Welch (not original time coords)
    assert not np.array_equal(item.xData, t)
    
    # 3. Change segment size (nperseg)
    dp.nperseg_sb.setValue(64)
    assert item.nperseg == 64
    
    # 4. Change plotting mode to Append
    dp.mode_combo.setCurrentIndex(1)  # Index 1 is Append Mode
    assert item.mode == MODE_APPEND
    
    # 5. Change history limit (max_samples) and verify time-domain cache slicing
    dp.psd_cb.setChecked(False)  # switch back to verify cache directly
    dp.history_sb.setValue(50)
    assert item.max_samples == 50
    assert len(item.x) == 50
    assert np.array_equal(item.xData, item.x)
    
    # 6. Save and reload to verify UI state persistence
    dpm.save()
    assert os.path.exists(dpm.save_file)
    
    fresh_dpm = DockPlotManager("TestExperiment")
    try:
        fresh_dpm.load()
        assert "dock1" in fresh_dpm.docks
        fresh_dp = fresh_dpm.docks["dock1"]
        
        # Verify UI control values are fully restored
        assert fresh_dp.psd_cb.isChecked() is False
        assert fresh_dp.mode_combo.currentIndex() == 1  # Append Mode index is 1
        assert fresh_dp.nperseg_sb.value() == 64
        assert fresh_dp.history_sb.value() == 50
        
        # Verify curve state is restored
        fresh_item = fresh_dp.data_items["curve1"]
        assert fresh_item.psd_mode is False
        assert fresh_item.mode == MODE_APPEND
        assert fresh_item.nperseg == 64
        assert fresh_item.max_samples == 50
        assert len(fresh_item.x) == 50
    finally:
        if os.path.exists(fresh_dpm.save_file):
            os.remove(fresh_dpm.save_file)

def test_realtime_preprocessing_filters(dpm):
    # Add a dock and curves
    dpm.add_dock_plot("dock1")
    
    # Define a simple scaling filter (y * 3.5)
    def scale_filter(x, y):
        return x, y * 3.5
        
    # Register filter
    dpm.add_filter("curve1", scale_filter)
    
    # Stream raw data
    raw_y = np.array([2.0, 4.0, 6.0])
    dpm.add_data("curve1", raw_y, dock_name="dock1")
    
    item = dpm.docks["dock1"].data_items["curve1"]
    # 1. Assert the raw data was scaled on the fly
    assert np.array_equal(item.y, [7.0, 14.0, 21.0])
    
    # 2. Clear filters and add more data
    dpm.clear_filters("curve1")
    dpm.add_data("curve1", raw_y)
    
    # In REPLACE mode, it should be the raw data [2, 4, 6]
    assert np.array_equal(item.y, raw_y)
    
    # 3. Verify state-sharing cross-channel filter works correctly
    class SharedFilter:
        def __init__(self):
            self.last_ref = None
        def process_ref(self, x, y):
            self.last_ref = y
            return x, y
        def process_sig(self, x, y):
            if self.last_ref is not None:
                return x, y - self.last_ref
            return x, y
            
    sf = SharedFilter()
    dpm.add_filter("ref_ch", sf.process_ref)
    dpm.add_filter("sig_ch", sf.process_sig)
    
    dpm.add_data("ref_ch", np.array([1.0, 2.0]))
    dpm.add_data("sig_ch", np.array([10.0, 20.0]), dock_name="dock1")
    
    # Signal channel should have subtracted the reference channel!
    sig_item = dpm.docks["dock1"].data_items["sig_ch"]
    assert np.array_equal(sig_item.y, [9.0, 18.0])
    
    # 4. Verify virtual calculated channels
    def virtual_hook(x, y):
        dpm.add_data("virtual_ch", (x, y * 10), dock_name="dock1")
        return x, y
        
    dpm.add_filter("source_ch", virtual_hook)
    dpm.add_data("source_ch", np.array([5.0, 10.0]), dock_name="dock1")
    
    # "virtual_ch" should have been dynamically created and populated!
    assert "virtual_ch" in dpm.docks["dock1"].data_items
    v_item = dpm.docks["dock1"].data_items["virtual_ch"]
    assert np.array_equal(v_item.y, [50.0, 100.0])
