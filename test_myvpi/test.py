import pyvpi
import pyvpi_cons as cons
import pyvpi_tools
from pyvpi_tools import AtTime
import sys
import os
import time
from threading import Thread, current_thread
from pyvpi_tools import Simtime
import asyncio
import IPython
import uuid
import psutil
import gc

pyvpi.setDebugLevel(40)

process = psutil.Process(os.getpid())
GMEM=0

def print_mem():
    GMEM=process.memory_info()[0]
    print("MEM: %d"%GMEM)



print('*'*20)
print("Simtime = {}".format(Simtime.value))

time_unit = {'s':0, 'ms':-3, 'us':-6, 'ns':-9, 'ps':-12, 'fs':-15}
pending_task = []

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,), daemon=True, name='thread1')
t.start()

        
def add_task(coro):
    asyncio.run_coroutine_threadsafe(coro, new_loop)

async def printx(x):
    while(1):
        print("PRINT%d"%x)
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

def func(self):
    try:
        # print("here is wait @%d"%Simtime.value)
        new_loop.call_soon_threadsafe(self.wait_ev.set)
        # print(pending_task)
        while(1):
            # print("loop")
            time.sleep(0.001)
            if self.wait_ev.is_set():
                break
        pending_task.remove(self)
        pyvpi.removeCb(self)
        # print("end of call back")
    except Exception as e:
        print(e)

class Timer(pyvpi.CbData):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        self.evs = []
        #self.wait_ev = Wait_Event(Simtime.value)
        
    def create_cbdata(self):
        cbdata = pyvpi.CbData()
        cbdata.reason = cons.cbAfterDelay
        cbdata.time = pyvpi.Time(cons.vpiSimTime)
        cbdata.time.low = 0
        cbdata.time.high = 0
        setAbsTime(cbdata, self.t, self.unit)
        cbdata.callback = func
        cbdata.wait_ev = Wait_Event(Simtime.value)
        return cbdata

    def __await__(self):
        cbdata = self.create_cbdata()
        pyvpi.registerCb(cbdata)
        pending_task.append(cbdata)
        # print("start wait", cbdata)
        return cbdata.wait_ev.wait().__await__()
        
#IPython.embed()

Rega = pyvpi_tools.Reg("top.a")
Regb = pyvpi_tools.Reg("top.b")
async def task():
    try:
        n = 0
        a = Timer(1,'us')
        for _ in range(1000):
            # print('Ctime1=%d'%Simtime.value)
            await Timer(1,'us')
            n+=1
            print(Rega.value)
            # Rega.value = n
            # print('Ctime2=%d'%Simtime.value)
            # Rega.value= Rega.value+1
            # if(n%100==0):
            #     print_mem()
            #     print(sys.getrefcount(Rega))
            #     # print(sys.getrefcount(func))           
    except Exception as e:
        print(e)
    print("TASK DONE\n")


async def task2():
    try:
        a = pyvpi_tools.Reg('top.a')
        b = pyvpi_tools.Reg('top.a')
        n = 0
        x = Timer(1,'us')
        while(1):
            # print('T2time1=%d'%Simtime.value)
            await x
            n+=1
            m = a.value + 1
            b.value = m
            # a.value = n + 1
            # print(sys.getrefcount(a._value))
            # await asyncio.sleep(0.001)
            if(n%500==0):
                print_mem()
                # print('task2: ', sys.getrefcount(Regb))
                # print(sys.getrefcount(a._handle))
    except Exception as e:
        print(n)
        print(e)



# add_task(task())
add_task(task2())

time.sleep(0.2)