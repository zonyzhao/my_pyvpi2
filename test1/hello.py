import pyvpi
import pyvpi_cons as cons
import Crypto.Cipher.AES
import mmap
import ctypes
import traceback
import numpy as np
#import matplotlib.pyplot as plt

def getAllHandles(handle,type) :
    ans = []
    iter = pyvpi.iterate(type,handle)
    while True :
        h = pyvpi.scan(iter)
        if not h :
            break
        ans.append(h)
    return ans

def test():
    """
    c = a+b;
    """
    print('py: hello world')

if __name__ == '__main__':
    test()
#    plt.plot(np.sin(2*np.pi*20*np.linspace(0,1,200)))
#    plt.show()
