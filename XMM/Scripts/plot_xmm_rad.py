#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#           plot_xmm_rad.py: plot xmm radiation flux and environment                            #
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
#import astropy.io.fits  as pyfits
import numpy
import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')

from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines
import matplotlib.gridspec     as gridspec

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
#
#--- import several functions
#
import mta_common_functions as mcf
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
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#--------------------------------------------------------------------------
#-- plot_xmm_rad: plot xmm radiation flux and environment                --
#--------------------------------------------------------------------------

def plot_xmm_rad():
    """
    plot xmm radiation flux and environment
    input:  none, but read from:
                <xmm_dir>/Data/xmm_7day.archive2
                <tle_dir>/Data/xmm.spctrk
                <tle_dir>/Data/cxo.spctrk
    output: <html_dir>/XMM/Plots/mta_xmm_plot.png
    """
#
#--- read the radiation data
#
    ifile = xmm_dir + 'Data/xmm_7day.archive2'
    data  = mcf.read_data_file(ifile)
    [atime, le0, le1, le2, hes0, hes1, hes2, hec] = convert_to_col_data2(data)
#
#--- read xmm orbit
#
    ifile = tle_dir + 'Data/xmm.spctrk'
    data  = mcf.read_data_file(ifile)
    [xtime, x_eci,y_eci,z_eci,vx,vy,vz] = convert_to_col_data(data)
#
#--- compute the altitutde of xmm
#
    xorbit = numpy.sqrt(numpy.square(x_eci) + numpy.square(y_eci) + numpy.square(z_eci))
    xorbit = xorbit /1000.0         #--- unit in kkm 

    ifile = xmm_dir + 'Data/crmreg_xmm.dat'
    [xrtime, xloc] = read_region_data(ifile)
    xrtime = convert_to_doy(xrtime)
    [xstart, xstop, x_color] = get_region(xrtime, xloc)
#
#--- read cxo orbit
#
    ifile = tle_dir + 'Data/cxo.spctrk'
    data  = mcf.read_data_file(ifile)
    [ctime, cx_eci,cy_eci,cz_eci,cvx,cvy,cvz] = convert_to_col_data(data)

    ifile = xmm_dir + 'Data/crmreg_cxo.dat'
    [crtime, cloc] = read_region_data(ifile)
    crtime = convert_to_doy(crtime)
    [cstart, cstop, c_color] = get_region(crtime, cloc)
#
#--- convert time from chandra time to doy of this year
#
    atime_d = convert_to_doy(atime)
    xtime_d = convert_to_doy(xtime)
    ctime_d = convert_to_doy(ctime)
#
#--- current time in doy of this year
#
    c_pos = (current_chandra_time - year_start)/ 86400.0 + 1
#
#--- plotting starts here ------
#
#
#--- plotting range is from 5 days before to 2 day after today
#
    xmin = this_doy - 4
    xmax = this_doy + 3
#
#--- first plot: radiation plot
#
    plt.close('all')
    mpl.rcParams['font.size'] = 10
    props = font_manager.FontProperties(size=10)
    plt.subplots_adjust(hspace=0.09)

    ymin = 1
    ymax = 1000000
    ax0 = plt.subplot(111)
    ax0.set_autoscale_on(False)
    ax0.set_xbound(xmin, xmax)
    ax0.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax0.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax0.set_facecolor('xkcd:black')
#
#--- plotting data
#
    plt.semilogy(atime_d, le0,  color='moccasin',    marker='.', ms=0.5, lw=0)
    plt.semilogy(atime_d, le1,  color='aqua',        marker='.', ms=0.5, lw=0)
    plt.semilogy(atime_d, hes1, color='red',         marker='.', ms=0.5, lw=0)
    plt.semilogy(atime_d, hes2, color='orange',      marker='.', ms=0.5, lw=0)
    plt.semilogy(atime_d, hec,  color='greenyellow', marker='.', ms=0.5, lw=0)
#
#--- plotting current position
#
    plt.plot([c_pos,c_pos], [ymin, ymax], ls='--', lw=1, color='white')
    c_pos1 = c_pos + 0.1
    plt.text(c_pos1,1e4, "Current Time",rotation='vertical', color='white', size=7)

#
#--- plotting 1e2 and 1e4 lines
#
    plt.plot([xmin,xmax], [1e2,1e2], ls =':', lw=0.8, color='white')
    plt.plot([xmin,xmax], [1e4,1e4], ls =':', lw=0.8, color='white')
#
#--- adding labels
#
    xmid  = 0.5 * (xmax + xmin)
    xdiff = xmax - xmin
    xpos1 = xmin + 0.01 * xdiff
    xpos2 = xmin + 0.19 * xdiff
    xpos3 = xmin + 0.39 * xdiff
    xpos4 = xmin + 0.59 * xdiff
    xpos5 = xmin + 0.79 * xdiff
    ypos  = 300000
    plt.text(xpos1, ypos, 'le0 (1-1.5MeV)',    color='moccasin',    size=6)
    plt.text(xpos2, ypos, 'le1 (1.5-4.5MeV)',  color='aqua',        size=6)
    plt.text(xpos3, ypos, 'hes1 (2.7-9MeV)',   color='red',         size=6)
    plt.text(xpos4, ypos, 'hes2 (9-37MeV)',    color='orange',      size=6)
    plt.text(xpos5, ypos, 'hec (12.5-100MeV)', color='greenyellow', size=6)
    ax0.set_ylabel('XMM Protons Cnts/Sec')
#
#--- don't put the x label
#
#    line = ax0.get_xticklabels()
#    for label in  line:
#        label.set_visible(False)
#
#
#---set plot surface
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 5.0)
#
#--- save the plot
#
    outname = html_dir + 'XMM/Plots/mta_xmm_plot_p1.png'
    plt.savefig(outname, format='png', dpi=300)
#
#--- second plot ------
#
    plt.close('all')
    mpl.rcParams['font.size'] = 10
    props = font_manager.FontProperties(size=10)
    plt.subplots_adjust(hspace=0.09)
#
#--- first panel: XMM Orbit
#
    ymin = 0
    ymax = 130
    ax1 = plt.subplot(211,sharex=ax0)
    ax1.set_autoscale_on(False)
    ax1.set_xbound(xmin, xmax)
    ax1.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax1.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax1.set_facecolor('xkcd:black')
#
#--- plot data
#
    plt.plot(xtime_d, xorbit, color='aqua',   lw = 1)
#
#--- plotting current position
#
    plt.plot([c_pos,c_pos], [ymin, ymax], ls='--', lw=1, color='white')
#
#--- adding labels
#
    ax1.set_ylabel('XMM Altitude (kkm)', size=9)
#
#--- second panel: xmm/cxo region plot
#
    ax2 = plt.subplot(212,sharex=ax0)
    ax2.set_autoscale_on(False)
    ax2.set_xbound(xmin, xmax)
    ax2.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax2.set_ylim(ymin=0, ymax=2, auto=False)
    ax2.set_facecolor('xkcd:black')

    for k in range(0, len(xstart)):
        xset = [xstart[k], xstop[k]]
        plt.fill_between(xset, 1.2, 1.8, color= x_color[k])
#
    for k in range(0, len(cstart)):
        xset = [cstart[k], cstop[k]]
        plt.fill_between(xset, 0.2, 0.8, color= c_color[k])

    ax2.set_ylabel('CXO        XMM')
    xpos1 = xmin + 0.05  * xdiff
    xpos2 = xmin + 0.3  * xdiff
    xpos3 = xmin + 0.6  * xdiff

    plt.text(xpos1, 0.95, 'Solar Wind',    color='greenyellow',   size=9)
    plt.text(xpos2, 0.95, 'Magnetosheath', color='darkturquoise', size=9)
    plt.text(xpos3, 0.95, 'Magnetosphere', color='yellow',        size=9)
#
#--- add x ticks label only on the last panel and remove y ticks from the last panel
#
    line = ax2.get_yticklabels()
    for label in  line:
        label.set_visible(False)

    line = ax1.get_xticklabels()
    for label in  line:
        label.set_visible(False)
#
#--- x axis label
#
    line = 'Time (DOY Year: ' + str(this_year) + ')'
    ax2.set_xlabel(line)
#
#---set plot surface
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 4.0)
#
#--- save the plot
#
    outname = html_dir + 'XMM/Plots/mta_xmm_plot_p2.png'
    plt.savefig(outname, format='png', dpi=300)
    plt.close('all')

#--------------------------------------------------------------------------
#-- convert_to_col_data: convert the list of data line into column data   -
#--------------------------------------------------------------------------

def convert_to_col_data(data):
    """
    output: a list of numpy arrays of:
                xtime   --- numpy array of time in seconds from 1970.1.1
                x       --- numpy array of x
                y       --- numpy array of y
                z       --- numpy array of z
                vx      --- numpy array of vx (soloar wind)
                vy      --- numpy array of vy (soloar wind)
                vz      --- numpy array of vz (soloar wind)
    """
    xtime = []
    x     = []
    y     = []
    z     = []
    vx    = []
    vy    = []
    vz    = []
    for ent in data[5:]:
        atemp = re.split('\s+', ent)
#
#--- convert time in seconds from 1970.1.1
#
        try:
            out   = time.strftime('%Y:%m:%d', time.strptime(atemp[1] + ':' + atemp[2], '%Y:%j'))
            btemp = re.split(':', out)
            ut    = convert_to_chandra(atemp[1], btemp[1], btemp[2], atemp[3], atemp[4], atemp[5])
        except:
            continue

        xtime.append(ut)
        x.append(float(atemp[6]))
        y.append(float(atemp[7]))
        z.append(float(atemp[8]))
        vx.append(float(atemp[9]))
        vy.append(float(atemp[10]))
        vz.append(float(atemp[11]))

    xtime = numpy.array(xtime)
    x     = numpy.array(x)
    y     = numpy.array(y)
    z     = numpy.array(z)
    vx    = numpy.array(vx)
    vy    = numpy.array(vy)
    vz    = numpy.array(vz)

    return[xtime, x, y, z, vx, vy, vz]

#--------------------------------------------------------------------------
#-- convert_to_col_data2: convert the list of data line into column data: radiation data version
#--------------------------------------------------------------------------

def convert_to_col_data2(data):
    """
    convert the list of data line into column data: radiation data version
    input:  data    --- a list of data list
    output: a list of numpy array of [time, le0, le1, le2, hes0, hes1, hes2, hec]
    """
    xtime = []
    le0   = []
    le1   = []
    le2   = []
    hes0  = []
    hes1  = []
    hes2  = []
    hec   = []

    for ent in data:
        atemp = re.split('\s+', ent)
        xtime.append(float(atemp[0]))
        le0.append(float(atemp[1]))
        le1.append(float(atemp[2]))
        le2.append(float(atemp[3]))
        hes0.append(float(atemp[4]))
        hes1.append(float(atemp[5]))
        hes2.append(float(atemp[6]))
        hec.append(float(atemp[7]))

    xtime = numpy.array(xtime)
    le0   = numpy.array(le0)
    le1   = numpy.array(le1)
    le2   = numpy.array(le2)
    hes0  = numpy.array(hes0)
    hes1  = numpy.array(hes1)
    hes2  = numpy.array(hes2)
    hec   = numpy.array(hec)

    return [xtime, le0, le1, le2, hes0, hes1, hes2, hec]

#--------------------------------------------------------------------------
#-- read_region_data: read region data                                   --
#--------------------------------------------------------------------------

def read_region_data(ifile):
    """
    read region data
    input:  ifile   --- a file name contain region data
    outpu:  rtime   --- a list of time
            loc     --- a list of locatinon indicator
    """
    data = mcf.read_data_file(ifile)
    rtime = []
    loc   = []
    for ent in data:
        atemp = re.split('\s+', ent)
        rtime.append(float(atemp[0]))
        loc.append(int(float(atemp[-1])))

    rtime = numpy.array(rtime)
    loc   = numpy.array(loc)

    return [rtime, loc]


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

#--------------------------------------------------------------------------
#-- convert_to_doy: convert to chandra time to day of year of this year  --
#--------------------------------------------------------------------------

def convert_to_doy(ctime):
    """
    convert to chandra time to day of year of this year
    input:  ctime   --- a list of time in seconds from 1998.1.1
    output: dtime   --- a list of time in doy of this year
        note: see at the top for year_start value
    """
    dtime = []
    for ent in ctime:
        out = (ent - year_start) / 86400.0
        if out > 0:
            out += 1
        dtime.append(out)

    return dtime

#--------------------------------------------------------------------------
#-- get_region: set color coded time period of where the satellite is    --
#--------------------------------------------------------------------------

def get_region(atime, aloc):
    """
    set color coded time period of where the satellite is 
    input:  atime   --- a list of time
            aloc    --- where is the satellite is:
                            1: solar wind
                            2: magnetoshearth
                            3: magnetoshpere
    output: astart  --- a list of starting time
            astop   --- a list of stopping time
            color   --- a list of color during the  period
    """
    astart = [atime[0]]
    astop  = []
    ind    = [aloc[0]]
    prev   = aloc[0]
    alen   = len(atime)
    for k in range(0, alen):
        if aloc[k] != prev:
            astop.append(atime[k])
            astart.append(atime[k])
            ind.append(aloc[k])
            prev = aloc[k]

    astop.append(atime[alen-1])

    color = []
    for ent in ind:
        if ent == 1:
            color.append('greenyellow')
        elif ent == 2:
            color.append('darkturquoise')
        else:
            color.append('yellow')

    return [astart, astop, color]

#------------------------------------------------------------------------------

if __name__ == '__main__':

    plot_xmm_rad()
