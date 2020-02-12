export PYTHONPATH += .:./..

DES_TARGET := libvpi

#export LD_LIBRARY_PATH := $(LD_LIBRARY_PATH):$(PWD):/home1/sean.chen/.local/lib

#IUS_HOME   	  = /tools/cadence/INCISIV1320s033/tools/inca/
IUS_HOME          = /cad/eda/cadence/INCISIV/12.20.008/linux_i/tools.lnx86/inca
INC_PATH 	  = -I$(IUS_HOME)/include
INC_PATH     += -I/users/dzhao/anaconda2/include/python2.7
LIB_PATH      = -L/users/dzhao/anaconda2/lib
LIB_REF       = -lpython2.7 -lm -ldl -lutil
CFLAGS        = -c -g $(INC_PATH) -fPIC
SRC_C         = ../src/pyvpi.c \
                ../src/pyvalue.c \
                ../src/pytime.c \
                ../src/pystrength.c \
                ../src/pyvector.c   \
                ../src/pyhandle.c   \
                ../src/pycbdata.c   \
                ../src/pydelays.c	\
				../src/pysystfdata.c

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
	rm -rf wlft* work *.wlf *.so *.o *.log sim_build

vpi : $(SRC_C)
	gcc $(CFLAGS) $(SRC_C)
	ld $(LIB_PATH) $(LIB_REF) -shared -o libvpi.so \
	$(SRC_O)

run :
	irun -64 -sv -v93  -loadvpi $(DES_TARGET) +access+rwc -nclibdirname sim_build -plinowarn  test.sv

