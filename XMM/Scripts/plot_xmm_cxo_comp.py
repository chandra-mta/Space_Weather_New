#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#           plot_xmm_cxo_comp.py: plot xmm and cxo gsm orbits and compare                       #
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
#import astropy.io.fits  as pyfits
import numpy
import matplotlib as mpl

sys.path.append('/data/mta4/Script/Python3.10/lib/python3.10/site-packages')
from geopack import geopack

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

f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.10/MTA/')
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
#-- plot_xmm_cxo_comp: plot xmm and cxo orbits and compare               --
#--------------------------------------------------------------------------

def plot_xmm_cxo_comp():
    """
    plot xmm and cxo orbits in gsm coordinates and compare
    input:  none, but read from:
                <xmm_dir>/Data/xmm_7day.archive2
                <tle_dir>/Data/xmm.spctrk
                <tle_dir>/Data/cxo.spctrk
    output: <html_dir>/XMM/Plots/mta_plot_xmm_comp.png
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
    [x_gsm, y_gsm, z_gsm] = compute_gsm(xtime, x_eci,y_eci,z_eci)
#
#--- read cxo orbit
#
    ifile = tle_dir + 'Data/cxo.spctrk'
    data  = mcf.read_data_file(ifile)
    [ctime,cxo_x_eci,cxo_y_eci,cxo_z_eci,cxo_vx,cxo_vy,cxo_vz] = convert_to_col_data(data)
    [cxo_x_gsm, cxo_y_gsm, cxo_z_gsm] = compute_gsm(ctime, cxo_x_eci,cxo_y_eci,cxo_z_eci)
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
#--- plotting starts here
#
    plt.close('all')
    mpl.rcParams['font.size'] = 10
    props = font_manager.FontProperties(size=10)
    plt.subplots_adjust(hspace=0.09)
#
#--- plotting range is from 5 days before to 2 day after today
#
    xmin = this_doy - 4
    xmax = this_doy + 3
#
#--- top panel: radiation plot
#
    ymin = 1
    ymax = 1000000
    ax0 = plt.subplot(411)
    ax0.set_autoscale_on(False)
    ax0.set_xbound(xmin, xmax)
    ax0.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax0.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax0.set_facecolor('xkcd:black')
#
#--- plotting data
#
    plt.semilogy(atime_d, le0,  color='moccasin',    marker='.', ms=1, lw=0)
    plt.semilogy(atime_d, le1,  color='aqua',        marker='.', ms=1, lw=0)
    plt.semilogy(atime_d, hes1, color='red',         marker='.', ms=1, lw=0)
    plt.semilogy(atime_d, hes2, color='orange',      marker='.', ms=1, lw=0)
    plt.semilogy(atime_d, hec,  color='greenyellow', marker='.', ms=1, lw=0)
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
    xpos1 = xmin + 0.55 * xdiff
    xpos2 = xmin + 0.65 * xdiff
    xpos3 = xmin + 0.75 * xdiff
    xpos4 = xmin + 0.85 * xdiff
    xpos5 = xmin + 0.95 * xdiff
    ypos  = 300000
    plt.text(xpos1, ypos, 'le0',  color='moccasin',   size=9)
    plt.text(xpos2, ypos, 'le1',  color='aqua',       size=9)
    plt.text(xpos3, ypos, 'hes1', color='red',        size=9)
    plt.text(xpos4, ypos, 'hes2', color='orange',     size=9)
    plt.text(xpos5, ypos, 'hec',  color='greenyellow', size=8)
    ax0.set_ylabel('Cnts/Sec')
#
#--- second panel: GSM X plots
#
    ymin = -20
    ymax =  20
    ax1 = plt.subplot(412,sharex=ax0)
    ax1.set_autoscale_on(False)
    ax1.set_xbound(xmin, xmax)
    ax1.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax1.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax1.set_facecolor('xkcd:black')
#
#--- plot data
#
    plt.plot(xtime_d, x_gsm,     color='orange', lw = 1)
    plt.plot(ctime_d, cxo_x_gsm, color='aqua',   lw = 1)
    plt.plot([c_pos,c_pos], [ymin, ymax], ls='--', lw=1, color='white')
#
#--- plotting current position
#
    plt.plot([xmin,xmax], [0,0], ls =':', lw=0.8, color='white')
#
#--- adding labels
#
    ax1.set_ylabel('X_GSM(Re)')
    ypos = 0.80 * ymax
    plt.text(xpos3, ypos, 'XMM',  color='orange',   size=9)
    plt.text(xpos4, ypos, 'CXO',  color='aqua',     size=9)
#
#--- third panel: GSM Y plot
#
    ax2 = plt.subplot(413,sharex=ax0)
    ax2.set_autoscale_on(False)
    ax2.set_xbound(xmin, xmax)
    ax2.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax2.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax2.set_facecolor('xkcd:black')

    plt.plot(xtime_d, y_gsm,     color='orange', lw = 1)
    plt.plot(ctime_d, cxo_y_gsm, color='aqua',   lw = 1)

    plt.plot([c_pos,c_pos], [ymin, ymax], ls='--', lw=1, color='white')

    plt.plot([xmin,xmax], [0,0], ls =':', lw=0.8, color='white')
    ax2.set_ylabel('Y_GSM(Re)')
#
#--- fourth panel: GSM Z plot
#
    ax3 = plt.subplot(414,sharex=ax0)
    ax3.set_autoscale_on(False)
    ax3.set_xbound(xmin, xmax)
    ax3.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax3.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax3.set_facecolor('xkcd:black')

    plt.plot(xtime_d, z_gsm,     color='orange', lw = 1)
    plt.plot(ctime_d, cxo_z_gsm, color='aqua',   lw = 1)

    plt.plot([c_pos,c_pos], [ymin, ymax], ls='--', lw=1, color='white')

    plt.plot([xmin,xmax], [0,0], ls =':', lw=0.8, color='white')
    ax3.set_ylabel('Z_GSM(Re)')
#
#--- add x ticks label only on the last panel
#
    for i in range(0, 4):
        ax = 'ax' + str(i)
        if i != 3:
            line = eval("%s.get_xticklabels()" % (ax))
            for label in  line:
                label.set_visible(False)
        else:
            pass
#
#--- x axis label
#
    line = 'Time (DOY Year: ' + str(this_year) + ')'
    ax3.set_xlabel(line)
#
#---set plot surface
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 7.0)
#
#--- save the plot
#
    outname = html_dir + 'XMM/Plots/mta_plot_xmm_comp.png'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        outname = test_out + "/" + os.path.basename(outname)
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
        xgm = xgsm / earth
        ygm = ygsm / earth
        zgm = zgsm / earth
        gx.append(xgm)
        gy.append(ygm)
        gz.append(zgm)

    gx = numpy.array(gx)
    gy = numpy.array(gy)
    gz = numpy.array(gz)

    return [gx, gy, gz]


#------------------------------------------------------------------------------

if __name__ == '__main__':

    plot_xmm_cxo_comp()
