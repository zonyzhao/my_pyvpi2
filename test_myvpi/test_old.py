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

process = psutil.Process(os.getpid())
GMEM=0

def print_mem():
    GMEM=process.memory_info()[0]
    print("MEM: %d"%GMEM)

pyvpi.setDebugLevel(40)

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

def func(self):
    # print("here is wait @%d"%Simtime.value)
    new_loop.call_soon_threadsafe(self.done)
    while(any([x.arm_time<Simtime.value for x in pending_task])):
        time.sleep(0.001)
    # print_mem()
    pyvpi.removeCb(self)

class Timer(pyvpi.CbData):
    def __init__(self, t=0, unit=None):
        super().__init__()
        self.t = t
        self.unit = unit
        if t==0 or unit is None:
            self.name = "Timer {}".format(self.t)
        else:
            self.name = "Timer {} {}".format(self.t, self.unit)
        self.reason = cons.cbAfterDelay
        self.time = pyvpi.Time(cons.vpiSimTime)
        self.time.low = 0
        self.time.high = 0
        self.setAbsTime(self.t, self.unit)
        self.wait_ev = asyncio.Event()
        self.callback = func
    
    def setAbsTime(self, time, unit=None):
        unit_sim = _get_unit()
        unit_target = 0
        if unit == None:
            unit_target = unit_sim
        else:
            if unit in ['s', 'ms', 'us', 'ns', 'ps', 'fs']:
                unit_target = time_unit[unit]
        dxt = time*10**(unit_target-unit_sim)
        self.time.low = int(dxt%(2**32))
        self.time.high = int(dxt//(2**32))
    


       
    def register(self):
        pyvpi.registerCb(self)

    def __await__(self):
        self.setAbsTime(self.t, self.unit)
        self.wait_ev = asyncio.Event()
        self.register()
        self.arm_time = Simtime.value
        pending_task.append(self)
        # print('arm_time:', self.arm_time)
        return self.wait().__await__()
    
    def done(self):
        self.wait_ev.set()
        

    async def wait(self):
        await self.wait_ev.wait()
        pending_task.remove(self)


#IPython.embed()

Rega = pyvpi_tools.Reg("top.a")
async def task():
    a = Timer(1,'us')
    while(1):
        # print('Ctime1=%d'%Simtime.value)
        await a
        # print('Ctime2=%d'%Simtime.value)
        Rega.value +=1


import tracemalloc



async def task2():
    n = 0
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()
    for _ in range(10000):
        # print('T2time1=%d'%Simtime.value)
        await Timer(1.31,'us')
    snapshot2 = tracemalloc.take_snapshot()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    print("[ Top 10 differences ]")
    for stat in top_stats[:10]:
        print(stat)




# add_task(task())
add_task(task2())

time.sleep(0.2)