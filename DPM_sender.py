import zmq
"""
Maybe this is more of a general "Data publisher"

data sending format:
a dictionary with:
* name
* data <- could also be a pandas array or xarray or something? 
* axis (optional)
* category (optional)
* timestamp (optional)
* other metadata (optional)
* type (optional, but probably a curve)
Should probably change this to use tinyrpc
"""
#import zmq
#
#from tinyrpc import RPCClient
#from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
#from tinyrpc.transports.zmq import ZmqClientTransport
#
#ctx = zmq.Context()
#
#rpc_client = RPCClient(
#    JSONRPCProtocol(),
#    ZmqClientTransport.create(ctx, 'tcp://127.0.0.1:5001')
#)
#
#str_server = rpc_client.get_proxy()
#
## call a method called 'reverse_string' with a single string argument
#result = str_server.reverse_string('Hello, World!')
#
#print("Server answered:", result)
import pickle

PORT = 5561
class DPMSender(object):
    def __init__(self, pubName=b"default"):
        self.sock= zmq.Context().socket(zmq.PUB)
        self.sock.set_hwm(10)
        self.sock.bind("tcp://*:%i" % PORT)
        self.pubName = bytes(pubName, "utf") #tag associated with this sender

       
    def pubPoints(self, name, y, x=None):
        datD = {"name": name,
                'data': y,
                'coords': x,
                'type': 'points'}
        msg = b'%s '%self.pubName + pickle.dumps(datD)

    def pubTraces(self, name, y, x=None):
        datD = {"name": name,
                'data': y,
                'coords': x,
                'type': 'traces'}
        #msg = b'%s '%self.pubName + pickle.dumps({name: (x,y)})
        msg = b'%s '%self.pubName + pickle.dumps(datD)
        self.sock.send(msg)

    def pubArbData(self, name, data, dat_type='arb'):
        datD = {"name": name,
                'data': data,
                'type': dat_type}
        msg = b'%s '%self.pubName + pickle.dumps(datD)
        self.sock.send(msg)

    def close(self):
        '''Closes the port (ZMQ)'''
        self.sock.close()

if __name__ == "__main__":
    import numpy as np
    from time import sleep
    sender = DPMSender(pubName="myexperiment")
    x = np.linspace(0,1,1000)
    k = 0
    while 1:
        r = np.random.uniform()
        y= np.sin(2*np.pi*10*x**2 + 0.1*k) +r
        y2= np.sin(2*np.pi*10*x**2* (0.2*(k %10) ) ) +r
        sender.pubTraces(b"test1", x, y)
        sender.pubTrace(b"test2", x, y2)
        print("sent")
        sleep(0.5)
        
