#!/proj/sot/ska3/flight/bin/python
"""
**fetch_goes_tables.py**: Fetch GOES particle tables and data from SWPC NOAA

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 21, 2025

"""
import os
import json
import urllib
import argparse
from astropy.table import Table
import numpy as np
from time import sleep
#
# --- Define Directory Pathing
#
GOES_DATA_DIR = '/data/mta4/Space_Weather/GOES/Data'
DIFF_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
INTG_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json'
INTG_ELECTRONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'

DIFF_COLS = ['P1', 'P2A', 'P2B', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8A', 'P8B', 'P8C', 'P9', 'P10']
INTG_COLS = ['>=1 MeV', '>=5 MeV', '>=10 MeV', '>=30 MeV', '>=50 MeV', '>=60 MeV', '>=100 MeV', '>=500 MeV']

DIFF_PROTON_UNIT = "protons/(cm^2*s*sr*keV)"
INTG_PROTON_UNIT = "protons/(cm^2*s*sr)"
INTG_ELECTRON_UNIT = "protons/(cm^2*s*sr)"

def fetch_goes_tables():
    """
    Fetch the relevant GOES data from the SWPC then format into a time-domain table with additional metadata.
    """

    diff_proton_table = json2table(DIFF_PROTONS_LINK)
    intg_proton_table = json2table(INTG_PROTONS_LINK)
    intg_electron_table = json2table(INTG_ELECTRONS_LINK)
#
# --- Reorient to energy or channel columns.
#
    x = reorient_particle_table(diff_proton_table, gen_column='channel') #: Reoriented table does not order columns by lowest energy by default
    x = x[['time_tag'] + DIFF_COLS]
    y = reorient_particle_table(intg_proton_table)
    y = y[['time_tag'] + INTG_COLS]
    z = reorient_particle_table(intg_electron_table)
#
# --- Include formatting and additional metadata as allowable in the ecsv format.
#
    for col in DIFF_COLS:
        x[col].unit = DIFF_PROTON_UNIT
        x[col].format = ".5e"
    for col in INTG_COLS:
        y[col].unit = INTG_PROTON_UNIT
        y[col].format = ".5e"
    z['>=2 MeV'].unit = INTG_ELECTRON_UNIT
    z['>=2 MeV'].format = ".5e"

    x.meta['source'] = DIFF_PROTONS_LINK
    y.meta['source'] = INTG_PROTONS_LINK
    z.meta['source'] = INTG_ELECTRONS_LINK

    x.write(f"{GOES_DATA_DIR}/goes_differential_protons.ecsv", overwrite = True, format='ascii.ecsv', delimiter=',')
    y.write(f"{GOES_DATA_DIR}/goes_integral_protons.ecsv", overwrite = True, format='ascii.ecsv', delimiter=',')
    z.write(f"{GOES_DATA_DIR}/goes_integral_electrons.ecsv", overwrite = True, format='ascii.ecsv', delimiter=',')

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", help = "Determine data output file path")
    args = parser.parse_args()

    if args.mode == 'test':
        if args.path:
            GOES_DATA_DIR = args.path
        else:
            GOES_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(GOES_DATA_DIR, exist_ok=True)

        fetch_goes_tables()

    elif args.mode == "flight":
        fetch_goes_tables()