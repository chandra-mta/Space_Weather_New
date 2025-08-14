#!/proj/sot/ska3/flight/bin/python
"""

**fetch_kp_tables.py**: Fetch KP index forecast tables and data from SWPC NOAA

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 24, 2025


:NOTE:
    - https://kp.gfz.de/en/
    - https://kp.gfz.de/en/data
    - https://www.gfz.de/en/section/geomagnetism/data-products-services/geomagnetic-kp-index
    - https://spaceweather.gfz.de/products-data/forecasts/forecast-kp-index
    - https://www.swpc.noaa.gov/products/planetary-k-index
    - https://www.swpc.noaa.gov/sites/default/files/images/u2/TheK-index.pdf
"""
import os
import json
from time import sleep
from datetime import datetime, timedelta
import urllib
from astropy.table import Table
from cxotime import CxoTime
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
SOURCE_SWPC = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
SOURCE_IAGA = "https://www-app3.gfz-potsdam.de/kp_index/qlyymm.tab"
CXONOW = CxoTime()

def fetch_kp_tables():
    """
    Fetch and write out the multiple versions of KP tables for each observatory source.

    :NOTE: Each observatory source pulls also pulls from other observatories in real-time and use their own weighting algorithm to calculate KP estimates.
    """

    swpc_kp = fetch_SWPC_KP()
    iaga_kp = fetch_IAGA_KP()

    swpc_filename = f"{KP_DATA_DIR}/kp_swpc.ecsv"
    swpc_kp.meta['description'] = "Forecast of the planetary KP index as sourced from the SWPC. Includes observed, estimated, and predicted values. https://www.swpc.noaa.gov/products/planetary-k-index."
    swpc_kp.meta['sources'] = [
        {'origin_link': SOURCE_SWPC,
         'origin_script': os.path.abspath(__file__),
         'update_time': CXONOW.date,
         'mta_owned_origin': False,
         'output_file': swpc_filename
        }
    ]
    swpc_kp.write(swpc_filename, overwrite=True, delimiter=',')

    iaga_filename = f"{KP_DATA_DIR}/kp_iaga.ecsv"
    iaga_kp.meta['description'] = "Observations of the planetary KP index as compiled by the IAGA. https://www-app3.gfz-potsdam.de/kp_index/qlyymm.html."
    iaga_kp.meta['sources'] = [
        {'origin_link': SOURCE_IAGA,
         'origin_script': os.path.abspath(__file__),
         'update_time': CXONOW.date,
         'mta_owned_origin': False,
         'output_file': iaga_filename
        }
    ]
    iaga_kp.write(iaga_filename, overwrite=True, delimiter=',')

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

def fetch_SWPC_KP():
    """
    Fetch the KP forecast data from the SWPC and orient into a workable astropy table

    :Links: https://www.swpc.noaa.gov/products/planetary-k-index
    """
    forecast = read_json(SOURCE_SWPC)
    kp_forecast_table = reorient_forecast(forecast)
    return kp_forecast_table

@rerun
def fetch_IAGA_KP():
    """
    Fetches the KP measurement and estimates as weighted by the IAGA
    
    :Links: https://www-app3.gfz-potsdam.de/kp_index/qlyymm.html    
    :NOTE: Columns are date, 3-hour-blocks_kp(8), daily_sum, average_ap, average_cp
    """
    def _translate(s):
        """
        Translate string marker to float value.
        """
        if s[1] == '+':
            return round(float(s[0]) + 0.33,3)
        elif s[1] == '-':
            return round(float(s[0]) - 0.33,3)
        elif s[1] == 'o':
            return round(float(s[0]),3)
    
    #: IAGA source formats data as a custom string parse with custom tab delimination
    with urllib.request.urlopen(SOURCE_IAGA, timeout = 10) as url:
        output = url.read().decode()
        raw_lines = [line.strip() for line in output.split('\n') if line != '']
    
    #: Cut the tabs by line and ignore the daily average and sums, keeping on the KP index for each hour block
    kp_lines = [x.split()[:9] for x in raw_lines]
    
    #: Iterate through each day
    time_tag = []
    kp = []
    for day in kp_lines:
        date = datetime.strptime(day[0], '%y%m%d')
        for i, entry in enumerate(day[1:]):
            time = date + timedelta(hours=3*i)
            time_tag.append(time.isoformat(timespec='seconds') + 'Z')
            kp.append(_translate(entry))
    
    return Table([time_tag, kp], names = ('time_tag', 'kp'))

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