export PYTHONPATH += .:./..

DES_TARGET := libvpi

#export LD_LIBRARY_PATH := $(LD_LIBRARY_PATH):$(PWD):/home1/sean.chen/.local/lib

#IUS_HOME   	  = /tools/cadence/INCISIV1320s033/tools/inca/
PYTHON_HOME	  = /users/dzhao/anaconda3
IUS_HOME          = /cad/eda/cadence/INCISIV/12.20.008/linux_i/tools.lnx86/inca
INC_PATH 	  = -I$(IUS_HOME)/include
INC_PATH     += -I$(PYTHON_HOME)/include/python3.6m
LIB_PATH      = -L$(PYTHON_HOME)/lib
#python 2.7
#LIB_REF       = -lpython2.7 -lm -ldl -lutil
#python 3.5
LIB_REF       = -lpython3.6m -lm -ldl -lutil
CFLAGS        = -c -g $(INC_PATH) -fPIC
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
	rm -rf wlft* work *.wlf *.so *.o *.log sim_build *.err

vpi : $(SRC_C)
	gcc $(CFLAGS) $(SRC_C)
	ld $(LIB_PATH) $(LIB_REF) -shared -o libvpi.so \
	$(SRC_O)
	cp libvpi.so pyvpi.so

run :
	irun -64 -sv -v93  -loadvpi $(DES_TARGET) +access+rwc -nclibdirname sim_build -plinowarn  test.sv

