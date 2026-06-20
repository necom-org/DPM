
from setuptools import setup

setup(
    name='DPM',    
    version='0.01', 
    py_modules=['DPM', 'streaming_data_item', 'DPM_listener', 'DPM_sender', 'FancyPlotItem'],
    package_data={'': ['words']},
    include_package_data=True
)