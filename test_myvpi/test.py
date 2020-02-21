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
import pprint

pyvpi.setDebugLevel(10)


process = psutil.Process(os.getpid())
GMEM=0
DMEM = 0

def print_mem():
    global DMEM, GMEM
    DMEM = process.memory_info()[0] - GMEM
    GMEM=process.memory_info()[0]
    pyvpi.printf("MEM: %d\n"%GMEM)
    pyvpi.printf("DMEM: %d\n"%DMEM)

# IPython.embed()


pyvpi.setDebugLevel(10)

b = pyvpi.handleByName('top.a')
n = 0

a = pyvpi.Value(cons.vpiIntVal)
while(1):
    pyvpi.setDebugLevel(40)
    for _ in range(10000):
        b = pyvpi.handleByName('top.a')
        del b
        # pyvpi.getValue(b,a)
        # a.value = a.value+1
    # pyvpi.setDebugLevel(10)
    b = 'a'
    print_mem()
    # print(n)

print_mem()
pprint.pprint(gc.garbage)
# from pyvpi_tools import *

