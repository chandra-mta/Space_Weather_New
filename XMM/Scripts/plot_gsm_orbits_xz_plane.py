#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#   plot_gsm_orbits_xz_plane.py: plot xmm and cxo orbits in gsm coordinates in xz plane         #
#                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                               #
#           last update: Mar 16, 2021                                                           #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import time
import math
import Chandra.Time
from datetime import datetime
#import astropy.io.fits  as pyfits
import numpy
import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')

from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines

#
#--- Define Directory Pathing
#
XMM_DIR = "/data/mta4/Space_Weather/XMM"
TLE_DIR = "/data/mta4/Space_Weather/TLE"
HTML_DIR = '/data/mta4/www/RADIATION_new'

#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.11/lib/python3.11/site-packages')
#
#--- import several functions
#
from geopack import geopack

#
#--- Earth radius
#
EARTH    =  6378.0

#--------------------------------------------------------------------------
#-- plot_gsm_orbits_xz_plane: plot xmm and cxo orbits in gsm coordinates in xz plane
#--------------------------------------------------------------------------

def plot_gsm_orbits_xz_plane():
    """
    plot xmm and cxo orbits in gsm coordinates in xz plane
    input:  none, but read from various locations
    output: <html_dir>/XMM/Plots/mta_xmm_plot_gsm.png'
    """
#
#--- read xmm orbit
#
    ifile = f"{TLE_DIR}/Data/xmm.spctrk"
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    [xtime, x_eci,y_eci,z_eci,vx,vy,vz] = convert_to_col_data(data)
    [x_gsm, y_gsm, z_gsm] = compute_gsm(xtime, x_eci,y_eci,z_eci)
#
#--- read cxo orbit
#
    ifile = f"{TLE_DIR}/Data/cxo.spctrk"
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    [ctime,cxo_x_eci,cxo_y_eci,cxo_z_eci,cxo_vx,cxo_vy,cxo_vz] = convert_to_col_data(data)
    [cxo_x_gsm, cxo_y_gsm, cxo_z_gsm] = compute_gsm(ctime, cxo_x_eci,cxo_y_eci,cxo_z_eci)
#
#--- current time
#
    out     = time.strftime('%Y:%m:%d:%H:%M:%S', time.gmtime())
    ctemp   = re.split(':', out)
    current = ut_in_secs(ctemp[0], ctemp[1], ctemp[2], ctemp[3], ctemp[4], ctemp[5])
#
#--- set plotting period to +/- 1.35 day
#
    [xtime, x_eci, y_eci, z_eci, x_gsm, z_gsm, z_gsm, vx, vy, vz] = \
       select_data_in_rnage(current, xtime, x_eci, y_eci, z_eci, x_gsm, z_gsm, z_gsm, vx, vy, vz)

    [ctime, cxo_x_eci, cxo_z_eci, cxo_z_eci, cxo_x_gsm,\
     cxo_y_gsm, cxo_z_gsm, cxo_vx, cxo_vy, cxo_vz] \
             =select_data_in_rnage(current, ctime, cxo_x_eci, cxo_y_eci, cxo_z_eci,\
                                   cxo_x_gsm, cxo_y_gsm, cxo_z_gsm, cxo_vx, cxo_vy, cxo_vz)
#
#--- get crm region (color list)
#
    ifile = f"{XMM_DIR}/Data/crmreg_xmm.dat"
    xmm_color = crm_region(ifile, xtime)

    ifile = f"{XMM_DIR}/Data/crmreg_cxo.dat"
    cxo_color = crm_region(ifile, ctime)
#
#--- van allen
#
    van_x  = []
    van_z  = []
    van_zn = []
    for k in range(0, 400):
        x = -3.0 + 0.015 * k 
        z = math.sqrt(9.0 - x*x)
        van_x.append(x)
        van_z.append(z)
        van_zn.append(-1.0 * z)
    van_x.append(3.0)
    van_z.append(0.0)
    van_zn.append(0.0)
#
#--- magnetoshearth
#
    mag_x  = []
    mag_z  = []
    mag_zn = []
    for k in range(0, 100):
        x = 0.07 * k 
        z = math.sqrt(49.0 - x*x)
        mag_x.append(x)
        mag_z.append(z)
        mag_zn.append(-1.0 * z)
    mag_x.append(7.0)
    mag_z.append(0.0)
    mag_zn.append(0.0)
#
#--- plotting starts here
#
    plt.close('all')
    mpl.rcParams['font.size'] = 10
    props = font_manager.FontProperties(size=10)
    plt.subplots_adjust(hspace=0.10)
    ax = plt.subplot(111)
    xmin = -20
    xmax =  20
    ymin = -20
    ymax =  20
    ax.set_autoscale_on(False)
    ax.set_xbound(xmin, xmax)
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax.set_facecolor('xkcd:black')
#
#--- xmm orbit; each segment needs to be plot separately depending on the color
#
    x  = []
    z  = []
    cl = xmm_color[0]
    for k in range(0,  len(x_gsm)):
#
#---while the orbit is in the same region, just save the data
#
        if xmm_color[k] == cl:
            x.append(x_gsm[k])
            z.append(z_gsm[k])
#
#--- region changed; plot the last orbital segment
#
        else:
            plt.plot(z, x, color=cl, marker='.', markersize='0.0', ls = ':', lw=2.0)
            x = [x_gsm[k]]
            z = [z_gsm[k]]
            cl = xmm_color[k]
#
#--- if there is leftover, plot the segment
#
    if len(x) > 0:
        plt.plot(z, x, color=cl, marker='.', markersize='0.0', ls = ':', lw=2.0)
#
#--- current position and a day before position
#
    cpos = find_index_of_time(current, xtime)
    plt.plot([z_gsm[cpos]],[x_gsm[cpos]], marker='*', markersize=6, color='aqua')

    plt.plot([-20, z_gsm[cpos]], [x_gsm[cpos], x_gsm[cpos]], marker='.',\
                markersize='0.0', ls=':', lw=1.0, color='white')

    cpos = find_index_of_time(current-86400, xtime)
    plt.plot([z_gsm[cpos]],[x_gsm[cpos]], marker='p', markersize=6, color='salmon')
#
#--- cxo orbit; each segment needs to be plot separately depending on the color
#
    plt.plot(cxo_z_gsm,cxo_x_gsm, color='white', marker='.', markersize='0.0', ls = '-', lw=1.0)
    x  = []
    z  = []
    cl = cxo_color[0]
    for k in range(0,  len(cxo_x_gsm)):
#
#---while the orbit is in the same region, just save the data
#
        if cxo_color[k] == cl:
            x.append(cxo_x_gsm[k])
            z.append(cxo_z_gsm[k])
#
#--- region changed; plot the last orbital segment
#
        else:
            plt.plot(z, x, color=cl, marker='.', markersize='0.0', ls = '-', lw=2.0)
            x = [cxo_x_gsm[k]]
            z = [cxo_z_gsm[k]]
            cl = cxo_color[k]
    if len(x) > 0:
#
#--- if there is leftover, plot the segment
#
        plt.plot(z, x, color=cl, marker='.', markersize='0.0', ls = '-', lw=2.0)
#
#--- current position and a day before position
#
    cpos = find_index_of_time(current, ctime)
    plt.plot([cxo_z_gsm[cpos]],[cxo_x_gsm[cpos]], marker='*', markersize=6, color='aqua')

    plt.plot([-20, cxo_z_gsm[cpos]], [cxo_x_gsm[cpos], cxo_x_gsm[cpos]], \
                marker='.', markersize='0.0', ls=':', lw=1.0, color='white')

    cpos = find_index_of_time(current-86400, ctime)
    plt.plot([cxo_z_gsm[cpos]],[cxo_x_gsm[cpos]], marker='p', markersize=6, color='salmon')
#
#--- the earth center
#
    plt.plot([0], [0], marker='+', markersize='6', color='white')
#
#--- van allen belt
#
    plt.plot(van_z,  van_x, color='orange', marker='.', markersize='0.0', lw=0.8)
    plt.plot(van_zn, van_x, color='orange', marker='.', markersize='0.0', lw=0.8)
#
#--- magnetosheath
#
    plt.plot(mag_z,  mag_x, color='lime', marker='.', markersize='0.0', lw=0.8)
    plt.plot(mag_zn, mag_x, color='lime', marker='.', markersize='0.0', lw=0.8)
#
#--- sun direction
#
    plt.arrow(0,12, 0, 5, color='yellow',head_width=0.8)
    plt.text(0.1, 13, "SUN", color='yellow', size=6)
#
#--- axis label
#
    ax.set_ylabel('X_GSM(Re)')
    ax.set_xlabel('Z_GSM(Re)')
#
#--- other explanation texts
#
    plt.text(5, 17, 'Norm. Magnetoshearth', color='lime',    size=8)
    plt.text(5, 15, 'Norm. Van Allen Belts', color='orange', size=8)

    plt.plot([-15,-10],[17, 17], marker='.', markersize='0.0', ls = '-', lw=2.0, color='white')
    plt.text(-8, 16.5, 'CXO', color='white')

    plt.plot([-15,-10],[15, 15], marker='.', markersize='0.0', ls = ':', lw=2.0, color='white')
    plt.text(-8, 14.5, 'XMM', color='white')

    plt.plot([-15], [-16], marker='*', markersize=6, color='aqua')
    plt.text(-13, -16.5, 'Current Position', size=8, color='aqua')

    plt.plot([-15], [-18], marker='p', markersize=6, color='salmon')
    plt.text(-13, -18.5, 'One Day Ago', size=8, color='salmon')

    plt.plot([5,7],[-16,-16],lw=0.8,color='greenyellow')
    plt.text(8, -16.5, 'Solar Wind', color='greenyellow', size=7)

    plt.plot([5,7],[-17,-17],lw=0.8,color='darkturquoise')
    plt.text(8, -17.5, 'Magnetosheath', color='darkturquoise', size=7)

    plt.plot([5,7],[-18,-18],lw=0.8,color='yellow')
    plt.text(8, -18.5, 'Magnetosphere', color='yellow', size=7)

    disp_time = time.strftime('%Y-%m-%d:%H:%M:%S', time.gmtime())
    text = 'Last Update: ' + disp_time + ' (UT)'
    plt.text(6,-23, text, color='black', size=5)
#
#---set plot surface
#
    fig = plt.gcf()
    fig.set_size_inches(5.0, 5.0)
#
#--- save the plot
#
    outname = f"{HTML_DIR}/XMM/Plots/mta_xmm_plot_gsm_xz.png"
    plt.tight_layout()
    plt.savefig(outname, format='png', dpi=300)
    plt.close('all')

#--------------------------------------------------------------------------
#-- convert_to_col_data: convert the list of data line into column data   -
#--------------------------------------------------------------------------

def convert_to_col_data(data):
    """
    convert the list of data line into column data
    input:  data    --- a list of data list
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
            ut    = ut_in_secs(atemp[1], btemp[1], btemp[2], atemp[3], atemp[4], atemp[5])
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
#-- ut_in_secs: convert calendar date into univarsal time in sec         --
#--------------------------------------------------------------------------

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
    
    uts  = (datetime.datetime(year, mon, day, hh, mm, ss) \
                    - datetime.datetime(1970,1,1)).total_seconds()
    uts += 86400.0
    
    return uts

#--------------------------------------------------------------------------
#-- compute_gsm: convert x, y, z coordinates to that of gsm              --
#--------------------------------------------------------------------------

def compute_gsm(t, x, y, z):
    """
    convert x, y, z coordinates to that of gsm
    input:  x   --- x coordinates
            y   --- y coordinates
            z   --- z coordinates
    output: gx  --- gsm x 
            gy  --- gsm y
            gz  --- gsm z
    """
    gx = []
    gy = []
    gz = []
    for k in range(0, len(t)):
        psi = geopack.recalc(t[k])
        xgeo, ygeo, zgeo = geopack.geigeo(x[k], y[k], z[k], 1)
        xgsm, ygsm, zgsm = geopack.geogsm(xgeo, ygeo, zgeo, 1)
        xgm = xgsm / EARTH
        ygm = ygsm / EARTH
        zgm = zgsm / EARTH
        gx.append(xgm)
        gy.append(ygm)
        gz.append(zgm)

    gx = numpy.array(gx)
    gy = numpy.array(gy)
    gz = numpy.array(gz)

    return [gx, gy, gz]

#--------------------------------------------------------------------------
#-- select_data_in_rnage: select data for the +/- 1.35 days of the current time
#--------------------------------------------------------------------------

def select_data_in_rnage(current, xtime, x_e, y_e, z_e, x_g, y_g, z_g, vx, vy, vz):
    """
    select data for the +/- 1.35 days of the current time
    input:  current --- current time in seconds from 1970.1.1
            xtime, x_e, y_e, z_e, x_g, y_g, z_g, vx, vy, vz --- lists of data to be selected
    output: xtime, x_e, y_e, z_e, x_g, y_g, z_g, vx, vy, vz --- lists of selected data sets
    """
    start   = current  - 1.35 * 86400
    stop    = current  + 1.35 * 86400
    xtime   = numpy.array(xtime)
    index1  = xtime >= start
    index2  = xtime <= stop 
    index   = index1 * index2

    xtime   = xtime[index]
    x_e     = x_e[index]
    y_e     = y_e[index]
    z_e     = z_e[index]
    x_g     = x_g[index]
    y_g     = y_g[index]
    z_g     = z_g[index]
    vx      = vx[index]
    vy      = vy[index]
    vz      = vz[index]

    return [xtime, x_e, y_e, z_e, x_g, y_g, z_g, vx, vy, vz]

#--------------------------------------------------------------------------
#-- crm_region: find out which crm region the satellite is in for given times 
#--------------------------------------------------------------------------

def crm_region(ifile, xtime):
    """
    find out which crm region the satellite is in for given times
    input:  ifile   --- crm region data file
            xtime   --- a list of time in secnods from 1970.1.1
    output: color   --- a list of color assigned for each time value
    """
#
#--- crm region data
#
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    ctime = []
    area  = []
#
#--- convert time in seconds from 1998.1.1 to seconds from 1970.1.1
#
    for ent in data:
        atemp = re.split('\s+', ent)
        out   = chandra_to_ut_in_sec(atemp[0])
        ctime.append(out)
        area.append(float(ent[-1]))
#
#--- match the current list of time
#
    color = []
    start = 0
    chk   = 0
    for x in xtime:
        if chk == 1:
            break

        for m in range(start, len(ctime)):
            comp  = ctime[m]
            m1 = m + 1
            if m1 < len(ctime):
                comp2 = ctime[m1]
            else:
                chk = 1
                break
            if x >= comp and x < comp2:
                if area[m] == 1:
                    color.append('greenyellow')
                elif area[m] == 2:
                    color.append('darkturquoise')
                else:
                    color.append('yellow')
                start = m - 5
                if start < 0:
                    start = 0
                break
#
#--- if the region data is shorter than time data, just fill with the last color entry
#
    if chk > 0:
        k = len(color)
        for m in range(k, len(xtime)):
            color.append(color[k-1])

    return color

#--------------------------------------------------------------------------
#-- chandra_to_ut_in_sec: change chandra time to UT in seconds from 1970.1.1
#--------------------------------------------------------------------------

def chandra_to_ut_in_sec(ctime):
    """
    change chandra time to UT in seconds from 1970.1.1
    input:  ctime   --- chandra time (seconds from 1998.1.1)
    output: out     --- ut in seconds from 1970.1.1
    """
    out   = Chandra.Time.DateTime(ctime).date
    btemp = re.split('\.', out)
    out   = time.strftime('%Y:%m:%d:%H:%M:%S', time.strptime(btemp[0], '%Y:%j:%H:%M:%S'))
    [year, mon, day , hh, mm, ss] = re.split(':', out)
    out = ut_in_secs(year, mon, day, hh, mm, ss)

    return out

#--------------------------------------------------------------------------
#-- find_index_of_time: find the index of the given time from the time list
#--------------------------------------------------------------------------

def find_index_of_time(current, utime):
    """
    find the index of the given time from the time list
    input:  current --- a time which index in the time list to be found
            utime   --- a list of time
    output: pos     --- an index of the time postion
    """

    dlen = len(utime)
    for k in range(0, dlen):
        if k+1 == dlen:
            pos = k
            break
        if (current >= utime[k]) and (current < utime[k+1]):
            pos = k
            break

    return pos

#------------------------------------------------------------------------------

if __name__ == '__main__':

    plot_gsm_orbits_xz_plane()
