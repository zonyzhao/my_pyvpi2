import pyvpi
import pyvpi_cons as cons

def test():
    """
    c = a+b;
    """

    a = pyvpi.handleByName("top.u_pyadaptor.a")
    b = pyvpi.handleByName("top.u_pyadaptor.b")
    c = pyvpi.handleByName("top.u_pyadaptor.c")
    p = pyvpi.handleByName("top.p")
    s = pyvpi.getStr(cons.vpiName, p)
    pyvpi.printf('p is {}\n'.format(s))
    st = pyvpi.getStr(cons.vpiType,p)
    pyvpi.printf('p type = {}\n'.format(st))

    it = pyvpi.iterate(cons.vpiMember, p)
    xt = pyvpi.scan(it)
    while(xt):
        st = pyvpi.getStr(cons.vpiFullName,xt)
        pyvpi.printf('P Member name = {} \n'.format(st))
        xt = pyvpi.scan(it)


    ph = pyvpi.handle(cons.vpiTypespec,p)
    p_name = pyvpi.getStr(cons.vpiName,ph)
    pyvpi.printf('p type name = {}\n'.format(p_name))


    val_a = pyvpi.Value(cons.vpiIntVal)
    val_b = pyvpi.Value(cons.vpiIntVal)
    val_c = pyvpi.Value(cons.vpiIntVal)

    pyvpi.getValue(a,val_a)
    pyvpi.getValue(b,val_b)
    pyvpi.getValue(c,val_c)

    try:
        val_c.value = val_a.value + val_b.value
        pyvpi.putValue(c, val_c)
        pyvpi.printf("py a:{} + b:{} = c:{}\n".format(val_a.value, val_b.value, val_c.value))
    except:
        # skip if value is unknown
        pass

if __name__ == '__main__':
    test()
