#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################
#                                                                               #
#           plot_crm_flux_data.py: create crm predicted flux plot               #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Mar 16, 2021                                           #
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
    sys.path.append('/data/mta4/Script/Python3.8/MTA/')
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
today                = time.strftime('%Y:%j:00:00:00', time.gmtime())
today_chandra_time   = Chandra.Time.DateTime(today).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#--------------------------------------------------------------------------------
#-- plot_crm_flux_data: create crm predicted flux plot                         --
#--------------------------------------------------------------------------------

def plot_crm_flux_data():
    """
    create crm predicted flux plot
    input:  <crm3_dir>/Data/CRMsummary.dat
            <ephem_dir>/Data/PE.EPH.gsme_spherical_short
            <comm_dir>/Data/comm_data
            <crm3_dir>/Data/CRM3_p.dat30
            /proj/sot/acis/FLU-MON/FPHIST-2001.dat
            /proj/sot/acis/FLU-MON/GRATHIST-2001.dat
    output: <html_dir>/Prbit/Plots/crmpl.png        --- extranal flux plot
            <html_dir>/Prbit/Plots/crmplatt.png     --- attenuated flux plot
    """
#
#--- read crm summary data table
#
    [kp, ace, fluence, afluence] = read_crmsummary()
#
#--- read orbital data
#
    [otime, altitude, latgsm, longsm, radgse, latgse, longse] = read_coord_data()
    orbit_color_list = read_region_data(otime)
#
#--- read dsn contact data
#
    [dsn_start, dsn_stop] = read_contact_data()
#
#--- read instrument data
#
    [inst_start, inst_stop] = read_inst_list()
#
#--- read otg data
#
    [otg_start, otg_stop] = read_otg_list()
#
#--- read crm flux model data
#
    [ftime_list, flux_list, color_list] = read_flux_model(kp)
#
#--- convert them to predictive flux and attenuated flux
#
    try:
        [flux, flux_atten] = create_attenuation_list(ftime_list, flux_list,\
                                inst_start, inst_stop, otg_start, otg_stop,\
                                ace, fluence, afluence, otime, altitude)
    except:
        exit(1)
#
#--- convert time into day of year
#
    otime      = convert_to_doy(otime)
    dsn_start  = convert_to_doy(dsn_start)
    dsn_stop   = convert_to_doy(dsn_stop)

    for k in range(0, 4):
        inst_start[k] = convert_to_doy(inst_start[k])
        inst_stop[k]  = convert_to_doy(inst_stop[k])

    for k in range(0, 2):
        otg_start[k]  = convert_to_doy(otg_start[k])
        otg_stop[k]   = convert_to_doy(otg_stop[k])

    for k in range(0, 10):
        ftime_list[k] = convert_to_doy(ftime_list[k])
#
#--- plot data: exteranl flux
#
    plot_crm(otime, altitude, orbit_color_list, dsn_start, dsn_stop, inst_start, inst_stop, \
             otg_start, otg_stop, ftime_list, flux, color_list, kp, atten=0)
#
#--- plot data: attenuated flux
#
    plot_crm(otime, altitude, orbit_color_list, dsn_start, dsn_stop, inst_start, inst_stop, \
             otg_start, otg_stop, ftime_list, flux_atten, color_list, kp, atten=1)

#--------------------------------------------------------------------------------
#-- read_crmsummary: read data from CRMsummary.data file                      ---
#--------------------------------------------------------------------------------

def read_crmsummary():
    """
    read data from CRMsummary.data file
    input: <crm3_dir>/Data/CRMsummary.dat
    output: kp          --- kp value
            ace         --- ace flux value
            fluence     --- fluence
            afluence    --- attenunated fluence
    """
    ifile = crm3_dir + 'Data/CRMsummary.dat'
    data  = mcf.read_data_file(ifile)

    atemp    = re.split(':', data[1])
    kp       = float(atemp[1].strip())
    atemp    = re.split(':', data[2])
    ace      = float(atemp[1].strip())
    atemp    = re.split(':', data[11])
    fluence  = float(atemp[1].strip())
    atemp    = re.split(':', data[12])
    afluence = float(atemp[1].strip())

    return [kp, ace, fluence, afluence]

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
#--- set start and stop time
#
    start = today_chandra_time - 2.0 * 86400.
    stop  = start + 10.0 * 86400.0
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

def read_region_data(time_list, cre=0):
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
#--- set start and stop time
#
    start = today_chandra_time - 2.0 * 86400.
    stop  = start + 10.0 * 86400.0
#
#--- read data 
#
    infile = crm3_dir + '/Data/CRM3_p.dat30'
    data   = mcf.read_data_file(infile)
    ctime  = []
    region = []
    for ent in data:
        atemp = re.split('\s+', ent)
        rtime = float(atemp[0])
        if rtime < start:
            continue
        elif rtime > stop:
            break
        ctime.append(rtime)
        region.append(int(float(atemp[1])))
#
#--- compare two time list and find which region satellite is in
#
    color  = []
    r_list = []
    start = 0
    clen  = len(ctime)
    chk   = 0
    tlen  = len(time_list)
    for n in range(0, tlen):
        r_list.append(1)
        otime = time_list[n]

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
                r_list[n] =  1
                break

            elif otime >=ctime[k] and otime < ctime[k1]:
                if region[k] == 1:
                    color.append('aqua')
                    r_list[n] = 1
                elif region[k] == 2:
                    color.append('fuchsia')
                    r_list[n] = 2
                else:
                    color.append('yellow')
                    r_list[n] = 3
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
        val    = r_list[-1]
        for k in range(len(color), len(time_list)):
            color.append(lcolor)
            r_list.append(val)

    color  = color[:clen]
    r_list = r_list[:clen]
    if cre == 0:
        return color
    else:
        return r_list

#--------------------------------------------------------------------------------
#-- read_flux_model: read CRM flux model                                       --
#--------------------------------------------------------------------------------

def read_flux_model(kp):
    """
    read CRM flux model
    input:  kp  --- kp value
            <crm3_dir>/Data/CRM3_p.dat*
    output: time_list   --- a list of lists of times
            flux_list   --- a list of lists of flux
            color_list  --- a list of lists of color indicating a region where the satellite is in
            note, there are 11 sub lists in all three lists. the last list is
                  based on the current kp value
    """
#
#--- find the model # corresponding to kp value
#
    ikp = int(10 * kp)
    lkp = str(ikp)
    if ikp < 10:
        lkp = '0' + lkp
#
#--- set start and stop time
#
    start = today_chandra_time -2.0 * 86400.
    stop  = start + 10.0 * 86400.0
#
#--- select 10 models + kp correspoinding flux
#
    tail_list  = ['00', '10', '20', '30', '40', '50', '60', '70', '80', '90', lkp]
    time_list  = [[], [], [], [], [], [], [], [], [], [], []]
    color_list = [[], [], [], [], [], [], [], [], [], [], []]
    flux_list  = [[], [], [], [], [], [], [], [], [], [], []]
#
#--- read each of them and save the fluxes
#
    for k in range(0, 11):
        ifile = crm3_dir + 'Data/CRM3_p.dat' + tail_list[k]
        data  = mcf.read_data_file(ifile)
        for ent in data:
            atemp = re.split('\s+', ent)
            xtime = float(atemp[0])
            if xtime < start:
                continue
            elif xtime > stop:
                break
            area  = float(atemp[1])     #--- where the satellite is such as solar wind region
            flux  = float(atemp[2])

            time_list[k].append(xtime)
            flux_list[k].append(flux)
#
#--- change the region in which the satellite is to color code
#--- yellow --- magnetosphere
#--- fuchisa--- magnetosphearth
#--- aqua   --- soloar wind
#
            if area == 1:
                color_list[k].append('aqua')
            elif area == 2:
                color_list[k].append('fuchsia')
            else:
                color_list[k].append('yellow')

    return [time_list, flux_list, color_list]

#--------------------------------------------------------------------------------
#-- read_inst_list: create lists of start and stop time of each instrument is in use 
#--------------------------------------------------------------------------------

def read_inst_list():
    """
    create lists of start and stop time of each instrument is in use
    input: none but read from:
            /proj/sot/acis/FLU-MON/FPHIST-2001.dat
    output: inst_start  --- a list of lists of starting time of each instrument
            inst_stop   --- a list of lists of stopping time of each instrument
            order of the instrument is: ACIS-I, ACIS-S, HRC-I, HRC-S
    """
#
#--- set start and stop time
#
    start = today_chandra_time -  3.0 * 86400.0
    stop  = today_chandra_time + 10.0 * 86400.0
#
#--- read instrument starting time table
#
    ifile = '/proj/sot/acis/FLU-MON/FPHIST-2001.dat'
    data  = mcf.read_data_file(ifile)
#
#--- create lists of starting time and stopping time for ACIS-I, ACIS-S, HRC-I, HRC-S 
#--- set their positional index to 0, 1, 2, and 3, respectively
#
    inst_start = [[], [], [], []]
    inst_stop  = [[], [], [], []]
#
#--- dummy instrument indicator
#
    pinst = -999
#
#--- start checking the data
#
    klen  = len(data)
    for k in range(0, klen):
        atemp = re.split('\s+', data[k])
        try:
            ctime = Chandra.Time.DateTime(atemp[0]).secs
        except:
            continue
        if ctime < start:
            continue
        elif ctime > stop:
            break

        if atemp[1] == 'ACIS-I':
            pos = 0
        elif atemp[1] == 'ACIS-S':
            pos = 1
        elif atemp[1] == 'HRC-I':
            pos = 2
        elif atemp[1] == 'HRC-S':
            pos = 3
        else:
            continue
        inst_start[pos].append(ctime)
#
#--- unless the previous inst is a dummy one, stop time is the same as the starting
#--- time of this round
#
        if pinst < 0:
            pinst = pos
            continue

        inst_stop[pinst].append(ctime)
        pinst = pos
#
#--- add the future time for the last stopping time
#
    if pinst >= 0:
        inst_stop[pinst].append(6374591994)        #---- 2200:001:00:00:00

    return [inst_start, inst_stop]

#--------------------------------------------------------------------------------
#-- read_otg_list: create lists of start and stop time of each otg is in use    -
#--------------------------------------------------------------------------------

def read_otg_list():
    """
    create lists of start and stop time of each otg is in use
    input:  none but read from:
            /proj/sot/acis/FLU-MON/GRATHIST-2001.dat
    output: otg_start   --- a list of lists of starting time
            otg_stop    --- a list of lists of stopping time
            order of otg is : HETG, LETG
    """
#
#--- set start and stop time
#
    start = today_chandra_time -  3.0 * 86400.0
    stop  = today_chandra_time + 10.0 * 86400.0

    ifile = '/proj/sot/acis/FLU-MON/GRATHIST-2001.dat'
    data  = mcf.read_data_file(ifile)
    otg_start = [[], []]
    otg_stop  = [[], []]

    prev_state = -999
    for ent in data:
#
#--- check which otg is on (or off)
#
        atemp = re.split('\s+', ent)
        try:
            ctime = Chandra.Time.DateTime(atemp[0]).secs
        except:
            continue
        if ctime < start:
            continue
        elif ctime > stop:
            break
        state = -999
        if atemp[1] == 'HETG-IN' and atemp[2] == 'LETG-IN':
            state =-999
        elif atemp[1] == 'HETG-IN' and atemp[2] == 'LETG-OUT':
            state = 0
        elif atemp[1] == 'HETG-OUT' and atemp[2] == 'LETG-IN':
            state = 1
#
#--- if otg is turned off (or something wrong), add stopping time to the previous otg
#
        if state < 0:
            if prev_state >= 0:
                otg_stop[prev_state].append(ctime)
#
#--- if otg is turned on or changed, add starting time to that otg, and close the previous otg
#
        else:
            otg_start[state].append(ctime)

            if prev_state >= 0:
                otg_stop[prev_state].append(ctime)

        prev_state = state
#
#--- add the future time for the last stopping time
#
    if prev_state >= 0:
        otg_stop[prev_state].append(6374591994)     #--- 2200:001:00:00:00

    return [otg_start, otg_stop]

#--------------------------------------------------------------------------------
#-- create_attenuation_list: create predictive flux models and their attenuated counterparts
#--------------------------------------------------------------------------------

def create_attenuation_list(ftime_list, flux_list, inst_start, inst_stop, otg_start,\
                            otg_stop, ace, fluence, afluence, otime, altitude):
    """
    create predictive flux models and their attenuated counterparts
    input:  ftime_list  --- a list of lists of time
            flux_list   --- a list of lists of CRM flux model
            inst_start  --- a list of lists of instrument starting time
            inst_stop   --- a list of lists of instrument stopping time
            otg_start   --- a list of lists of otg starting time
            otg_stop    --- a list of lists of otg stopping time
            ace         --- current ace value
            fluence     --- current fluence value
            afluence    --- current attenuated fluence value
            otime       --- a list of time of the orbital data
            altitude    --- a list of altitude of the satellite
    output: nfluxi      --- a list of predictive fluence values
            nfluxia     --- a list of predictive attenuated fluence values
    """
#
#--- convert lists to numpy array
#
    nptime = numpy.array(ftime_list)
    nflux  = numpy.array(flux_list)
#
#--- assign values to compute attenuation factor for instruments and otgs.
#
    flen = len(ftime_list[0])
    inst = numpy.ones(flen)
    otg  = numpy.ones(flen)
#
#--- acis: no change, but hrc will be 0 (totally attenuated)
#
#--- hrc i
#
    for k in range(0, len(inst_start[2])):
        ind = (nptime[0] >= inst_start[2][k]) & (nptime[0] < inst_stop[2][k])
        inst[ind] = 0
#
#--- hrc s
#
    for k in range(0, len(inst_start[3])):
        ind = (nptime[0] >= inst_start[3][k]) & (nptime[0] < inst_stop[3][k])
        inst[ind] = 0
#
#--- hetg 
#
    for k in range(0, len(otg_start[0])):
        ind = (nptime[0] >= otg_start[0][k]) & (nptime[0] < otg_stop[0][k])
        otg[ind] = 0.2
#
#--- letg
#
    for k in range(0, len(otg_start[1])):
        ind = (nptime[0] >= otg_start[1][k]) & (nptime[0] < otg_stop[1][k])
        otg[ind] = 0.5
#
#--- create instrumental attenuation value array
#
    af = inst * otg
#
#---- find the perigees
#
    pg = numpy.ones(flen)
    for k in range(0, len(otime)-3):
        diff1 = altitude[k+1] - altitude[k]
        diff2 = altitude[k+2] - altitude[k+1]
        if diff1 <= 0 and diff2 >= 0:
            ind = (nptime[0] >= otime[k]) & (nptime[0] < otime[k+1])
            pg[ind] = 0
#
#--- read region data
#
    r_list  = read_region_data(ftime_list[0], cre=1)
    r_array = numpy.array(r_list)
#
#--- update the flux data depending on which region the satellite is in
#
#--- magnetosphere
#
    ind           = (r_array == 1)
    nflux[:,ind]  = ace
#
#--- magnetoshearth
#
    ind           = (r_array == 2)
    nflux[:, ind] = nflux[:,ind] + 2.0 * ace
#
#--- solar wind
#
    ind           = (r_array == 3)
    nflux[:, ind] = nflux[:,ind] + 0.5 * ace
#
#--- modify the flux farther
#
    nflux   = nflux * 300.0
    nfluxi  = numpy.copy(nflux)
    nfluxa  = numpy.copy(nflux)
    nfluxia = numpy.copy(nfluxa)
    nfluxa  = nfluxa * af

    for k in range(0, 11):
        nfluxi[k,0]  = fluence
        nfluxia[k,0] = afluence

    for m in range(1, flen):
        nfluxi[:,m]  = nfluxi[:,m-1]  * pg[m] + nflux[:,m]
        nfluxia[:,m] = nfluxia[:,m-1] * pg[m] + nfluxa[:,m]

    return [nfluxi, nfluxia]

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
#-- plot_crm: plot predictive CRM fluence model                                --
#--------------------------------------------------------------------------------

def plot_crm(otime, altitude, orbit_color_list, dsn_start, dsn_stop, inst_start, inst_stop,\
             otg_start, otg_stop, ftime_list, flux_list, color_list, kp, atten=0):
    """
    plot predictive CRM fluence model
    input:  otime       --- a list of time related to orbits
            altitude    --- a list of altitude
            orbit_color --- a list of color which indicates where the satellite is in
            dsn_start   --- a list of dsn contact starting time
            dsn_stop    --- a list of dsn contact stopping time
            inst_start  --- a list of lists of starting time of each instrument
            inst_stop   --- a list of lists of stopping time of each instrumet
            otg_start   --- a list of lists of starting time of each otg
            otg_stop    --- a list of lists of stopping time of each otg
            ftime_list  --- a list of lists of time related to flux
            flux_list   --- a list of lists of flux(fluence)
            color_list  --- a list of lists of color related to flux
            kp          --- a current kp value
            atten       --- whether this is external (0) or attenuated (1) plot
    output: <html_dir>/Orbit/Plots/crmpl.png or crmplatt.png
    """
#
#--- set the plotting range.
#
    hh   = float(time.strftime("%H", time.gmtime()))
    xmin = this_doy + hh / 24.0 
#
#--- there are 3 pannels with shared x axis
#
    xmax  = xmin + 7
    xdff  = xmax - xmin
    xtxt  = xmin - 0.10 * xdff
    xtxt2 = xmax - 0.15 * xdff
    ymin1 = 0
    ymax1 = 0.15
    ymin2 = 0
    ymax2 = 7
    ymin3 = 1e6
    ymax3 = 1e11
    ytxt3 = 6e10
#
#---- set a few parameters
#
    plt.close('all')
    mpl.rcParams['font.size'] = 6
    props = font_manager.FontProperties(size=6)
    f, (ax0, ax1, ax2) = plt.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [1, 1, 3]})
    plt.subplots_adjust(hspace=0.02)
#
#--- altitude plot
#
    ax0.set_autoscale_on(False)
    ax0.set_xbound(xmin, xmax)
    ax0.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax0.set_ylim(ymin=ymin1, ymax=ymax1, auto=False)
    ax0.set_facecolor('xkcd:black')

    x1 = len(otime)
    x2 = len(altitude)
    x3 = len(orbit_color_list)
    ot_list = otime
    at_list = altitude
    ct_list = orbit_color_list
    if x1 < x3:
        ct_list = orbit_color_list[:x3]
    if x1 > x3:
        ot_list = otime[:x3]
        at_list = altitude[:x3]

    ax0.scatter(ot_list, at_list, color=ct_list, marker='.',  s=0.5)

    ax0.set_ylabel('Altitude (Mm)', fontweight='heavy')
#
#--- DSN plot
#
    for k in range(0, len(dsn_start)):
        ax0.axvspan(dsn_start[k], dsn_stop[k], alpha=0.8, color='white')
#
#--- no tick labeling 
#
    line = ax0.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- otg/instruent on/off plot
#
    ax1.set_autoscale_on(False)
    ax1.set_xbound(xmin, xmax)
    ax1.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax1.set_ylim(ymin=ymin2, ymax=ymax2, auto=False)
    ax1.set_facecolor('xkcd:black')
#
#--- the indicator line is too fat; trim starting and stopping times a bit to 
#--- display the interval correctly
#
    f1 = 1.0005
    f2 = 0.9995
#
#--- acis s plot
#
    ax1.plot([xmin, xmax], [1, 1], color='white', lw =0.8)
    for k in range(0, len(inst_start[1])):
        start = f1 * inst_start[1][k]
        stop  = f2 * inst_stop[1][k]
        ax1.plot([start, stop], [1, 1], color='red', lw =3.0)
#
#--- acis i plot
#
    ax1.plot([xmin, xmax], [2, 2], color='white', lw =0.8)
    for k in range(0, len(inst_start[0])):
        start = f1 * inst_start[0][k]
        stop  = f2 * inst_stop[0][k]
        ax1.plot([start, stop], [2, 2], color='red', lw =3.0)
#
#--- hrc s plot
#
    ax1.plot([xmin, xmax], [3, 3], color='white', lw =0.8)
    for k in range(0, len(inst_start[3])):
        start = f1 * inst_start[3][k]
        stop  = f2 * inst_stop[3][k]
        ax1.plot([start, stop], [3, 3], color='red', lw =3.0)
#
#--- hrc i plot
#
    ax1.plot([xmin, xmax], [4, 4], color='white', lw =0.8)
    for k in range(0, len(inst_start[2])):
        start = f1 * inst_start[2][k]
        stop  = f2 * inst_stop[2][k]
        ax1.plot([start, stop], [4, 4], color='red', lw =3.0)
#
#--- hetg plot
#
    ax1.plot([xmin, xmax], [5, 5], color='white', lw =0.8)
    for k in range(0, len(otg_start[0])):
        start = f1 * otg_start[0][k]
        stop  = f2 * otg_stop[0][k]
        ax1.plot([start, stop], [5, 5], color='red', lw =3.0)
#
#--- letg plot
#
    ax1.plot([xmin, xmax], [6, 6], color='white', lw =0.8)
    for k in range(0, len(otg_start[1])):
        start = f1 * otg_start[1][k]
        stop  = f2 * otg_stop[1][k]
        ax1.plot([start, stop], [6, 6], color='red', lw =3.0)
#
#--- DSN plot --- only center position indicated
#
    for k in range(0, len(dsn_start)):
        xdsn = 0.5 * (dsn_start[k] + dsn_stop[k])
        ax1.plot([xdsn, xdsn], [ymin2, ymax2], alpha=1.0, color='white', lw=0.6)
#
#--- no tick labeling 
#
    line = ax1.get_xticklabels()
    for label in line:
        label.set_visible(False)

    line = ax1.get_yticklabels()
    for label in line:
        label.set_visible(False)
#
#--- label each  inst/otg
#
    ax1.text(xtxt, 0.8, 'ACIS-S', fontweight='heavy')
    ax1.text(xtxt, 1.8, 'ACIS-I', fontweight='heavy')
    ax1.text(xtxt, 2.8, ' HRC-S', fontweight='heavy')
    ax1.text(xtxt, 3.8, ' HRC-I', fontweight='heavy')
    ax1.text(xtxt, 4.8, '  HETG', fontweight='heavy')
    ax1.text(xtxt, 5.8, '  LETG', fontweight='heavy')
#
#--- flux plot
#
    ax2.set_autoscale_on(False)
    ax2.set_xbound(xmin, xmax)
    ax2.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax2.set_ylim(ymin=ymin3, ymax=ymax3, auto=False)
    ax2.set_facecolor('xkcd:black')
#
#--- use semi log plot; each color segment must be plotted separately
#
    for k in range(0, 10):
        [kcolor, kcstart, kcstop] = devide_data_in_color(color_list[k])
        for m in range(0, len(kcolor)):
            x = ftime_list[k][kcstart[m]:kcstop[m]]
            y = flux_list[k][kcstart[m]:kcstop[m]]
            plt.semilogy(x, y, color=kcolor[m], marker='.',ms=0.7,lw=0)
#
#--- kp related plot; use a single color(lime) to indicate this line is special
#
    plt.semilogy(ftime_list[0], flux_list[10], color='lime', marker='.', ms=0.7, lw=0)
    ax2.text(xtxt2, ytxt3, 'KP: ' + str(kp), color='lime', fontweight='heavy', fontsize=9) 
#
#--- DSN plot --- center position only
#
    for k in range(0, len(dsn_start)):
        xdsn = 0.5 * (dsn_start[k] + dsn_stop[k])
        ax2.plot([xdsn, xdsn], [ymin3, ymax3], alpha=1.0, color='white', lw=0.6)
#
#---- threshold
#
    ax2.plot([xmin, xmax], [3e9,3e9], color='red', lw =0.6)
#
#--- label both axes
#
    ax2.set_ylabel('Proton Fluence (p/cm2-sr-MeV)', fontweight='heavy')
    ax2.set_xlabel('UTC Date (Day of Year)', fontweight='heavy')
#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 5.0)
#
#--- save the plot in png format
#
    if atten == 0:
        outname = html_dir + 'Orbit/Plots/' + 'crmpl.png'
    else:
        outname = html_dir + 'Orbit/Plots/' + 'crmplatt.png'

    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')

#--------------------------------------------------------------------------------
#-- devide_data_in_color: devide the data into segments dpending on the color   -
#--------------------------------------------------------------------------------

def devide_data_in_color(color_list):
    """
    devide the data into segments dpending on the color
    input:  color_list  --- a list of color
    output: color       --- a list of color
            cstart      --- a list of indices when the color starts
            cstop       --- a list of indices when the color stops
    """
    color  = [color_list[0]]
    cstart = [0]
    cstop  = []
    pcolor = color_list[0]
    for k in range(1, len(color_list)):
        if color_list[k] != pcolor:
            cstop.append(k)
            cstart.append(k)
            color.append(color_list[k])
            pcolor = color_list[k]
        
    cstop.append(len(color_list))

    return [color, cstart, cstop]

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

#--------------------------------------------------------------------------------

if __name__ == "__main__":

    plot_crm_flux_data()
