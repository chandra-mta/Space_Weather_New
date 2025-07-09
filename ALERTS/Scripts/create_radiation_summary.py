#!/proj/sot/ska3/flight/bin/python
"""
**create_radiation_summary.py**: Compute GOES fluence of this orbital period

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 07, 2025
"""
import sys
import os
from astropy.table import Table
import re
import numpy as np
from cxotime import CxoTime
import urllib.request
import json
import argparse
import getpass
import traceback
#
# --- Define Directory Pathing
#
EPHEM_FILE = "/data/mta4/Space_Weather/EPHEM/Data/PE.EPH.gsme_spherical"
ALERTS_DATA_DIR = "/data/mta4/Space_Weather/ALERTS/Data"
CXONOW = CxoTime()

#
#--- json data locations proton and electron
#
PLINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
ELINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'

def create_radiation_summary():
    run_goes_fluence_extract()

def run_goes_fluence_extract():
    """
    compute GOES fluence of this orbital period
    input: none, but read from web
    output: <alert_dir>/Data/goes_fluence.dat
    """
#
#--- get the orbit starting time
#
    orbit_start = find_the_orbit_period()
    if orbit_start is None:
        raise ValueError("Orbit starting time not found.")

    proton_table = json2table(PLINK)
    electron_table = json2table(ELINK)
    proton_table = reorient_particle_table(proton_table, gen_column = 'channel', column_list = ['P4', 'P7'])
    electron_table = reorient_particle_table(electron_table)

    #: Keep only entires which are after the start of this orbit.
    proton_table.add_column(CxoTime(proton_table['time_tag']).secs, name='cxotime')
    electron_table.add_column(CxoTime(electron_table['time_tag']).secs, name='cxotime')
    proton_table = proton_table[proton_table['cxotime'] >= orbit_start]
    electron_table = electron_table[electron_table['cxotime'] >= orbit_start]

    #: Convert proton unit to MEV in line with Electron Unit
    proton_table['P4'] = proton_table['P4']*1e3
    proton_table['P7'] = proton_table['P7']*1e3

    #: Compute fluence for each energy distinction. Multiply by 300 seconds for sum of 5-min segment table entries
    #: Ignore invalid values. Invalid proton marker is -1e5, invalid electron marker is 4.
    p4_fluence = sum(proton_table[proton_table['P4'] >= 0]['P4']) * 300
    p7_fluence = sum(proton_table[proton_table['P7'] >= 0]['P7']) * 300
    e2_fluence = sum(electron_table[electron_table['>=2 MeV'] > 4]['>=2 MeV']) * 300

    #: Also record the final flux value for each channel.

    goes_fluence_dict = {
        "cxotime": proton_table['cxotime'][-1],
        "p4_fluence": p4_fluence,
        "p7_fluence": p7_fluence,
        "e2_fluence": e2_fluence,
        "p4_last_flux": proton_table['P4'][-1],
        "p7_last_flux": proton_table['P7'][-1],
        "e2_last_flux": electron_table['>=2 MeV'][-1]
    }
    with open(f"{ALERTS_DATA_DIR}/goes_fluence.json", 'w') as f:
        json.dump(goes_fluence_dict, f, indent = 4)

def find_the_orbit_period():
    """
    find the last orbital starting time
    input: none but read from: 
                <ephem_dir>/Data/PE.EPH.gsme_spherical
    output: the orbit starting time in seconds from 19981.1.

    :TODO: Store ephemeris calculation in small csv file for astropy ascii parsing
    """
    with open(EPHEM_FILE) as f:
        data = [line.strip() for line in f.readlines()]
    t_list = []
    alt    = []
    for ent in data:
        atemp = re.split(r'\s+', ent)
        stime = float(atemp[0])
        if stime > CXONOW.secs:
            break
        #: saves time and altitude only
        t_list.append(stime)
        alt.append(float(atemp[1]))

    dlen   = len(t_list)
    t_list = t_list[::-1]
    alt    = alt[::-1]
    for k in range(0, dlen-2):
        if (alt[k] >= alt[k+1]) and (alt[k+1] <= alt[k+2]):
            return t_list[k+1]

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
        with urllib.request.urlopen(jlink) as url:
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
        column_list = sorted(set(table[gen_column]))
    
    new_rows = []
    for time in time_list:
        row = {time_column: time}
        for col in column_list:
            selection = np.logical_and(table[time_column] == time, table[gen_column] == col)
            if sum(selection) == 0:
                flux = np.ma.masked
            else:
                flux = table[selection]['flux'].data[0]
            row.update({col: flux})
        new_rows.append(row)
    
    return Table(rows = new_rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-m",
        "--mode",
        choices=["flight", "test"],
        required=True,
        help="Determine running mode.",
    )
    parser.add_argument(
        "-p",
        "--path",
        required=False,
        help="Directory path to determine output location of plot.",
    )
    args = parser.parse_args()
    #
    # --- Determine if running in test mode and change pathing if so
    #

    if args.mode == "test":
        #
        # --- Path output to same location as unit tests
        #
        ALERTS_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        if args.path:
            ALERTS_DATA_DIR = args.path
        os.makedirs(ALERTS_DATA_DIR, exist_ok=True)
        try:
            create_radiation_summary()
        except json.decoder.JSONDecodeError:
            traceback.print_exc()
            #: No cleanup of lock files
    elif args.mode == "flight":
        #
        # --- Create a lock file and exit strategy in case of race conditions
        #
        import getpass

        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(
                f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            )
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        try:
            create_radiation_summary()
        except json.decoder.JSONDecodeError:
            traceback.print_exc() #: Record issue with downloaded JSON and finish.
        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")

