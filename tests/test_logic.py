import pytest
import numpy as np
from streaming_data_item import unpack_data
from DPM_listener import DPMListener

def test_unpack_data_mapping():
    data = {'y': np.array([1, 2, 3]), 'x': np.array([0, 1, 2])}
    x, y = unpack_data(data)
    assert np.array_equal(x, [0, 1, 2])
    assert np.array_equal(y, [1, 2, 3])

def test_unpack_data_mapping_no_x():
    data = {'y': np.array([10, 20])}
    x, y = unpack_data(data)
    assert np.array_equal(x, [0, 1])
    assert np.array_equal(y, [10, 20])

def test_unpack_data_tuple_xy():
    # This is expected to fail currently due to the bug in unpack_data
    x_in = np.array([0, 1, 2])
    y_in = np.array([4, 5, 6])
    x, y = unpack_data((x_in, y_in))
    assert np.array_equal(x, x_in)
    assert np.array_equal(y, y_in)

def test_unpack_data_single_array():
    y_in = np.array([7, 8, 9])
    # If len(y_in) >= 2, the current code treats it as 'y' and generates 'x'
    x, y = unpack_data(y_in)
    assert np.array_equal(y, y_in)
    assert len(x) == len(y_in)

def test_parse_topic():
    label, category = DPMListener.parse_topic(b"mycat:mylabel")
    assert label == b"mylabel"
    assert category == b"mycat"

def test_parse_topic_no_category():
    label, category = DPMListener.parse_topic(b"mylabel")
    assert label == b"mylabel"
    assert category is None
