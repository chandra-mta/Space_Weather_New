#!/proj/sot/ska3/flight/bin/python
"""
**fetch_goes_tables.py**: Fetch GOES particle tables and data from SWPC NOAA

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 21, 2025

"""
import os
import sys
import json
import urllib
from astropy.io import ascii
from astropy.table import Table
import numpy as np
from time import sleep
#
# --- Define Directory Pathing
#
GOES_DATA_DIR = '/data/mta4/Space_Weather/GOES/Data'
DIFF_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-1-day.json'
INTG_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json'
INTG_ELECTRONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json'


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

def reorient_particle_table(table, gen_column = 'energy', column_list = None):
    """
    Take a particle table with multiple time tag entires (one for each energy).
    This is the default for SWPC data products. Then reorient to single time entries with flux for each column
    """
    for col in table.columns:
        if 'time' in col:
            time_column = col
    
    time_list = sorted(set(table[time_column].data))
    if column_list is None:
        column_list = set(table[gen_column])
    
    new_rows = []
    for time in time_list:
        row = {time_column: time}
        selection = table[time_column] == time
        for i in table[selection]:
            row[i[gen_column]] = i['flux']
        for j in column_list - set(row.keys()): #: Unincluded flux values
            row[j] = np.ma.masked
        new_rows.append(row)
    
    return Table(rows = new_rows)