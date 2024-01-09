#!/proj/sot/ska3/flight/bin/python

#####################################################################################################
#                                                                                                   #
#               plot_goes_data.py: get goes data and plot the data                                  #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Mar 16, 2021                                                           #
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
import numpy as np
import Chandra.Time
import urllib.request
import json
import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines
import argparse
#
#--- Defining Directory Pathing
#
HTML_DIR = "/data/mta4/www/RADIATION_new"
PLOT_DIR = os.path.join(HTML_DIR,"GOES", "Plots")

#
#--- json data
#
DLINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
CLINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json'
#
#--- protone energy designations and output file names
#
DIFF_LIST = ['1020-1860 keV',   '1900-2300 keV',   '2310-3340 keV',    '3400-6480 keV',\
             '5840-11000 keV',  '11640-23270 keV', '25900-38100 keV',  '40300-73400 keV',\
             '83700-98500 keV', '99900-118000 keV','115000-143000 keV','160000-242000 keV',\
             '276000-404000 keV']

CUM_LIST  = ['>=1 MeV',  '>=5 MeV',   '>=10 MeV', '>=30 MeV', '>=50 MeV',\
             '>=60 MeV', '>=100 MeV', '>=500 MeV']

#
#--- other setting
#
M_LIST = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#
#--- current goes satellite #
#
GSATELLITE = 'Primary'
#---------------------------------------------------------------------------------------------------
#-- plot_goes_data: get goes data and plot the data                                               --
#---------------------------------------------------------------------------------------------------

def plot_goes_data():
    """
    get goes data and plot the data
    input:  none but read from: 
        https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json
        https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json
    output: <plot_dir>/goes_particles.png
            <plot_dir>/goes_proton.png
    """
    ddata = extract_goes_data(DLINK, DIFF_LIST, 1e3)
    dtime = convert_in_ydate(ddata[0][0])
    [p1, p2, p3, p4, p5, p6] = compute_p_vals(ddata)
    plot_data(dtime, p1, p2, p4, "p/cm2-s-sr-MeV", "Proton Flux (Differential)", f"{PLOT_DIR}/goes_protons.png", 0)

    pdata = extract_goes_data(CLINK, CUM_LIST, 1.0)
    dtime = convert_in_ydate(pdata[0][0])
    i2    = pdata[2][1]
    i3    = pdata[4][1]
    i5    = pdata[6][1]
    plot_data(dtime, i2, i3, i5, "p/cm2-s-sr", "Proton Flux (Integral)", f"{PLOT_DIR}/goes_particles.png", 1)

#----------------------------------------------------------------------------
#-- extract_goes_data: extract GOES satellite flux data                    --
#----------------------------------------------------------------------------

def extract_goes_data(jlink, energy_list, factor):
    """
    extract GOES satellite flux data
    input: jlink--- json web address or file
    energy_list --- a list of energy designation 
    output: <data_dir>/<out file>
    """
    if jlink.startswith('http'):
#
#--- read json file from the web
#
        try:
            with urllib.request.urlopen(jlink) as url:
                data = json.loads(url.read().decode())
        except:
            data = []
    else:
        if os.path.isfile(jlink):
            try:
                with open(jlink) as f:
                    data = json.load(f)
            except:
                data = []
    if len(data) < 1:
        exit(1)
#
#--- go through all energy ranges
#
    elen   = len(energy_list)
    d_save = []
    for k in range(0, elen):
        t_list = []
        f_list = []
        energy = energy_list[k]

        for ent in data:
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
                flux  = float(ent['flux']) * factor
#
#--- convert time into seconds from 1998.1.1
#
                otime = ent['time_tag']
                otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                stime = int(Chandra.Time.DateTime(otime).secs)
         
                t_list.append(otime)
                f_list.append(flux)

        d_save.append([t_list, f_list])
    return d_save

#----------------------------------------------------------------------------
#-- compute_p_vals: create combined flux data for table displays           --
#----------------------------------------------------------------------------

def compute_p_vals(data):
    """
    create combined flux data for table displays
    input:  data--- a list of lists of data: [[<time>, <data1>], [<time>, <data2>],...]
    output: a list of lists of:
            p1 :  1.0MeV - 3.3MeV
            p2 :  3.4MeV - 11MeV
            p3 :  11MeV  - 38MeV
            p4 :  40MeV  - 98MeV
            p5 :  99MeV  - 143MeV
            p6 :  160MeV - 404MeV
    """
#
#--- extract flux data parts
#
    c0  = data[0][1]
    c1  = data[1][1]
    c2  = data[2][1]
    c3  = data[3][1]
    c4  = data[4][1]
    c5  = data[5][1]
    c6  = data[6][1]
    c7  = data[7][1]
    c8  = data[8][1]
    c9  = data[9][1]
    c10 = data[10][1]
    c11 = data[11][1]
    c12 = data[12][1]
#
#--- combine the data
#
    p1 = []                 #--- c0 + c1 + c2:  1.0MeV - 3.3MeV
    p2 = []                 #--- c3 + c4:   3.4MeV - 11MeV
    p3 = []                 #--- c5 + c6:   11MeV  - 38MeV
    p4 = []                 #--- c7 + c8:   40MeV  - 98MeV
    p5 = []                 #--- c9 + c10;  99MeV  - 143MeV
    p6 = []                 #--- c11 + c12: 160MeV - 404MeV
#
#--- sometime each channel has a different number of entries--- usually  no difference
#--- but occasionally 1 or 2 differnces; if that is the case use one before at the end
#
    for  k in range(0, len(c0)):
        try:
            val1 = (c0[k] *(1.85 - 1.02)  + c1[k] * (2.3 - 1.9) + c2[k]  * (3.3 - 2.3)) / (3.3 -1.0)
        except:
            pass
        try:
            val2 = (c3[k] * (6.48 - 3.4) + c4[k] * (11.0 - 5.84)) / (11 - 3.4)
        except:
            pass
        try:
            val3 = (c5[k] * (23.27-11.64) + c6[k] *(38.1 - 25.9)) / (38.1 - 11.64)
        except:
            pass
        try:
            val4 = (c7[k] * (73.4 - 40.3)+ c8[k] * (98.5 - 83.7)) / (98.5 - 40.3)
        except:
            pass
        try:
            val5 = (c9[k] * (118.0 - 99.9) + c10[k] * (143.0 - 115.0)) /( 143 - 99.9)
        except:
            pass
        try:
            val6 = (c11[k] * (242.0 - 160.0) + c12[k] * (404.0 - 276.0)) / (404. - 160.0)
        except:
            pass
        p1.append(val1)
        p2.append(val2)
        p3.append(val3)
        p4.append(val4)
        p5.append(val5)
        p6.append(val6)
    
    return [p1, p2, p3, p4, p5, p6]

#---------------------------------------------------------------------------------------------------
#-- plot_data: create two panel plot                                                              --
#---------------------------------------------------------------------------------------------------

def plot_data(dtime, py0, py1, py2, ylabel, title, outname, ind):
    """
    create two panel plot
    input:  p_data  --- a list of data arrays of the primary data
            s_data  --- a list of data arrays of the secondary data
            gsatellite  --- a list of goes number (order: primary, secondary)
            ylabel  --- a label of y axis
            title   --- title
            ind     --- indicator of whether this is proton (0) or particle (1) plot
    output: outname --- two panel png plot    
    """

    c_list = ['fuchsia', 'green', 'blue']
    c_list = ['red', 'blue', '#51FF3B']
#
#--- set time tick label
#
    [x_tic_pos, x_tic_lab] = create_time_label()

    xmin  = x_tic_pos[0]
    xmax  = x_tic_pos[-1]
#
#--- proton case
#
    if ind == 0:
        l_list = ['1-3.3MeV', '3.4-11MeV', '.  40-98MeV']

        plim1  = 300.0 /3.3
        plim2  = 8.47 / 12.0
        ymin  = 1.e-3
        ymax  = 1.e4
#
#--- particle case
#
    else:
        l_list  = ['>10MeV', '>50MeV', '. >100Mev']
        plim1   = 13.0
        plim2   = ''
        ymin  = 1.e-2
        ymax  = 1.e4

    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)
#
    ax0 = plt.subplot(111)
    create_panel(ax0, xmin, xmax, ymin, ymax, dtime, py0, py1, py2, plim1, plim2,\
                 ylabel, GSATELLITE, l_list, c_list, title, ind)

#--- add x ticks label 
#
    plt.xticks(x_tic_pos, x_tic_lab)
    ax0.set_xlabel("Coordinated Universal Time")
#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = plt.gcf()
    fig.set_size_inches(8.0, 5.0)
#
#--- save the plot in png format
#
    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')

#---------------------------------------------------------------------------------------------------
#-- create_panel: create a plot for a given panel                                                 --
#---------------------------------------------------------------------------------------------------

def create_panel(ax, xmin, xmax, ymin, ymax, s_time, y0, y1, y2, plim1, plim2, ylabel,\
                 GSATELLITE, l_list, c_list, title, ind):
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
            gsatellite  --- a list of goes numbers
            l_list  --- a list of labels of the data
            c_list  --- a list of the colors
            title   --- title
            ind     --- indicator of pronton (0) or particle (1)
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
    if ind == 0:
        yp    = 0.4 * ymax
    else:
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
    [x, y] = adjust_data_length(s_time, y0)
    p, = plt.semilogy(x, y, color=c_list[0], marker='.', markersize=0,lw=0.8)

    [x, y] = adjust_data_length(s_time, y1)
    p, = plt.semilogy(x, y, color=c_list[1], marker='.', markersize=0,lw=0.8)

    [x, y] = adjust_data_length(s_time, y2)
    p, = plt.semilogy(x, y, color=c_list[2], marker='.', markersize=0,lw=0.8)
#
#-- add limit lines
#
    if ind == 0:
        p, = plt.semilogy([xmin, xmax], [plim1, plim1], color='red', lw=2)
        p, = plt.semilogy([xmin, xmax], [plim2, plim2], color='red', lw=2)
    else:
        ax.yaxis.set_label_position("right")
        pass
#
#--- add labels
#
    ax.set_ylabel(ylabel)

    xdiff = xmax - xmin
    line  = 'GOES-R: ' + title

    plt.title(line, fontsize=12, fontweight='bold', fontstyle='italic')

    plt.text(x1, yp, l_list[0], color=c_list[0], fontsize=12)
    plt.text(x2, yp, l_list[1], color=c_list[1], fontsize=12)
    plt.text(x3, yp, l_list[2], color=c_list[2], fontsize=12)

    if ind == 0:
        plt.text(xpos, 0.5 *plim1, 'P4GM\nLimit', color=c_list[1], fontsize=10)
        plt.text(xpos, 0.5 *plim2, 'P41GM\nLimit', color=c_list[2], fontsize=10)

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def adjust_data_length(x, y):

    xlen = len(x)
    ylen = len(y)
    if xlen == ylen:
        return [x, y]
    
    elif xlen > ylen:
        x = x[:ylen]
        return  [x, y]
    
    elif ylen > xlen:
        y = y[:xlen]
        return [x, y]
    
    else:
        return [x, y]


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
        lmon  = M_LIST[k]
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

def convert_in_ydate(t_list):
    """
    convert time format from <yyyy>:<mm>:<dd>:<hh>:<mm>:<ss>: to yday
    input:  t_list      --- a list of date in <yyyy>:<mm>:<dd>:<hh>:<mm>:<ss>
    output: yday_list   --- a list of date in yday
    """
    atemp = re.split(':', t_list[0])
    byear = int(float(atemp[0]))
    if is_learyear(byear):
        base = 366
    else:
        base = 365

    yday_list = []
    for ent in t_list:
        atemp = re.split(':', ent)
        cyear = int(float(atemp[0]))
        val   = float(atemp[1])  + float(atemp[2]) / 24.0 + float(atemp[3]) / 1440.0 
#
#--- check whether the year changed during the data period
#
        if cyear > byear:
            val += base

        yday_list.append(val)

    return yday_list
    
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
    output: yday --- yday
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
#-- is_learyear: chek the year is a leap year                                                      --
#---------------------------------------------------------------------------------------------------

def is_learyear(year):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", required=False, action='store_true', help="Boolean to determine running as test.")
    args = parser.parse_args()

#
#--- Determine if running in test mode and change pathing if so
#
    if args.test:
#
#--- Path output to same location as unit tests
#
        OUT_DIR = os.path.join(os.getcwd(),"test","outTest")
        PLOT_DIR = os.path.join(OUT_DIR,"GOES", "Plots")
        os.makedirs(PLOT_DIR, exist_ok=True)
        plot_goes_data()
    else:
#
#--- Create a lock file and exit strategy in case of race conditions
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog.")
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        plot_goes_data()

#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")