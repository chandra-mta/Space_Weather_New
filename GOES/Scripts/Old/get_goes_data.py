#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################################
#                                                                                                   #
#               get_goes_data.py: get goes data and plot the data                                   #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Sep 24, 2018                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import string
import random
import operator
import time
import datetime
import numpy
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

f= open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#--- temp writing file name
#
rtail  = int(time.time())
zspace = '/tmp/zspace' + str(rtail)
#
#--- set direcotries
#
data_dir   = goes_dir + 'Data/'
templ_dir  = goes_dir + 'Scripts/Template/'
web_dir    = html_dir + 'GOES/'
plot_dir   = web_dir  + 'Plots/'
#
#--- set ftp paths etc
#
ftp1   = 'ftp://' + noaa_ftp + 'pchan/'
ftp2   = 'ftp://' + noaa_ftp + 'particle/'
froot  = [ftp1, ftp2]

fn     = ['pchan_5m.txt', 'part_5m.txt']
p_file = ['goes_protons.png', 'goes_particles.png']
u_list = ["p/cm2-s-sr-MeV", "p/cm2-s-sr"]
t_list = ['Proton Flux', 'Particle Flux']
#
#--- other setting
#
m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

#---------------------------------------------------------------------------------------------------
#-- get_goes_data: get goes data and plot the data                                                --
#---------------------------------------------------------------------------------------------------

def get_goes_data():
    """
    get goes data and plot the data
    input:  none but read from ftp://ftp.swpc.noaa.gov/pub/lists/
    output: <data_dir>/Gp_<part/pchan>_5m.txt 
            <data_dir>/Gs_<part/pchan>_5m.txt
            <plot_dir>/goes_perticls.png
            <plot_dir>/goes_protons.png
    """
#
#--- download data
#
    g_list = []

    for k in range(0, len(fn)):
#
#--- primary data
#
        out1 = data_dir + 'Gp_' + fn[k]
        cmd = "/usr/bin/lynx -source  " + froot[k] + 'Gp_' + fn[k] + "> " + out1
        #cmd = 'wget -q -O' + out1 + ' ' + froot[k] + 'Gp_' + fn[k]  
        os.system(cmd)
#
#--- secondary data
#
        out2 = data_dir + 'Gs_' + fn[k]
        cmd = "/usr/bin/lynx -source  " + froot[k] + 'Gs_' + fn[k] + "> " + out2
        #cmd = 'wget -q -O' + out2 + ' ' + froot[k] + 'Gs_' + fn[k]  
        os.system(cmd)
#
#--- find goes satellite numbers
#
        g_list.append(find_goes_num(out1))
        g_list.append(find_goes_num(out2))
#
#--- read data and plot them
#
        try:
            p_data = collect_plot_data(froot[k], fn[k], 'Gp_')
            s_data = collect_plot_data(froot[k], fn[k], 'Gs_')
    
            plot_data(p_data, s_data, g_list, u_list[k], t_list[k], k)
        except:
            pass

#---------------------------------------------------------------------------------------------------
#-- convert_to_arrays: convert data into array data                                               --
#---------------------------------------------------------------------------------------------------

def convert_to_arrays(data):
    """
    convert data into array data
    input:  data--- n line data set
    output: nave--- a linst of arrays
    """
    
    c_len = len(re.split('\s+', data[0]))
    save  = []
    for k in range(0, c_len):
        save.append([])
    
    for ent in data:
        atemp = re.split('\s+', ent)
        for k in range(0, c_len):
            save[k].append(float(atemp[k]))
#
#--- sort the array by time
#--- col 4: julian time / col 5: seconds of the day
#
    tsave  = []
    for k in range(0, len(save[0])):
        val = float(save[4][k]) + float(save[5][k]) / 86400.0
        tsave.append(val)

    tarray = numpy.array(tsave)
    inds   = tarray.argsort()

    nsave = []
    for k in range(0, c_len):

        tarray = numpy.array(save[k])
        sarray = tarray[inds[::-1]]
        nsave.append(sarray)

    return nsave

#---------------------------------------------------------------------------------------------------
#-- collect_plot_data: collect the past 3 days amounts of data                                    --
#---------------------------------------------------------------------------------------------------

def collect_plot_data(froot, fn, part):
    """
    collect the past 3 days amounts of data
    input:  froot   --- ftp path
            fn      --- file sufix
            part    --- data type
    output: adata   --- a list of arrays of data
    """
    sdata = []
    for k in range(0, 3):
        tday  = datetime.datetime.now() - datetime.timedelta(days=k)
        atemp = re.split('\s+', str(tday))
        tday  = atemp[0].replace('-', '')
        ftp   = froot + tday + '_' + part + fn

        try:
            cmd   = "/usr/bin/lynx -source  " +  ftp + '> ' + zspace
            #cmd   = 'wget -q -O' + zspace + ' ' + ftp
            os.system(cmd)
        except:
            continue

        try:
            data  = read_data_file(zspace, remove=1)
        except:
            continue
#
#--- the data start from row 26
#
        data  = data[26:]
        sdata = sdata + data

    adata = convert_to_arrays(sdata)

    return adata

#---------------------------------------------------------------------------------------------------
#-- find_goes_num: find goes satellite number                                                     --
#---------------------------------------------------------------------------------------------------

def find_goes_num(ifile):
    """
    find goes satellite number
    input:  ifile   --- data file name
    output: g_num   --- goes satellite number
    """
    
    g_num = 'nan'
    data = read_data_file(ifile)
    for ent in data:

        mc = re.search('GOES', ent)
        if mc is not None:
            atemp = re.split('GOES-', ent)
            btemp = re.split('\s+', atemp[1])
#
#--- for the case like: 5-minute  GOES-15 Energetic Proton Flux Channels
#
            if len(btemp) > 0:
                g_num = btemp[0].strip()
#
#--- for the case like: # Source: GOES-15
#
            else:
                g_num = atemp[1].strip()
            break

    return g_num
    
#---------------------------------------------------------------------------------------------------
#-- plot_data: create two panel plot                                                              --
#---------------------------------------------------------------------------------------------------

def plot_data(p_data, s_data, g_list, ylabel, title, ind):
    """
    create two panel plot
    input:  p_data  --- a list of data arrays of the primary data
            s_data  --- a list of data arrays of the secondary data
            g_list  --- a list of goes number (order: primary, secondary)
            ylabel  --- a label of y axis
            title   --- title
            ind     --- indicator of whether this is proton (0) or particle (1) plot
    output: outname --- two panel png plot    
    """

    c_list = ['fuchsia', 'green', 'blue']
#
#--- set time tick label
#
    [x_tic_pos, x_tic_lab] = create_time_label()

    xmin  = x_tic_pos[0]
    xmax  = x_tic_pos[-1]
    ymin  = 1.e-3
    ymax  = 1.e4
#
#--- convert time in yday
#
    p_time = create_time_array(p_data[0], p_data[1], p_data[2], p_data[5])
    s_time = create_time_array(s_data[0], s_data[1], s_data[2], s_data[5])
#
#--- proton case
#
    if ind == 0:
        py0 = p_data[6]             #--- p1
        py1 = p_data[7]             #--- p2
        py2 = p_data[10]            #--- p5

        sy0 = s_data[6] 
        sy1 = s_data[7] 
        sy2 = s_data[10] 

        l_list = ['P1: 0.8 - 4', 'P2: 4-9', 'P5: 40-80']

        plim1  = 300.0 /3.3
        plim2  = 8.47 / 12.0
        outname = plot_dir + 'goes_protons.png'
#
#--- particle case
#
    else:
        py0 = p_data[8]             #--- I3 (>10 Mev)
        py1 = p_data[9]             #--- I4 (>30 Mev)
        py2 = p_data[10]            #--- I5 (>50 Mev)

        sy0 = s_data[8] 
        sy1 = s_data[9] 
        sy2 = s_data[10] 

        l_list  = ['I3 > 10', 'I4 > 30', 'I5 >50 Mev']
        plim1   = 13.0
        plim2   = ''
        outname =  plot_dir + 'goes_particles.png'

    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)
#
#--- first panel
#
    ax0 = plt.subplot(211)
    create_panel(ax0, xmin, xmax, ymin, ymax, s_time, py0, py1, py2, plim1, plim2,\
                 ylabel, g_list, l_list, c_list, title, ind,  0)
#
#--- second panel
#
    ax1   = plt.subplot(212)
    create_panel(ax1, xmin, xmax, ymin, ymax, s_time, sy0, sy1, sy2, plim1, plim2,\
                 ylabel, g_list, l_list, c_list, title, ind,  1)
#
#
#--- add x ticks label only on the last panel
#
    for label in ax0.get_xticklabels():
        label.set_visible(False)

    plt.xticks(x_tic_pos, x_tic_lab)
    ax1.set_xlabel("Coordinated Universal Time")
#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(8.0, 10.0)
#
#--- save the plot in png format
#
    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')

#---------------------------------------------------------------------------------------------------
#-- create_panel: create a plot for a given panel                                                 --
#---------------------------------------------------------------------------------------------------

def create_panel(ax, xmin, xmax, ymin, ymax, s_time, y0, y1, y2, plim1, plim2, ylabel, g_list, l_list, c_list, title, ind, pan):
    """
    create a plot for a given panel
    input:  ax  --- panel
            xmin    --- x min
            xmax    --- x amx
            ymin    --- y min
            ymax    --- y max
            s_time  --- an array of x data
            y0      --- an array of y data 0
            y1      --- an array of y data 1
            y2      --- an array of y data 2
            ylabel  --- y label
            g_list  --- a list of goes numbers
            l_list  --- a list of labels of the data
            c_list  --- a list of the colors
            title   --- title
            ind     --- indicator of pronton (0) or particle (1)
            pan     --- indicator of praimary (0) or secondary (1)
    output: ax      --- panel plotted
    """
#
#--- set position parameters
#
    xmin  = float(xmin)
    xmax  = float(xmax)
    xdiff = xmax - xmin
    x1    = xmin + 0.02 * xdiff
    x2    = xmin + 0.20 * xdiff
    x3    = xmin + 0.35 * xdiff
    xpos  = xmax + 0.01 * xdiff
    yp    = 0.4 * ymax
#
#--- set panel parameters
#
    ax.set_autoscale_on(False)
    ax.set_xbound(xmin, xmax)
    ax.set_xlim(xmin=xmin, xmax=xmax,  auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
#
#--- plot lines
#
    p, = plt.semilogy(s_time, y0, color=c_list[0], marker='.', markersize=0,lw=0.8)
    p, = plt.semilogy(s_time, y1, color=c_list[1], marker='.', markersize=0,lw=0.8)
    p, = plt.semilogy(s_time, y2, color=c_list[2], marker='.', markersize=0,lw=0.8)
#
#-- add limit lines
#
    if ind == 0:
        p, = plt.semilogy([xmin, xmax], [plim1, plim1], color='red', lw=2)
        p, = plt.semilogy([xmin, xmax], [plim2, plim2], color='red', lw=2)
    else:
        p, = plt.semilogy([xmin, xmax], [plim1, plim1], color='green', lw=2)
#
#--- add labels
#
    ax.set_ylabel(ylabel)

    xdiff = xmax - xmin
    if pan == 0:
        line  = 'GOES-' + g_list[pan] + ': ' + title + ' (Primary)'
    else:
        line  = 'GOES-' + g_list[pan] + ': ' + title + ' (Secondary)'

    plt.title(line, fontsize=12, fontweight='bold', fontstyle='italic')

    text(x1, yp, l_list[0], color=c_list[0], fontsize=12)
    text(x2, yp, l_list[1], color=c_list[1], fontsize=12)
    text(x3, yp, l_list[2], color=c_list[2], fontsize=12)

    if ind == 0:
        text(xpos, 0.5 *plim1, 'P4GM\nLimit', color=c_list[1], fontsize=10)
        text(xpos, 0.5 *plim2, 'P41GM\nLimit', color=c_list[2], fontsize=10)

#---------------------------------------------------------------------------------------------------
#-- create_time_label: create literal date label                                                  --
#---------------------------------------------------------------------------------------------------

def create_time_label():
    """
    create literal date label
    input: none
    output: x_l_pos --- a list of the date positions in y-day
            x_label --- a list of the literal dates
    """

    d_label = [k_day_ago(-1)]
    for k in range(0, 3):
        d_label.append(k_day_ago(k))

    d_label.reverse()
    x_label = []
    x_l_pos = []
    for ent in d_label:
        atemp = re.split('\s+', ent)
        year  = int(atemp[0])
        mon   = int(atemp[1])
        day   = int(atemp[2])
        yday  = convert_in_yday(year, mon, day, 0)
        x_l_pos.append(int(yday))

        k     = mon -1
        lmon  = m_list[k]
        lab   = lmon + ' ' + atemp[2]
        x_label.append(lab)


    return [x_l_pos, x_label]

#---------------------------------------------------------------------------------------------------
#-- k_day_ago: find date of the k days ago. if k is negative k days from today                    --
#---------------------------------------------------------------------------------------------------

def k_day_ago(k):
    """
    find date of the k days ago. if k is negative k days from today
    input:  k       --- number of days either positive (past) or negative (future)
    output: tday    --- day in the format of <yyyy> <mm> <dd>
    """

    if k < 0:
        k = abs(k)
        tday  = datetime.datetime.now() + datetime.timedelta(days=k)
    else:
        tday  = datetime.datetime.now() - datetime.timedelta(days=k)

    atemp = re.split('\s+', str(tday))
    tday  = atemp[0].replace('-', ' ')

    return tday


#---------------------------------------------------------------------------------------------------
#-- create_time_array: create a time array in the form of y day                                   --
#---------------------------------------------------------------------------------------------------

def create_time_array(yarray, marray, darray, sarray):
    """
    create a time array in the form of y day
    input:  yarray  --- array of year values
            marray  --- array of month values
            darray  --- array of day values
            sarray  --- array of seconds of the day values
    output: arraay  --- array of y days
            if the year changes, y day will be that of the year started
    """

    byear = yarray[0]
    if isLeapYear(byear):
        base = 366
    else:
        base = 365

    save = []
    for k in range(0, len(yarray)):
        yday = convert_in_yday(yarray[k], marray[k], darray[k], sarray[k])
        if yarray[k] > byear:
            yday += base

        save.append(yday)

    return numpy.array(save)
    
#---------------------------------------------------------------------------------------------------
#-- convert_in_yday: convert the day into yday                                                    --
#---------------------------------------------------------------------------------------------------

def convert_in_yday(y, m, d, sec):
    """
    convert the day into yday
    input:  y   --- year 
            m   --- month
            d   --- day
            sec --- seconds in the day
    output: yda --- yday
    """

    m     = add_lead_zero(int(m))
    d     = add_lead_zero(int(d))
    ftime = str(int(y)) + ':' + m + ':' + d  

    yday  = time.strptime(ftime, '%Y:%m:%d')
    yday  = float(time.strftime("%j", yday))
    yday += float(sec) / 86400.0

    return yday

#---------------------------------------------------------------------------------------------------
#-- add_lead_zero: add leading 0 to make number string to two digits                              --
#---------------------------------------------------------------------------------------------------

def add_lead_zero(val):
    """
    add leading 0 to make number string to two digits
    input:  val --- value to be examine
    output: val --- adjusted string value
    """
    if int(val) < 10:
        val = '0' + str(val)
    else:
        val = str(val)

    return val

#---------------------------------------------------------------------------------------------------
#-- isLeapYear: chek the year is a leap year                                                      --
#---------------------------------------------------------------------------------------------------

def isLeapYear(year):
    """
    chek the year is a leap year
    Input:      year  ---   in full lenth (e.g. 2014, 813)
    Output:     False --- not leap year
                True  --- yes it is leap year
    """
    year = int(float(year))
    chk  = year % 4     #---- evry 4 yrs leap year
    chk2 = year % 100   #---- except every 100 years (e.g. 2100, 2200)
    chk3 = year % 400   #---- excpet every 400 years (e.g. 2000, 2400)
    
    val  = False
    if chk == 0:
        val = True
    if chk2 == 0:
        val = False
    if chk3 == 0:
        val = True
    
    return val


#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    f    = open(ifile, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    if remove > 0:
        if os.path.isfile(ifile):
            cmd = 'rm ' + ifile
            os.system(cmd)

    return data
    
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_file(ifile):

    f    = open(ifile, 'r')
    data = f.read()
    f.close()

    return data

#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    get_goes_data()
