#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#       create_gsm_gse_orbit_plots.py: create gsm and gse orbit plots           #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Mar 03, 2020                                           #
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
from mpl_toolkits.mplot3d import Axes3D
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

data_dir = gsm_plot_dir + 'Data/'

#--------------------------------------------------------------------------------
#-- create_gsm_gse_orbit_plots: create gsm and gse orbit plots                 --
#--------------------------------------------------------------------------------

def create_gsm_gse_orbit_plots():
    """
    create gsm and gse orbit plots
    input:  none, but read from:
            <ephem_dir>/Data/PE.EPH.gsme_in_Re
    output: <htm_dir>/Orbit/Plots/<gsm/gse>ORBIT.png
    """
#
#--- read data
#
    [otime, xgsm, ygsm, zgsm, xgse, ygse, zgse] = read_gsm_gse_data()
#
#--- plot data
#
    create_orbit_plot('gsm', otime, xgsm, ygsm, zgsm)
    create_orbit_plot('gse', otime, xgse, ygse, zgse)

#--------------------------------------------------------------------------------
#-- read_gsm_gse_data: read PE.EPH.gsme_in_Re and select out data              --
#--------------------------------------------------------------------------------

def read_gsm_gse_data():
    """
    read PE.EPH.gsme_in_Re and select out the potion that contains the
    data from today to the end of 2nd day from today
    input:  <ephem_dir>/Data/PE.EPH.gsme_in_Re
    output: <gsm_dir>/Data/gs_data_2_day
            return:  [otime, xgsm, ygsm, zgsm, xgse, ygse, zgse]
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
#
#--- there are two data sets with different starting and stopping time
#
    start2 = Chandra.Time.DateTime(stday).secs
    start1 = start2 - 86400.0
    stop1  = start2 + 86400.0
    stop2  = start2 + 2.0 * 86400.0
#
#--- read data
#
    ifile = ephem_dir + 'Data/PE.EPH.gsme_in_Re'
    with open(ifile, 'r') as f:
        data  = [line.strip() for line in f.readlines()]
    
    otime = []
    xgsm  = []
    ygsm  = []
    zgsm  = []
    xgse  = []
    ygse  = []
    zgse  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        atime = float(atemp[0])
        if atime < start1:
            continue
        elif atime > stop2:
            break
        else:
            if atime < stop1:
                otime.append(atime)
                xgsm.append(float(atemp[1]))
                ygsm.append(float(atemp[2]))
                zgsm.append(float(atemp[3]))
                xgse.append(float(atemp[4]))
                ygse.append(float(atemp[5]))
                zgse.append(float(atemp[6]))

            if atime >= start2:
                line = ent + '\n'
    
    out = data_dir + 'gs_data_2_day'
    with open(out, 'w') as fo:
        fo.write(line)
    
    return [otime, xgsm, ygsm, zgsm, xgse, ygse, zgse]

#--------------------------------------------------------------------------------
#-- create_orbit_plot: plot an orbital data                                   ---
#--------------------------------------------------------------------------------

def create_orbit_plot(dset, otime, x, y, z):
    """
    plot an orbital data
    input:  dset    --- either 'gsm' or 'gse'
            otime   --- a list of time
            x       --- a list of x position
            y       --- a list of y position
            z       --- a list of z position
    output: <html_dir>/Orbit/Plots/<dset>ORBIT.png
    """
#
#--- create data set to use 2D plot
#
    xb = []
    yb = []
    zb = []
    for k in range(0, len(x)):
        xb.append(20)
        yb.append(-20)
        zb.append(-20)

    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)
#
#--- tell it that this is 3D plotting
#
    fig = plt.figure()
    ax  = fig.gca(projection='3d')
    ax.set_xlim(-20, 20)
    ax.set_ylim(-20, 20)
    ax.set_zlim(-20, 20)
#
#--- plot Earth position in 3D and 2D serfaces
#
    ax.plot([0],   [0],   [0], marker='o', ms='8', color='orange', alpha=0.5)
    ax.plot([-21], [0],   [0], marker='o', ms='8', color='orange', alpha=0.5)
    ax.plot([0],  [21],   [0], marker='o', ms='8', color='orange', alpha=0.5)
    ax.plot([0],   [0], [-21], marker='o', ms='8', color='orange', alpha=0.5)
#
#--- connect positions with thin lines
#
    ax.plot([0, 0],   [0, 0],  [0, -20], lw=1, ls=':', color='orange')
    ax.plot([0, 0],   [0, 20], [0, 0],   lw=1, ls=':', color='orange')
    ax.plot([0, -20], [0, 0],  [0, 0],   lw=1, ls=':', color='orange')
#
#--- plot 2D surface plots
#
    ax.plot(yb, x,  z, lw=1.5, ls='--', color='lime')
    ax.plot(y,  xb, z, lw=1.5, ls='--', color='lime')
    ax.plot(y,  x,  zb,lw=1.5, ls='--', color='lime')
#
#--- plot 3D plot
#
    ax.plot(y,  x,  z, lw=2,          color='lime')
#
#--- find the current satellite position
#
    pos = find_current_pos(otime)
    xc  = x[pos]
    yc  = y[pos]
    zc  = z[pos]
#
#--- plot the current satellite position in 3D
#
    ax.plot([yc], [xc], [zc], marker='*', ms='8', color='blue')
#
#--- connect positions with thin lines
#
    ax.plot([yc, yc],  [xc, xc], [zc, -20], lw=1, ls=':', color='lime')
    ax.plot([yc, yc],  [xc, 20], [zc, zc],  lw=1, ls=':', color='lime')
    ax.plot([yc, -20], [xc, xc], [zc, zc],  lw=1, ls=':', color='lime')
#
#--- ax labels
#
    xlab = 'X' + dset.upper()
    ylab = 'Y' + dset.upper()
    zlab = 'Z' + dset.upper()
#
#--- need to rotate the labels to match the axes
#
    ax.set_xlabel(ylab, rotation=-22)
    ax.set_ylabel(xlab, rotation=55)
    ax.set_zlabel(zlab, rotation=90)
#
#--- put explanations of the markers (in 2D surface)
#
    mpl.rcParams['font.size'] = 10
    out   = Chandra.Time.DateTime(otime[pos]).date
    otemp = re.split('\.', out)
    ctext = 'Current Position (' + otemp[0] + ')'
    ax.text2D(0.05, 0.95, ctext,   color='blue', transform=ax.transAxes)
    ax.text2D(0.05, 0.90, 'Earth', color='orange',  transform=ax.transAxes)
#
#-- add tick label on only the major ticks
#
    major_ticks= np.arange(-20, 21, 10)
    minor_ticks= np.arange(-20, 21, 5)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)
    ax.set_yticks(major_ticks)
    ax.set_yticks(minor_ticks, minor=True)
    ax.set_zticks(major_ticks)
    ax.set_zticks(minor_ticks, minor=True)
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)
#
#--- set the size of the plotting area in inch
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 5.0)
#
#--- save the plot in png format
#
    outname = html_dir + 'Orbit/Plots/' + dset.upper()+ 'ORBIT.png'
    #outname = dset.upper()+ 'ORBIT.png'
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

#--------------------------------------------------------------------------------

if __name__ == "__main__":

    create_gsm_gse_orbit_plots()
