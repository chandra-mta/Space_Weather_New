#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#           update_k_index.py: update k index data file                             #
#                                                                                   #
#               author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                                   #
#               last updae: Mar 24, 2020                                            #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import numpy
import unittest
import time
import random
from datetime import datetime
from time import gmtime, strftime, localtime
import Chandra.Time
import Ska.engarchive.fetch as fetch
#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

t_step = [0, 3, 6, 9, 12, 15, 18, 21]

haddress  = 'http://www-app3.gfz-potsdam.de/kp_index/qlyymm.tab'
f_k_index = 'https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt'
l_k_index = 'https://services.swpc.noaa.gov/text/27-day-outlook.txt'

mon_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
data_dir = kp_dir + 'Data/'

#-----------------------------------------------------------------------------------
#-- update_k_index: updata k index data file                                      --
#-----------------------------------------------------------------------------------

def update_k_index(hname=''):
    """
    updata k index data file
    input:  hname   --- htp address. if not given, <haddress> is used
            f_k_index   --- http address for the predicted kp indicies
    output: <data_dir>/k_index_data         --- observed + predictive kp list
            <data_dir>/k_index_data_past    --- observed kp list
    """
    if hname == '':
        hname = haddress
#
#--- there are two lists; one is with  predicted kp and another without
#
    d_file   = data_dir + 'k_index_data'
    d_file_p = data_dir + 'k_index_data_past'
#
#--- read the measured kp
#
    [t_list, k_list] = get_file(hname)
#
#--- find the last entry time of the observed kp list
#
    try:
        data   = read_data_file(d_file_p)
        atemp  = re.split('\s+', data[-1])
        l_time = int(atemp[0])
    except:
        l_time = 0.0
#
#--- add the new part on the observed kp list
#
    with open(d_file_p, 'a') as fo:
        for k in range(0, len(t_list)):
            if t_list[k] > l_time:
                line = str(t_list[k]) + '\t' + str(k_list[k]) + '\n'
                fo.write(line)
#
#--- replace a "predictive" list with the observed list
#
    cmd = 'cp -f ' + d_file_p + ' ' + d_file
    os.system(cmd)
#
#--- add predicted part
#
    [t_list2, k_list2] = futre_k_index(f_k_index)
    with open(d_file, 'a') as fo:
        for k in range(0, len(t_list2)):
            if t_list2[k] > t_list[-1]:
                line = str(t_list2[k]) + '\t' + str(k_list2[k]) + '\n'
                fo.write(line)
#
#--- add long term guss
#
    [t_list3, k_list3] = get_long_term_kp()
    with open(d_file, 'a') as fo:
        for k in range(0, len(t_list3)):
            if t_list3[k] > t_list2[-1]:
                line = str(t_list3[k]) + '\t' + str(k_list3[k]) + '\n'
                fo.write(line)

#-----------------------------------------------------------------------------------
#-- get_file: read the data from source and lists of time and k index             --
#-----------------------------------------------------------------------------------

def get_file(hname):
    """
    read the data from source and lists of time and k index
    input:  hname   --- htp address
    output: t_list  --- a list of time in seconds from 1998.1.1
            k_list  --- a list of k index 
    """
#
#--- read the web data; we assume the data is something like:
#--- 80803  1- 1o 1o 2+  2o 1+ 0+ 1-    9+      5 0.2
#
    cmd = 'wget -q -O ' + zspace + ' ' + hname
    os.system(cmd)

    data = read_data_file(zspace, remove=1)

    t_list = []
    k_list = []
    for ent in data:
        atemp = re.split('\s+', ent)
        if len(atemp[0]) != 6:
            continue
#
#--- convert the time into seconds from 1998.1.1
#
        tdate  = datetime.strptime(atemp[0], '%y%m%d').strftime("%Y:%j:00:00:00")
        chdate = Chandra.Time.DateTime(tdate).secs
#
#--- there are 8 k index values on each line (every 3 hrs)
#--- but the last line (today) may not be fill all the way
#
        for k in range(0, len(t_step)):
            m = k + 1
            try:
                val = int(atemp[m][0])
                ped = atemp[m][1]
                if ped == '-':
                    add = -0.3
                elif ped == '+':
                    add = 0.3
                else:
                    add = 0.0
                val += add
            
            except:
                continue

            dtime = int(chdate + t_step[k] * 3600.0)
            t_list.append(dtime)
            k_list.append(val)

    return [t_list, k_list]

#-----------------------------------------------------------------------------------
#-- read_data_file: read data file                                                --
#-----------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):
    """
    read data file
    input:  ifile   --- input file name
            remove  --- if > 0, remove the file after reading
    output: data    --- a list of the data
    """
    with  open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    if remove > 0:
        cmd = 'rm ' + ifile
        os.system(cmd)

    return data


#-----------------------------------------------------------------------------------
#-- futre_k_index: read the predicted k indices from a web site                  ---
#-----------------------------------------------------------------------------------

def futre_k_index(hname):
    """
    read the predicted k indices from a web site
    input:  hname   --- htp address
                https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt
    output: t_list  --- a list of time in seconds from 1998.1.1
            k_list  --- a list of k index 
    """
#       :Product: Geomagnetic Forecast
#       :Issued: 2020 Feb 04 2205 UTC
#       # Prepared by the U.S. Dept. of Commerce, NOAA, Space Weather Prediction Center
#       #
#       NOAA Ap Index Forecast
#       Observed Ap 03 Feb 005
#       Estimated Ap 04 Feb 005
#       Predicted Ap 05 Feb-07 Feb 005-012-008
#       
#       NOAA Geomagnetic Activity Probabilities 05 Feb-07 Feb
#       Active                10/40/25
#       Minor storm           01/15/10
#       Moderate storm        01/01/01
#       Strong-Extreme storm  01/01/01
#       
#       NOAA Kp index forecast 05 Feb - 07 Feb
#                    Feb 05    Feb 06    Feb 07
#        00-03UT        2         3         2
#        03-06UT        2         4         3
#        06-09UT        1         3         3
#        09-12UT        1         2         2
#        12-15UT        1         2         2
#        15-18UT        1         2         2
#        18-21UT        1         3         2
#        21-00UT        2         3         2

#
#--- download the file and read it
#
    cmd = 'wget -q -O ' + zspace + ' ' + hname
    os.system(cmd)

    data = read_data_file(zspace, remove=1)

    t_list = []
    k_list = []
    chk = 0
    d_list  = []
    kp_list = [[],[],[],[]]
    for ent in data:
        ent.strip()
        if chk == 0:
#
#--- find year of the data
#
            mc = re.search(':Issued:', ent)
            if mc is not None:
                atemp = re.split('\s+', ent)
                year  = int(float(atemp[1]))
                continue
#
#--- checking where the data part starts
#
            mc = re.search('NOAA Kp index forecast', ent)
            if mc is None:
                continue
            else:
                chk = 1
                continue
#
#--- data part starts
#
        else:
            mchk = 0
            try:
                val = float(ent[0])
            except:
                mchk = 1
#
#--- date part three entry dates
#
            if mchk > 0:
                atemp = re.split('\s+', ent)
                fmon  = find_month(atemp[0])
                fday  = atemp[1]
                date  = fmon + ':' + fday
                d_list.append(date)

                fmon  = find_month(atemp[2])
                fday  = atemp[3]
                date  = fmon + ':' + fday
                d_list.append(date)
                
                fmon  = find_month(atemp[4])
                fday  = atemp[5]
                date  = fmon + ':' + fday
                d_list.append(date)

#
#--- kp data and hour 
#
            else:
                atemp = re.split('\s+', ent)
                btemp = re.split('-',   atemp[0])
                ut    = btemp[1].replace('UT', '')
                kp_list[0].append(ut)
                kp_list[1].append(atemp[1])
                kp_list[2].append(atemp[2])
                kp_list[3].append(atemp[3])
#
#--- rearrange so that the data are arranged linearly
#
    t_list = []
    k_list = []
    for k in range(0, 3):
        m = k + 1
        for n in range(len(kp_list[0])):

            stime = convert_time_format(d_list[k], kp_list[0][n])
            t_list.append(stime)
            k_list.append(kp_list[m][n])

    return [t_list, k_list]

#-----------------------------------------------------------------------------------
#-- get_long_term_kp: download a longer term predicted kp data                    --
#-----------------------------------------------------------------------------------

def get_long_term_kp():
    """
    download a longer term predicted kp data
    input:  https://services.swpc.noaa.gov/text/27-day-outlook.txt
    output: t_list  --- a list of time in seconds from 1998.1.1
            kp_list --- a list of kp values
    """
#--- download the file and read it
#
    cmd = 'wget -q -O ' + zspace + ' ' + l_k_index
    os.system(cmd)

    data = read_data_file(zspace, remove=1)

    t_list  = []
    kp_list = []
    for ent in data:
        if ent == '':
            continue
        if ent[0] == ':' or ent[0] == '#':
            continue

        atemp = re.split('\s+', ent)
        year  = int(float(atemp[0]))
        mon   = find_month(atemp[1])
        day   = atemp[2]
        kp    = atemp[5]
        for hh in t_step:
            shh = str(hh)
            if hh < 10:
                shh = '0' + shh
            ltime = str(year) + ':' + mon + ':' + day + ':' + shh
            ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H'))
            stime = int(Chandra.Time.DateTime(ltime).secs)

            t_list.append(stime)
            kp_list.append(kp)

    return [t_list, kp_list]


#-----------------------------------------------------------------------------------
#-- find_month: convert letter month to digit month                               --
#-----------------------------------------------------------------------------------

def find_month(mon):
    """
    convert letter month to digit month
    input:  mon     --- letter month 
    output: cmon    --- digit month
    """
    imon = 0
    for k in range(0, 12):
        if mon == mon_list[k]:
            imon = k + 1
            break

    cmon = str(imon)
    if imon < 10:
        cmon = '0' + cmon

    return cmon

#-----------------------------------------------------------------------------------
#-- convert_time_format: convert time from mon:day and hh to Chandra time         --
#-----------------------------------------------------------------------------------

def convert_time_format(mon_day, hh):
    """
    convert time from mon:day and hh to Chandra time
    input:  mon_day --- <mm>:<dd>
            hh      --- hour in <hh>
    output: stime   --- seconds from 1998.1.1
    """
    date = time.strftime('%Y:%j', time.gmtime())
    atemp = re.split(':', date)
    tyear = int(float(atemp[0]))
    tyday = int(float(atemp[1]))
#
#--- the first few days of year may contain the data from the last year
#
    if tyday < 4:
        atemp = re.split(':', mon_day)
        if float(atemp[0]) == 12:
            tyear -= 1
#
#--- convert time format to seconds from 1998.1.1
#
    date  = str(tyear) + ':' + mon_day + ':' + hh + ':00:00'
    date  = time.strftime('%Y:%j:%H:%M:%S', time.strptime(date, '%Y:%m:%d:%H:%M:%S'))
    stime = int(Chandra.Time.DateTime(date).secs)

    return stime

#-----------------------------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv)  == 2:
        hname = sys.argv[1]

    else:
        hname = ''

    update_k_index(hname)
