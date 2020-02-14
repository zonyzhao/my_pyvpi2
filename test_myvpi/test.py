import pyvpi
import pyvpi_cons as cons
import pyvpi_tools
import sys
import os
import time
from threading import Thread, current_thread
from pyvpi_tools import Simtime
import asyncio
import IPython
import uuid
import psutil

process = psutil.Process(os.getpid())

def print_mem():
    print("MEM: %d"%process.memory_info()[0])

pyvpi.setDebugLevel(40)

print('*'*20)
print("Simtime = {}".format(Simtime.value))

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
        self.callback = self.func
    
    def setAbsTime(self, time, unit=None):
        time_unit = {'s':0, 'ms':-3, 'us':-6, 'ns':-9, 'ps':-12, 'fs':-15}
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
    
    def func(self, arg):
        print("here is wait @%d"%Simtime.value)
        new_loop.call_soon_threadsafe(self.done)
        while(self.wv<Simtime.value):
            print("WV:", self.wv)
            time.sleep(0.0001)
        print_mem()

       
    def register(self):
        pyvpi.registerCb(self)

    def __await__(self):
        self.setAbsTime(self.t, self.unit)
        self.wait_ev = asyncio.Event()
        self.register()
        self.wv = Simtime.value
        print('Expect WV:', self.wv)
        return self.wait().__await__()
    
    def done(self):
        self.wait_ev.set()
        #self.wv = 1

    async def wait(self):
        await self.wait_ev.wait()

#IPython.embed()

async def task():
    a = Timer(1,'us')
    while(1):
        print('Ctime1=%d'%Simtime.value)
        await a
        print('Ctime2=%d'%Simtime.value)

async def task2():
    b = Timer(1.31,'us')
    while(1):
        print('T2time1=%d'%Simtime.value)
        await b
        print('T3time2=%d'%Simtime.value)

add_task(task())
add_task(task2())

time.sleep(0.2)