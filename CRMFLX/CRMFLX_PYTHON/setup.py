#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python
from setuptools import setup
from Cython.Build import cythonize

setup(
    name='CRM FLX',
    ext_modules=cythonize("crmflx.pyx"),
    zip_safe=False,
)
