
import pyvpi
import pyvpi_cons as cons
import pyvpi_tools
from pyvpi_tools import AtTime
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

RT = []
PENDING_CB = []
process = psutil.Process(os.getpid())
GMEM=0

def print_mem():
    GMEM=process.memory_info()[0]
    pyvpi.printf("MEM: %d\n"%GMEM)


main_lock = threading.Lock()

# from pyvpi import printf
# print=printf

print('*'*20)
print('\n')
print("Simtime = {}".format(Simtime.value))
print('\n')
time_unit = {'s':0, 'ms':-3, 'us':-6, 'ns':-9, 'ps':-12, 'fs':-15}
pending_task = []

def delay(n):
    time.sleep(0.01)

def get_current_function_name():
    return inspect.currentframe().f_code.co_name

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,), daemon=True, name='thread1')
t.start()

        
def add_task(coro):
    return asyncio.run_coroutine_threadsafe(coro, new_loop)

async def task3():
    for _ in range(100):
        await asyncio.sleep(1)
        print("T3\n")

# add_task(task3())

async def printx(x):
    while(1):
        print("PRINT%d"%x)
        print('\n')
        await asyncio.sleep(x)

def _get_unit():
    return pyvpi.getTimeScale(cons.vpiTimePrecision)-2**32

def get_simtime_unit():
    unit_dict = {0:'s', -3:'ms', -6:'us', -9:'ns', -12:'ps', -15:'fs'}
    return unit_dict[_get_unit()]

class Wait_Event(asyncio.Event):
    def __init__(self, t):
        super().__init__()
        self.arm_time = t
        self.waiting = 0

def setAbsTime(cbdata, time, unit=None):
    unit_sim = _get_unit()
    unit_target = 0
    if unit == None:
        unit_target = unit_sim
    else:
        if unit in ['s', 'ms', 'us', 'ns', 'ps', 'fs']:
            unit_target = time_unit[unit]
    dxt = time*10**(unit_target-unit_sim)
    cbdata.time.low = int(dxt%(2**32))
    cbdata.time.high = int(dxt//(2**32))


XXX = 0

def loop_schedule(self):
    try:
        # pyvpi.printf(repr(new_loop))
        # pyvpi.printf('\n')
        thread = threading.current_thread()
        # pyvpi.printf("***THRADNAME= %s***\n"%thread.name)
        if thread.name=="MainThread":
            # pyvpi.printf("***call_soon_threadsafe***\n")
            self.loop.call_soon_threadsafe(self.wait_ev.set)
        else:
            self.wait_ev.set()
            return
        # pyvpi.printf(repr(self.ct))
        # pyvpi.printf('\n')
        # pyvpi.printf("wait_ev is ")
        # pyvpi.printf(repr(self.wait_ev))
        # pyvpi.printf('\n')
        # pyvpi.printf(repr(self))
        # pyvpi.printf('\n')
        while(1):
            time.sleep(0.0001)
            if self.wait_ev.is_set():
                if "Future pending" in repr(self.ct):
                        break
                elif self.ct.done():
                        break
                else:
                    continue
        # pyvpi.printf('\n')
        # pyvpi.printf("<<<<<<<<<<<<<<<<<<<<<<<<<<<\n")
        # pyvpi.printf(repr(self.ct))
        # pyvpi.printf('\n')
    except Exception as e:
        print(e)

def TimerFunc(self):
    # with main_lock:
    # pyvpi.printf("<<<<<<<<<<<<<<TimerFunc<<<<<<<<<<<<<\n")
    # pyvpi.printf("<<<<<<<<<<<<Simtime=%d<<<<<<<<<<<\n"%Simtime.value)
    loop_schedule(self)
    # time.sleep(0.0016)
    pyvpi.removeCb(self)
    # time.sleep(0.0016)


def ChangeFunc(self):
    # with main_lock:
    # pyvpi.printf("<<<<<<<<<<<<<<ChangeFunc<<<<<<<<<<<<<\n")
    # pyvpi.printf("<<<<<<<<<<<<<<Simtime=%d<<<<<<<<<<<\n"%Simtime.value)
    # pyvpi.printf("<<<<<<<<<<<<<<CbTime=%d<<<<<<<<<<<\n"%self.wait_ev.arm_time)
    # tasks = asyncio.all_tasks(new_loop)
    # pyvpi.printf(repr(tasks))
    # pyvpi.printf('\n')    
    loop_schedule(self)
    # time.sleep(0.0016)
    pyvpi.removeCb(self)
    # time.sleep(0.0016)

def PosEdgeFunc(self):
    if self.value.value>self.edge:
        ChangeFunc(self)

def NegEdgeFunc(self):
    if self.value.value<self.edge:
        ChangeFunc(self)

class Timer(object):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        self.evs = []
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbAfterDelay
        # cbdata.reason = cons.cbReadWriteSynch
        cbdata.time = pyvpi.Time(cons.vpiSimTime)
        cbdata.time.low = 0
        cbdata.time.high = 0
        setAbsTime(cbdata, self.t, self.unit)
        cbdata.callback = TimerFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata

    def __await__(self):
        cbdata = self.create_cbdata()
        cbdata.loop = asyncio.get_event_loop()
        cbdata.ct = asyncio.current_task(cbdata.loop )
        pyvpi.registerCb(cbdata)
        # PENDING_CB.append(cbdata)
        # print("start wait "+repr(self)+'\n')
        return cbdata.wait_ev.wait().__await__()
        
class RWSynch(object):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        self.evs = []
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbReadWriteSynch
        # cbdata.reason = cons.cbReadWriteSynch
        cbdata.time = pyvpi.Time(cons.vpiSimTime)
        cbdata.time.low = 0
        cbdata.time.high = 0
        setAbsTime(cbdata, self.t, self.unit)
        cbdata.callback = TimerFunc
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata

    def __await__(self):
        cbdata = self.create_cbdata()
        cbdata.loop = asyncio.get_event_loop()
        cbdata.ct = asyncio.current_task(cbdata.loop )
        pyvpi.registerCb(cbdata)
        # PENDING_CB.append(cbdata)
        # print("start wait "+repr(self)+'\n')
        return cbdata.wait_ev.wait().__await__()

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
        #self.wait_ev = Wait_Event(Simtime.value)
        
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
        cbdata.loop = asyncio.get_event_loop()
        cbdata.ct = asyncio.current_task(cbdata.loop )
        pyvpi.registerCb(cbdata)
        print("start Edge wait "+repr(self)+'at time:%d\n'%Simtime.value)
        return cbdata.wait_ev.wait().__await__()

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



async def task():
    n = 0
    Rega = pyvpi_tools.Reg("top.a")
    Regb = pyvpi_tools.Reg("top.b")
    clk = pyvpi_tools.Reg("top.clk")
    try:
        await Timer(100,'us')
        for _ in range(1000):
            print('Ctime1=%d \n'%Simtime.value)
            print('waiting trigger\n')
            await Edge(Rega)
            print("edge triggered\n")
            # print(Rega.value)
            n+=1
            # print(n)
            # Rega.value = n
            # print('Ctime2=%d'%Simtime.value)
            # Rega.value= Rega.value+1
            if(n%100==0):
                print_mem()
            #     print(sys.getrefcount(Rega))
            #     # print(sys.getrefcount(func))           
    except Exception as e:
        RT.append(e)
        print(RT)
    print("TASK DONE\n")


a = pyvpi.handleByName('top.a')
x = pyvpi.Value(cons.vpiIntVal)
y = pyvpi.Value(cons.vpiIntVal)

async def task2():
    try:
        n = 0
        k = 0
        dd = Timer(1,'us')
        # for _ in range(1000):
        while(1):
            # print('T2time1=%d'%Simtime.value)
            await Timer(1.0,'us')
            # await RWSynch(0)
            # print("HAHA")
            # Simtime.value
            # time.sleep(0.001)
            n+=1
            # x.value
            pyvpi.getValue(a,x)
            # print(repr(type(x.value)))
            # print('*****')
            # # print('\n')
            x.value = x.value+1
            # k= x.value + 1
            # # # # if x.value==128:
            # # #     # x.value = 0
            # # y.value = n
            pyvpi.putValue(a,x)
            # print('value changed\n')
            # print(n)
            # print('x = %s\n'%x.value)
            # print('y = %s\n'%y.value)
            # print()
            # await Timer(4, 'us')
            # b.value = m
            # a.value = n + 1
            # print(sys.getrefcount(a._value))
            # await asyncio.sleep(0.001)
            # print(asyncio.all_tasks(new_loop))
            if(n%5000 == 0):
                print_mem()
                # print(Simtime.value)
                # print(n)
                # gc.collect()
                # print("GC: %d"%len(gc.get_objects()))
                # print('task2: ', sys.getrefcount(Regb))
                # print(sys.getrefcount(a._handle))
    except Exception as e:
        RT.append(e)
        print(RT)


async def task3():
    for _ in range(100):
        await asyncio.sleep(0.05)
        print("T3\n")
    

# @pyvpi_tools.At('top.a')
# def printx(self):
#     print("hellox")
add_task(task())

add_task(task2())
# add_task(task2())


# @pyvpi_tools.AtTime(200e-6)
# def ip(self):
#     IPython.embed()

# @pyvpi_tools.AtTime(1000000.0e-9)
# def ip(self):
#     IPython.embed()

pyvpi.setDebugLevel(40)
# time.sleep(0.6)

@pyvpi_tools.SysTask(tfname="$ipython")
def itr(self):
    print('heelo')
    IPython.embed()
