#!/usr/bin/env python3
# encoding: utf-8

from distutils.core import setup, Extension

dedrop_module = Extension('dedrop', sources = ['dedrop.c'])
marshal3_module = Extension('marshal3', sources = ['marshal.c', 'hashtable.c'])

setup(name='dedrop',
      version='0.1.0',
      description='dedrop module written in C',
      ext_modules=[dedrop_module,marshal3_module])
