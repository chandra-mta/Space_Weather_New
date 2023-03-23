#!/proj/sot/ska3/flight/bin/python

#################################################################################
#                                                                               #
#       collect_goes_long.py: collect data for the long term use                #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: Apr 22, 2021                                           #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import math
import time
import datetime
import Chandra.Time
import urllib.request
import json
import random
import numpy

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

#import mta_common_functions     as mcf
#
#--- set a temporary file name
#
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- json data locations proton and electron
#
plink = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json'
#
#--- protone energy designations and output file names
#
proton_list = ['1020-1860 keV',   '1900-2300 keV',   '2310-3340 keV',    '3400-6480 keV',\
               '5840-11000 keV',  '11640-23270 keV', '25900-38100 keV',  '40300-73400 keV',\
               '83700-98500 keV', '99900-118000 keV','115000-143000 keV','160000-242000 keV',\
               '276000-404000 keV']
#
#--- goes data directory
#
data_dir  = goes_dir + 'Data/'
#
#--- current goes satellite #
#
satellite = "Primary"

#----------------------------------------------------------------------------
#-- collect_goes_long: collect data for the long term use                  --
#----------------------------------------------------------------------------

def collect_goes_long():
    """
    collect data for the long term use
    input: none, but read from web
        https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json
    output: <data_dir>/goes_data_r.txt
                Time P1  P2A P2B P3  P4  P5  P6  P7  P8A P8B P8C P9  P10 HRC Proxy
    """
#
#--- find the last entry time
#
    outfile = goes_dir + 'Data/goes_data_r.txt'
    #data    = mcf.read_data_file(outfile)
    with open(outfile, 'r') as f:
        data = [line.strip() for line in f.readlines()]
    m       = -1
    cut     = 0
    while cut == 0:
        atemp   = re.split('\s+', data[m])
        if len(atemp) > 0: 
            try:
                cut     = Chandra.Time.DateTime(atemp[0]).secs
                break
            except:
                m -= 1
        else:
            m = -1
#
#--- extract proton data
#
    p_data = extract_goes_data(plink, proton_list)
#
#--- time list
#
    t_list = p_data[0][0]
    d_len  = len(t_list)
#
#--- banch up the fluxes (definition of p values are different from the older ones)
#
#    [p1, p2, p3, p4, p5, p6] = compute_p_vals(p_data)
#
#--- compute hrc proxy
#
    hrc_val = compute_hrc(p_data)
#
#--- aline will save the text output of the table which is used by CRM
#
    line = ''

    for k in range(0, d_len):
        stime = Chandra.Time.DateTime(t_list[k]).secs
        if stime < cut:
            continue
        line = line + t_list[k]  + '\t\t'

        for m in range(0, 13):
            try:
                line = line + adjust_format(p_data[m][1][k])  + "\t"
            except:
                line = line + "0.0\t"

        line = line + "%5.0f\t\n" % (hrc_val[k])
#
#---  print out data file for ACIS Rad use
#
    with open(outfile, 'a') as fo:
        fo.write(line)

#----------------------------------------------------------------------------
#-- extract_goes_data: extract GOES satellite flux data                    --
#----------------------------------------------------------------------------

def extract_goes_data(dlink, energy_list):
    """
    extract GOES satellite flux data
    input: dlink        --- json web address
            energy_list --- a list of energy designation 
    output: <data_dir>/<out file>
    """
#
#--- read json file from the web
#
    try:
        with urllib.request.urlopen(dlink) as url:
            data = json.loads(url.read().decode())
    except:
        data = []
#
#--- go through all energy ranges
#
    elen   = len(energy_list)
    d_save = []
    for k in range(0, elen):
        t_list = []
        f_list = []
        energy = energy_list[k]
#
#--- check the last entry time and select only last 2hrs
#
        ltime  = check_last_entry_time(data)
        ctime  = ltime - 3600.0 * 2
        for ent in data:
#
#--- get the data from a specified satellite
#
#            if ent['satellite'] != satellite:
#                continue
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
                flux  = float(ent['flux']) * 1e3   #--- keV to MeV
#
#--- convert time into seconds from 1998.1.1
#
                otime = ent['time_tag']
                #dtime = time.strftime('%Y:%j:%H:%M',    time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))

                t_list.append(otime)
                f_list.append(flux)

        d_save.append([t_list, f_list])

    return d_save

#----------------------------------------------------------------------------
#-- check_last_entry_time: check the last data entry time of the given data file 
#----------------------------------------------------------------------------

def check_last_entry_time(data):
    """
    check the last data entry time of the given data file
    input:  data    --- data
    output: ltime   --- the last entry time in seconds from 1998.1.1
    """

    ent = data[-1]
    otime = ent['time_tag']
    otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
    stime = int(Chandra.Time.DateTime(otime).secs)

    return stime

#----------------------------------------------------------------------------
#-- compute_p_vals: create combined flux data for table displays           --
#----------------------------------------------------------------------------

def compute_p_vals(data):
    """
    create combined flux data for table displays
    input:  data    --- a list of lists of data: [[<time>, <data1>], [<time>, <data2>],...]
    output: a list of lists of:
            p1 :  1.0MeV - 3.3MeV
            p2 :  3.4MeV - 11MeV
            p3 :  11MeV  - 38MeV
            p4 :  40MeV  - 98MeV
            p5 :  99MeV  - 143MeV
            p6 :  160MeV - 404MeV
    """
#
#--- extract flux data parts
#
    c0  = data[0][1]
    c1  = data[1][1]
    c2  = data[2][1]
    c3  = data[3][1]
    c4  = data[4][1]
    c5  = data[5][1]
    c6  = data[6][1]
    c7  = data[7][1]
    c8  = data[8][1]
    c9  = data[9][1]
    c10 = data[10][1]
    c11 = data[11][1]
    c12 = data[12][1]
#
#--- combine the data
#
    p1 = []             #--- c0 + c1 + c2:  1.0MeV - 3.3MeV
    p2 = []             #--- c3 + c4:       3.4MeV - 11MeV
    p3 = []             #--- c5 + c6:       11MeV  - 38MeV
    p4 = []             #--- c7 + c8:       40MeV  - 98MeV
    p5 = []             #--- c9 + c10;      99MeV  - 143MeV
    p6 = []             #--- c11 + c12:     160MeV - 404MeV
    for  k in range(0, len(c0)):
        val = (c0[k] *(1.85 - 1.02)  + c1[k] * (2.3 - 1.9) + c2[k]  * (3.3 - 2.3)) / (3.3 -1.0)
        p1.append(val)

        val = (c3[k] * (6.48 - 3.4) + c4[k] * (11.0 - 5.84)) / (11 - 3.4)
        p2.append(val)

        val = (c5[k] * (23.27-11.64) + c6[k] *(38.1 - 25.9)) / (38.1 - 11.64)
        p3.append(val)

        val = (c7[k] * (73.4 - 40.3)+ c8[k] * (98.5 - 83.7)) / (98.5 - 40.3)
        p4.append(val)

        val = (c9[k] * (118.0 - 99.9) + c10[k] * (143.0 - 115.0)) /( 115 - 99.9)
        p5.append(val)

        val = (c11[k] * (242.0 - 160.0) + c12[k] * (404.0 - 276.0)) / (404. - 160.0)
        p6.append(val)

    return [p1, p2, p3, p4, p5, p6]

#----------------------------------------------------------------------------
#-- compute_hrc: compute hrc proxy value                                   --
#----------------------------------------------------------------------------

def compute_hrc(data):
    """
    compute hrc proxy value

    HRC_PROXY = 6000 x P4 + 270000 x P5 + 100000 x P6
        P4 ~ 11640-23270 keV + 25900-38100 keV 
        P5 ~ 40300-73400 keV, 
        P6 ~ 83700-98500 keV + 99900-118000 keV + 115000-143000 keV + 160000-242000 keV.
        and:
        c0: '1020-1860 keV',
        c1: '1900-2300 keV',
        c2: '2310-3340 keV',
        c3: '3400-6480 keV',
        c4: '5840-11000 keV',
        c5: '11640-23270 keV',
        c6: '25900-38100 keV',
        c7: '40300-73400 keV',
        c8: '83700-98500 keV',
        c9: '99900-118000 keV',
        c10: '115000-143000 keV',
        c11: '160000-242000 keV',
        c12: '276000-404000 keV'
    input:  data    --- a list of lists of data: [[<time>, <data1>], [<time>, <data2>],...]
    output: hrc     --- hrc proxy list
    """
    c5  = data[5][1]
    c6  = data[6][1]
    c7  = data[7][1]
    c8  = data[8][1]
    c9  = data[9][1]
    c10 = data[10][1]
    c11 = data[11][1]

    hrc = []
    for k in range(0, len(c5)):
        try:
#            val = 6000.0 *  (c5[k] * (23.27-11.64) + c6[k]* (38.1 - 25.9))/(38.1 - 11.64)\
#             + 270000.0 * (c7[k])\
#             + 100000.0 * (c8[k] *(98.5-83.7) + c9[k] * (118-99.9)\
#             + c10[k]*(143.-115) + c11[k]*(242.-160.)) /(242.-83.7)
#
#--- after 2021:112:06:05:00
#
#            val = 143.0 * c5[k] + 64738.0 * c6[k] + 162505.0 * c7[k] + 16.1    #--- 16.1 = 4127.0 /256.0
#
#--- after 2021:125:06:05:00
#
            val = 143.0 * c5[k] + 64738.0 * c6[k] + 162505.0 * c7[k] + 4127    
        except:
            val = 0.0

        hrc.append(val)

    return hrc

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def adjust_format(val):

    val = float(val)
#    if val < 10:
#        out = "%1.5f" % (val)
#    elif val < 100:
#        out = "%2.4f" % (val)
#    elif val < 1000:
#        out = "%3.3f" % (val)
#    elif val < 10000:
#        out = "%4.2f" % (val)
#    elif val < 100000:
#        out = "%5.1f" % (val)
#    else:
#        out = "%5.0f" % (val)
    
    out = "%1.3e"  % (val)
    return out

                                                                                           
#----------------------------------------------------------------------------

if __name__ == "__main__":

    collect_goes_long()

