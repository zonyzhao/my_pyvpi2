import pyvpi
import pyvpi_cons as cons


def test():
    """
    c = a+b;
    """
    time = pyvpi.Time()
    pyvpi.getTime(time)
    pyvpi.printf('py: hello world at %d\n' % time.time)

    handle_a = pyvpi.handleByName("top.a")
    val_a = pyvpi.Value(cons.vpiIntVal)

    pyvpi.getValue(handle_a, val_a)
    print(val_a.format)
    try:
        val_a.value += 1
        pyvpi.putValue(handle_a, val_a)
        print('py:      a = %d'%val_a.value)
    except:
        #
        pass

if __name__ == '__main__':
    test()
