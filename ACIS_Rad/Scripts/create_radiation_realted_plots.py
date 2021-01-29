#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#####################################################################################################
#                                                                                                   #
#       create_radiation_realted_plots.py: control sceript to create radiation realted plots        #
#                                                                                                   #
#           author: t. isobe    (tiosbe@cfa.harvard.edu)                                            #
#                                                                                                   #
#           last update: Aug 03, 2020                                                               #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import subprocess
import Chandra.Time
import time
#
#--- pylab plotting routine related modules
#
import matplotlib as mpl
if __name__ == '__main__':
    mpl.use('Agg')
#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))

bin_dir = acis_dir + 'Scripts/'
sys.path.append(bin_dir)

import create_config_plot       as ccp
import create_rad_cnt_plots     as crcp

mon_list1 = [31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]
mon_list2 = [31, 60, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

lmon_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun','jul', 'aug', 'sep', 'oct', 'nov', 'dec']
#
#--- set a directory
#
plot_dir = html_dir + '/ACIS_Rad/Plots/'

#----------------------------------------------------------------------------------------------------------
#-- create_radiation_realted_plots: control sceript to create radiation realted plots                   ---
#----------------------------------------------------------------------------------------------------------

def create_radiation_realted_plots():
    """
    control sceript to create radiation realted plots
    input:  none 
    output: radiation related png files
    """
#
#--- find today's date
#
    today = time.strftime("%Y:%j:00:00:00", time.gmtime())
    stop  = Chandra.Time.DateTime(today).secs
    start = stop - 30 * 86400
    start = Chandra.Time.DateTime(start).date
#
#---last 30 days
#
    out1 = plot_dir    + "rad_cnts_curr.png"
    out2 = plot_dir    + "rad_use_curr.png"
#
#---- we are not creating the following three plots anymore (Jan 2019)
#
    out3 = plot_dir    + "mon_diff_curr.png"
    out4 = plot_dir    + "per_diff_curr.png"
    out5 = plot_dir    + "mon_per_diff_curr.png"

    create_plots(start, today, out1, out2, out3, out4, out5)
#
#---- if it is the first 3 days of the month create last month's plots
#
    today   = time.strftime("%Y:%m:%d:00:00:00", time.gmtime())
    atemp   = re.split(':', today)
    year    = int(atemp[0])
    mon     = int(atemp[1])
    day     = int(atemp[2])
    if day < 3:
        lmon    = mon -1
        if lmon < 1:
            lmon = 12
            lyear = year - 1
        else:
            lyear  = year

        monyear = lmon_list[lmon-1] + str(lyear)[2] + str(lyear)[3]
     
        smon = str(mon)
        if mon < 10:
            smon = '0' + smon
        stop = str(year) + ':' + smon + ':01:00:00:00'
        stop = time.strftime("%Y:%j:%H:%M:%S",time.strptime(stop, "%Y:%m:%d:%H:%M:%S"))
        slmon = str(lmon)
        if lmon < 10:
            slmon = '0' + slmon
        start = str(lyear) + ':' + slmon + ':01:00:00:00'
        start = time.strftime("%Y:%j:%H:%M:%S",time.strptime(start, "%Y:%m:%d:%H:%M:%S"))
    
        cout1 = plot_dir + "rad_cnts_"     + monyear + ".png"
        cout2 = plot_dir + "rad_use_"      + monyear + ".png"
        cout3 = plot_dir + "mon_diff_"     + monyear + ".png"
        cout4 = plot_dir + "per_diff_"     + monyear + ".png"
        cout5 = plot_dir + "mon_per_diff_" + monyear + ".png"


        create_plots(start, stop, cout1, cout2, cout3, cout4, cout5)

    exit(1)         #---- we are not plotting  longer period anymore
#-------------------------------------------------------------------------------
#--- last year
#
    if (yday > 2) and (yday < 5):
        out1 = plot_dir + "rad_cnts_"     + syear2  + ".png"
        out2 = plot_dir + "rad_use_"      + syear2  + ".png"
        out1  = ''
        out2  = ''
        out3 = plot_dir + "mon_diff_"     + syear2  + ".png"
        out4 = plot_dir + "per_diff_"     + syear2  + ".png"
        out5 = plot_dir + "mon_per_diff_" + syear2  + ".png"

        start = last_year + ':001' + ':00:00:00'
        stop  = lmon_year + ':001' + ':00:00:00'
        stop  = str(year) + ':001' + ':00:00:00'
        create_plots(start, stop, out1, out2, out3, out4, out5)

#
#--- last one year
#
    if yday % 3 == 0:
        out1 = plot_dir + "rad_cnts_last_one_year.png"
        out2 = plot_dir + "rad_use_last_one_year.png"
        out1 = ''
        out2 = ''
        out3 = plot_dir + "mon_diff_last_one_year.png"
        out4 = plot_dir + "per_diff_last_one_year.png"
        out5 = plot_dir + "mon_per_diff_last_one_year.png"

        start = last_year + ":" + today + ':00:00:00'
        #stop  = lmon_year + ":" + today + ':00:00:00'
        stop  = str(year) + ":" + today + ':00:00:00'
        create_plots(start, stop, out1, out2, out3, out4, out5)
#
#--- entire period
#
    if day == 10:
        out1 = plot_dir + "rad_cnts_all.png"
        out2 = plot_dir + "rad_use_all.png"
        out1 = ''
        out2 = ''
        out3 = plot_dir + "mon_diff_all.png"
        out4 = plot_dir + "per_diff_all.png"
        out5 = plot_dir + "mon_per_diff_all.png"

        start = '1999:200'
        stop  = str(year) + ':' + str(yday)
        create_plots(start, stop, out1, out2, out3, out4, out5)

#----------------------------------------------------------------------------------------------------------
#-- isLeapYear: check whehter the year is a leap year                                                    --
#----------------------------------------------------------------------------------------------------------

def isLeapYear(year):
    """
    check whehter the year is a leap year
    Input:  year   in full lenth (e.g. 2014, 813)
    Output: 0--- not leap year
            1--- yes it is leap year
    """
    year = int(float(year))
    chk  = year % 4     #---- evry 4 yrs leap year
    chk2 = year % 100   #---- except every 100 years (e.g. 2100, 2200)
    chk3 = year % 400   #---- excpet every 400 years (e.g. 2000, 2400)
    
    val  = 0
    if chk == 0:
        val = 1
    if chk2 == 0:
        val = 0
    if chk3 == 0:
        val = 1
    
    return val

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

def create_plots(start, stop, out1, out2, out3, out4, out5):
    """
    call several python functions to create plots
    input:  start   --- start time in <yyyy>:<ddd>:<hh>:<mm>:<ss>
            stop    --- stop time in <yyyy>:<ddd>:<hh>:<mm>:<ss>
            out1    --- png file name for radiation plot
            out2    --- png file name for configuration plot
            out3    --- png file name for mon diff plot
            out4    --- png file name for per diff plot
            out5    --- png file name for mon per diff plot
    output: png plots files
    """
#
#--- radiation plot
#
    if out1 != '':
        crcp.plot_radiation_counts(start, stop, out1)

#--- configuration plot
#
    if out2 != '':
        ccp.create_config_plot(start, stop, out2)

#    create_mon_diff(start, stop, out3)
#    create_per_diff(start, stop, out4)
#    create_mon_per_diff(start, stop, out5)

#----------------------------------------------------------------------------------------------------------
#
#--- pylab plotting routine related modules
#
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines as lines

if __name__ == "__main__":

    create_radiation_realted_plots()

