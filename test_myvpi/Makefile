export PYTHONPATH += .:./..

DES_TARGET := pyvpi

#export LD_LIBRARY_PATH := $(LD_LIBRARY_PATH):$(PWD):/home1/sean.chen/.local/lib

#IUS_HOME   	  = /tools/cadence/INCISIV1320s033/tools/inca/
PYTHON_HOME	  = /opt/anaconda
IUS_HOME          = /opt/cadence/INCISIVE151/tools
INC_PATH 	  = -I$(IUS_HOME)/include
INC_PATH     += -I$(PYTHON_HOME)/include/python3.7m
#INC_PATH     += -I$(PYTHON_HOME)/include/python3.6m
#INC_PATH     += -I$(PYTHON_HOME)/include/python2.7
LIB_PATH      = -L$(PYTHON_HOME)/lib
#python 2.7
#LIB_REF       = -lpython2.7 -lm -ldl -lutil
#python 3.6
#LIB_REF       = -lpython3.6m -lm -ldl -lutil
#python 3.7
LIB_REF       = -lm -ldl -lutil -lpython3.7m 
CFLAGS        = -c -g $(INC_PATH) -fPIC

#CC			  = $(IUS_HOME)/cdsgcc/gcc/4.8/bin/gcc
CC			  = gcc
SRC_C         = ../src_py3/pyvpi.c \
                ../src_py3/pyvalue.c \
                ../src_py3/pytime.c \
                ../src_py3/pystrength.c \
                ../src_py3/pyvector.c   \
                ../src_py3/pyhandle.c   \
                ../src_py3/pycbdata.c   \
                ../src_py3/pydelays.c	\
				../src_py3/pysystfdata.c

SRC_O         = pyvpi.o \
                pyvalue.o \
                pycbdata.o \
                pytime.o \
                pystrength.o \
                pyvector.o  \
                pyhandle.o  \
                pydelays.o	\
				pysystfdata.o

all : clean vpi run

clean :
	rm -rf wlft* work *.wlf *.so *.o *.log sim_build *.err *.history *.key

vpi : $(SRC_C)
	$(CC) $(CFLAGS) $(SRC_C)
	ld $(LIB_PATH) $(LIB_REF) -shared -o pyvpi.so \
	$(SRC_O)
	cp pyvpi.so libvpi.so
	cp pyvpi.so libdpi.so
#
run_gui :
	irun -gui -debug -64 -sv -v93  -loadvpi pyvpi.so  +access+rwc -nclibdirname sim_build -plinowarn  test.sv

run:
	LD_PRELOAD=/opt/anaconda/lib/libpython3.7m.so irun -debug -64 -sv -v93  -loadvpi pyvpi.so +access+rwc -nclibdirname sim_build -plinowarn  test.sv
