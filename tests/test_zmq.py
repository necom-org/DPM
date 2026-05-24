import pytest
import zmq
import pickle
import time
import numpy as np
from DPM_sender import DPMSender
from DPM_listener import DPMListener
from unittest.mock import MagicMock

def test_zmq_communication():
    port = 5570
    sender = DPMSender(pubName="testpub", port=port)
    
    # We need to wait a bit for ZMQ to bind/connect
    time.sleep(0.1)
    
    # Mock DPM to avoid GUI
    mock_dpm = MagicMock()
    listener = DPMListener(subName="testpub", dpm=mock_dpm, port=port)
    
    time.sleep(0.1)
    
    test_data = [1, 2, 3]
    sender.pub_traces(b"mylabel", test_data)
    
    # Wait for message to arrive
    time.sleep(0.2)
    
    if listener.sock.poll(100):
        topic, msg = listener.sock.recv().split(b' ', 1)
        label, category = listener.parse_topic(topic)
        data = pickle.loads(msg)
        
        assert label == b"mylabel"
        assert category == b"testpub"
        assert data['data'] == test_data
    else:
        pytest.fail("Message not received")

    sender.close()
    listener.close()

def test_zmq_integration():
    port = 5571
    sender = DPMSender(pubName="testint", port=port)
    time.sleep(0.1)
    
    # Mock DPM
    mock_dpm = MagicMock()
    listener = DPMListener(subName="testint", dpm=mock_dpm, port=port)
    time.sleep(0.1)
    
    test_data = np.array([4, 5, 6])
    sender.pub_traces(b"intlabel", test_data)
    
    time.sleep(0.2)
    
    # Run update
    result = listener.update()
    assert result is True
    
    # Verify add_data call
    mock_dpm.add_data.assert_called_once()
    args, kwargs = mock_dpm.add_data.call_args
    assert args[0] == 'intlabel'
    assert np.array_equal(args[1], test_data)
    assert kwargs['dock_name'] == 'testint'

    sender.close()
    listener.close()

def test_zmq_mode_and_samples():
    port = 5572
    sender = DPMSender(pubName="testmode", port=port)
    time.sleep(0.1)
    
    mock_dpm = MagicMock()
    mock_item = MagicMock()
    mock_dpm.all_data_items = {'modelabel': [mock_item]}
    
    listener = DPMListener(subName="testmode", dpm=mock_dpm, port=port)
    time.sleep(0.1)
    
    sender.pub_traces("modelabel", [10, 20], mode='append', max_samples=42)
    time.sleep(0.2)
    
    result = listener.update()
    assert result is True
    
    mock_item.setAppendMode.assert_called_once_with(42)
    
    sender.close()
    listener.close()

