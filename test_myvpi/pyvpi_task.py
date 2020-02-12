import pyvpi
import pyvpi_tools 
from pyvpi_tools import Simtime
import pyvpi_cons as cons
import sys
import os
import numpy as np
import threading
import asyncio
from functools import partial
import time
from IPython import embed
import traceback
import gc

from ctypes import cdll, Structure, c_char_p, c_uint8,c_wchar_p, c_uint16, c_uint32, byref, c_uint, c_ubyte, c_ulonglong, c_char, c_int, c_byte


running_loop = []

DEBUG=1

class EXT():
    def __init__(self):
        self._lib = cdll.LoadLibrary("./INCA_libs/worklib/main/sv/_sv_export.so")
        self.scope = pyvpi.getSvScopeName()

    def force(self, name, val):
        if pyvpi.getSvScopeName()== None:
            pyvpi.setSvScopeByName(self.scope)
        self._lib.dpi_force(c_char_p(('main.dut.'+name).encode()), c_char_p(str(val).encode()))


SIM_LOCK = threading.Event() # a thread event to block ncsim
SIM_LOCK.sim_run = 0  # indicator for sim

# _lock = threading.Lock()
# PENDING_TASK = []

class _event(pyvpi.CbData):
    '''Evt consume time
    '''
    def __init__(self):
        super().__init__()
        self.name = 'sync'
        self.reason = cons.cbReadWriteSynch
        self.time = pyvpi.Time(cons.vpiSimTime)
        self.time.low = 0
        self.time.high = 0
        self.callback = self.__class__.func

    def log(self, info='CALL', ex=None, ts=1):
        if DEBUG==1:
            timestr = ': at Sim:%d  CPU %f'%(Simtime.value, time.time())
            s = '{:10}: '.format(self.name)
            s += '{:15}: '.format(info)
            s += '{} '.format(ex)
            if ts:
                s += timestr
            s += '\n'
            pyvpi.printf(s)

    def register(self):
        pyvpi.registerCb(self)

    @staticmethod
    def func(self):
        pass

    def remove(self):
        pyvpi.removeCb(self)

    def setSimTime(self, time):
        self.time.low = int(time % 2**32)
        self.time.high = int(time // 2**32)

    def _get_unit(self):
        return pyvpi.getTimeScale(cons.vpiTimePrecision) - 2**32

    def get_unit(self):
        '''get simulation unit, retrun str'''
        unit_dict = {0:'s',-3:'ms',-6:'us',-9:'ns',-12:'ps',-15:'fs'}
        unit_s = self._get_unit()
        return unit_dict[unit_s]

    def setAbsTime(self, time, unit=None):
        timeunit_dict = {'s':0,'ms':-3,'us':-6,'ns':-9,'ps':-12,'fs':-15}
        unit_s = self._get_unit()
        unit_t = 0
        if unit==None:
            unit_t = unit_s
        else:
            if unit in ['s','ms','us','ns','ps','fs']:
                unit_t = timeunit_dict[unit]
        dxt = time * 10**(unit_t-unit_s)
        self.time.low = int(dxt % 2**32)
        self.time.high = int(dxt // 2**32)    

class RWSynch(_event):
    def __init__(self):
        super().__init__()
        self.name = 'RWSynch'
        self.reason = cons.cbReadWriteSynch
        self.lock = threading.Event()
        self.wait_ev = asyncio.Event()
        self.loop = None
        self.armed = 0

    @staticmethod
    def func(self):
        try:
            self.armed = 1
            self.log('CALL BEG')
            self.lock.wait()
            self.lock.clear()
            self.log('CALL END')
            self.armed = 0
        except Exception as e:
            self.log('Error', str(e))
            raise e

    def register(self):
        self.log("CB REG")
        pyvpi.registerCb(self)


_sync = RWSynch()

class Timer(_event):
    '''Evt consume time
    '''
    def __init__(self, t, unit = None):
        super().__init__()
        self.t = t
        self.unit = unit
        self.name = 'Timer %s'%t
        self.reason = cons.cbAfterDelay
        self.setAbsTime(self.t, self.unit)
        self.lock = threading.Event()
        self.wait_ev = asyncio.Event()
        self.loop = None
        self.armed = 0

    def __del__(self):
        self.log("DEL")

    @staticmethod
    def func(self):
        try:
            self.armed = 1
            self.log('CALL BEG')
            self.loop.call_soon_threadsafe(self.wait_ev.set)
            self.lock.wait()
            self.lock.clear()
            self.log('CALL END')
            self.armed = 0
        except Exception as e:
            self.log('Error', str(e))
            raise e

    def __await__(self):    
        yield from self.wait().__await__()

    async def wait(self):
        try:
            self.log("WAIT BEG")
            self.wait_ev.clear()
            self.loop = asyncio.get_event_loop()
            self.setAbsTime(self.t, self.unit)
            self.register()
            self.log('arm status', self.armed)
            self.log("WAIT INI")
            await self.wait_ev.wait()
            self.lock.set()
            self.log("WAIT END")
            self.remove()
        except Exception as e:
            print(e)
            raise e



class Edge(_event):
    '''Evt consume time
    '''
    def __init__(self, reg):
        super().__init__()
        if type(reg)==str:
            reg = pyvpi_tools.Reg(reg)
        self.reg = reg
        self.name = '{} Edge'.format(self.reg.fullname) 
        self.trgobj = self.reg.handle
        self.reason = cons.cbValueChange
        self.lock = threading.Event()
        self.wait_ev = asyncio.Event()
        self.loop = None
        self.armed = 0

    @staticmethod
    def func(self):
        try:
            self.armed = 1
            self.log('CALL BEG')
            self.loop.call_soon_threadsafe(self.wait_ev.set)
            self.lock.wait()
            self.lock.clear()
            self.log('CALL END')
            self.armed = 0
        except Exception as e:
            self.log('Error', str(e))
            raise e

    def __await__(self):    
        yield from self.wait().__await__()

    async def wait(self):
        try:
            self.log("WAIT BEG")
            self.wait_ev.clear()
            self.loop = asyncio.get_event_loop()
            self.register()
            self.log('arm status', self.armed)
            self.log("WAIT INI")
            await self.wait_ev.wait()
            self.lock.set()
            self.log("WAIT END")
            self.log("TRG VALUE", self.reg.value)
            self.remove()
        except Exception as e:
            print(e)
            raise e

    async def __eq__(self, val):
        while(1):
            await self.wait()
            if self.reg.value == val:
                return 1

    async def __lt__(self,val):
        while(1):
            await self.wait()
            if self.reg.value < val:
                return 1        

    async def __gt__(self,val):
        while(1):
            pyvpi.printf("current value is %d\n"%self.reg.value)
            await self.wait()
            if self.reg.value > val:
                return 1      




class _run_sim(_event):
    '''Evt consume time
    '''
    def __init__(self, t=1, unit = 's'):
        super().__init__()
        self.t = t
        self.unit = unit
        self.name = 'RunSim %s'%t
        self.reason = cons.cbAfterDelay
        self.setAbsTime(self.t, self.unit)
        self.loop = None

    def __del__(self):
        self.log("DEL")

    @staticmethod
    def func(self):
        try:
            SIM_LOCK.sim_run = 1
            SIM_LOCK.wait()
            time.sleep(0.1)
        except Exception as e:
            self.log('Error', str(e))
            raise e

    def __call__(self, t=1, unit='s'):
        self.setAbsTime(t,unit)
        self.register()
        if SIM_LOCK.sim_run == 1:
            SIM_LOCK.set()
            SIM_LOCK.clear()
        SIM_LOCK.sim_run = 0

RUN_SIM = _run_sim()