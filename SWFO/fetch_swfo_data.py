#!/proj/sot/ska3/flight/bin/python
"""
**fetch_swfo_data.py.py**: Fetch the SWFO related data files

:Author: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Sep 03, 2025

"""
import os
import json
import urllib
from astropy.table import Table
import numpy as np
from time import sleep
from cxotime import CxoTime
import argparse
import getpass
import signal
#
# --- Define Directory Pathing
#
SWFO_DATA_DIR = "/data/mta4/Space_Weather/SWFO/Data"
OUT_SWFO_DATA_DIR = SWFO_DATA_DIR

SWFO_LINK = "Undetermined"

def rerun(func):
    """
    Function decorator which sleeps and reruns the provided function upon encountering a set of errors.
    """
    _freq = 3
    _errors = (json.decoder.JSONDecodeError, urllib.error.URLError)
    def wrapper_func(*args,**kwargs):
        _last_exception = None
        for i in range(_freq):
            try:
                return func(*args, **kwargs)
            except _errors as e:
                _last_exception = e
                sleep(5)
        _last_exception.add_note(f'@rerun ran function {_freq} times. Still encountered error.')
        raise _last_exception
    return wrapper_func

@rerun
def json2table(jlink):
    """Extract JSON file and format into Astropy Table

    :param jlink: JSON web address or file
    :type jlink: str
    :return: astropy table of the provided data.
    :rtype: astropy.Table

    """
    if os.path.isfile(jlink):
        with open(jlink) as f:
            data = json.load(f)
    else:
        with urllib.request.urlopen(jlink, timeout = 10) as url:
            data = json.loads(url.read().decode())
    data = Table(data)
    return data