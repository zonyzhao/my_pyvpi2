import pyvpi
import pyvpi_cons as cons
# from scipy import signal
#from IPython import embed
import os
import sys

try:
    pyvpi.gd
except Exception:
    pyvpi.gd = dict()
    pyvpi.gd['Registered_event'] = []
    pyvpi.printf("Global Dict created\n")


INT_VAL = [cons.vpiIntVal, cons.vpiReg, cons.vpiIntNet, cons.vpiIntVar, cons.vpiIntegerNet, cons.vpiIntegerVar]
REAL_VAL = [cons.vpiRealVal, cons.vpiRealVar, cons.vpiRealNet]
STR_VAL = [cons.vpiStringVal, cons.vpiStringVar]

time_unit = {'s':0, 'ms':-3, 'us':-6, 'ns':-9, 'ps':-12, 'fs':-15}

def _get_unit():
    return pyvpi.getTimeScale(cons.vpiTimePrecision)-2**32

def get_simtime_unit():
    unit_dict = {0:'s', -3:'ms', -6:'us', -9:'ns', -12:'ps', -15:'fs'}
    return unit_dict[_get_unit()]

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

class Reg(object):
    '''
    access to registers in verilog.
    >>>freq = Reg("tb_r_adpll880_nl01.dut.DCO.fout")
    >>>freq.format(cons.vpiRealVal)
    >>>pyvpi.printf("Get frequency = %s \n"%(freq.get()))

    newly added: format using the default property defined
    '''

    def __init__(self, s):
        self._handle = pyvpi.handleByName(s)
        self._type = pyvpi.get(cons.vpiType, self._handle)
        if self._type in INT_VAL:
            self._format = cons.vpiIntVal
            self._f = int
        elif self._type in REAL_VAL:
            self._format = cons.vpiRealVal
            self._f = float
        elif self._type in STR_VAL:
            self._format = cons.vpiStringVal
            self._f = str
        else:
            self._format = cons.vpiIntVal
            self._f = int
        self._value = pyvpi.Value(self._format)
        self._signed = pyvpi.get(cons.vpiSigned, self._handle)
        self._size = pyvpi.get(cons.vpiSize, self._handle)
        self.forced = 0

    @property
    def fullname(self):
        rt = pyvpi.getStr(cons.vpiFullName, self._handle)
        return rt

    @property
    def handle(self):
        return self._handle

    def format(self, format):
        self._format = format
        self._value = pyvpi.Value(format)

    # def get(self):
    #     pyvpi.getValue(self._handle, self._value)
    #     rt = self._value.value
    #     return rt

    @property
    def value(self):
        # print("get")
        pyvpi.getValue(self._handle, self._value)
        return self._f(self._value.value)

    @property
    def signed_value(self):
        if self.value>=2**(self._size-1):
            return self.value-2**(self._size)
        else:
            return self.value

    @value.setter
    def value(self, x):
        self.put(x)


    # def put(self, val):
    #     if self._type==36: # net type, use force)
    #         self.force(val)
    #         self.forced = 1
    #     else:
    #         self._put(val)

    def put(self, val):
        self._value.value = self._f(val)
        # print("set")
        pyvpi.putValue(self._handle, self._value)

    def force(self, val):
        self._value.value = self._f(val)
        pyvpi.putValue(self._handle, self._value, None, cons.vpiForceFlag)
        self.forced = 1

    def release(self):
        pyvpi.putValue(self._handle, self._value, None, cons.vpiReleaseFlag)
        self.forced = 0


class RealReg(Reg):
    """Real value Registers"""

    def __init__(self, s):
        super().__init__(s)
        self.format(cons.vpiRealVal)
        self._f = float


class IntReg(Reg):
    """docstring for IntReg"""

    def __init__(self, s):
        super().__init__(s)
        self.format(cons.vpiIntVal)
        self._f = int


class _SimTime(object):
    '''
    A objest get the simulation time.
    '''

    def __init__(self):
        self._time = pyvpi.Time(cons.vpiScaledRealTime)
        self.unit = pyvpi.getTimeScale(cons.vpiTimePrecision) - 2**32

    @property
    def value(self):
        pyvpi.getTime(self._time)
        return self._time.real

    @property
    def abstime(self):
        return self.value * 10**(self.unit)

    def __repr__(self):
        timeunit_dict = {0:'s',-3:'ms',-6:'us',-9:'ns',-12:'ps',-15:'fs'}
        return str(self.value)+' '+timeunit_dict[self.unit]

def get_current_simtime():
    x = _SimTime()
    return x.abstime

Simtime = _SimTime()


# class myfilter(object):
#     '''
#     an easy filter class which can be used in verilog.
#     >>>b, a = signal.butter(10,1/16)
#     >>>ft = myfilter(b,a)
#     '''

#     def __init__(self, b, a):
#         self.b = b
#         self.a = a
#         self.zi = signal.lfilter_zi(b, a) * 0
#         self.out = 0

#     def run(self, x):
#         self.out, zi = signal.lfilter(self.b, self.a, [x], zi=self.zi)
#         self.zi = zi
# #        #self.out = x
#         return self.out[0]

#     def __call__(self, x):

#         return self.run(x)


class Event(pyvpi.CbData):
    '''
    A system call back event
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.register_in_gd = True
        self.name = ''
        for name, val in kwargs.items():
            setattr(self, name, val)

    def func(self):
        pass

    def register(self):
        '''
        Register cb
        '''
        pyvpi.registerCb(self)
        if self.register_in_gd:
            self.add_to_gd()
        # pyvpi.printf("Event %s registered. \n" % self.name)

    def add_to_gd(self):
        pyvpi.gd['Registered_event'].append(self)

    def remove(self):
        '''
        remove cb
        '''
        pyvpi.removeCb(self)
        if self.register_in_gd:
            self.remove_from_gd()

    def remove_from_gd(self):
        pyvpi.gd['Registered_event'].remove(self)

    # def __call__(self, func):
    #     self.callback = func
    #     self.register()

    def __call__(self, *args):
        if args is not ():
            self.func = args[0]
        self.callback = self._myfunc
        self.register()
        return self.func

    def _myfunc(self, arg):
        try:
            self.myfunc(arg)
        except Exception as e:
            pyvpi.printf("\n")
            pyvpi.printf("#" * 25 + "Python Exception Found : %s" %
                         self.name + "#" * 25 + '\n')
            pyvpi.printf(repr(type(e)) + "\n")
            pyvpi.printf(repr(e) + "\n")

    def myfunc(self, arg):
        self.func(arg)


#def start_interactive():
#    embed()

# Time related event
class Always(Event):
    '''
    Delay some time
    the same like #(time) in verilog
    '''

    def __init__(self, dt, **kwargs):
        super().__init__()
        self.reason = cons.cbAfterDelay
        self.time = pyvpi.Time(cons.vpiSimTime)
        self.dxt = dt / 10**(Simtime.unit)
        pyvpi.printf("dxt is %f \n" % self.dxt)
        self.time.low = int(self.dxt % 2**32)
        self.time.high = int(self.dxt // 2**32)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        self.func(arg)
        self.time.low = int(self.dxt % 2**32)
        self.time.high = int(self.dxt // 2**32)
        pyvpi.registerCb(self)


class Delay(Event):
    '''
    Delay some time
    the same like #(time) in verilog
    '''

    def __init__(self, dt, **kwargs):
        super().__init__()
        self.reason = cons.cbAfterDelay
        self.time = pyvpi.Time(cons.vpiSimTime)
        self.time.low = int(dt % 2**32)
        self.time.high = int(dt // 2**32)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        self.func(arg)
        # self.remove()


class AtTime(Event):
    '''
    At specific time, in absolution time (eg. 1us = 1e-6)
    '''

    def __init__(self, dt, **kwargs):
        super().__init__()
        self.reason = cons.cbAfterDelay
        self.time = pyvpi.Time(cons.vpiSimTime)
        # pyvpi.getTime(self.time)
        # pyvpi.printf("current time is %s fs.\n" % self.time.time)
        dxt = dt / 10**(Simtime.unit) - self.time.time
        #pyvpi.printf("dxt is %f \n" % dxt)
        self.time.low = int(dxt % 2**32)
        self.time.high = int(dxt // 2**32)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        self.func(arg)
        self.remove()

class ReadWriteSynch(Event):
    '''
    At specific sim time later, in absolution time (eg. 1us = 1e-6)
    '''
    def __init__(self, dt, **kwargs):
        super().__init__()
        self.reason = cons.cbReadWriteSynch
        self.time = pyvpi.Time(cons.vpiSimTime)
        self.time.low = int(dt % 2**32)
        self.time.high = int(dt // 2**32)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        self.func(arg)
        self.remove()

# value related event


class Posedge(Event):
    '''
    At posedge of some signal,
    Same as @posedge(signal_name)
    '''

    def __init__(self, reg_name, **kwargs):
        super().__init__()
        self.register_in_gd = True
        self.reason = cons.cbValueChange
        self.reg = IntReg(reg_name)
        self.trgobj = self.reg.handle
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        if(self.reg.value == 1):
            self.func(arg)


class Negedge(Event):
    '''
    At negedge of some signal,
    Same as @negedge(signal_name)
    '''

    def __init__(self, reg_name, **kwargs):
        super().__init__()
        self.register_in_gd = True
        self.reason = cons.cbValueChange
        self.reg = IntReg(reg_name)
        self.trgobj = self.reg.handle
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        if(self.reg.value == 0):
            self.func(arg)


class At(Event):
    '''
    At change of some signal,
    Same as @(signal_name)
    '''

    def __init__(self, reg_name, **kwargs):
        super().__init__()
        self.register_in_gd = True
        self.reason = cons.cbValueChange
        self.reg = IntReg(reg_name)
        self.trgobj = self.reg.handle
        for name, val in kwargs.items():
            setattr(self, name, val)

    def myfunc(self, arg):
        self.func(arg)


# @Event(reason=cons.cbStartOfReset, name='Reset all', register_in_gd=False)
# def sim_restart(self):
#     pyvpi.printf("reset called.\n")
#     if 'PYVPI_TB' in os.environ.keys():
#         tb_name = os.environ['PYVPI_TB']
#         if tb_name != "":
#             exec(open(tb_name).read())


class SysTask(pyvpi.SysTfData):
    '''
    A system task
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def register(self):
        '''
        Register cb
        '''
        pyvpi.registerSysTf(self)

    def __call__(self, func):
        self.calltf = func
        self.register()


###
def start_info(s):
    pyvpi.printf("\n")
    pyvpi.printf("******** Start of Python ********\n")
    pyvpi.printf(s + "\n")


def end_info():
    pyvpi.printf('******** End of Python ********\n')
    pyvpi.printf("\n")


def runfile(fn):
    with open(fn) as f:
        exec("".join(f.readlines()))


@SysTask(tfname="$ipython")
def itr(self):
    print('Enter ipython for debug')
    IPython.embed()