#!/proj/sot/ska3/flight/bin/python
"""
**run_goes_fluence_extract.py**: Compute GOES fluence of this orbital period

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jul 01, 2025
"""
import os
from astropy.table import Table
import re
import numpy as np
from cxotime import CxoTime
import urllib.request
import json
#
# --- Define Directory Pathing
#
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"
EPHEM_FILE = "/data/mta4/Space_Weather/EPHEM/Data/PE.EPH.gsme_spherical"
ALERTS_DIR = "/data/mta4/Space_Weather/ALERTS"
ALERTS_WEB_DIR = "/data/mta4/www/RADIATION/Alerts"
CXONOW = CxoTime()

#
#--- json data locations proton and electron
#
PLINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
ELINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'

def run_goes_fluence_extract():
    """
    compute goese fluece of this orbital period
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
    #: Ignore invalid values. Invalid proton marker is -1e5, invalid electron marker is 4?
    p4_fluence = sum(proton_table[proton_table['P4'] >= 0]['P4']) * 300
    p7_fluence = sum(proton_table[proton_table['P7'] >= 0]['P7']) * 300
    e2_fluence = sum(electron_table[electron_table['>=2 MeV'] < 4]['>=2 MeV']) * 300

    #: Also record the final flux value for each channel.

#
#--- print out the data
#
    line = '#TIME\t\t\t\tP4\t\t\tP7\t\t\tE>2.0MeV\n'
    line = line + current_time_date + '\t'

    if p_diff[0] == 'na':
        line = line + 'NA\t'
        line = line + 'NA\t'
        line = line + 'NA\n'
        line = line + 'Fluence:' + ' ' * 9 + '\t'
        line = line + 'NA\t'
        line = line + 'NA\t'
        line = line + 'NA\n'
    else:
        line = line +  adjust_format(p_diff[0]) + '\t'
        line = line +  adjust_format(p_diff[1]) + '\t'
        line = line +  adjust_format(e_diff[0]) + '\n'
        line = line + 'Fluence:' + ' ' * 9 + '\t'
        line = line +  adjust_format(p_acc[0])  + '\t'
        line = line +  adjust_format(p_acc[1])  + '\t'
        line = line +  adjust_format(e_acc[0])  + '\n'

    ofile = f"{ALERTS_DIR}/Data/goes_fluence.dat"
    with open(ofile, 'w') as fo:
        fo.write(line)

def adjust_format(val):
    try:
        return '%5.3e' % float(val)
    except:  # noqa: E722
        return 'n/a'

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
                flux = None
            else:
                flux = table[selection]['flux'].data[0]
            row.update({col: flux})
        new_rows.append(row)
    
    return Table(rows = new_rows)

if __name__ == "__main__":

    run_goes_fluence_extract()
