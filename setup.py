#!/usr/bin/env python

from distutils.core import setup, Extension
import glob
import os
import os.path
import sys
import platform

#All c source
c_src = glob.glob(os.path.join("src","*.c"))

inc_dirs = []
lib_dirs = []
libs     = []

inc_dirs = ['/cad/eda/cadence/INCISIV/12.20.008/linux_i/tools.lnx86/inca/include']

setup(name = '',
      version = '1.0',
      description = '',
      author = 'Gene Kong',
      author_email = 'genekong.sw@gmail.com',
      url = 'https://github.com/gyx2545965/pyvpi',
      py_modules = ['pyvpi_cons'],
      ext_modules = [Extension('pyvpi',
                               c_src,
                               include_dirs = inc_dirs,
                               library_dirs = lib_dirs,
                               libraries = libs,
                               )]
      )
