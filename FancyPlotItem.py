
import numpy as np
import pickle
import pyqtgraph as pg
import sys
from numpy import *
from time import sleep
import time
import collections



class FancyPlotItem(pg.PlotItem):
    """ Pyqtgraph plot item with methods for accessing individual curves
    """
