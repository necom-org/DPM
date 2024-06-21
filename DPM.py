""" Evolution of DAM (Dock Area Manager)

The ultimate idea is that you feed it named data sources, and it will plot them in a sensible default way. 
This default way can be modified by mouse clicks, and can be remembered by the program.

Minimal example functionality... of how I want it to look.

dpm = DockPlotManager("MyPlotManager")

# Data is incoming...
x = linspace(0,1,1000)
y = sin(2*pi*x*5)
y2 = sin(2*pi*x*5)*(x-0.5)
y3 = (x-0.5)**2

data1 = (x,y)
dpm.input_data("curve1", data1) #The default set of plots

data2 = (x,y2)
dpm.input_data("set2:curve1", data2) #Another set called "set2"

data3 = (x,y3)
dpm.input_data("set2:curve2", data3)

# After each input, the plot will be updated.
# Many changes could be made to the display via mouse-clicks (or code)
# As many of these as possible should be remembered after closing/reopening the plots.


Another goal is for it to be easily updatable from remote data sources. 
That said, this might be achieved fairly easily, by writing a thread the reads data from
a ZMQ stream, does some option conversion, then plots it.
e.g.
dpm.addListener(sourceName, translationFunction =None, sinkName (?) )



Need to add:  ??
* an interface for turning on/off data streams
* An option for plotting existing data streams in various ways.
* a plot-level method for removing/pausing/adding streams
* A data structure for keeping track of data streams and where they are being plotted (in order to pass it on)
"""


import numpy as np
import pickle
from pyqtgraph.dockarea import *
import pyqtgraph as pg
import sys
from time import sleep
import time
from collections.abc import Mapping
from collections import namedtuple, defaultdict
from streaming_data_item import StreamingDataItem
import os

Curve = namedtuple("Curve", ["x", "y", "label", "category"])

def random_word():
    if random_word.words is None:
        dir_name =os.path.dirname(__file__) 
        fname = os.path.join(dir_name, 'words')
        random_word.words = open(fname).readlines()
    word_num = int(np.random.uniform()*len(random_word.words))
    return random_word.words[word_num]
random_word.words = None
penL = [pg.mkPen(s) for s in 'wrgbcmyk']

try:
    from qtconsole import inprocess
except (ImportError, NameError):
    print(
        "This requires `qtconsole` to run. Install with `pip install qtconsole` or equivalent."
    )


class JupyterConsoleWidget(inprocess.QtInProcessRichJupyterWidget):
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
    """ Container for a PlotWidget (in the future, perhaps multiple widgets. But only one for now.)

    Methods:
    * addCurve(name, data, *args) <- make a new curve
    * updateCurve(name, data) <- pass on data to the relevant curve
    * addData(name, data) <- main interface.
    
    Probably:
    * setMaxCurves(curves = 'all')
    * setMaxSamples(curves = 'all')
    * setAppendMode(curves = 'all')
    * setReplaceMode(curves = 'all')
    """
    #curveD = None
    def __init__(self, name,  curves={}, title=None, size=(400,200), defaultPlotKwargs={}):
        super().__init__(name, size=size)
        self.defaultPlotKwargs = defaultPlotKwargs
        self.dataD = defaultdict(list)
        if title is None:
            title=name
        self.plotWidget = pg.PlotWidget(title=title)
        self.plotItem =self.plotWidget.plotItem
        self.addWidget(self.plotWidget);
        self.plotItem.addLegend()
        if curves:
            for key, data in curves.items():
                self.addNewItem(name=key, data=data)


    def addNewItem(self, name, data):
        pen = penL[0]
        if self.dataD:
            inUsePens = [di.opts['pen'] for di in self.dataD.values()] 
            for pen in penL:
                if pen not in inUsePens:
                    break
        item = StreamingDataItem(data, cv_name=name, pen=pen, **self.defaultPlotKwargs)
        self.dataD[name] = item
        self.plotItem.addItem(item, name=name)
        return item
    def removeItem(self, name):
        item = self.dataD.pop(name)
        self.plotWidget.removeItem(item)

    def addData(self, name, data):
        if name not in self.dataD:
            if name is None:  # choose a random word as a name
                name = random_word()
                #name = str(self.default_names[len(self.curveD)])
            self.addNewItem(name, data)
        else:
            self.dataD[name].addData(data)
    
    def addCurve(self, name, data):
        self.plotWidget
        if isinstance(data,Mapping): #It's a dictionary, with elements {x,y,label}
            x,y =data['x'], data['y']
        else:
            if len(data)==2:
                #x=data[0], y=data[1]
                x,y = data
            else:
                y = data[0]
                x = np.arange(y.size)

        if name is None:  # choose a number as a name, according to how many plots we have already
            name = str(self.default_names[len(self.curveD)])
        if name in self.curveD:
            print("overwriting curve: {}".format(name))
            self.plotWidget.removeItem(self.curveD[name])
        #If plots are too big plot downsampled array
        if y.size < 1000000:
            plot_data_item = self.plotWidget.plot(x, y, name=name)
        else:
            plot_data_item = self.plotWidget.plot(x[0:-1:100], y[0:-1:100], name=name)
        streaming_pdi = StreamingDataItem(plot_data_item, **self.defaultPlotKwargs)
        self.curveD[name] = streaming_pdi

    def setData(self, data, name=None):
        if name is None:
            name = next(iter(self.curveD)) # update the "first" item
        self.curveD[name].setData(data)

    def setAppendMode(self, max_samples=None):
        for key,item in self.dataD.items():
            print('setting append for curve {}'.format(key))
            item.setAppendMode(max_samples)

    def setReplaceMode(self):
        for item in self.dataD:
            item.setReplaceMode()

    #def setData(self, name, data):
    #    self.plotWidget

class DockPlotManager(object):
    """ A class to simply manage a pyqtgraph DockArea, with docks that contain easy-to-update plots..
    Tha idea is that you make a DPM, feed it data, and it will do an
    ok job of plotting that data and remembering your settings (chosen
    by mouse clicks). WIP.
dpm
    Ultimately it should be a quick way of showing updating experiment data.;

    Use case:
    dpm = DockPlotManager("MyExperiment")
    dpm.updateCurve("raw", (x,y), widgetName=None)
    #If it doesn't already exist, the above will add a curve named "raw" to the database and add plot it in it's own window.
    #If "widgetName" is specified, then the widget with that name will be updated with a curve called "raw". Else the widget will be created.
    #TODO If the curve already exists, any plots that depend on it will be updated

    #Alternatively:
    dpm.updateFromDict(widgetName, {'trace1': y, 'trace2':y2})
    #Will update several curves at once


    """
    win=None
    area=None
    dockD=None
    app = None

    def __init__(self, name='Dock window', defaultPlotKwargs = {}):
        self.state = None
        self.name=name
        self.app = pg.mkQApp("DPM App")
        area = DockArea()
        win = pg.QtWidgets.QMainWindow()
        #win.resize(400,300)
        win.setWindowTitle(name)
        self.area=area
        self.dockD={}
        self.dataD = defaultdict(list)
        self.win=win
        self.defaultPlotKwargs= defaultPlotKwargs

        #Save area
        #saveDock=Dock("saveArea", size=(10,10))
        #w1 = pg.LayoutWidget()
        label = pg.QtWidgets.QLabel("""Save/restore state""")
        saveBtn = pg.QtWidgets.QPushButton('Save state')
        restoreBtn = pg.QtWidgets.QPushButton('Restore state')
        restoreBtn.setEnabled(False)
        #w1.addWidget(label, row=0, col=0)
        #w1.addWidget(saveBtn, row=1, col=0)
        #w1.addWidget(restoreBtn, row=2, col=0)
        #saveDock.addWidget(w1)
        #saveBtn.clicked.connect(self.save)
        #restoreBtn.clicked.connect(self.load)
        #self.saveBtn=saveBtn
        #self.restoreBtn=restoreBtn
        #self.area.addDock(saveDock)

        # create jupyter console widget (and  dock)
        self.jupyter_console_widget = JupyterConsoleWidget()
        self.jupyter_console_dock = Dock("Jupyter Console Dock", size=(1,1))
        self.jupyter_console_dock.addWidget(self.jupyter_console_widget)
        kernel = self.jupyter_console_widget.kernel_manager.kernel
        kernel.shell.push(dict(np=np, dpm=self))
        self.jpkernel = kernel
        area.addDock(self.jupyter_console_dock, "bottom" )
        win.setCentralWidget(area)


        self.win.show()

    def save(self):
        self.state = self.area.saveState()
        pickle.dump(self.state, open("dockManager_{}_{}.pkl".format(__name__, self.name), 'wb') )
        self.restoreBtn.setEnabled(True)
    def load(self):
        try:
            if self.state is None:
                state=pickle.load(open("dockManager_{}_{}.pkl".format(__name__, self.name), 'rb') )
                #state={k:v for k,v in state if k in self.dockD.keys()}
            print(self.state)
            self.area.restoreState(self.state, missing='ignore')
        except Exception as e:
            print(e.args[0])
            raise(e)

    def addDockPlot(self, name, curves=None, title=None, defaultPlotKwargs = {}):
        dockPlot=DockPlot(name, curves=curves, title=title, defaultPlotKwargs=defaultPlotKwargs)
        self.area.addDock(dockPlot)
        self.dockD[name]=dockPlot
        for name,item in dockPlot.dataD.items():
            self.dataD[name].append(item)
        return dockPlot
    def getPlotItem(self, name):
        return self.dockD[name].findChild(pg.PlotWidget).plotItem

    @classmethod
    def format_input(data):
        """ Make input data into a standard format.

        Mostly what we want is to end up with a "Curve": x, y, label, category

        Possible inputs:
        Mapping, e.g.: {"x":, "y":, "label":, "category"} (where anything except "y" is optiona)
        Single array: y 
        A tuple of two arrays: x, y

        If elements are left out, a default target is assumed.
        """
        
        #if isinstance(data, Mapping): #It's a dictionary, with elements {x,y,label}


        pass

    #def updateCurve(self, plot_name, curve_name, data):
    def updateCurve(self, curve):
        #data = (x,) if y is None else (x,y)
        if curve.category not in self.dockD:
            self.addDockPlot(name = curve.category, title = curve.category)
        self.dockD[curve.category].setData((curve.x, curve.y), name = curve.label)

    def addNewItem(self, data_name, data, dock_name):
        """ Make a new dataItem from some data, and add it.
        to a plot. If the named plot doesn't exist, we'll make that too.
        """
        if dock_name is None:
            if len(self.dockD):
                dock_name = list(self.dockD.keys())[0] #make it the first one
            else:
                dock_name = random_word()

        if dock_name not in self.dockD: #The named dock d
            dp= self.addDockPlot(dock_name, curves={data_name: data}, title=dock_name, defaultPlotKwargs = self.defaultPlotKwargs)
            newDI = dp.dataD[data_name]
        else:
            dp = self.dockD[dock_name]
            newDI = dp.addNewItem(data_name, data)
            self.dataD[data_name].append(newDI)
        #print(f'{data_name}: {self.dataD[data_name]} after addNewItem')
        return newDI

    #User interface below:
    def input_data(self, data, name=None):
        """ Recieve new data and do something sensible with it.

        Ways to call input_data:
        * input_data(data)
        * input_data(data: DataArray)
        * input_data(data: dict( can be turned into an xarray)
        After this, it'll be an xarray.DataArray
         
        name can have parts to it (i.e. absorption:start, and absorption:end). By default, traces with the same 'category' (the first part) will be plotted on the same graph
        """
        #curveL = self.format_input(data)
        if hasattr(data, 'shape'): #Make it an xarray
            data = x.DataArray(data)
        elif isinstance(data, Mapping): #It's a dictionary
            if 'name' in data: # it's a full description
                name = data['name']
                
                if not 'type' in dataD or dataD['type'] == 'curve':
                    self.updateCurve(curve)
        else:
            print("Not sure what to do with type {}".format(dataD['type']))

        if not data.name and not name:
            data.name= random_word()
            
    def addData(self, name, data, dock_name=None):
        dataItems = self.dataD[name]
        if not dataItems: #not in the dict- put it in a new dock
            dataItem = self.addNewItem(name, data, dock_name)
            #dataItems.append(dataItem)
        else: 
            #print(dataItems)
            for dataItem in dataItems:
                dataItem.addData(data)

    def updateFromDict(self, D):
        """ Update/create plots from the dictionary D containing curves to be plotted
        """
        for plot_name, data in D.items():
            if plot_name not in self.dockD:
                self.addDockPlot(plot_name)
            if isinstance(data, Mapping): #It's a dictionary, with elements {x,y,label}
                for curve_name, dat in data:
                    self.updateCurve(plot_name, *dat, curve_name)
            else:
                if len(data)>2: # If so, we'll assume it's a single array, not x,y
                    data = (data,)
                self.updateCurve(plot_name, *data)


if __name__ =="__main__":
    #Run in ipython (probably with --pylab)
    from numpy import *
    from PyQt6 import QtTest
    x = linspace(0,1,1000)
    y = sin(2*pi*30*x)
    dpm = DockPlotManager("MyExperiment")
    dpm.addDockPlot("dp_one", curves={"cv_one":{'x':x,'y':y}, "cv_two":{'x':x**2, 'y':y} }, title="first dp")
    if 1:
        #dpm.addDockPlot("dp_two", curves={"cv_three":(x,exp(x)), "cv_four":(x**2, x) }, title="second dp")
        dpm.addDockPlot("dp_two", curves={"cv_three":np.array((x,exp(x))).T, "cv_four":{'x':x**2, 'y':x} }, title="second dp")

        x2 = linspace(1,2,100)
        #dpm.addData("cv_three", (x2, 2*sin(2*pi*x2)))
        #dpm.updateCurve("test", "one", (x,y**2))
        #dpm.updateFromDict({'raw' : (x, y)})

        dpm.dockD['dp_two'].setAppendMode( max_samples=100)

        for k in range(1,4):
            x = np.linspace(0,.5,5)+k*0.5
            y = np.sin(2*pi*x)
            dpm.addData("cv_four", (x, y))
            QtTest.QTest.qWait(300)



