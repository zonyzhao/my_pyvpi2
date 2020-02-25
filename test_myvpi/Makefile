export PYTHONPATH += .:./..

DES_TARGET := pyvpi

#export LD_LIBRARY_PATH := $(LD_LIBRARY_PATH):$(PWD):/home1/sean.chen/.local/lib

PYTHON_HOME	  =${ANACONDAHOME}
XRUN	      =xrun
IUS_HOME      =$(strip $(shell cds_root ${XRUN}))/tools
INC_PATH 	  =-I${IUS_HOME}/include
PYVERSION     =$(shell python -c 'import sys;x=sys.version_info;print("{}.{}".format(*x))')
INC_PATH     +=-I${PYTHON_HOME}/include/python${PYVERSION}m
LIB_PATH      =-L$(PYTHON_HOME)/lib
LIB_REF       =-lm -ldl -lutil -lpython${PYVERSION}m 
CFLAGS        =-c -g $(INC_PATH) -fPIC
PYVPI_TB	  =test_task.py
PRELOAD  = ${PYTHON_HOME}/lib/libpython$(PYVERSION)m.so

#CC			  = ${IUS_HOME}/cdsgcc/gcc/6.3/bin/gcc
CC			  =gcc
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

test:
	@echo ${INC_PATH}

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
	PYVPI_TB=$(PYVPI_TB) LD_PRELOAD=$(PRELOAD) $(XRUN) -gui -debug -sv -loadvpi pyvpi.so  +access+rwc -nclibdirname sim_build -plinowarn  test.sv

run:
	PYVPI_TB=$(PYVPI_TB) LD_PRELOAD=$(PRELOAD) $(XRUN) -debug -sv -loadvpi pyvpi.so +access+rwc -nclibdirname sim_build  test.sv -plidebug -plierr_verbose -pliverbose
