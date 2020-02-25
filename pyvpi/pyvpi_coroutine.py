
import pyvpi
import pyvpi_cons as cons
import pyvpi_tools
from pyvpi_tools import AtTime, _get_unit, get_simtime_unit, setAbsTime
import sys
import os
import time
import threading
from threading import Thread, current_thread
from pyvpi_tools import Simtime
import asyncio
import IPython
import uuid
import psutil
import gc
import inspect

pyvpi.printf("************************\n")
pyvpi.printf("PYVPI_COROUTINE         \n")
pyvpi.printf("************************\n")

def public(f):
    """Use a decorator to avoid retyping function/class names.
    * Based on an idea by Duncan Booth:
    http://groups.google.com/group/comp.lang.python/msg/11cbb03e09611b8a
    * Improved via a suggestion by Dave Angel:
    http://groups.google.com/group/comp.lang.python/msg/3d400fb22d8a42e1
    Take this fuction from COCOTB
    """
    all = sys.modules['__main__'].__dict__
    if f.__name__ not in all.keys():  # Prevent duplicates if run from an IDE.
        all[f.__name__]=f
    return f

public(public)



def delay(n):
    time.sleep(0.01)

def get_current_function_name():
    return inspect.currentframe().f_code.co_name

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()



schedule_loop = asyncio.new_event_loop()
loop_thread = Thread(target=start_loop, args=(schedule_loop,), daemon=True, name='loop_thread')
loop_thread.start()

print(sys.modules['__main__'].__dict__)

sys.modules['__main__'].__dict__['schedule_loop']=schedule_loop
sys.modules['__main__'].__dict__['loop_thread']=loop_thread
        
# public(schedule_loop)
# public(_thread)

@public
def fork(coro):
    global schedule_loop
    return asyncio.run_coroutine_threadsafe(coro, schedule_loop)

@public
class Wait_Event(asyncio.Event):
    def __init__(self, t):
        super().__init__()
        self.arm_time = t
        self.waiting = 0

@public
def loop_schedule(self):
    try:
        thread = threading.current_thread()
        if thread.name=="MainThread":
            self.loop.call_soon_threadsafe(self.wait_ev.set)
        else:
            self.wait_ev.set()
            return
        while(1):
            time.sleep(0.0001)
            if self.wait_ev.is_set():
                if "Future pending" in repr(self.ct):
                        break
                elif self.ct.done():
                        break
                else:
                    continue
    except Exception as e:
        print(e)

@public
def TimerFunc(self):
    # pyvpi.printf("Timer Func @{}\n".format(Simtime.value))
    loop_schedule(self)
    pyvpi.removeCb(self)

@public
def ChangeFunc(self):
    loop_schedule(self)
    pyvpi.removeCb(self)

@public
def PosEdgeFunc(self):
    if self.value.value>self.edge:
        ChangeFunc(self)

@public
def NegEdgeFunc(self):
    if self.value.value<self.edge:
        ChangeFunc(self)

@public
class Timer(object):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        # pyvpi.printf(self.name)
        # pyvpi.printf('\n')
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbAfterDelay
        cbdata.time = pyvpi.Time(cons.vpiSimTime)
        cbdata.time.low = 0
        cbdata.time.high = 0
        setAbsTime(cbdata, self.t, self.unit)
        cbdata.callback = TimerFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata

    def __await__(self):
        # pyvpi.printf("1\n")
        cbdata = self.create_cbdata()
        # pyvpi.printf("2\n")
        cbdata.loop = asyncio.get_running_loop()
        # pyvpi.printf("3\n")
        cbdata.ct = asyncio.current_task(cbdata.loop )
        # pyvpi.printf("4\n")
        pyvpi.registerCb(cbdata)
        # pyvpi.printf("register timer {}\n".format(self.name))
        return cbdata.wait_ev.wait().__await__()

@public        
class RWSynch(object):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbReadWriteSynch
        cbdata.time = pyvpi.Time(cons.vpiSimTime)
        cbdata.time.low = 0
        cbdata.time.high = 0
        setAbsTime(cbdata, self.t, self.unit)
        cbdata.callback = TimerFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata

    def __await__(self):
        cbdata = self.create_cbdata()
        cbdata.loop = asyncio.get_running_loop()
        cbdata.ct = asyncio.current_task(cbdata.loop )
        pyvpi.registerCb(cbdata)
        return cbdata.wait_ev.wait().__await__()

@public
class Edge(object):
    def __init__(self, trigobj=None, edge = 1):
        super().__init__()
        self.edge = edge
        if trigobj == None:
            self.reg = None
        elif type(trigobj)==str:
            self.reg = pyvpi_tools.Reg(trigobj)
        else:
            self.reg = trigobj
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbValueChange
        cbdata.trgobj = self.reg.handle
        cbdata.callback = ChangeFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        cbdata.reg = self.reg
        cbdata.edge = self.edge
        return cbdata

    def __await__(self):
        cbdata = self.create_cbdata()
        cbdata.loop = asyncio.get_running_loop()
        cbdata.ct = asyncio.current_task(cbdata.loop )
        pyvpi.registerCb(cbdata)
        print("start Edge wait "+repr(self)+'at time:%d\n'%Simtime.value)
        return cbdata.wait_ev.wait().__await__()

@public
class PoseEdge(Edge):
    def __init__(self, trigobj= None):
        super().__init__(trigobj, 0.5)

    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbValueChange
        cbdata.reg = self.reg
        cbdata.trgobj = self.reg.handle
        cbdata.callback = PosEdgeFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        cbdata.edge = self.edge
        return cbdata

@public
class NegEdge(Edge):
    def __init__(self, trigobj= None):
        super().__init__(trigobj, 0.5)

    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbValueChange
        cbdata.reg = self.reg
        cbdata.edge = self.edge
        cbdata.trgobj = self.reg.handle
        cbdata.callback = NegEdgeFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata





pyvpi.printf("************************\n")
pyvpi.printf("PYVPI_COROUTINE IMPORTED\n")
pyvpi.printf("************************\n")