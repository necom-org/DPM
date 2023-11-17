import pyqtgraph as pg
from collections.abc import Mapping
import numpy as np

def unpack_data(data):
    if isinstance(data, Mapping):
        y = data['y']
        if 'x' in data:
            x = data['x']
            print(len(x))
        else:
            x= np.arange(y.size)
    elif len(data) >=2:
        y = data
        x= np.arange(y.size)
    else:
        x, y = data
    return x,y

MODE_REPLACE = 0
MODE_APPEND = 1
class StreamingDataItem(pg.PlotDataItem):
    """ A PlotDataitem with convenience methods to be updated on the fly.

    This has attributes suited to live-streaming/updating data:

        max_samples <= number of samples to remember when appending
        max_curves <= number of curves to remember in replace mode
        update_mode (= APPEND_MODE, REPLACE_MODE)

    and methods:
        setAppendMode(max_samples=None);
        setReplaceMode(max_curves=None);
        addData()

    """
    dx = 1
    def __init__(self, *args, 
            mode= MODE_REPLACE,
            max_samples = 1000,
            **kwargs):
        if 'cv_name' in kwargs:
            name= kwargs.pop('cv_name')
            print('cv_name: ', name)
            kwargs["name"] = name
        else:
            name = None
        super().__init__(*args, **kwargs)
        self.x = self.xData
        self.y = self.yData
        self.max_samples= max_samples
        self.max_curves=3
        self.mode = mode
        self.cv_name=name

    def setAppendMode(self, max_samples=None):
        print('setting append for ', self.cv_name)
        self.mode = MODE_APPEND
        if max_samples is not None and max_samples > 1:
            self.max_samples=max_samples

    def setReplaceMode(self, max_curves=None):
        print('set replace mode for ', self.cv_name)
        self.mode == MODE_REPLACE
        if max_curves is not None:
            self.max_curves=max_curves

    def replaceData(self, x,y, *args, **kwargs):
        #work out x, y
        #Save data to self.
        super().setData(x,y, *args, **kwargs)
        # could add extra curves here...
        #pi =self.getHoldingPlotItem()
    def removeThyself(self):
        """remove myself from a plot I'm currently on"""
        self.getHoldingPlotItem().removeItem(self)

    def appendData(self, x,y=None):
        dx = self.dx
        if y is None:
            y = x
            x= self.x[-1] +dx+ np.arange(len(y))*dx
        elif x is None:
            x= self.x[-1] +dx+ np.arange(len(y))*dx
            
        self.x = np.append(self.x, x)
        self.y = np.append(self.y, y)
        self.x = self.x[-self.max_samples:]
        self.y = self.y[-self.max_samples:]
        self.setData(self.x,self.y)

        # Do a little pre-processing on the data
        # Append it to the current data

    def addData(self, data):
        x,y =unpack_data(data)
        if self.mode == MODE_APPEND:
            self.appendData(x,y)
        else:
            self.replaceData(x,y)

    def getHoldingPlotItem(self):
        pltItem= self.parentItem().parentItem().parentItem()
        if type(pltItem) is pg.PlotItem :
            return pltItem
        else:
            raise ValueError("It's not a plot item!")
        #else return None
    def _show(self):
        pltWidget = pg.PlotWidget()
        pltWidget.addItem(self)
        win = pg.QtGui.QMainWindow()
        win.setCentralWidget(pltWidget)
        self.win = win
        self.plotWidget = pltWidget
        win.show()


if __name__ == "__main__":
    import time
    import numpy as np
    from numpy import pi
    from PyQt5 import QtTest
    k = 0
    x = np.linspace(0,.5,3)+k*0.5
    y = np.sin(2*pi*x)
    sdi = StreamingDataItem(x,y, name="test_sdi")
    sdi._show()
    if 1:
        for k in range(1,20):
            x = np.linspace(0,.5,3)+k*0.5
            y = np.sin(2*pi*x)
            sdi.appendData(x,y)
            #time.sleep(.3)
            QtTest.QTest.qWait(100)
        #sdi.addToPlot()
