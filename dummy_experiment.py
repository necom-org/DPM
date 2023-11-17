""" Let's pretend we're doing an experiment.

We'll record scope data, and send that over to a DPM. We'll also do some processing on it, and send that over too.
"""
import numpy as np
from DPM_sender import DPMSender
import time
from time import sleep
if __name__ == "__main__":
    Npts = 100
    datL = np.random.normal(size=(50,Npts))

    def getScope():
        k = 0
        while 1:
            x = np.linspace(0,1,Npts) + time.time()
            dat = datL[k] + np.sin(2*np.pi*x*1.8)
            yield x, dat
            k = (k+1) % len(datL)

    sender = DPMSender("myexperiment")

    scope = getScope()
    while 1:
        # Get scope data
        x,y = next(scope)
        V1 = (np.sin(2*np.pi*x*1.8)*y).sum()
        V2 = (np.cos(2*np.pi*x*1.8)*y).sum()
        tNow = time.time()

        sender.pubTraces(b"test1", x, y)
        sender.pubTraces(b"several", x, [y**2, y**3, y**4])
        sender.pubPoints(b"areas", tNow, [V1, V2])

        print("sent")
        sleep(0.4)
