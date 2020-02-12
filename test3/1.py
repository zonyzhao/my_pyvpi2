import numpy as np
from scipy import signal
import os
import subprocess
import sys
import time
print("#"*50)

with open('env_python.txt') as f:
    for l in f.readlines():
        ll = l.strip()
        [k,v] = ll.split(":",1)
        os.environ[k]=v

#sys.path.append('/users/dzhao/anaconda3/bin')
#print(sys.path)
x = np.sin(2*np.pi*20*np.linspace(0,1,1000))
i = 0
import matplotlib.pyplot as plt

class myfilter(object):
    def __init__(self,b,a):
        self.b = b
        self.a = a
        self.zi = signal.lfilter_zi(b,a)*0
        self.out = 0

    def run(self,x):
        self.out, zi = signal.lfilter(self.b,self.a,[x],zi=self.zi)
        self.zi = zi
        #self.out = x 
        return self.out[0]
##
if 1:
    # with open('env.txt','w') as f:
    #     ks = list(os.environ.keys())
    #     ks.sort()
    #     for k in ks:
    #         f.writelines(k+':'+os.environ[k]+'\n')
    buffer = [0]*8
    b, a = signal.butter(3,0.05)
    ft = myfilter(b,a)
    i = 0
    x = []
    while(i<200):
        x.append(ft.run(1))
        i+=1
    plt.plot(x)
    plt.show()
if 0:
    from pyvpi import *
    import pyvpi_cons as cons
    cb = CbData()
    setDebugLevel(30)
    cb.reason = cons.cbValueChange
    cb.user_data = [ft,0]
    
    clk = handleByName("top.clk")
    def callback(self):
        buffer.append(self.user_data[0].run(1))
        x = np.random.randn(100)
        printf('hello\n')
        printf('buffer mean = %f \n'%np.mean(buffer))
        #plt.clf()
        #plt.plot(x)
        #plt.show()
        #plt.pause(0.5)
            
    cb.trgobj = clk
    cb.callback = callback
    
    registerCb(cb)
