#!/proj/sot/ska3/flight/bin/python
"""

**fetch_kp_tables.py**: Fetch KP index forecast tables and data from SWPC NOAA

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 24, 2025


:NOTE:
    - https://kp.gfz.de/en/
    - https://kp.gfz.de/en/data
    - https://www.gfz.de/en/section/geomagnetism/data-products-services/geomagnetic-kp-index
    - https://www.swpc.noaa.gov/products/planetary-k-index
    - https://www.swpc.noaa.gov/sites/default/files/images/u2/TheK-index.pdf
"""
import os
import json
from time import sleep
import urllib
from astropy.table import Table
import getpass
import signal
#
# --- Define Directory Pathing
#
KP_DATA_DIR = "/data/mta4/Space_Weather/KP/Data"
#
# --- Globals
#
KP_FORECAST_LINK = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"

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
        _last_exception.add_note(f'Decorator ran function {_freq} times. Still encountered error.')
        raise _last_exception
    return wrapper_func

@rerun
def read_json(link):
    """Generalized json file reader

    :param link: URL or file path
    :type link: str
    """
    if os.path.isfile(link):
        with open(link) as f:
            data = json.load(f)
    else:
        with urllib.request.urlopen(link, timeout = 10) as url:
            data = json.loads(url.read().decode())
    return data