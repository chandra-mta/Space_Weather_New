#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#       update_goes_differential_page.py: update goes differential html page    #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: Jan 31, 2020                                           #
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
import numpy
import matplotlib as mpl
if __name__ == '__main__':
    mpl.use('Agg')

from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines


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
import random
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- json data locations proton and electron
#
plink = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
#
#--- protone energy designations and output file names
#
proton_list = ['1020-1860 keV',   '1900-2300 keV',   '2310-3340 keV',    '3400-6480 keV',\
               '5840-11000 keV',  '11640-23270 keV', '25900-38100 keV',  '40300-73400 keV',\
               '83700-98500 keV', '99900-118000 keV','115000-143000 keV','160000-242000 keV',\
               '276000-404000 keV']

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def run():
    out15 = get_hrc_p_15()
    out16 = get_hrc_p_16()

    plt.close('all')
    mpl.rcParams['font.size'] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)

    xmin = min(out15[0])
    xmax = max(out15[0])
    ymin = min(min(out15[1]), min(out16[1]))
    ymax = max(max(out15[1]), max(out16[1]))
    ydiff = ymax - ymin
    ymin -= 0.2 * ydiff
    ymax += 0.2 * ydiff

    ax = plt.subplot(111)
    ax.set_autoscale_on(False)
    ax.set_xbound(xmin, xmax)
    ax.set_xlim(xmin=xmin, xmax=xmax,  auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax.set_xlabel('Time')
    ax.set_ylabel('HRC Proxy')

    goes15, = plt.plot(out15[0], out15[1], color='red',  marker='.', markersize=0, lw=0.8, label='GOES15')
    goes16, = plt.plot(out16[0], out16[1], color='blue', marker='.', markersize=0, lw=0.8, label='GOES16')

    plt.legend(handles=[goes15, goes16])

    plt.savefig('test_out.png', format='png')
    plt.close('all')

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def get_hrc_p_15():

    data   = mcf.read_data_file('./goes15_diff')
    ktime  = []
    pdata  = [[],[],[],[],[],[],[],[],[],[],[]]

    for ent in data:
        if ent[0] == '#':
            continue
        atemp = re.split('\s+', ent)
        ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' +  atemp[3]
        ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H%M'))
        stime = Chandra.Time.DateTime(ltime).secs
        ktime.append(stime)
        for k in range(0, 11):
            m = k + 6
            pdata[k].append(float(atemp[m]))


    hrcp = []
    for k in range(0, len(ktime)):
        val = 6000 * pdata[3][k] + 270000 * pdata[4][k] + 100000 * pdata[5][k]
        val /=10
        hrcp.append(val)

    return [ktime, hrcp]

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def get_hrc_p_16():

    data = mcf.read_data_file('./goes16_diff')

    ktime = []
    hrcp = []
    for ent in data:
        if ent[0] == '#':
            continue
        atemp = re.split('\s+', ent)
        ltime = atemp[0] + ':00'
        stime = Chandra.Time.DateTime(ltime).secs
        ktime.append(stime)
        hrcp.append(float(atemp[-1]))

    return [ktime, hrcp]

#----------------------------------------------------------------------------

if __name__ == "__main__":
    run()
