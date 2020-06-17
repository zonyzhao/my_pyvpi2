import pyvpi
import pyvpi_tools
import pyvpi_cons as cons
from pyvpi_tools import Simtime
import sys
import os
import numpy as np
from threading import Thread, Event
import threading
import asyncio
from functools import partial
import time
from IPython import embed
from enum import IntEnum
from pyvpi_coroutine import Timer, Edge
# Header Bits
# class HEADER_BITS():

AP=1
DP=0

# class HEADER_WR():
READ=1
WRITE=0

# DP Register Addresses

# class DP_ADDR():
DPIDR     = 0x0
ABORT     = 0x0
CTRLSTAT  = 0x4
DLCR      = 0x4
TARGETID  = 0x4
HALTEV    = 0x4
RESEND    = 0x8
SELECT    = 0x8
RDBUFF    = 0xc
TARGETSEL = 0xc


# AP Register Addresses

#define CSW  0x00
#define TAR  0x04
#define DRW  0x0c
#define BD0  0x10
#define BD1  0x14
#define BD2  0x18
#define BD3  0x1c
#define CFG  0xf4
#define BASE 0xf8
#define IDR  0xfc
# class AP_ADDR():
CSW  = 0x00
TAR  = 0x04
DRW  = 0x0c
BD0  = 0x10
BD1  = 0x14
BD2  = 0x18
BD3  = 0x1c
CFG  = 0xf4
BASE = 0xf8
IDR  = 0xfc

# CSW Register Fields
# class CSW_FIELDS():
CSW_INCR_OFF      = (0 << 4)
CSW_INCR_SINGLE   = (1 << 4)
CSW_PROT_USER     = (0 << 25)
CSW_PROT_PRIV     = (1 << 25)
CSW_PROT_BUFF     = (1 << 26)
CSW_PROT_CACH     = (1 << 27)
CSW_SIZE_BYTE     = 0
CSW_SIZE_HALFWORD = 1
CSW_SIZE_WORD     = 2

def SW_HEADER_PARITY(APnDP,RnW,Address):
    return ( (APnDP & 0x1) ^ (RnW & 0x1) ^ ((Address & 0x4) >> 2) ^ ((Address & 0x8) >> 3) )

def SW_HEADER(APnDP,RnW,Address):
    return (1 | ((APnDP & 0x1) << 1) | ((RnW & 0x1) << 2) | ((Address & 0xC) << 1) | SW_HEADER_PARITY(APnDP,RnW,Address) << 5 | 0 << 6 | 1 << 7)
# SW responses

#define SW_DP_ACK_OK 1
#define SW_DP_ACK_WAIT 2
#define SW_DP_ACK_FAULT 4
# class SW_RESPONSE():
SW_DP_ACK_OK    = 1
SW_DP_ACK_WAIT  = 2
SW_DP_ACK_FAULT = 4

# class SWDS_SEQ():
SWD_to_DS    =  0xE3BC
DS_to_SWD_0  =  0x6209F392
DS_to_SWD_1  =  0x86852D95
DS_to_SWD_2  =  0xE3DDAFE9
DS_to_SWD_3  =  0x19BC0EA2
SW_ACTV_CODE =  0x1A

import struct
from numpy import nan

WREALZSTATE=struct.unpack('>d',b'\xff\xff\xff\xff\x00\x00\x00\x00')[0]

WREALXSTATE=nan

class DAPSTATUS():
    def __init__(self):
        self.jtagnsw = 0
        self.jtagapndp = 2
        self.on = 0
        self.banksel = 0xff
        self.csw = 0xffffffff
        self.error = 0
        self.ack = 0
        self.stkerrclr = 0
        self.readout = 0
        

class SWD():
    '''SWD interface
    '''
    def __init__(self):
        self.swclk = pyvpi_tools.Reg('main.swdclk')
        self.swdio = pyvpi_tools.Reg('main.swdio')
        self.swclk_net = pyvpi_tools.Reg('main.swdclk_net')
        self.swdio_net = pyvpi_tools.Reg('main.swdio_net')
        self.freq = 10e6
        self.vl = 0
        self.vh = 1.2
        self.pose_trig_w = True
        self.pose_trig_r = False
        self.APnDP = 1  # 1=Ap  0=Dp
        self.RnW = 0 # 0=write 1= read
        self.Address = 0 # Ap or DP reg address
        pyvpi.printf('SWD created\n')
        self.trig = Edge(self.swclk)
        self.hclk= Timer(1/2/self.freq,'s') 
        self.swclk.value = 0
        self.DAPSTATUS = DAPSTATUS()
        self._log = pyvpi_tools.Reg('main.cmd')
        self._log2 = pyvpi_tools.Reg('main.ack')

    def log(self, args):
        self._log.value = args

    def log2(self, args):
        self._log2.value = args


    async def _reset(self, n=2):
        for _ in range(50):
            await self._write(1)
        for _ in range(n):
            await self._write(0)
        # await self._write(0)

    def _release(self):
        self.swdio.value = WREALZSTATE
        # self.swdio.value = 0

    def _hold(self):
        self.swdio.value = 0

    async def _nclk(self, n=1):
        for _ in range(n):
            self.swclk.value = self.vh
            await self.hclk 
            self.swclk.value = 0
            await self.hclk 
            

    async def _clk(self, n=1):
        for _ in range(n):
            self.swclk.value = 0
            await self.hclk 
            self.swclk.value = self.vh
            await self.hclk 
            

    async def _write(self,bit):
        self.swclk.value = 0
        await self.hclk 
        self.swdio.value = bit*self.vh
        await self.hclk 
        self.swclk.value = self.vh
        await self.hclk 
        self.swclk.value = 0
        
        

    async def _read(self):
        self.swclk.value = 0
        await self.hclk 
        self.swclk.value = self.vh
        val = self.swdio_net.value
        await self.hclk
        self.swclk.value = 0 
        await self.hclk 
        
        # self.log('V=%d'%self.swdio_net.value)
        return val

    async def _idle(self,n=2):
        # self.log('IDLE')
        for _ in range(n):
            await self._write(0)

    @property
    def SW_HEADER(self):
        return 1|((self.APnDP&0x1)<<1)|((self.RnW&0x1)<<2)|((self.Address & 0xC)<<1)|self.SW_HEADER_PARITY<<5|0<<6|1<<7

    @property
    def SW_HEADER_PARITY(self):
        return ((self.APnDP&0x1)^(self.RnW&0x1)^((self.Address&0x4)>>2)^((self.Address&0x8)>>3))

    async def SWConnect(self):
        await self.SWHeader()
        id = await self.SWDataRead()
        return id

    async def SerialWireClockOut(self, data, numbits):
        self.log("SerialWireClockOut = 0x%x bits=%d"%(data,numbits))
        for i in range(numbits):
            await self._write((data>>i)&0x1)
            # self.log("SerialWireClockOut = 0x%x bits=%d"%(data,numbits))


    async def SerialWireClockIn(self, numbits):
        self.log("SerialWireClockIn bits = %d"%numbits)
        self._release()
        data = 0
        for i in range(numbits):
            data = data>>1
            data |= ((await self._read())>0.5)<<31   
        self.log2("SerialWireClockIn data = 0x%x"%(data))
        return data


    async def SWHeader(self,AnD=DP,WnR=READ,Addr=DPIDR):
        self.log('SWHeader AnD=%d, WnR=%d, Addr = %d'%(AnD,WnR,Addr))
        # await self._idle(12)
        self.APnDP = AnD
        self.RnW = WnR
        self.Address = Addr
        # await self._idle(4)
        self.DAPSTATUS.ack = 0
        await self.SerialWireClockOut(self.SW_HEADER, 8)
        ack = await self.SerialWireClockIn(4)
        ack = (ack>>(29))&0x7
        pyvpi.printf('ACK for HEADER = 0x%x\n'%ack)
        # assert ack==1, 'Error in ACK'
        self.DAPSTATUS.ack = 1
        return ack

    async def SWDataRead(self):
        self.log('SWDataRead')
        data = await self.SerialWireClockIn(32);
        await self.SerialWireClockIn(2)
        self.log2('SWDataRead = 0x%x'%data)
        self.readout = data
        return data

    async def SWDataWrite(self, data):
        self.log('SWDataWrite = 0x%x'%data)
        await self._nclk() 
        await self.SerialWireClockOut(data,32);
        parity = 0
        for i in range(32):
            parity += ((data>>i)&1)
        # self.log('SWDataWrite_Parity = 0x%x'%parity)
        await self.SerialWireClockOut(parity,1);

    async def JTAGDormSwitch(self):
        await self.SerialWireClockOut(0x1f,5)
        await self.SerialWireClockOut(0x33bbbbba,32)

    async def DormToSWSwitch(self):
        await self.SerialWireClockOut(0xff,8)
        await self.SerialWireClockOut(0x6209f392,32);
        await self.SerialWireClockOut(0x86852d95,32);
        await self.SerialWireClockOut(0xe3ddafe9,32);
        await self.SerialWireClockOut(0x19bc0ea2,32);
        await self.SerialWireClockOut(0x0,4);
        await self.SerialWireClockOut(0x1A,8); 
        await self._idle(4)       
        await self._reset(8)

    async def ConnectSW(self):
        await self.JTAGDormSwitch()
        await self.DormToSWSwitch()
        id = await self.SWConnect()
        self.log('id = 0x%x\n'%id)
        # if id == 0xbe12477:
        #     pyvpi.printf('SW Connected with ID=0x%x\n'%id)
        # else:
        #     raise Exception('No SW Connected')

    async def PowerUpAccess(self):
        await self.ConnectSW()
        await self.DPWriteCTRLSTAT(0x50000000)
        ack = await self.DPReadCTRLSTAT()

    async def DPWriteCTRLSTAT(self, ctrlstat):
        await self.SWHeader(DP,WRITE,CTRLSTAT)
        await self.SWDataWrite(ctrlstat)

    async def DPReadCTRLSTAT(self):
        await self.SWHeader(DP,READ,CTRLSTAT)
        ack = await self.SWDataRead()     
        return ack

    async def WriteMem(self, addr, data):
        self.log('WriteMem')
        csw = CSW_INCR_OFF | CSW_SIZE_WORD | CSW_PROT_PRIV | CSW_PROT_BUFF | CSW_PROT_CACH
        await self.APWriteCSW(csw)
        await self.APWriteTAR(addr)
        await self.APWriteDRW(data)
        await self.DPReadRDBUFF()

    async def ReadMem(self, addr):
        self.log('ReadMem')
        await self.APWriteCSW(0x2000002)
        await self.APWriteTAR(addr)
        await self.APReadDRW()
        ack = await self.DPReadRDBUFF()
        self.readout = ack
        return ack

    async def APWriteCSW(self, csw):
        self.log("APWriteCSW")
        if self.DAPSTATUS.csw !=csw:
            await self.DPWriteBANKSEL(0)
            await self.SWHeader(AP,WRITE,CSW)
            await self.SWDataWrite(csw)
            self.DAPSTATUS.csw = csw

    async def DPWriteBANKSEL(self,banksel):
        self.log("DPWriteBANKSEL")
        if self.DAPSTATUS.banksel != banksel:
            await self.SWHeader(DP,WRITE,SELECT)
            await self.SWDataWrite(banksel)
            self.DAPSTATUS.banksel = banksel

    async def APWriteTAR(self, addr):
        await self.DPWriteBANKSEL(0)
        await self.SWHeader(AP, WRITE, TAR)
        await self.SWDataWrite(addr)

    async def APReadDRW(self):
        await self.DPWriteBANKSEL(0)
        await self.SWHeader(AP, READ, DRW)
        return await self.SWDataRead()

    async def APWriteDRW(self,data):
        await self.DPWriteBANKSEL(0)
        await self.SWHeader(AP, WRITE, DRW)
        await self.SWDataWrite(data)     

    async def DPReadRDBUFF(self):
        await self.SWHeader(DP, READ, RDBUFF)
        return await self.SWDataRead() 