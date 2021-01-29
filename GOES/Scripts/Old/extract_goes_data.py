#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#   extract_goes_data.py: extract GOES satellite proton/electron flux data      #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: Jan 23, 2020                                           #
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
sys.path.append('/data/mta/Script/Python3.6/MTA/')

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
plink = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json'
elink = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json'
#
#--- protone energy designations and output file names
#
proton_list = ['>=1 MeV', '>=5 MeV', '>=10 MeV', '>=30 MeV', '>=50 MeV',\
               '>=60 MeV', '>=100 MeV', '>=500 MeV']
pout_list   = ['goes_001mev_data', 'goes_005mev_data', 'goes_010mev_data', 'goes_030mev_data',\
               'goes_050mev_data', 'goes_060mev_data', 'goes_100mev_data', 'goes_500mev_data']
#
#--- electron energy designation and output file name
#
elec_list   = ['>=2 MeV',]
eout_list   = ['goes_electron',]
#
#--- goes data directory
#
data_dir = goes_dir + 'Data/'

#----------------------------------------------------------------------------
#-- run_goes_data_extract: extract GOES satellite proton/electron flux data  
#----------------------------------------------------------------------------

def run_goes_data_extract():
    """
    extract GOES satellite proton/electron flux data
    input: none, but read from web
    output: <data_dir>/<out file>
    """
#
#--- proton data
#
    extract_goes_data(plink, proton_list, pout_list)
#
#--- electron data
#
    extract_goes_data(elink, elec_list,   eout_list)

#----------------------------------------------------------------------------
#-- extract_goes_data: extract GOES satellite flux data                    --
#----------------------------------------------------------------------------

def extract_goes_data(dlink, energy_list, out_list):
    """
    extract GOES satellite flux data
    input: dlink        --- json web address
            energy_list --- a list of energy designation 
            out_list    --- a list of output file names
    output: <data_dir>/<out file>
    """
#
#--- read json file from the web
#
    with urllib.request.urlopen(dlink) as url:
        data = json.loads(url.read().decode())
#
#--- go through all energy ranges
#
    elen  = len(energy_list)
    for k in range(0, elen):
        t_list = []
        f_list = []
        energy = energy_list[k]
#
#--- check the last entry time and make sure that the data won't be repeated
#
        ltime  = check_last_entry_time(out_list[k])
        line   = ''
        for ent in data:
#
#--- get the data from a specified satellite
#
            if ent['satellite'] != satellite:
                continue
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
                flux  = float(ent['flux'])
#
#--- convert time into seconds from 1998.1.1
#
                otime = ent['time_tag']
                otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                stime = int(Chandra.Time.DateTime(otime).secs)

                if stime <= ltime:
                    continue
    
                line  = line + str(stime) + '\t' + str(flux) + '\n'
#
#---- append the data to existing data file
#
        if line != '':
            outfile = data_dir + out_list[k]
            with open(outfile, 'a') as fo:
                fo.write(line)

#----------------------------------------------------------------------------
#-- check_last_entry_time: check the last data entry time of the given data file 
#----------------------------------------------------------------------------

def check_last_entry_time(fname):
    """
    check the last data entry time of the given data file
    input:  fname   --- a file name
    output: ltime   --- the last entry time in seconds from 1998.1.1
    """

    ifile = data_dir + fname
    if os.path.isfile(ifile):
        data  = mcf.read_data_file(ifile)
        atemp = re.split('\s+', data[-1])
        ltime = float(atemp[0])

    else:
        ltime = 0.0

    return ltime


#----------------------------------------------------------------------------

if __name__ == "__main__":

    run_goes_data_extract()
