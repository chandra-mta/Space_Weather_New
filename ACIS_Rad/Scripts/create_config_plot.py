#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

#####################################################################################################
#                                                                                                   #
#       create_config_plot.py: create configuration plot for monthly report                         #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               last update: Mar 16, 2021                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import string
import random
import operator
import math
import numpy
#import astropy.io.fits  as pyfits
import time
import Chandra.Time
import unittest

import matplotlib as mpl
if __name__ == '__main__':
        mpl.use('Agg')

from pylab import *
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines as lines

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
#
#--- append  pathes to private folders to a python directory
#
bin_dir = acis_dir + 'Scripts/'
bin_dir = acis_dir + 'Scripts/Test/'
sys.path.append(bin_dir)
#
#--- import several functions
#
import extract_radiation_data    as erd        #---- radiation related data reading
#
#--- temp writing file name
#
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#---- the testing period
#
test_start = 531187196       #--- 2014:305:00:00:00 (Nov  1, 2014)
test_stop  = 532483196       #--- 2014:320:00:00:00 (Nov 15, 2014)

color1 =['red','blue', 'lime', 'green', 'yellow']
color2 =['yellow','blue', 'red', 'green', 'lime']
color3 =['red','blue', 'lime', 'yellow', 'green']
color4 =['maroon','lime', 'red', 'blue', 'fuchsia']

m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

#----------------------------------------------------------------------------------------------------------
#-- create_config_plot: create a configulation display panel for a give time period                      --
#----------------------------------------------------------------------------------------------------------

def create_config_plot(start, stop, outname,  mag_plot=1):
    """
    create a configulation display panel for a give time period
    input:  start   --- starting time in sec from 1998.1.1
            stop    --- stopping time in sec from 1998.1.1
            outname --- png output file name
    output: outname --- png file
    """
#
#--- check time format
#
    try:
        start = int(float(start))
        stop  = int(float(stop))
    except:
        start = int(Chandra.Time.DateTime(start).secs) + 2.0
        stop  = int(Chandra.Time.DateTime(stop).secs)

#    x1 = Chandra.Time.DateTime(start).date
#    x2 = Chandra.Time.DateTime(stop).date
#
#---- set a few parameters
#
    if mag_plot == 0:
        pnum = 5
    else:
        pnum = 6

    plt.close("all")
    mpl.rcParams['font.size'] = 11 
    #mpl.rcParams['font.weight'] = 'strong' 
    props = font_manager.FontProperties(size=6)
    plt.subplots_adjust(hspace=0.05)
    plt.subplots_adjust(wspace=0.12)
#
#--- set a few others
#
    syr   = checkyear(start)
    xpos  = stime_to_ydate(stop, syr=syr) + 0.1 
    ystep = 0.2
#
#--- read sim information
#
    [acis_i_start, acis_i_stop, acis_s_start, \
     acis_s_stop,  hrc_i_start, hrc_i_stop,   \
     hrc_s_start,  hrc_s_stop,  hetg_start,   \
     hetg_stop,    letg_start,  letg_stop,    \
     radmon_start, radmon_stop, fmt, time]  = erd.find_sim_position(start, stop)
#
#--- hetg /letg information plot
#
    start_set = [hetg_start, letg_start]
    stop_set  = [hetg_stop,  letg_stop]

    ax1 = plt.subplot(pnum, 1, 1)
    plot_strip_box(ax1,start, stop, start_set, stop_set, color1)

    plt.text(xpos, 0.8, "HETG", color=color1[0])
    plt.text(xpos, 0.6, "LETG", color=color1[1])
#
#--- acis /hrc information plot
#
    start_set = [acis_i_start, acis_s_start, hrc_i_start, hrc_s_start]
    stop_set  = [acis_i_stop,  acis_s_stop,  hrc_i_stop,  hrc_s_stop]
    ax2 = plt.subplot(pnum, 1, 2)
    plot_strip_box(ax2,start, stop, start_set, stop_set, color1)

    plt.text(xpos, 0.9, "ACIS I ", color=color1[0])
    plt.text(xpos, 0.7, "ACIS S ", color=color1[1])
    plt.text(xpos, 0.5, "HRC I ",  color=color1[2])
    plt.text(xpos, 0.3, "HRC S ",  color=color1[3])
#
#--- cti information plot
#
    [cti_start, cti_stop]               = erd.read_ccd_data(start, stop)
    start_set = [cti_start]
    stop_set  = [cti_stop]
    ax3 = plt.subplot(pnum, 1, 3)
    plot_strip_box(ax3, start, stop, start_set, stop_set, color1)
#
#--- altitude information plot
#
    [atime, alt, magx, magy, magz, crm]  = erd.read_orbit_data(start, stop)
    plot_line(ax3, start, stop, atime, alt)

    plt.text(xpos, 0.8, "CTI  ",     color=color1[0])
    plt.text(xpos, 0.7, "Check  ",   color=color1[0])
    plt.text(xpos, 0.4, "Altitude ", color="green")
#
#--- radmon information plot
#
    start_set = [radmon_start]
    stop_set  = [radmon_stop]
    ax4 = plt.subplot(pnum, 1, 4)
    plot_strip_box(ax4, start, stop, start_set, stop_set, color1)
#
#--- hrc sheild rate plot
#
    [htime, rate] = erd.read_hrc_data(start, stop)
    if len(htime) > 0:
        plot_line(ax4, start, stop, htime, rate)
#
#--- goes p3 rate plot
#
#    [gtime, p1, p2, p3]                 = erd.read_goes_data(start, stop)
#    plot_points(ax4, start, stop, gtime, p3, color='lime', pts=0.5,lw=0)

    plt.text(xpos, 0.8, "Radmon", color=color1[0])
    plt.text(xpos, 0.6, "HRC", color="green")
    plt.text(xpos, 0.5, "Shield", color="green")
    plt.text(xpos, 0.4, "Rate", color="green")
#    plt.text(xpos, 0.2, "GOES P3", color="green")
#
#--- magnetsphere plot
#
    if mag_plot != 0:
        [start_set, stop_set] = find_mag_region(start, stop)
        axm = plt.subplot(6, 1, 5)
        plot_strip_box(axm, start, stop, start_set, stop_set, color1)

        plt.text(xpos, 0.9, "Solar",    color=color1[0])
        plt.text(xpos, 0.8, "Wind",     color=color1[0])
        plt.text(xpos, 0.6, "Magneto-", color=color1[1])
        plt.text(xpos, 0.5, "sheath",   color=color1[1])
        plt.text(xpos, 0.3, "Magneto-", color=color1[2])
        plt.text(xpos, 0.2, "sphere",   color=color1[2])
#
#--- often the data are not available; so make a note on the plot
#
        diff1 = stop - start
        tlast = time[len(time)-1]
        diff2 = tlast - start
        ratio = diff2 / diff1
        if ratio < 0.7:
            xnote = 0.5 * (stop - tlast)
            plt.text(xnote, 0.5, "No Data", color='maroon')
#
#--- FMT format information plot
#
    [start_set, stop_set] = find_fmt_region(start, stop, fmt, time)

    ax5 = plt.subplot(pnum, 1, pnum)
    plot_strip_box(ax5, start, stop, start_set, stop_set, color4)

    plt.text(xpos, 0.9, "FMT1", color=color4[0])
    plt.text(xpos, 0.7, "FMT2", color=color4[1])
    plt.text(xpos, 0.5, "FMT3", color=color4[2])
    plt.text(xpos, 0.3, "FMT4", color=color4[3])
    plt.text(xpos, 0.1, "FMT5", color=color4[4])
#
#--- plot x axis tick label only at the bottom ones
#
    if mag_plot == 0:
        ax_list = [ax1, ax2, ax3, ax4, ax5]
    else:
        ax_list = [ax1, ax2, ax3, ax4, ax5, axm]

    for ax in ax_list:
        for label in ax.get_yticklabels():
            label.set_visible(False)
        if ax != ax5:
            for label in ax.get_xticklabels():
                label.set_visible(False)
        else:
            pass
#
#--- x axis label
#
    tdiff = stop - start
    aout  = Chandra.Time.DateTime(int(0.5*(start+stop))).date
    atemp = re.split(':', aout)

    xlabel = "Time (DOY) " + str(atemp[0])
    ax5.set_xlabel(xlabel)

#
#--- set the size of the plotting area in inch (width: 10.0in, height 5.0in)
#   
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12.0, 10.0)
    #fig.tight_layout()                 #---- this makes too tight; commented out
#
#--- save the plot in png format
#   
    plt.savefig(outname, format='png', dpi=100)
    plt.close('all')


#----------------------------------------------------------------------------------------------------------
#-- find_mag_region: find magnetsphere, magnetosheath, and solar wind time periods                       --
#----------------------------------------------------------------------------------------------------------

def find_mag_region(start, stop):
    """
    find magnetsphere, magnetosheath, and solar wind time periods
    input:  start   --- starting time in sec from 1998.1.1
            stop    --- stopping time in sec from 1998.1.1
    ouput:  [start_set, stop_set]
                start_set = [wind_start, shth_start, sphr_start]
                stop_set  = [wind_stop,  shth_stop,  sphr_stop]
    """

    [time, alt, magx, magy, magz, crm]   = erd.read_orbit_data(start, stop)
    wind_start = []
    wind_stop  = []
    shth_start = []
    shth_stop  = []
    sphr_start = []
    sphr_stop  = []
#
#--- find the starting condition
#
    if crm[0] == 1:
        wind_start.append(time[0])
    elif crm[0] == 2:
        shth_start.append(time[0])
    elif crm[0] == 3:
        sphr_start.append(time[0])
#
#--- find changing time and mark the new period
#
    prev  = crm[0]
    for k in range(1, len(crm)):

        if crm[k] == prev:
            continue 

        if prev == 1:
            wind_stop.append(time[k-1])
        elif prev == 2:
            shth_stop.append(time[k-1])
        elif prev == 3:
            sphr_stop.append(time[k-1])

        if crm[k] == 1:
            wind_start.append(time[k])
        elif crm[k] == 2:
            shth_start.append(time[k])
        elif crm[k] == 3:
            sphr_start.append(time[k])

        prev  = crm[k]
#
#-- close the last set
#
    klast = len(crm) -1
    if crm[klast] == 1:
        wind_stop.append(time[klast])
    elif crm[klast] == 2:
        shth_stop.append(time[klast])
    elif crm[klast] == 3:
        sphr_stop.append(time[klast])


    start_set = [wind_start, shth_start, sphr_start]
    stop_set  = [wind_stop,  shth_stop,  sphr_stop]

    return [start_set, stop_set]

#----------------------------------------------------------------------------------------------------------
#-- find_fmt_region: find fmt changing periods                                                           --
#----------------------------------------------------------------------------------------------------------

def find_fmt_region(start, stop, fmt, time):
    """
    find fmt changing periods
    input:  start   --- starting time in sec from 1998.1.1
            sopt    --- stopping time in sec from 1998.1.1
            fmt     --- a list of fmt values
            time    --- a list of time coresponding to fmt list
    output: [start_set, stop_set]
            start_set = [fmt1_start, fmt2_start, fmt3_start, fmt4_start, fmt5_start]
            stop_set  = [fmt1_stop,  fmt2_stop,  fmt3_stop,  fmt4_stop,  fmt5_stop]
    """
#
#--- create dictioinary with fmt names
#
    s_start = {}
    s_stop  = {}
    for fval in ['fmt1', 'fmt2','fmt3','fmt4','fmt5','fmt6','fmt7','fmt8']:
        s_start[fval] = []
        s_stop[fval]  = []

    flen = len(fmt)
#
#--- start reading fmt; if fmt is same as one before, skip
#
    prev = fmt[0].lower()
    s_start[prev] = [time[0]]

    for k in range(1, flen):
        fval = fmt[k].lower()
        if fval == prev:
            continue
        else:
            s_stop  = update_dict_ent(s_stop,  prev, time[k])
            s_start = update_dict_ent(s_start, fval, time[k])
            prev    = fval
#
#--- closet the last entry
#
    flast  = fmt[flen-1].lower()
    ftime  = time[flen-1]
    s_stop = update_dict_ent(s_stop, flast, ftime)
#
#--- since fmt3 , fmt4, fmt5 don't happen often and rather quick, expand the "line" width
#--- so that we can see on the plot
#
    for fval in ['fmt3','fmt4','fmt5']:
        for k in range(0, len(s_stop[fval])):
            s_stop[fval][k] += 1000

    start_set = [s_start['fmt1'], s_start['fmt2'], s_start['fmt3'], s_start['fmt4'], s_start['fmt5']]
    stop_set  = [s_stop['fmt1'],  s_stop['fmt2'],  s_stop['fmt3'],  s_stop['fmt4'],  s_stop['fmt5']]

    return [start_set, stop_set]

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

def update_dict_ent(cdict, key, val):

    try:
        out = cdict[key]
        out.append(val)
        cdict[key] = out
    except:
        cdict[key] = [val]

    return cdict


#----------------------------------------------------------------------------------------------------------
#-- plot_strip_box: plotting shaded boxes on a panel                                                     --
#----------------------------------------------------------------------------------------------------------

def plot_strip_box(ax, start, stop, bstart_set, bstop_set, color=['red','blue', 'yellow', 'green', 'lime']):
    """
    plotting shaded boxes on a panel
    input:  ax          --- panel name
            start       --- xmin
            stop        --- xmax
            bstart_set  --- a list of lists of the beginning positions
            bstop_set   --- a list of lists of the ending positions
            color       --- a list of color. default is ['red','blue', 'yellow', 'green', 'lime']
    """
    syr  = checkyear(start)
    xmin = int(stime_to_ydate(start, syr=syr)) -1
    if xmin < 0:
        xmin = 0
    xmax = int(stime_to_ydate(stop, syr=syr)) + 1
    ymin = 0
    ymax = 1.0
    ax.set_autoscale_on(False) 
    ax.set_xbound(xmin,xmax) 
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
#
#--- go through each data set
#
    for i in range(0, len(bstart_set)):
        bset = bstart_set[i]
        eset = bstop_set[i]
#
#--- go through each begining and ending pair to create shaded area
#
        for j in range(0, len(bset)):
            begin = stime_to_ydate(bset[j], syr=syr)
            end   = stime_to_ydate(eset[j], syr=syr)
            if(end < begin):
                continue

            p = plt.axvspan(begin, end, facecolor=color[i], alpha=0.5)


#----------------------------------------------------------------------------------------------------------
#-- plot_line: plotting a line for a given x and y data set                                             ---
#----------------------------------------------------------------------------------------------------------

def plot_line(ax, start, stop, x, y, color='green'):
    """
    plotting a line for a given x and y data set
    input:  ax      ---- panel name
            start   ---- xmin
            stop    ---- xmax
            color   ---- color of the line; default: green
            x       ---- a list of x values
            y       ---- a list of y values
    output: a  line on panel ax. 
    """
    syr  = checkyear(start)
    xmin = int(stime_to_ydate(start, syr=syr))+1
    xmax = int(stime_to_ydate(stop, syr))
    ymin = 0
    ymax = 1.0
    ax.set_autoscale_on(False) 
    ax.set_xbound(xmin,xmax) 
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)

    pmax = max(y)
    pmin = min(y)
    xval = []
    yval = []
    for i in range(0, len(x)):
        tx = stime_to_ydate(x[i], syr)
        ty = (float(y[i])-pmin) / (pmax-pmin)

        xval.append(tx)
        yval.append(ty)

    plt.plot(xval, yval, color=color, lw=2)

#----------------------------------------------------------------------------------------------------------
#-- plot_points: plotting a scattered diagram for a given x and y data set                              ---
#----------------------------------------------------------------------------------------------------------

def plot_points(ax, start, stop, x, y, color='green',pts=1.5, lw='0'):
    """
    plotting a scattered diagram for a given x and y data set
    input:  ax      ---- panel name
            start   ---- xmin
            stop    ---- xmax
            color   ---- color of the points; default: green
            pts     ---- marker size; default: 1.5
            lw      ---- line width: default: 0
            x       ---- a list of x values
            y       ---- a list of y values
    output: a scattered diagram on panel ax. 
    """
    syr  = checkyear(start)
    xmin = int(stime_to_ydate(start, syr=syr))+1
    xmax = int(stime_to_ydate(stop, syr=syr))
    ymin = 0
    ymax = 1.0
    ax.set_autoscale_on(False) 
    ax.set_xbound(xmin,xmax) 
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)

    pmax = max(y)
    xval = []
    yval = []
    for i in range(0, len(x)):
        tx = stime_to_ydate(x[i], syr=syr)
        ty = float(y[i]) / pmax

        xval.append(tx)
        yval.append(ty)

    plt.plot(xval, yval, color=color, lw=lw, marker='*', markersize=pts)


#----------------------------------------------------------------------------------------------------------
#-- stime_to_ydate: convert time in sec from 1998.1.1 to ydate                                          ---
#----------------------------------------------------------------------------------------------------------

def stime_to_ydate(stime, syr=''):
    """
    convert time in sec from 1998.1.1 to ydate. no year info
    input: stime        ---- time in sec from 1998.1.1
    output: ydate       ---- ydate
    """
    stime = int(stime)
    out   = Chandra.Time.DateTime(stime).date
    atemp = re.split(':', out)
    year  = int(atemp[0])
    ydate =  float(atemp[1]) + float(atemp[2])/24.0 + float(atemp[3])/1440.0 + float(atemp[4]) /86400.0
    if syr != '':
        if year > syr:
            if isLeapYear(syr) == 1:
                ydate += 366
            else:
                ydate += 365
    return ydate

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

def checkyear(stime):

    stime = int(stime) + 3  #--- there is a fuzzy area at the beggining of the year; so add fudge factor
    out   = Chandra.Time.DateTime(stime).date
    atemp = re.split(':', out)

    return int(atemp[0])

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

def isLeapYear(year):
    """
    chek the year is a leap year
    Input:year   in full lenth (e.g. 2014, 813)
    
    Output:   0--- not leap year
    1--- yes it is leap year
    """
    
    year = int(float(year))
    chk  = year % 4 #---- evry 4 yrs leap year
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


#-------------------------------------------------------------------------------------------

#
#--- pylab plotting routine related modules
#

#from pylab import *
#import matplotlib.pyplot as plt
#import matplotlib.font_manager as font_manager
#import matplotlib.lines as lines
#from matplotlib.transforms import Bbox


if __name__ == "__main__":
    mag_plot = 1
    
    if len(sys.argv) == 3:
        start = sys.argv[1]
        stop  = sys.argv[2]
        out   = 'out.png'
    elif len(sys.argv) == 4:
        start = sys.argv[1]
        stop  = sys.argv[2]
        out   = sys.argv[3]
    else:
        print("Input: start stop in the format of 2014:204:00:00:00 or in seconds from 1998.1.1")
        exit(1)

    create_config_plot(start, stop, out,  mag_plot)





