#!/proj/sot/ska3/flight/bin/python

#################################################################################
#                                                                               #
#   run_goes_fluence_extract.py: compute goese fluece of this orbital period    #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: Mar 16, 2021                                           #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import math
import time
import Chandra.Time
import maude
import urllib.request
import json
import random

path = '/data/mta4/Space_Weather/house_keeping/dir_list'
with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a private folder
#
sys.path.append(goes_dir)
sys.path.append('/data/mta4/Script/Python3.8/MTA/')

import mta_common_functions     as mcf
#
#--- set a temporary file name
#
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- current goes satellite #
#
satellite = 16
#
#--- json data locations proton and electron
#
plink = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
elink = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json'
#proton_list = ['1020-1860 keV','1900-2300 keV','2310-3340 keV','3400-6480 keV', '5840-11000 keV',\
#               '11640-23270 keV','25900-38100 keV','40300-73400 keV','83700-98500 keV',\
#               '99900-118000 keV','115000-143000 keV', '160000-242000 keV','276000-404000 keV']
#pout_list   = ['P1', 'P2A', 'P2B', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8A', 'P8B', 'P8C', 'P9', 'P10']
#elink = 'https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-3-day.json'
#elec_list  = ["80-115 keV", "115-165 keV", "165-235 keV", "235-340 keV",\
#              "340-500 keV", "500-700 keV", "700-1000 keV", "1000-1900 keV"]
#eout_list   = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8']
#
#--- protone energy designations and output file names
#
proton_list = ['5840-11000 keV', '40300-73400 keV']
pout_list   = ['P4', 'P7']
#
#--- electron energy designation and output file name
#
elec_list = ['>=2 MeV',]
eout_list = ['goes_electron',]
#
#--- directories, files...
#
data_dir = goes_dir + 'Data/'
ephem_file       = ephem_dir + 'Data/PE.EPH.gsme_spherical'

#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs


#----------------------------------------------------------------------------
#-- run_goes_fluence_extract: compute goese fluece of this orbital period  --
#----------------------------------------------------------------------------

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
    if ostart == False:
        print("Something is wrong and could not get the orbit starting time\n")
        exit(1)
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

    ofile = alerts_dir + 'Data/goes_fluence.dat'
    with open(ofile, 'w') as fo:
        fo.write(line)

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def adjust_format(val):

    if mcf.is_neumeric(val):
        out = '%5.3e' % float(val)
    else:
        out = 'n/a'

    return out

#----------------------------------------------------------------------------
#-- compute_goes_fluence: extract GOES satellite flux data and compute the fluence of the current period
#----------------------------------------------------------------------------

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

#----------------------------------------------------------------------------
#-- find_the_orbit_period: find the last orbital starting time             --
#----------------------------------------------------------------------------

def find_the_orbit_period():
    """
    find the last orbital starting time
    input: none but read from: 
                <ephem_dir>/Data/PE.EPH.gsme_spherical
    output: the orbit starting time in seconds from 19981.1.
    """
    data = mcf.read_data_file(ephem_file)
    t_list = []
    alt    = []
    for ent in data:
        atemp = re.split('\s+', ent)
        stime = float(atemp[0])
        if stime > current_chandra_time:
            break

        t_list.append(stime)
        alt.append(float(atemp[1]))

    dlen   = len(t_list)
    t_list = t_list[::-1]
    alt    = alt[::-1]
    for k in range(0, dlen-2):
        if (alt[k] >= alt[k+1]) and (alt[k+1] <= alt[k+2]):
            return t_list[k+1]

    return False


#----------------------------------------------------------------------------

if __name__ == "__main__":

    run_goes_fluence_extract()
