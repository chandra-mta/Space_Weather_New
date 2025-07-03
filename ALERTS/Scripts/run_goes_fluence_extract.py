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
    ostart = find_the_orbit_period()
    if ostart is None:
        raise ValueError("Orbit starting time not found.")
#
#--- proton data
#
    p_diff, p_acc = compute_goes_fluence(plink, proton_list, ostart, 1.e3)
#
#--- electron data
#
    e_diff, e_acc = compute_goes_fluence(elink, elec_list, ostart, 1.0)
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

def compute_goes_fluence(dlink, energy_list, ostart, factor):
    """
    extract GOES satellite flux data and compute the fluence of the current period
    input: dlink        --- json web address
            energy_list --- a list of energy designation 
            ostart      --- orbit starting time in seconds from 1998.1.1
    output: <data_dir>/<out file>
    """
#
#--- read json file from the web
#
    try:
        with urllib.request.urlopen(dlink) as url:
            data = json.loads(url.read().decode())
    except:
        return ['na', 'na'], ['na', 'na']
#
#--- go through all energy ranges
#
    elen   = len(energy_list)
    d_save = []
    a_save = []
    for k in range(0, elen):
        fluence = 0.0
        aflux   = 0.0
        energy = energy_list[k]
        for ent in data:
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
#
#--- convert time into seconds from 1998.1.1
#
                otime = ent['time_tag']
                otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                stime = int(Chandra.Time.DateTime(otime).secs)
                if stime < ostart:
                    continue
                try:
                    flux  = float(ent['flux'])
                except:
                    continue
#
#--- a bad value appeas as negative
#
                if flux < 0.0:
                    continue 
#
#--- for the case of electron,  the null value seems 4.0; so drop it
#
                if factor == 1.0 and flux <= 4.0:
                    continue
#
#--- data is given every 5 mins
#
                aflux    = flux * factor
                fluence += aflux * 300


        d_save.append(aflux)
        a_save.append(fluence)


    return d_save, a_save

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
