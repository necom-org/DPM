""" Little server that listens on a given port for sent trace data. The server simply sends them on to a DockPlotManager. It doesn't do any clever processing.
"""
import zmq
import pickle
from DPM import DockPlotManager
import pyqtgraph as pg

PORT = 5561
class DPMListener(object):
    """A simple way of updating a DAM from other processes. Use DAMSender
    from other processes to send data here."""
    timer = None
    def __init__(self, subName=b"default", dpm=None):
        try:
            subName = bytes(subName, "utf")
        except TypeError:
            pass
        self.sock= zmq.Context().socket(zmq.SUB)
        self.sock.set_hwm(10)
        self.sock.connect("tcp://localhost:%s" % PORT)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"%s" % subName )
        if dpm is None:
            dpm =DockPlotManager(name=str(subName))
        self.dpm = dpm
        if 0:
            rawPltL=[]
            for col in range(3):
                for row in range(3):
                    rawPltL.append(gwRaw.addPlot(col=col, row=row))
            self.rawPltL=rawPltL
            subPltL=[]
            for col in range(2):
                for row in range(2):
                    subPltL.append(gwRaw.addPlot(col=col, row=row))
            self.gwRaw=gwRaw
            self.gwSub=gwSub

    @staticmethod
    def parse_topic(topic_st):
        category = None
        splt = topic_st.split(b":")
        label = splt.pop()
        if splt:
            category = splt.pop()
        if splt:
            print("extra data in topic: '{}' is left".format(splt))
        return label, category
    def update(self):
        if self.sock.poll(10):
            topic,msg= self.sock.recv().split(b' ', 1)
            label, category = self.parse_topic(topic)
            data = pickle.loads(msg)
            print(label,category)
            print(data)
            #self.dpm.input_data()
            #self.dpm.updateFromDict(D)
            #print("{} updated".format(topic))
        else:
            print("Nothing recieved")
            return None

    def startUpdating(self, interval):
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval)

    def stop(self):
        self.timer.stop()

    def close(self):
        self.sock.close()
        if self.timer:
            self.timer.stop()

if __name__ == "__main__":
    listener = DPMListener("myexperiment")
    listener.startUpdating(100)
