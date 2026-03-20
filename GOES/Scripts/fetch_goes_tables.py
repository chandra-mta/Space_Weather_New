#!/proj/sot/ska3/flight/bin/python
"""
**fetch_goes_tables.py**: Fetch GOES particle tables and data from SWPC NOAA

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 21, 2025

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
import json
import urllib.request
import urllib.error
import argparse
from astropy.table import Table, Column, join
import numpy as np
from time import sleep
from cxotime import CxoTime
import getpass
import signal
#
# --- Define Directory Pathing
#
GOES_DATA_DIR = '/data/mta4/Space_Weather/GOES/Data'
DIFF_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
INTG_PROTONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json'
INTG_ELECTRONS_LINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'
XLINK = 'https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json'
EVENTLINK = "https://services.swpc.noaa.gov/json/edited_events.json"


DIFF_COLS = ['P1', 'P2A', 'P2B', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8A', 'P8B', 'P8C', 'P9', 'P10']
INTG_COLS = ['>=1 MeV', '>=5 MeV', '>=10 MeV', '>=30 MeV', '>=50 MeV', '>=60 MeV', '>=100 MeV', '>=500 MeV']

DIFF_PROTON_UNIT = "protons/(cm^2*s*sr*MeV)"
INTG_PROTON_UNIT = "protons/(cm^2*s*sr)"
INTG_ELECTRON_UNIT = "protons/(cm^2*s*sr)"
CXONOW = CxoTime()

def main():
    fetch_goes_tables()
    make_xray_table()

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
        x[col] *= 1000 #: This is a unit conversion from the SWPC differential unit in KeV to the Chandra usage of GOES in proxies in MeV units.
        x[col].unit = DIFF_PROTON_UNIT
        x[col].format = ".5e"
    for col in INTG_COLS:
        y[col].unit = INTG_PROTON_UNIT
        y[col].format = ".5e"
    z['>=2 MeV'].unit = INTG_ELECTRON_UNIT
    z['>=2 MeV'].format = ".5e"

#
# --- Write table file metadata
#
    x_filename = f"{GOES_DATA_DIR}/goes_differential_protons.ecsv"
    x.meta['description'] = "Differential directional proton fluxes reported in 13 energy bands between 1.02 MeV and 404 MeV from the GOES-R series satellite. https://www.spaceweather.gov/products/goes-proton-flux."
    x.meta['sources'] = [
        {
            'origin_link': DIFF_PROTONS_LINK,
            'origin_script': os.path.abspath(__file__),
            'update_time': CXONOW.date,
            'mta_owned_origin': False,
            'output_file': x_filename
        }
    ]
    y_filename = f"{GOES_DATA_DIR}/goes_integral_protons.ecsv"
    y.meta['description'] = "Integral proton fluxes reported in 8 energy thresholds between ≥1 and ≥500 MeV from the GOES-R series satellite. https://www.spaceweather.gov/products/goes-proton-flux."
    y.meta['sources'] = [
        {
            'origin_link': INTG_PROTONS_LINK,
            'origin_script': os.path.abspath(__file__),
            'update_time': CXONOW.date,
            'mta_owned_origin': False,
            'output_file': y_filename
        }
    ]
    z_filename = f"{GOES_DATA_DIR}/goes_integral_electrons.ecsv"
    z.meta['description'] = "Integral electron fluxes for ≥2 MeV from the GOES-R series satellite. https://www.spaceweather.gov/products/goes-electron-flux."
    z.meta['sources'] = [
        {
            'origin_link': INTG_ELECTRONS_LINK,
            'origin_script': os.path.abspath(__file__),
            'update_time': CXONOW.date,
            'mta_owned_origin': False,
            'output_file': z_filename
        }
    ]
    x.write(x_filename, overwrite = True, format='ascii.ecsv', delimiter=',')
    y.write(y_filename, overwrite = True, format='ascii.ecsv', delimiter=',')
    z.write(z_filename, overwrite = True, format='ascii.ecsv', delimiter=',')

def make_xray_table():
    """
    Pull X-ray events from SWPC and save webpage table to file
    """
    flare_table = json2table(XLINK)
    event_table = json2table(EVENTLINK)
    #
    # --- Flare table contains the all observed x-ray events by GOES
    # --- The full events table is filtered to provide active region of these flares
    #
    sel = np.zeros(len(event_table), dtype=bool)
    for idx, row in enumerate(event_table):
        for flare_row in flare_table:
            if row['begin_datetime'] == flare_row['time_tag'][:-1] and row['observatory'] == f"G{flare_row['satellite']}":
                sel[idx] = True
    #
    # --- With the correctly selected events, further refine in order to concatenate data tables.
    #
    flare_matching_events = event_table[sel]
    flare_matching_events.rename_column('begin_datetime','time_tag')
    flare_matching_events['time_tag'] = [f"{x}Z" for x in flare_matching_events['time_tag']]

    if len(flare_table) == 0 and len(flare_matching_events) == 0:
        #: No x-ray events. Maintain metadata but write empty table.
        flare_table.add_column(Column(name = 'region', dtype=np.dtype('O')))
    else:
        flare_table = join(flare_table, flare_matching_events['time_tag', 'region'], join_type='left')
    #
    # --- Event might not list the AR (Listed as None), or it might not match with flare_table (Listed as np.ma.masked)
    #
    flare_table['region'] = flare_table['region'].tolist()
    #: Apply metadata
    filename = f'{GOES_DATA_DIR}/goes_flares.ecsv'
    flare_table['max_xrlong'].unit = "W/m^2*s"
    flare_table['current_int_xrlong'].unit = "W/m^2"

    flare_table.meta["description"] = (
        "X-ray flare fluxes and classifications from the GOES-R series satellite. The begin time of an X-ray event is defined as the first minute, in a sequence of 4 minutes, of steep monotonic increase in 0.1-0.8 nm flux. The X-ray event maximum is taken as the minute of the peak X-ray flux. The end time is the time when the flux level decays to a point halfway between the maximum flux and the pre-flare background level. The max_xrlong column consists of the peak flux. The current_int_xrlong is the integrated flux. A flare source region column is included in this table as determined from the SWPC events table. https://www.swpc.noaa.gov/products/goes-x-ray-flux."
    )
    flare_table.meta['sources'] = [
        {
            'origin_link': XLINK,
            'origin_script': os.path.abspath(__file__),
            'update_time': CXONOW.date,
            'mta_owned_origin': False,
            'output_file': filename
        },
        {
            'origin_link': EVENTLINK,
            'origin_script': os.path.abspath(__file__),
            'update_time': CXONOW.date,
            'mta_owned_origin': False,
            'output_file': filename
        }
    ]
    #
    #--- Save table to GOES Data
    #
    flare_table.write(filename, overwrite = True, format='ascii.ecsv', delimiter = ',')

def rerun(func):
    """
    Function decorator which sleeps and reruns the provided function upon encountering a set of errors.
    """
    _freq = 3
    _errors = (json.decoder.JSONDecodeError, urllib.error.URLError)
    def wrapper_func(*args,**kwargs):
        _last_exception = Exception()
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

def reorient_particle_table(table, gen_column = 'energy', column_list = None) -> Table:
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

        main()

    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions
#
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            with open(f"/tmp/{user}/{name}.lock") as f:
                pid = int(f.readlines()[-1].strip())
                #Kill old stalling process and remove corresponding lock file.
                os.remove(f"/tmp/{user}/{name}.lock")
                try:
                    os.kill(pid,signal.SIGTERM)
                except ProcessLookupError:
                    pass
                #Generate lock file for the current corresponding process
                os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")
        else:
            #Previous script run must have completed successfully. Prepare lock file for this script run.
            os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")
        
        main()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")
