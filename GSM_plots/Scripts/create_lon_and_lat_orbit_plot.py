#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#   create_lon_and_lat_orbit_plot.py:create gsm and gse orbit plots             #
#                                     in londitude and latitude                 #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Mar 27, 2020                                           #
#                                                                               #
#################################################################################

import sys
import os
import string
import re
import numpy
import getopt
import time
import time
import Chandra.Time
import matplotlib as mpl
if __name__ == '__main__':
    mpl.use('Agg')
from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines
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
sys.path.append('/data/mta/Script/Python3.6/MTA/')
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

data_dir = gsm_plot_dir + 'Data/'
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#--------------------------------------------------------------------------------
#-- create_lon_and_lat_orbit_plot: create gsm and gse orbit plots in londitude and latitude
#--------------------------------------------------------------------------------

def create_lon_and_lat_orbit_plot():
    """
    create gsm and gse orbit plots in londitude and latitude
    input:  none, but read from:
            <ephem_dir>/Data/PE.EPH.gsme_spherical_short
    output: <htm_dir>/Orbit/Plots/<gsm/gse>ORBIT.png
    """
#
#--- read orbit data
#
    [otime, radgsm, latgsm, longsm, radgse, latgse, longse] = read_coord_data()
#
#--- read region data and color code it
#
    color = read_region_data(otime)
#
#--- read dsn contact information
#
    [dsn_start, dsn_stop] = read_contact_data()
#
#--- convert to day of year
#
    otime     = convert_to_doy(otime)
    dsn_start = convert_to_doy(dsn_start)
    dsn_stop  = convert_to_doy(dsn_stop)
#
#--- plot data
#
    plot_lon_lat_info('gsm', otime, radgsm, latgsm, longsm, color, dsn_start, dsn_stop)
    plot_lon_lat_info('gse', otime, radgse, latgse, longse, color, dsn_start, dsn_stop)
#
#--- update orbit.html
#
    update_orbit_html()

#--------------------------------------------------------------------------------
#-- read_coord_data: read spherical gsm and dse data from ephem site           ---
#--------------------------------------------------------------------------------

def read_coord_data():
    """
    read spherical gsm and dse data from ephem site
    input:  none but read from:
            <ephem_dir>/Data/PE.EPH.gsme_spherical_short
    output: [otime, radgsm, latgsm, longsm, radgse, latgse, longse]
    """
#
#--- set the time either 0h or 12 h start
#
    stday = time.strftime("%Y:%j", time.gmtime())
    chk   = float(time.strftime("%H", time.gmtime()))
    if chk < 12:
        stday = stday + ':00:00:00'
    else:
        stday = stday + ':12:00:00'

    start = Chandra.Time.DateTime(stday).secs
    stop  = start + 8.0 * 86400.0
#
#--- read data
#
    ifile = ephem_dir + 'Data/PE.EPH.gsme_spherical_short'
    data  = mcf.read_data_file(ifile)
    
    otime  = []
    radgsm = []
    latgsm = []
    longsm = []
    radgse = []
    latgse = []
    longse = []
    for ent in data:
        atemp = re.split('\s+', ent)
        atime = float(atemp[0])
        if atime < start:
            continue
        elif atime > stop:
            break
        else:
#
#--- gsm data
#
            otime.append(atime)
            radgsm.append(float(atemp[1]) /1.0e3)
            latgsm.append(-1.0 * (float(atemp[2]) -90.0))
            longsm.append(float(atemp[3]))
#
#--- gse data
#
            radgse.append(float(atemp[1]) /1.0e3)
            latgse.append(-1.0 * (float(atemp[4]) -90.0))
            longse.append(float(atemp[5]))

    return [otime, radgsm, latgsm, longsm, radgse, latgse, longse]

#--------------------------------------------------------------------------------
#-- read_contact_data: ead DSN contact information                             --
#--------------------------------------------------------------------------------

def read_contact_data():
    """
    read DSN contact information
    input:  none but read from:
            <comm_dir>/Data/comm_data
    output: dsn_start   --- a list of contact start time
            dsn_stop    --- a list of contact end time
    """
#    infile = comm_dir + '/Data/dsn_summary.dat'
#    data   = mcf.read_data_file(infile)
#    dsn_start = []
#    dsn_stop  = []
#    for ent in data:
#        atemp = re.split('\s+', ent)
#        if mcf.is_neumeric(atemp[-1]):
#            syear = atemp[-4]
#            syday = atemp[-3]
#            eyear = atemp[-2]
#            eyday = atemp[-1]
#            cstart = convert_to_ctime(syear, syday)
#            cstop  = convert_to_ctime(eyear, eyday)
#            dsn_start.append(cstart)
#            dsn_stop.append(cstop)

    infile = comm_dir + '/Data/comm_data'
    data   = mcf.read_data_file(infile)
    dsn_start = []
    dsn_stop  = []
    for ent in data[2:]:
        atemp = re.split('\s+', ent)
        if mcf.is_neumeric(atemp[4]):
            dsn_start.append(float(atemp[4]))
            dsn_stop.append(float(atemp[5]))

    return [dsn_start, dsn_stop]

#--------------------------------------------------------------------------------
#-- read_region_data: read region data and assign color to correspoinding time list 
#--------------------------------------------------------------------------------

def read_region_data(time_list):
    """
    read region data and assign color to correspoinding time list
    input:  time_list   --- a list of time
            also read from: <crm3_dir>/Data/CRM3_p.dat30
    output: color       --- a list of color correspond to the time_list
                region: 1   solar wind      color: aqua
                region: 2   magnetoshearth  color: fuchsia
                region: 3   magnetospheare  color: yellow
    """
#
#--- read data 
#
    infile = crm3_dir + '/Data/CRM3_p.dat30'
    data   = mcf.read_data_file(infile)
    ctime  = []
    region = []
    for ent in data:
        atemp = re.split('\s+', ent)
        ctime.append(float(atemp[0]))
        region.append(int(float(atemp[1])))
#
#--- compare two time list and find which region satellite is in
#
    color = []
    start = 0
    clen  = len(ctime)
    chk   = 0
    for otime in time_list:
        for k in range(start, clen):
            k1 = k + 1
            if k1 >= clen:
                chk = 1
                break
#
#--- if the region list could not cover the first part of the time list, use color "white"
#
            if k == 0 and otime < ctime[k]:
                color.append('white')
                break

            elif otime >=ctime[k] and otime < ctime[k1]:
                if region[k] == 1:
                    color.append('aqua')
                elif region[k] == 2:
                    color.append('fuchsia')
                else:
                    color.append('yellow')
                start = k - 5
                if start < 0:
                    start = 0
                break
            else:
                continue

        if chk > 0:
            break
#
#--- if the color list was not be filled, use the last region color to fill
#
    if len(color) < len(time_list):
        lcolor = color[-1]
        for k in range(len(color), len(time_list)):
            color.append(lcolor)

    return color

#--------------------------------------------------------------------------------
#-- convert_to_ctime: convert <yyyy> <doy>.<fractional doy> to Chandra Time    --
#--------------------------------------------------------------------------------

def convert_to_ctime(year, fyday):
    """
    convert <yyyy> <doy>.<fractional doy> to Chandra Time
    input:  year    --- year
            fyday   --- fractional day of year
    output: time in seconds from 1998.1.1
    """
    year  = str(year)

    ydate = float(fyday)
    yday  = int(ydate)
    frc   = 24 * (ydate - yday)
    hh    = int(frc)
    frc   = 60 *(frc - hh)
    mm    = int(frc)
    ss    = 60 *(frc - mm)
    ss    = int(ss)

    ltime = year  + ':' + mcf.add_leading_zero(yday, 3) + ':' + mcf.add_leading_zero(hh)
    ltime = ltime + ':' + mcf.add_leading_zero(mm)      + ':' + mcf.add_leading_zero(ss)

    ctime = Chandra.Time.DateTime(ltime).secs
    ctime = int(ctime)

    return ctime
    
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------

def plot_lon_lat_info(dset, otime, rad, lat, lon, color, dsn_start, dsn_stop):
    """
    create orbital plot with longitude and latitude
    input:  dset    --- either 'gsm' or 'gse'
            otime   --- a list of time in fractional doy
            rad     --- a list of radius in kkm
            lat     --- a list of latitude
            lon     --- a list of longditude
            color   --- a list of color indicating in which region the satellite is
            dsn_start   --- a list of DSN contact starting time
            dsn_stop    --- a list of DSN contact ending time
    output: <html_dir>/Orbit/Plots/<dset>.png
    """

    plt.close('all')
#
#--- set the plotting range.
#
    hh   = float(time.strftime("%H", time.gmtime()))
    xmin = this_doy + hh /24.0

    xmax = xmin + 7
    xdff = xmax - xmin
    xtxt = xmax + 0.01 * xdff       #--- position of explanatory text
    ymin1 = 0
    ymax1 = 0.15
    ymin2 = -190
    ymax2 =  190
    ymin3 = -100
    ymax3 =  100
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 8
    props = font_manager.FontProperties(size=8)
    plt.subplots_adjust(hspace=0.03)
#
#--- altitude plot
#
    ax0 = plt.subplot(311)
    ax0.set_autoscale_on(False)
    ax0.set_xbound(xmin, xmax)
    ax0.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax0.set_ylim(ymin=ymin1, ymax=ymax1, auto=False)
    ax0.set_facecolor('xkcd:black')

    plt.scatter(otime, rad, color=color, marker='.',  s=0.5)

    ax0.set_ylabel('Geocentric Alt (Mm)')
#
#--- no tick labeling 
#
    line = ax0.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- longitude plot
#
    ax1 = plt.subplot(312)
    ax1.set_autoscale_on(False)
    ax1.set_xbound(xmin, xmax)
    ax1.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax1.set_ylim(ymin=ymin2, ymax=ymax2, auto=False)
    ax1.set_facecolor('xkcd:black')
#
#--- there is a discontinuity on plot: so cover it with line
#
    plt.plot(otime, lon, color='white', marker='.', ms=0.0,  lw=0.3)
    plt.scatter(otime, lon, color=color, marker='.', s=0.5)
#
#--- DSN contact information
#
    for k in range(0, len(dsn_start)):
        plt.plot([dsn_start[k], dsn_stop[k]], [0, 0], color='white',  lw=3)

    ax1.set_ylabel('Longitude (deg)')
#
#--- no tick labeling
#
    line = ax1.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- mark the position of geotail, dusk etc
#
    plt.text(xtxt,  175, 'GEOTAIL', size=5, color='black')
    plt.text(xtxt,   85, 'DSUK',    size=5, color='black')
    plt.text(xtxt,   -5, 'SUNWARD', size=5, color='black')
    plt.text(xtxt,  -95, 'DAWN',    size=5, color='black')
    plt.text(xtxt, -185, 'GEOTAIL', size=5, color='black')
#
#--- latitude plot
#
    ax2 = plt.subplot(313)
    ax2.set_autoscale_on(False)
    ax2.set_xbound(xmin, xmax)
    ax2.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax2.set_ylim(ymin=ymin3, ymax=ymax3, auto=False)
    ax2.set_facecolor('xkcd:black')

    plt.scatter(otime, lat, color=color, marker='.', s=0.5)
#
#--- DSN plot
#
    for k in range(0, len(dsn_start)):
        plt.plot([dsn_start[k], dsn_stop[k]], [0, 0],  color='white', lw=3)

    ax2.set_xlabel('UTC Time (Day of Year)')
    ax2.set_ylabel('Latitude (deg)')

#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 5.0)
#
#--- save the plot in png format
#
    outname = html_dir + 'Orbit/Plots/' + dset.upper()+ '.png'
    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')

#--------------------------------------------------------------------------------
#-- find_current_pos: find the current position in the list                    --
#--------------------------------------------------------------------------------

def find_current_pos(otime):
    """
    find the current position in the list
    input:  otime   --- a list of time
    output: pos     --- an index of the list of where the current time indicates
    """
#
#--- find the current time
#
    current = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    current = Chandra.Time.DateTime(current).secs
#
#--- find the nearest time in the list and take the index
#
    pos  = 0
    olen = len(otime)
    for k in range(0, olen):
        k1 = k + 1
        if k1 == olen:
            pos = k
            break
        else:
            if current >=otime[k] and current < otime[k+1]:
                pos = k
                break
            else:
                continue

    return pos

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
#-- update_orbit_html: update orbit.html page with dsn contact           --
#--------------------------------------------------------------------------

def update_orbit_html():
    """
    update orbit.html page with dsn contact
    input: none but read from <comm_dir>/Data/comm_data
    output: <html_dir>/Orbit/orbit.html
    """
    comm_data = comm_dir + 'Data/comm_data'
    data = mcf.read_data_file(comm_data)
    line = '<table border=1 cellpadding=5 style="text-align:center; margin-right:auto;margin-left:auto;">\n'
    line = line + '<tr><th colspan=2>Support Time (GMT)</th><th colspan=2>Contact Time (GMT)</th>'
    line = line + '<th>Station</th><th>Site</th></tr>\n'
    line = line + '<tr><th colspan=6>&#160;</th></tr>\n' 
    for ent in data[2:]:
        atemp = re.split('\s+', ent)
        line  = line + '<tr><td>' + atemp[0] + '</td><td>' + atemp[1] + '</td>'
        line  = line + '<td>' + atemp[2] + '</td><td>' + atemp[3] + '</td>'
        btemp = re.split('\/', atemp[-1])
        line  = line + '<td>' + btemp[0] + '</td><td>' + btemp[1] + '</td></tr>\n'
    line = line + '</table>\n' 

    ifile = './Template/orbit.html'
    with open(ifile, 'r') as f:
        html = f.read()

    html  = html.replace("#COMM_DATA#", line)

    ofile = html_dir + 'Orbit/orbit.html'
    with open(ofile, 'w') as fo:
        fo.write(html)

#--------------------------------------------------------------------------------

if __name__ == "__main__":

    create_lon_and_lat_orbit_plot()
