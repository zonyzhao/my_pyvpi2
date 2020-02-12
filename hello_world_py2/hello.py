import pyvpi
import pyvpi_cons as cons
import numpy as np

def test():
    """
    c = a+b;
    """
    handle_a = pyvpi.handleByName("top.a")
    val_a = pyvpi.Value(cons.vpiIntVal)
    val_a.value = 5
    pyvpi.putValue(handle_a, val_a)
    time = pyvpi.Time()

    pyvpi.getTime(time)
    print('py: hello world at %d'%time.time)


if __name__ == '__main__':
    test()
