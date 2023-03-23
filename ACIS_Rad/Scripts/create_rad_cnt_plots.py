#!/proj/sot/ska3/flight/bin/python

#####################################################################################################
#                                                                                                   #
#           create_rad_cnt_plots.py: create radiation count rate plots                              #
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
#
#--- temp writing file name
#
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- others
#
colorList = ['red','blue', 'lime', 'green', 'maroon']
m_list    = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

#----------------------------------------------------------------------------------------------------------
#-- plot_radiation_counts: create radiation count rate plots                                             --
#----------------------------------------------------------------------------------------------------------

def plot_radiation_counts(start, stop, outname):
    """
    create radiation count rate plots 
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- stopping time in seconds from 1998.1.1
            outname --- output png file name
    output: outname 
    """
#
#--- check time format
#
    try:
        start = int(float(start))
    except:
        start = int(Chandra.Time.DateTime(start).secs) + 2.0

    try:
        stop  = int(float(stop))
    except:
        stop  = int(Chandra.Time.DateTime(stop).secs)

#
#--- set plotting plate
#
    plt.close("all")
    mpl.rcParams['font.size'] = 11 
    props = font_manager.FontProperties(size=6)
    plt.subplots_adjust(hspace=0.06)
#
#--- find starting year
#
    [byear, bydate] = convert_time_format3(start)
#
#--- goes data: the data set changed at Mar 01, 2020
#
    ax1       = plt.subplot(4, 1, 1)
    if stop <= 699411594:                           #--- Mar 01, 2020 01:00:00
        title     = 'GOES Primary Rates'
        ylabel    = 'particles/cm^2 Sr s MeV'
        pdata     = read_goes_data(start, stop, byear)
        dname_set = ['0.8-4','4-9','40-80', '(in Kev)']
        plot_strip(ax1, start, stop, 1.0e-2, 1.0e3, pdata[0], pdata[1:], dname_set, title, ylabel)
    else:
        title     = 'GOES R Rates'
        ylabel    = 'particles/cm^2 Sr s MeV'
        pdata     = read_goes_data_r(start, stop, byear)
        dname_set = ['1.0-3.3','3.4-11','40-98', '(in Kev)']
        plot_strip(ax1, start, stop, 1.0e-4, 1.0e3, pdata[0], pdata[1:], dname_set, title, ylabel)
#
#--- ace data
#
    pdata     = read_ace_data(start,  stop, byear)
    dname_set = ['47-65','112-187','310-580', '761-1220', '1060-1810', '(in Kev)']
    title     = 'ACE Rates'
    ylabel    = 'particles/cm^2 Sr s MeV'
    ax2       = plt.subplot(4, 1, 2)
    plot_strip(ax2, start, stop, 1.0e-4, 1.0e6, pdata[0], pdata[1:], dname_set, title, ylabel)
#
#--- xmm data
#
    pdata     = read_xmm_data(start,  stop)
    dname_set = ['LE1', 'LE2', 'HES1', 'HES2', 'HESC']
    title     = 'XMM Rates'
    ylabel    = 'Counts/sec'
    ax3       = plt.subplot(4, 1, 3)
    plot_strip(ax3, start, stop, 1.0e-1, 1.0e6, pdata[0], pdata[1:], dname_set, title, ylabel)
#
#--- acis data
#
    pdata     = read_cti_data(start,  stop)
    dname_set = ['CCD5', 'CCD6', 'CCD7']
    title     = 'ACIS Rates'
    ylabel    = 'Counts/sec'
    xlabel    = 'Year Date (Year: ' +  str(byear) + ')'
    ax4       = plt.subplot(4, 1, 4)
    t_list    = [pdata[0][0], pdata[1][0], pdata[2][0]]
    d_list    = [pdata[0][1], pdata[1][1], pdata[2][1]]
    plot_strip(ax4, start, stop, 0, 50.0, t_list, d_list, dname_set, title, ylabel, xname=xlabel, ylog=0)
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
#-- plot_strip: create plot panel data                                                                  ---
#----------------------------------------------------------------------------------------------------------

def plot_strip(ax, xmin, xmax, ymin, ymax, stime, data_set, dname_set, title, yname, xname = '', ylog=1):
    """
    create plot panel data
    input:  ax          --- ax name
            xmin        --- x min in seconds from 1998.1.1
            xmax        --- x max in seconds from 1998.1.1
            ymin        --- y min
            ymax        --- y max
            stime       --- a list of time in seconds from 1998.1.1; this can be a list of list of time
            data_set    --- a list of lists of data
            dname_set   --- a list of data names
            title       --- title of the plot
            yname       --- y label nanme
            xname       --- x label name; default:''
            ylog        --- indicator to set y axis in log 1: yes/0: no
    output: plot panel data
    """
#
#--- convert time into ydate
#
    if isinstance(stime[0], list):
        dchk = 1
        t_list = []
        for ent in stime:
            try:
                out = convert_s_list_to_yd_list(ent)
            except:
                out = []
            t_list.append(out)
    else:
        dchk = 0
        ytime         = convert_s_list_to_yd_list(stime)

    [year1, xmin] = convert_time_format3(xmin)
    [year2, xmax] = convert_time_format3(xmax)
    if year2 > year1:
        if isLeapYear(year1) == 1:
            base = 366
        else:
            base = 365
        xmax += base
#
#--- set plotting range
#
    ax.set_autoscale_on(False) 
    ax.set_xbound(xmin,xmax) 
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
#
#--- plot data; either semi log or none log format
#
    d_num = len(data_set)
    for k in range(0, d_num):
        if ylog == 1:
            if dchk == 0:
                if len(ytime) > 0:
                    plt.semilogy(ytime, data_set[k], color=colorList[k], marker='.', markersize=1, lw=0)
            else:
                if len(t_list[k]) > 0:
                    plt.semilogy(t_list[k], data_set[k], color=colorList[k], marker='.', markersize=1, lw=0)
        else:
            if dchk == 0:
                if len(ytime) > 0:
                    plt.plot(ytime, data_set[k], color=colorList[k], marker='.', markersize=1, lw=0)
            else:
                if len(t_list[k]) > 0:
                    plt.plot(t_list[k], data_set[k], color=colorList[k], marker='.', markersize=1, lw=0)

#
#--- put axis label
#
    ylabel(yname)
#
#--- only when xlabel is given, put x tix labels
#
    if xname != '':
        xlabel(xname)
    else:
        line = ax.get_xticklabels()
        for label in line:
            label.set_visible(False)
#
#--- title of the plot
#
    xdiff = xmax - xmin
    ydiff = ymax - ymin
    xpos  = xmin + 0.05 * xdiff
    if ylog == 1:
        ypos = 0.1 * ymax
    else:
        ypos = ymax - 0.20 * xdiff
    plt.text(xpos, ypos, title)
#
#--- label of the data; right side of the plot
#
    xpos  = xmax + 0.01 * xdiff
    for k in range(0, len(dname_set)):
        if ylog == 1:
            ypos = 0.2 * ymax / (10**k)

        else:
            ypos = 0.9 * ymax - 0.2 *k * ydiff
#
#--- if there is an explanatory content (assume that it is in "()"), use black font
#
        mc = re.search('\(', dname_set[k])
        if mc is not None:
            plt.text(xpos, ypos, dname_set[k], color='black')
        else:
            plt.text(xpos, ypos, dname_set[k], color=colorList[k])

#----------------------------------------------------------------------------------------------------------
#-- read_goes_data: read GOES Data between start and stop time period                                    --
#----------------------------------------------------------------------------------------------------------

def read_goes_data(start, stop, byear):
    """
    read GOES Data between start and stop time period
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- starting time in seconds from 1998.1.1
            byear   --- year of the starting time
    output: list of data: goes_time, goes_p1, goes_p2, goes_p5
    """
    goesfile  = goes_dir + 'Data/goes_data.txt'
    data      = read_data_file(goesfile)
    goes_time = []
    goes_p1   = []
    goes_p2   = []
    goes_p5   = []
    stime     = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        if int(atemp[0]) < byear:
            continue
        elif stime > stop:
            break
        else:
            stime = convert_time_format(atemp[0], atemp[1], atemp[2], atemp[3])
            goes_time.append(stime)
            goes_p1.append(float(atemp[6]))
            goes_p2.append(float(atemp[7]))
            goes_p5.append(float(atemp[10]))


#----------------------------------------------------------------------------------------------------------
#-- read_goes_data_r: read GOES Data between start and stop time period  (newer data set)                --
#----------------------------------------------------------------------------------------------------------

def read_goes_data_r(start, stop, byear):
    """
    read GOES Data between start and stop time period (newer data set)
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- starting time in seconds from 1998.1.1
            byear   --- year of the starting time
    output: list of data: goes_time, goes_p1, goes_p2, goes_p4
                p1 :  1.0MeV - 3.3MeV
                p2 :  3.4MeV - 11MeV
                p4 :  40MeV  - 98MeV
    """
    goesfile  = goes_dir + 'Data/goes_data_r.txt'
    data      = read_data_file(goesfile)

    goes_time = []
    goes_p1   = []
    goes_p2   = []
    goes_p4   = []
    for ent in data[2:]:        #--- the first two lines are headers
        adat  = re.split('\s+', ent)

        try:
            stime = Chandra.Time.DateTime(adat[0]).secs
            if stime < start:
                continue
            goes_time.append(stime)
        except:
            continue

        c0    = float(adat[1])
        c1    = float(adat[2])
        c2    = float(adat[3])
        c3    = float(adat[4])
        c4    = float(adat[5])
        c7    = float(adat[8])
        c8    = float(adat[9])
#
#--- combine the data for the bands
#
        val = (c0 *(1.85 - 1.02)  + c1 * (2.3 - 1.9) + c2  * (3.3 - 2.3)) / (3.3 -1.0)
        goes_p1.append(val)

        val = (c3 * (6.48 - 3.4) + c4 * (11.0 - 5.84)) / (11 - 3.4)
        goes_p2.append(val)

        val = (c7 * (73.4 - 40.3)+ c8 * (98.5 - 83.7)) / (98.5 - 40.3)
        goes_p4.append(val)


    return [goes_time, goes_p1, goes_p2, goes_p4]

#----------------------------------------------------------------------------------------------------------
#-- read_ace_data: read ACE Data between start and stop time period                                      --
#----------------------------------------------------------------------------------------------------------

def read_ace_data(start, stop, byear):
    """
    read ACE Data between start and stop time period
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- starting time in seconds from 1998.1.1
            byear   --- year of starting time
    output: list of data: ace_time, ace_ch1, ace_ch2, ace_ch3, ace_ch4, ace_ch5
    """
    acefile  = ace_dir  + 'Data/longterm/ace_data.txt'
    data     = read_data_file(acefile)
    ace_time = []
    ace_ch1  = []
    ace_ch2  = []
    ace_ch3  = []
    ace_ch4  = []
    ace_ch5  = []
    stime    = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        if int(atemp[0])  < byear:
            continue
        elif stime > stop:
            break
        else:
            stime = convert_time_format(atemp[0], atemp[1], atemp[2], atemp[3])
            ace_time.append(stime)
            ace_ch1.append(float(atemp[10]))
            ace_ch2.append(float(atemp[11]))
            ace_ch3.append(float(atemp[12]))
            ace_ch4.append(float(atemp[13]))
            ace_ch5.append(float(atemp[14]))

    return [ace_time, ace_ch1, ace_ch2, ace_ch3, ace_ch4, ace_ch5]

#----------------------------------------------------------------------------------------------------------
#-- read_xmm_data: read XMM Data between start and stop time period                                      --
#----------------------------------------------------------------------------------------------------------

def read_xmm_data(start, stop):
    """
    read XMM Data between start and stop time period
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- starting time in seconds from 1998.1.1
    output: list of data: le0, le1, le2, hes0, hes1, hes2. hesc
    """
#
#--- xmm data
#
    xmmfile  = xmm_dir  + 'Data/xmm.archive'
    data     = read_data_file(xmmfile)
    xmm_time = []
    le0      = []
    le1      = []
    le2      = []
    hes0     = []
    hes1     = []
    hes2     = []
    hesc     = []
    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            stime = float(atemp[0])
        except:
            continue
        if stime < start:
            continue
        elif stime > stop:
            continue
            #break
        else:
            try:
                xmm_time.append(stime)
                #le0.append(float(atemp[1]))
                le1.append(float(atemp[2]))
                le2.append(float(atemp[3]))
                #hes0.append(float(atemp[4]))
                hes1.append(float(atemp[5]))
                hes2.append(float(atemp[6]))
                hesc.append(float(atemp[7]))
            except:
                continue

    return [xmm_time, le1, le2, hes1, hes2, hesc]

#----------------------------------------------------------------------------------------------------------
#-- read_cti_data: read ACIS Data between start and stop time period                                    ---
#----------------------------------------------------------------------------------------------------------

def read_cti_data(start, stop):
    """
    read ACIS Data between start and stop time period
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- starting time in seconds from 1998.1.1
    output: list of data: ccd5, ccd6, ccd7
    """
    #ctifile     = mta_dir  + 'Data/cti_data.txt'
    ctifile  = '/data/mta4/www/DAILY/mta_rad/cti_data.txt'
    data     = read_data_file(ctifile)
    cti_start = []
    cti_stop  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            stime = float(atemp[0])
        except:
            stime = convert_time_format2(atemp[0])
        if stime < start:
            continue
        elif stime > stop:
            break
        else:
            etime = convert_time_format2(atemp[6])
            cti_start.append(stime)
            cti_stop.append(etime)
#
#--- find path names to the acis dose data for the given data period
#
    f_list = find_acis_does_files(start, stop)
#
#--- read ccd does data
#
    ccd5   = read_ccd_dose('ccd5', f_list, start, stop)
    ccd6   = read_ccd_dose('ccd6', f_list, start, stop)
    ccd7   = read_ccd_dose('ccd7', f_list, start, stop)
#
#--- select does data while cti measurements are going on
#
#    ccd5   = select_ccd_dose(ccd5, cti_start, cti_stop)
#    ccd6   = select_ccd_dose(ccd6, cti_start, cti_stop)
#    ccd7   = select_ccd_dose(ccd7, cti_start, cti_stop)

    return [ccd5, ccd6, ccd7]

#----------------------------------------------------------------------------------------------------------
#-- convert_time_format: given <yyyy> <mm> <dd> <hh>:<mm> time data, convert it to seconds from 1998.1.1 --
#----------------------------------------------------------------------------------------------------------

def convert_time_format(a0, a1, a2, a3):
    """
    given <yyyy> <mm> <dd> <hh>:<mm> time data, convert it to seconds from 1998.1.1
    input:  a0  --- year
            a1  --- month
            a2  --- month date
            a3  --- <hh>:<mm>
    output: out --- time in seconds from 1998.1.1
    """

    ltime = a0 + ':' + a1 + ':' + a2 + ':' + a3[0] + a3[1] + ':' + a3[2] + a3[3] + ':00'
    date_obj = time.strptime(ltime,   '%Y:%m:%d:%H:%M:%S')
    out      = time.strftime('%Y:%j:%H:%M:%S', date_obj)
    out      = int(Chandra.Time.DateTime(out).secs)

    return out

#----------------------------------------------------------------------------------------------------------
#-- convert_time_format2: convert time in %Y-%m-%dT%H:%M:%S into seconds from 1998.1.1                   --
#----------------------------------------------------------------------------------------------------------

def convert_time_format2(ltime):
    """
    convert time in %Y-%m-%dT%H:%M:%S into seconds from 1998.1.1
    input:  ltime   --- time in Y-%m-%dT%H:%M:%S format
    output: out     --- time in seconds from 1998.1.1
    """

    date_obj = time.strptime(ltime,   '%Y-%m-%dT%H:%M:%S')
    out      = time.strftime('%Y:%j:%H:%M:%S', date_obj)
    out      = int(Chandra.Time.DateTime(out).secs)

    return out

#----------------------------------------------------------------------------------------------------------
#-- convert_time_format3: convert time in seconds from 1998.1.1 to year and ydate                        --
#----------------------------------------------------------------------------------------------------------

def convert_time_format3(stime):
    """
    convert time in seconds from 1998.1.1 to year and ydate
    input:  stime   --- time in seconds from 1998.1.1
    output: [year, yday]    --- yday in fractional day
    """

    out   = Chandra.Time.DateTime(stime+1.0).date
    atemp = re.split(':', out)
    year  = int(atemp[0])
    yday  = float(atemp[1])
    hh    = float(atemp[2])
    mm    = float(atemp[3])
    ss    = float(atemp[4])
    yday += hh / 24.0 + mm / 1440.0 + ss / 86400.0

    return [year, yday]

#----------------------------------------------------------------------------------------------------------
#-- convert_s_list_to_yd_list: convert a list of time in seconds from 1998.1.1 to a list of ydate        --
#----------------------------------------------------------------------------------------------------------

def convert_s_list_to_yd_list(s_list):
    """
    convert a list of time in seconds from 1998.1.1 to a list of ydate
    input:  s_list  --- a list of time in seconds from 1998.1.1
    output: yd_list --- a list of time in fractional ydate
    """

    out   = Chandra.Time.DateTime(s_list[0] +2.0).date
    atemp = re.split(':', out)
    syear = int(atemp[0])

    if isLeapYear(syear) == 1:
        base = 366
    else:
        base = 365

    yd_list = []
    for ent in s_list:
        [year, yday] = convert_time_format3(ent)
        if year > syear:
            yday += base

        yd_list.append(yday)

    return yd_list

#----------------------------------------------------------------------------------------------------------
#-- find_acis_does_files: find acis does data file names of a given time period                          --
#----------------------------------------------------------------------------------------------------------

def find_acis_does_files(start, stop):
    """
    find acis does data file names of a given time period
    input:  start   --- starting time in seconds from 1998.1.1
            stop    --- stopping time in seconds from 1998.1.1
    output: f_list  --- a list of data file names
    """

    does_dir    = '/data/mta/Script/ACIS/Count_rate/Data/'

    [syr, smon] = find_year_mon(start)
    [eyr, emon] = find_year_mon(stop)

    f_list = []
    if syr == eyr:
        for k in range(smon, emon+1):
            mon = m_list[k-1]
            path = does_dir + mon.upper() + str(syr)
            f_list.append(path)
    else:
        for k in range(smon, 13):
            mon = m_list[k-1]
            path = does_dir + mon.upper() + str(syr)
            f_list.append(path)
        for k in range(1, emon+1):
            mon = m_list[k-1]
            path = does_dir + mon.upper() + str(eyr)
            f_list.append(path)

    return f_list

#----------------------------------------------------------------------------------------------------------
#-- find_year_mon: find year and month from the time in seconds from 1998.1.1                            --
#----------------------------------------------------------------------------------------------------------

def find_year_mon(stime):
    """
    find year and month from the time in seconds from 1998.1.1
    input:  stime   --- time in seconds from 1998.1.1
    output: yr, mon --- year and month
    """
    try:
        ltime  = Chandra.Time.DateTime(stime).date
        mc     = re.search('\.', ltime)
        if mc is not None:
            atemp = re.split('\.', ltime)
            ltime = atemp[0]

        d_obj  = time.strptime(ltime, "%Y:%j:%H:%M:%S")
        out    = time.strftime('%Y:%m', d_obj)
        atemp  = re.split(':', out)
        yr     = int(atemp[0])
        mon    = int(atemp[1])
    except:
        yr     = 0
        mon    = 0

    return [yr, mon]

#----------------------------------------------------------------------------------------------------------
#-- read_ccd_dose: read acis ccd does data                                                               --
#----------------------------------------------------------------------------------------------------------

def read_ccd_dose(ccd, f_list, start, stop):
    """
    read acis ccd does data
    input:  ccd     --- ccd name
            f_list  --- a list of acis does file names to be used
            start   --- starting time in seconds from 1998.1.1
            stop    --- stopping time in seconds from 1998.1.1
    output: t_list  --- a list of time in seconds from 1998.1.1
            d_list  --- a list of does data
    """

    t_list = []
    d_list = []
    for path in f_list:
        ifile = path  + '/' + ccd
        xxx = 999
        if xxx == 999:
        #try:
            data  = read_data_file(ifile)
        else:
        #except:
            return [[],[]]

        for ent in data:
            atemp = re.split('\s+', ent)
            xxx = 999
            if xxx == 999:
            #try:
                stime = float(atemp[0])
            else:
            #except:
                stime = dom_to_chandra_time(atemp[0])
            if stime < start:
                continue
            elif stime > stop:
                break
            else:
                t_list.append(stime)
                d_list.append(float(atemp[1]) / 300.0)


    return [t_list, d_list]

#----------------------------------------------------------------------------------------------------------
#-- select_ccd_dose: select out the does data for given data periods                                    ---
#----------------------------------------------------------------------------------------------------------

def select_ccd_dose(ccd, cti_start, cti_stop):
    """
    select out the does data for given data periods
    input:  ccd         --- a list of lists of ccd does data (time, dose)
            cti_start   --- a list of cti measurement starting time in seconds from 1998.1.1
            cti_stop    --- a list of cti measurement stopping time in seconds from 1998.1.1
    output: nt_list     --- a list of time in seconds from 1998.1.1
            nd_list     --- a list of does data
    """

    nt_list = []
    nd_list = []
    cstart  = 0
    cnum    = len(ccd[0])
    for k in range(0, len(cti_start)):
        for n in range(cstart, cnum):
            if ccd[0][n] < cti_start[k]:
                continue
            elif ccd[0][n] > cti_stop[k]:
                cstart = n - 10
                if cstart < 0:
                    cstart = 0
                break
            else:
                nt_list.append(ccd[0][n])
                nd_list.append(ccd[1][n])

    return [nt_list, nd_list]

#----------------------------------------------------------------------------------------------------------
#-- dom_to_chandra_time: convert time in dom to time in seconds from 1998.1.1                            --
#----------------------------------------------------------------------------------------------------------

def dom_to_chandra_time(dom):
    """
    convert time in dom to time in seconds from 1998.1.1
    input:  dom     --- time in day of mission
    output: stime   --- time in seconds from 1998.1.1
    """

    dom  = float(dom)

    idom = int(dom)
    fraq = dom - idom

    idom += 202
    year  = 1999
    found = 0
    while(found == 0):
        if isLeapYear(year) == 1:
            base = 366
        else:
            base = 365

        idom -= base
        if idom < 0:
            ydate = idom + base
            found = 1
            break
        year += 1


    lydate = str(ydate)
    if ydate < 10:
        lydate = '00' + lydate
    elif ydate < 100:
        lydate = '0'  + lydate

    atemp = fraq * 24.0
    hh    = int(atemp)
    diff  = (atemp - hh) * 60.0
    mm    = int(diff)
    diff  = (diff - mm) * 60.0
    ss    = int(diff)
    
    lhh   = str(hh)
    if hh < 10:
        lhh = '0' + lhh
    lmm   = str(mm)
    if mm < 10:
        lmm = '0' + lmm
    lss   = str(ss)
    if ss < 10:
        lss = '0' + lss

    ltime = str(year) + ':' + lydate + ':' + lhh + ':' + lmm + ':' + lss
    stime = Chandra.Time.DateTime(ltime).secs

    return stime

#----------------------------------------------------------------------------------------------------------
#-- read_data_file: read data file                                                                      ---
#----------------------------------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):
    """
    read data file
    input:  ifile   --- file name
            remove  --- if 1, remove the file after reading; otherwise keep it
    output: data    --- a list of data
    """

    if os.path.isfile(ifile):
        with  open(ifile, 'r') as f:
            data = [line.strip() for line in f.readlines()]
    else:
        data = []

    if remove == 1:
        cmd = 'rm -rf ' + ifile
        os.system(cmd)

    return data

#----------------------------------------------------------------------------------------------------------
#-- isLeapYear: chek whether the year is a leap year                                                    ---
#----------------------------------------------------------------------------------------------------------

def isLeapYear(year):
    """
    chek whether the year is a leap year
    Input:  year    --- in full lenth (e.g. 2014, 813)
    
    Output:     0--- not leap year
                1--- yes it is leap year
    """
    
    year = int(float(year))
    chk  = year % 4     #---- evry 4 yrs leap year
    chk2 = year % 100   #---- except every 100 years (e.g. 2100, 2200)
    chk3 = year % 400   #---- except every 400 years (e.g. 2000, 2400)
    
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
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines as lines

if __name__ == "__main__":
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
    plot_radiation_counts(start, stop, out)
