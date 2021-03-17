#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#           add_region_info.py: add region information to the crm data                          #
#                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                               #
#           last update: Mar 16, 2021                                                           #
#                                                                                               #
#################################################################################################

import sys
import os
import string
import re
import time
import math
import Chandra.Time
from datetime import datetime
from geopack  import geopack
import numpy
#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta/Script/Python3.8/MTA/')
sys.path.append('/data/mta4/Space_Weather/EPHEM/Scripts/')
#
#--- import several functions
#
import mta_common_functions as mcf
import convert_coord        as ecc
#
#--- temp writing file name
#
import random
rtail  = int(time.time() * random.random()) 
zspace = '/tmp/zspace' + str(rtail)
#
#--- Earth radius
#
earth    =  6378.0

#--------------------------------------------------------------------------
#-- add_region_info: add region information to crm database               -
#--------------------------------------------------------------------------

def add_region_info():
    """
    add region information to crm database
    input:  none, but read from:
            <kp_dir>Data/k_index_data
            <tle_dir>Data/xmm.gsme_in_Re
            <tle_dir>Data/cxo.gsme_in_Re
    output: <xmm_dir>/Data/crmreg_xmm.dat
            <xmm_dir>/Data/crmreg_cxo.dat
    """
#
#--- read kp data
#
    ifile = kp_dir + 'Data/k_index_data'
    data  = mcf.read_data_file(ifile)
    ktime = []
    kps   = []
    for ent in data:
        atemp = re.split('\s+', ent)
        ktime.append(float(atemp[0]))
        kps.append(float(atemp[1]))
#
#--- xmm data update
#
#--- read GSM data
#
    [xtime, utime, xgsm, ygsm, zgsm, xgse, ygse, zgse, alt] = read_gsm('xmm')
#
#--- find kp value for the each data
#
    nkps = match_kp(ktime, xtime, kps)
#
#--- write the result
#
    write_region_data(xtime, utime,  nkps, xgsm, ygsm, zgsm, alt, 'xmm')
#
#--- cxo data update
#
    [xtime, utime, xgsm, ygsm, zgsm, xgse, ygse, zgse, alt] = read_gsm('cxo')
    nkps = match_kp(ktime, xtime, kps)
    write_region_data(xtime, utime,  nkps, xgsm, ygsm, zgsm, alt, 'cxo')

#--------------------------------------------------------------------------
#-- read_gsm: read GSM data                                              --
#--------------------------------------------------------------------------

def read_gsm(satellite):
    """
    read GSM data
    input:  satellite   --- either xmm or cxo
            <tle_dir>/Data/<satellite>.gsme_in_Re
    output: a list of list of data:
                atime   --- time in seconds from 1998.1.1
                utime   --- time in seconds from 1970.1.1
                xgsm/ygsm/zgsm  --- GSM coords
                ygse/ygse/zgse  --- GSE coords
                alt             --- orbital altitude
    """
    if satellite == 'xmm':
        ifile = tle_dir + 'Data/xmm.gsme_in_Re'
    else:
        ifile = tle_dir + 'Data/cxo.gsme_in_Re'

#
#--- read the radiation data
#
    data  = mcf.read_data_file(ifile)

    atime = []
    utime = []
    xgsm  = []
    ygsm  = []
    zgsm  = []
    xgse  = []
    ygse  = []
    zgse  = []
    alt   = []
    for ent in data:
        atemp = re.split('\s+', ent)
#
#--- make it badk to kkm
#
        xgsm.append(float(atemp[1]) *1.e3)
        ygsm.append(float(atemp[2]) *1.e3)
        zgsm.append(float(atemp[3]) *1.e3)

        xgse.append(float(atemp[4]) *1.e3)
        ygse.append(float(atemp[5]) *1.e3)
        zgse.append(float(atemp[6]) *1.e3)

        year = int(float(atemp[7]))
        mon  = int(float(atemp[8]))
        day  = int(float(atemp[9]))
        hh   = int(float(atemp[10]))
        mm   = int(float(atemp[11]))
        ss   = int(float(atemp[12]))
#
#--- compute Chandra Time
#
        ctime = convert_to_chandra(year, mon, day, hh, mm, ss)
        atime.append(ctime)
#
#---- compute UTS
#
        uts = ut_in_secs(year, mon, day, hh, mm, ss)
        utime.append(uts)
        psi = geopack.recalc(uts)
#
#--- compute altitude
#
        xgeo, ygeo, zgeo = geopack.geogsm(float(atemp[1]), float(atemp[2]), float(atemp[3]), -1)
        x, y , z = geopack.geigeo(xgeo, ygeo, zgeo, -1)
        r = math.sqrt(x*x + y*y + z*z) * 1.e3
        alt.append(r)

    return [atime, utime, xgsm, ygsm, zgsm, xgse, ygse, zgse, alt]


#--------------------------------------------------------------------------
#-- write_region_data: write out the data                                --
#--------------------------------------------------------------------------

def write_region_data(xtime, utime,  nkps, xgsm, ygsm, zgsm, alt,  sat):
    """
    write out the data
    input:  atime   --- time in seconds from 1998.1.1
            utime   --- time in seconds from 1970.1.1
            xgsm/ygsm/zgsm  --- GSM coords
            ygse/ygse/zgse  --- GSE coords
            alt             --- orbital altitude
            sat             --- either xmm or cxo
    output: <xmm_dir>/Data/crmreg_<sat>.dat
    """
    line = ''
    for k in range(0, len(xtime)):
        psi = geopack.recalc(utime[k])
        xtail, ytail, ztail, lid = ecc.locreg(nkps[k], xgsm[k], ygsm[k], zgsm[k])
        line = line + '%9d'   % xtime[k] + '\t' 
        line = line + '%3.3f' % alt[k]   + '\t'
        line = line + '%3.3f' % xgsm[k]  + '\t'
        line = line + '%3.3f' % ygsm[k]  + '\t'
        line = line + '%3.3f' % zgsm[k]  + '\t'
        line = line + '%4d'   % lid      + '\n'

    ofile = xmm_dir + 'Data/crmreg_' + sat + '.dat'
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#-- match_kp: find kp value for the given time (list)                    --
#--------------------------------------------------------------------------

def match_kp(ktime, xtime, kps):
    """
    find kp value for the given time (list)
    input:  ktime   --- a list of time of corresponding kp value list
            xtime   --- a list of time 
            kps     --- a list of kp values
    output: nkps    --- a list of kp values matched to xtime list
    """
    klen  = len(ktime)
    nkps  = []
    start = 0
    for etime in xtime:
        for m in range(start, klen):
            if m + 1 >= klen:
                nkps.append(kps[-1])
                break

            if ktime[m] < etime:
                continue
            elif etime >= ktime[m] and etime < ktime[m+1]:
                nkps.append(kps[m])
                start = m - 5
                if start < 0:
                    start = 0
                break

    return nkps

#---------------------------------------------------------------------------------------
#-- ut_in_secs: onvert calendar date into univarsal time in sec                       --
#---------------------------------------------------------------------------------------

def ut_in_secs(year, mon, day, hh, mm, ss):
    """
    convert calendar date into univarsal time in sec (seconds from 1970.1.1)
    input:  year--- year
    mon --- month
    day --- day
    hh  --- hour
    mm  --- minutes
    ss  --- seconds
    output:uts  --- UT in seconds from 1970.1.1
    """
    year = int(float(year))
    mon  = int(float(mon))
    day  = int(float(day))
    hh   = int(float(hh))
    mm   = int(float(mm))
    ss   = int(float(ss))
    
    uts  = (datetime(year, mon, day, hh, mm, ss)\
                        - datetime(1970,1,1)).total_seconds()
    uts += 86400.0

    return uts

#--------------------------------------------------------------------------
#-- convert_to_chandra: convert calendar date into univarsal time in sec         --
#--------------------------------------------------------------------------

def convert_to_chandra(year, mon, day, hh, mm, ss):
    """
    convert calendar date into chandra time
    input:  year--- year
            mon --- month
            day --- day
            hh  --- hour
            mm  --- minutes
            ss  --- seconds
    output: ctime --- seconds from 1998.1.1
    """
    line = str(year) + ':' + str(mon) + ':' + str(day) + ':' 
    line = line + str(hh) + ':' + str(mm) + ':' + str(ss)
    line = time.strftime('%Y:%j:%H:%M:%S', time.strptime(line, '%Y:%m:%d:%H:%M:%S'))
    ctime = Chandra.Time.DateTime(line).secs

    return ctime

#------------------------------------------------------------------------------

if __name__ == '__main__':

    add_region_info()

