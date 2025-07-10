#!/proj/sot/ska3/flight/bin/python
"""
**create_radiation_summary.py**: Compute GOES fluence of this orbital period

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 07, 2025

:TODO: Change customized file format for data sets fetched to generate summary. Should be a commonly used standard.

"""
import sys
import os
from astropy.table import Table
from datetime import datetime
import numpy as np
from cxotime import CxoTime
from kadi.events import rad_zones
import urllib.request
import json
import argparse
import getpass
import traceback

#
# --- Define Directory Pathing
#
ALERTS_WEB_DIR = "/data/mta4/www/RADIATION/Alerts"
CRM_DATA_FILE = "/data/mta4/Space_Weather/CRM3/Data/CRMsummary.dat"
ACIS_ACE_FILE = "/proj/web-cxc/htdocs/acis/Fluence/current.dat"
COMM_DATA_FILE = "/data/mta4/Space_Weather/Comm_data/Data/comm_data"
FP_HISTORY_FILE = "/proj/sot/acis/FLU-MON/FPHIST-2001.dat"
CXONOW = CxoTime()

#
#--- json data locations proton and electron
#
PLINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
ELINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'

def create_radiation_summary():

    crm_data = read_crm_summary()
    cxo_orbit_start = CxoTime(crm_data['orbit_start'])
    time_data = {'seconds_in_orbit_period': round((CXONOW - cxo_orbit_start).sec)} #: astropy.time.core.TimeDelta when subtracted

    goes_fluence_data = compute_goes_fluence(cxo_orbit_start)
    acis_ace_data = read_acis_ace_data()
    comm_data = read_comm_data()

    next_rad = CxoTime(rad_zones.filter(start = CXONOW).table['start'][0])
    time_data['next_rad_zone_entry'] = next_rad.date.split('.')[0]
    time_data['seconds_till_rad_zone'] = round((next_rad - CXONOW).sec) #: astropy.time.core.TimeDelta when subtracted
    fp_history_table = read_fp_history_file()
    
    time_data['attenuated_rad_duration'] = find_acis_attenuated_time(fp_history_table, CXONOW, next_rad)
    time_data['attenuated_next_comm_duration'] = find_acis_attenuated_time(fp_history_table, CXONOW, CxoTime(comm_data['next_comm']))
    time_data['attenuated_second_comm_duration'] = find_acis_attenuated_time(fp_history_table, CXONOW, CxoTime(comm_data['second_comm']))

    rad_summ = {}
    rad_summ.update(crm_data)
    rad_summ.update(goes_fluence_data)
    rad_summ.update(acis_ace_data)
    rad_summ.update(comm_data)
    rad_summ.update(time_data)

    with open(f'{ALERTS_WEB_DIR}/radiation_summary.json', 'w') as f:
        json.dump(rad_summ, f, indent = 4)

def read_crm_summary():
    """
    Read the CRM summary file.
    
    :NOTE: Altitude describes the geocentric distance in (km), and the orbit leg (ascending or descending)
    :TODO: Identify manner of attenuation.
    """

    crm_data = {}
    with open(CRM_DATA_FILE) as f:
        data = [line.strip() for line in f.readlines() if line.strip() != '']
        crm_data['instrument_config'] = data[0].split(":")[1].strip()
        crm_data['orbit_start'] = data[6].split(" : ")[1].strip()
        crm_data['altitude'] = data[7].split(":")[1].strip()
        crm_data['crm_flux'] = float(data[9].split(":")[1].strip())
        crm_data['attenuated_crm_flux'] = float(data[10].split(":")[1].strip())
        crm_data['crm_fluence'] = float(data[11].split(":")[1].strip())
        crm_data['attenuated_crm_fluence'] = float(data[12].split(":")[1].strip())
        crm_data['crm_last_update'] = data[13].split(": ")[1].strip()
    
    crm_data['attenuated_flux_factor'] = crm_data['attenuated_crm_flux'] / crm_data['crm_flux']
    crm_data['attenuated_fluence_factor'] = crm_data['attenuated_crm_fluence'] / crm_data['crm_fluence']
    return crm_data

def compute_goes_fluence(cxo_orbit_start):
    """
    Compute GOES fluence of this orbital period.

    :param cxo_orbit_start: CxoTime object of the start of this current orbit as read from the CRM summary.
    :type cxo_orbit_start: CxoTime
    """

    proton_table = json2table(PLINK)
    electron_table = json2table(ELINK)
    proton_table = reorient_particle_table(proton_table, gen_column = 'channel', column_list = ['P4', 'P7'])
    electron_table = reorient_particle_table(electron_table)

    #: Keep only entires which are after the start of this orbit.
    proton_table.add_column(CxoTime(proton_table['time_tag']).secs, name='cxotime')
    electron_table.add_column(CxoTime(electron_table['time_tag']).secs, name='cxotime')
    proton_table = proton_table[proton_table['cxotime'] >= cxo_orbit_start.secs]
    electron_table = electron_table[electron_table['cxotime'] >= cxo_orbit_start.secs]

    #: Convert proton unit to MEV in line with Electron Unit
    proton_table['P4'] = proton_table['P4']*1e3
    proton_table['P7'] = proton_table['P7']*1e3

    #: Compute fluence for each energy distinction. Multiply by 300 seconds for sum of 5-min segment table entries
    #: Ignore invalid values. Invalid proton marker is -1e5, invalid electron marker is 4.
    p4_fluence = sum(proton_table[proton_table['P4'] >= 0]['P4']) * 300
    p7_fluence = sum(proton_table[proton_table['P7'] >= 0]['P7']) * 300
    e2_fluence = sum(electron_table[electron_table['>=2 MeV'] > 4]['>=2 MeV']) * 300

    #: Also record the final flux value for each channel.

    goes_fluence_data = {
        "goes_last_update": CxoTime(proton_table['cxotime'][-1]).date.split('.')[0],
        "p4_fluence": p4_fluence,
        "p7_fluence": p7_fluence,
        "e2_fluence": e2_fluence,
        "p4_last_flux": proton_table['P4'][-1],
        "p7_last_flux": proton_table['P7'][-1],
        "e2_last_flux": electron_table['>=2 MeV'][-1]
    }

    return goes_fluence_data

def read_acis_ace_data():
    """
    Pull the ACIS team's calculation for ACE flux, fluence, and attenuation to ACIS.

    :NOTE: Attenuated in this context references the flux and fluence experienced by ACIS for the ACE P3 channel.
    Therefore, if ACIS is not in the focal plane, then the measurement is attenuated to zero. This calculation is done byt ACIS team.
    """
    acis_ace_data = {}
    with open(ACIS_ACE_FILE) as f:
        data = [line.strip() for line in f.readlines() if line.strip() != '']
        _a = data[5].split()
        acis_ace_data['ace_last_update'] = datetime.strptime(f"{_a[0]}-{_a[1]:>02}-{_a[2]:>02}-{_a[3]:>04}", '%Y-%m-%d-%H%M').strftime("%Y:%j:%H:%M:%S")
        acis_ace_data['ace_p3_flux'] = float(_a[9])
        acis_ace_data['ace_p3_fluence'] = float(data[7].split()[9])
        acis_ace_data['attenuated_ace_p3_flux'] = float(data[13].split()[9])
        acis_ace_data['attenuated_ace_p3_fluence'] = float(data[15].split()[9])
    return acis_ace_data

def read_comm_data():
    """
    Comm time listed in GMT.
    """
    comm_data = {}
    with open(COMM_DATA_FILE) as f:
        data = [line.strip().split() for line in f.readlines() if line.strip() != '' and line[0] != "#"]
        for i in range(len(data)-1):
            if float(data[i][5]) < CXONOW.secs and float(data[i+1][5]) > CXONOW.secs:
                next_comm = CxoTime(float(data[i+1][5]) +1)
                second_comm = CxoTime(float(data[i+2][5]) +1)
                break
    comm_data['next_comm'] = next_comm.date.split('.')[0]
    comm_data['second_comm'] = second_comm.date.split('.')[0]
    comm_data['seconds_till_next_comm'] = round((next_comm - CXONOW).sec) #: astropy.time.core.TimeDelta when subtracted
    comm_data['seconds_till_second_comm'] = round((second_comm - CXONOW).sec)
    return comm_data

def read_fp_history_file():
    """
    File columns are start time, instrument, obsid
    """
    rows = []
    with open(FP_HISTORY_FILE) as f:
        data = [line.strip() for line in f.readlines()]
        for line in data[-30:]:
            #: Start times, instrument, obsid
            _a = line.split()
            rows.append({'start_cxotime': CxoTime(_a[0]), 'instrument': _a[1]})
    for i in range(len(rows)-1):
        rows[i]['stop_cxotime'] = rows[i+1]['start_cxotime']
        rows[i]['duration'] = (rows[i]['stop_cxotime'] - rows[i]['start_cxotime']).sec

    return Table(rows=rows[:-1])

def find_acis_attenuated_time(fp_history_table, period_start, period_stop):
    """
    The selected table will contain time intervals for instrumentation use which are
    - using ACIS-I or ACIS-S
    - overlapping with the period_start and period_stop argument time period

    In this overlap, we calculate the subinterval of period_start to first entry stop,
    then last entry start to period_stop,
    then add in durations of all periods from in-between entries.
    """
    instrument_sel = np.logical_or(fp_history_table['instrument']== 'ACIS-I',fp_history_table['instrument']== 'ACIS-S')
    time_sel = np.logical_and(fp_history_table['stop_cxotime'] >= period_start, fp_history_table['start_cxotime'] <= period_stop)
    full_sel = np.logical_and(instrument_sel, time_sel)

    x = fp_history_table[full_sel]
    if len(x) == 0:
        attenuated_time = 0
    elif len(x) == 1:
        #
        # --- We have two time intervals with intederminant overlap.
        # --- Put all four in time order, then two middle time points
        # --- will be the duration.
        #
        _b = sorted([period_start, period_stop, x[0]['start_cxotime'], x[0]['stop_cxotime']])
        attenuated_time = (_b[2] - _b[1]).sec
    else:
        #
        # --- period_start is indeterminately before or within first entry
        # --- period_stop is indeterminately within or after last entry
        #
        _c = sorted([period_start, x[0]['start_cxotime'], x[0]['stop_cxotime']])
        _d = sorted([period_stop, x[-1]['start_cxotime'], x[-1]['stop_cxotime']])
        first_subinterval = (_c[2] - _c[1]).sec
        second_subinterval = (_d[1] - _d[0]).sec
        inner_duration = sum(x[1:-1]['duration'])
        attenuated_time = first_subinterval + second_subinterval + inner_duration
    
    return round(attenuated_time)

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
        ALERTS_WEB_DIR = f"{os.getcwd()}/test/_outTest"
        if args.path:
            ALERTS_WEB_DIR = args.path
        os.makedirs(ALERTS_WEB_DIR, exist_ok=True)
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

