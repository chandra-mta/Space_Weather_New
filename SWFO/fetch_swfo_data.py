#!/proj/sot/ska3/flight/bin/python
"""
**fetch_swfo_data.py.py**: Fetch the SWFO related data files

:Author: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Sep 03, 2025


:Links:
    - http://sd-www.jhuapl.edu/ACE/EPAM/idf.html

"""
import os
import json
import urllib
from astropy.table import Table
from time import sleep
import argparse
import getpass
import signal
#
# --- Define Directory Pathing
#
SWFO_DATA_DIR = "/data/mta4/Space_Weather/SWFO/Data"
OUT_SWFO_DATA_DIR = SWFO_DATA_DIR
#
# --- Globals
#
SWFO_LINK = "Undetermined" #: Link to SWFO-L1 data from the SWPC.
PROTON_UNIT = "protons/(cm^2*s*sr*KeV)" #: Differential Flux Unit
ELECTRON_UNIT = "electrons/(cm^2*s*sr*KeV)" #: Differential Flux Unit
#: Columns to retain from the ACE-formatted L2 data from the SWFO-L1 STIS instrument.
_COLS = ('time_tag',
         'dsflag_de1',
         'de1',
         'dsflag_de4',
         'de4',
         'dsflag_p1',
         'p1',
         'dsflag_p2',
         'p2',
         'dsflag_p3',
         'p3',
         'dsflag_p4',
         'p4',
         'dsflag_p5',
         'p5',
         'dsflag_p6',
         'p6',
         'dsflag_fp6p',
         'fp6p',
         'dsflag_p7',
         'p7',
         'dsflag_p8',
         'p8'
         )

#: Descriptions of columns also includes energy band ranges in KeV.
_COLS_DESCRIPTION = {
    'time_tag': "Time point in ISOT format.",
    'de1': "LEMS30/Wart B, Deflected electrons. Range: (38-45)",
    'de4': "LEMS30/Wart B, Deflected electrons. Range: (175-315)",
    'p1': "LEMS120, Ions. Range: (47-68)",
    'p2': "LEMS120, Ions. Range: (68-115)",
    'p3': "LEMS120, Ions. Range: (115-195)",
    'p4': "LEMS120, Ions. Range: (195-321)",
    'p5': "LEMS120, Ions. Range: (310-580)",
    'p6': "LEMS120, Ions. Range: (587-1060)",
    'fp6p': "LEFS60, Ions. Range: (795-1193)",
    'p7': "LEMS120, Ions. Range: (1060-1900)",
    'p8': "LEMS120, Ions. Range: (1900-4800)",
}

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

def fetch_swfo_data():
    """
    Fetch the relevant SWFO L2 data formatted into ACE bins

    :NOTE: Status indication columns are as follows
        - 0: nominal
        - 4,6,7,8: bad data, unable to process
        - 9: no data
        - -1: missing data value
    """

    swfo_table = json2table(SWFO_LINK)
    swfo_table.sorted('time_tag')
    swfo_table = swfo_table[_COLS]
    for k,v in _COLS_DESCRIPTION.items():
        swfo_table[k].description = v
        swfo_table[k].unit = PROTON_UNIT
    #: Corrections
    swfo_table['time_tag'].unit = None
    swfo_table['de1'].unit = ELECTRON_UNIT
    swfo_table['de4'].unit = ELECTRON_UNIT
    #: TODO insert relevant metadata
    swfo_table.write("swfo_daily_table.ecsv", overwrite=True, delimiter=',')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", help = "Determine data output file path")
    args = parser.parse_args()

    if args.mode == 'test':
        if args.path:
            SWFO_DATA_DIR = args.path
        else:
            SWFO_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(SWFO_DATA_DIR, exist_ok=True)

        fetch_swfo_data()

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
        
        fetch_swfo_data()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")