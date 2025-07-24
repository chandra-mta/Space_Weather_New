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
import argparse
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

def fetch_kp_tables():
    """
    Fetch the KP forecast data from SWPC and orient into a workable astropy table with metadata
    """
    forecast = read_json(KP_FORECAST_LINK)
    kp_forecast_table = reorient_forecast(forecast)

    kp_forecast_table.meta['source'] = KP_FORECAST_LINK
    kp_forecast_table.meta['script'] = os.path.abspath(__file__)

    kp_forecast_table.write(f"{KP_DATA_DIR}/kp_forecast.ecsv", overwrite=True, format='ascii.ecsv', delimiter=',')

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

def reorient_forecast(forecast):
    """
    Reorient the KP SWPC forecast into an astropy table format
    """
    rows = []
    #:First list is the column headers
    for i in range(1,len(forecast)):
        new_row = {}
        #: We don't need the NOAA scale for radio blackouts,
        #: and we want to store time values in ISO 8601 format.
        a = forecast[i][0].split()
        new_row['time_tag'] = f"{a[0]}T{a[1]}Z"
        new_row['kp'] = float(forecast[i][1])
        new_row['observed'] = forecast[i][2]
        rows.append(new_row)
    
    kp_forecast_table = Table(rows=rows)
    return kp_forecast_table

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", help = "Determine data output file path")
    args = parser.parse_args()

    if args.mode == 'test':
        if args.path:
            KP_DATA_DIR = args.path
        else:
            KP_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(KP_DATA_DIR, exist_ok=True)

        fetch_kp_tables()

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

        fetch_kp_tables()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")