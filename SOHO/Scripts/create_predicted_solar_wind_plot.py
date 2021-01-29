#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#   create_predicted_solar_wind_plot.py: create predicted solar wind            #
#                                        speed and density plot                 #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Oct 13, 2020                                           #
#                                                                               #
#################################################################################

import sys
import os
import string
import re
import numpy
import getopt
import time
import urllib.request
import json
import Chandra.Time
#import copy 
from copy  import deepcopy
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
#
#--- data sources
#
#swepam = 'ftp://ftp.swpc.noaa.gov/pub/lists/ace2'
swepam = 'https://services.swpc.noaa.gov/json/ace/swepam/ace_swepam_1h.json'
mtof   = 'http://umtof.umd.edu/pm/crn/archive/'
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#-------------------------------------------------------------------------
#-- create_predicted_solar_wind_plot: create predicted soloar wind speed and density plot
#-------------------------------------------------------------------------

def create_predicted_solar_wind_plot():
    """
    create predicted soloar wind speed and density plot
    input:  none but read from:
            ftp://ftp.swpc.noaa.gov/pub/lists/ace2
            http://umtof.umd.edu/pm/crn/archive/
            <ephem_dir>/Data/PE.EPH.gsme_spherical
    ouptut: <orbit_dir>/Plots/solwind.png
    """
#
#-- ace swepam data
#
    [stime_list, sdensity, sspeed]       = download_swepam()
#
#--- soho mtof data
#
    [mtime_list, mdensity, mspped] = download_mtof()
#
#--- orbital information
#
    [gtime_list, alt_list, lon_list, lat_lst] = read_gsme_data()
#
#--- create prediction
#
    [dtime, aspd0, mspd0, aspdu0, mspdu0, aden0, mden0, adenu0, mdenu0,\
            aspd1, mspd1, aspdu1, mspdu1, aden1, mden1, adenu1, mdenu1,\
            adens, aspds, mdens, mspds]\
        = create_prediction(sdensity, sspeed, mdensity, mspped)
#
#--- plot the data
#
    create_plot(gtime_list, alt_list, lon_list, lat_lst, dtime, \
                aspd0, mspd0, aspdu0, mspdu0, aden0, mden0, adenu0, mdenu0,\
                aspd1, mspd1, aspdu1, mspdu1, aden1, mden1, adenu1, mdenu1,\
                adens, aspds, mdens, mspds)

#-------------------------------------------------------------------------
#-- download_swepam: download ace swepam data from ftp site            ---
#-------------------------------------------------------------------------

def download_swepam():
    """
    input: none but read from:
            https://services.swpc.noaa.gov/json/ace/swepam/ace_swepam_1h.json
    output: density --- dictionary of particle density; key chandra time in hr unit
            speed   --- dictionary of solar wind speed; key chandra time in hr unit
    """
#
#--- read soloar wind data from json site
#
    with urllib.request.urlopen(swepam) as url:
        data = json.loads(url.read().decode())

    time_list = []
    density   = {}
    speed     = {}

    for ent in data:
#
#--- drop bad data
#
        if ent['dsflag'] not in [0, 1]:
            continue
#
#--- time format is <yyyy><ddd><hh>
#
        ltime = time.strftime('%Y:%j:%H:00:00', time.strptime(ent['time_tag'], '%Y-%m-%dT%H:%M:%S'))
        ltime = int(Chandra.Time.DateTime(ltime).secs / 3600.)

        try:
            dval = float(ent['dens'])
            sval = float(ent['speed'])
        except:
            continue

        time_list.append(ltime)
        density[ltime] = dval
        speed[ltime]   = sval

    time_list = list(set(time_list))
    time_list = sorted(time_list)

    return [time_list,  density, speed]


#-------------------------------------------------------------------------
#-- download_swepam_xx: RETIRED....
#-------------------------------------------------------------------------

def download_swepam_xx():
    """    
    download ace swepam data from ftp site
    input: none but read from:
            ftp://ftp.swpc.noaa.gov/pub/lists/ace2
    output: time_list   --- a list of time in chandra time in hr unit
            density     --- dictionary of particle density; key chandra time in hr unit
            speed       --- dictionary of solar wind speed; key chandra time in hr unit
    """
#
#--- find available data (_ace_swepam_1h.txt)
#
    with urllib.request.urlopen(swepam_f) as url:
        bdata = url.read()
#
#--- downloaded data is in binary format; convert it into string
#
    sdata = bdata.decode('utf8')
    data  = re.split('\n+', sdata)

    swep_data = []
    for ent in data:
        ent = ent.strip()
        mc = re.search('ace_swepam_1h', ent)
        if mc is not None:
            atemp = re.split('\s+', ent)
            swep_data.append(atemp[-1])
#
#--- sort the data
#
    swep_data = sorted(swep_data)

    time_list    = []
    density = {}
    speed   = {}
    temp    = {}
#
#--- read only the last 6 data files
# 
    for ent in swep_data[-6:]:
        durl = swepam_f + '/' + ent
        #print(durl)
        with urllib.request.urlopen(durl) as url:
            bdata = url.read()
        sdata = bdata.decode('utf8')
        data  = re.split('\n+', sdata)

        for ent in data:
            ent.strip()
            atemp = re.split('\s+', ent)
            if not mcf.is_neumeric(atemp[0]):
                continue
            ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' 
            ltime = ltime + atemp[3][0] + atemp[3][1] + ':00:00'
            ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
            ltime = int(Chandra.Time.DateTime(ltime).secs/3600.0)
            try:
#
#--- use only good data
#
                if float(atemp[6]) in [0, 1]:
                    time_list.append(ltime)
                    val1 = float(atemp[7])
                    val2 = float(atemp[8])
                    val3 = float(atemp[9])
                    density[ltime] =  val1
                    speed[ltime]   =  val2
                    temp[ltime]    =  val3
                else:
                    continue
            except:
                continue

    time_list = list(set(time_list))
    time_list = sorted(time_list)

    return [time_list, density, speed]

#-------------------------------------------------------------------------
#-- download_mtof: download soho mtof data from html site              ---
#-------------------------------------------------------------------------

def download_mtof():
    """    
    download soho mtof data from html site
    input: none but read from:
            http://umtof.umd.edu/pm/crn/archive/
    output: time_list   --- a list of time in chandra time in hr unit
            density     --- dictionary of particle density; key chandra time in hr unit
            speed       --- dictionary of solar wind speed; key chandra time in hr unit
    """
#
#--- find available data (CRN_*.USED)
#
    with urllib.request.urlopen(mtof) as url:
        bdata = url.read()
#
#--- downloaded data is in binary format; convert it into string
#
    sdata = bdata.decode('utf8')
    data  = re.split('\n+', sdata)

    crn_data = []
    for ent in data:
        ent = ent.strip()
        atemp = re.split('\,', ent)
        mc = re.search('USED', atemp[0])
        if mc is not None:
            btemp = re.split('USED\"\>', atemp[0])
            ctemp = re.split('\<\/A', btemp[1])
            crn_data.append(ctemp[0])
#
#--- sort the data
#
    crn_data = sorted(crn_data)

    time_list    = []
    density = {}
    speed   = {}
#
#--- read only the last 6 data files
# 
    for ent in crn_data[-6:]:
        #print(ent)
        durl = mtof + '/' + ent
        with urllib.request.urlopen(durl) as url:
            bdata = url.read()
        sdata = bdata.decode('utf8')
        data  = re.split('\n+', sdata)

        for ent in data:
            ent.strip()
            atemp = re.split('\s+', ent)
            if not mcf.is_neumeric(atemp[0]):
                continue
            ltime = atemp[0] + ':' + atemp[1]
            ltime = int(Chandra.Time.DateTime(ltime).secs/3600.0)
            try:
                angle = float(atemp[2])
                vth   = float(atemp[3])
                dens  = float(atemp[4])
                vsw   = float(atemp[5])
                pmmin = float(atemp[6])
                pmmax = float(atemp[7])
            except:
                continue
#
#--- drop bad data
#
            if pmmax == -1:
                continue

            time_list.append(ltime)
            density[ltime] = dens
            speed[ltime]   = vsw
    time_list = list(set(time_list))
    time_list = sorted(time_list)

    return [time_list, density, speed]
    
#-------------------------------------------------------------------------
#-- read_gsme_data: read gsme data                                      --
#-------------------------------------------------------------------------

def read_gsme_data():
    """
    read gsme data 
    input: none, but read from:
        <ephem_dir>/Data/PE.EPH.gsme_spherical
    output: time    --- a list of time in day of year
            alt     --- a list of altitude
            lon     --- a list of longitude
            lat     --- a list of latitude
    """

    ifile = ephem_dir + 'Data/PE.EPH.gsme_spherical'
    data  = mcf.read_data_file(ifile)

    time  = []
    alt   = []
    lon   = []
    lat   = []
    for ent in data:
        atemp = re.split('\s+', ent)
        ctime = float(atemp[0])
        time.append(convert_to_doy(ctime))
        alt.append(float(atemp[1]))
        lat.append(-1.0 * float(atemp[2])+90.0)
        lon.append(float(atemp[3]))
#
#--- usually ephem data is a few days short of 30 day period; extend the data 
#--- to fill the orbital data
#
    [time, alt, lon, lat] = extend_orbit_period(time, alt, lon, lat)

    return [time, alt, lon, lat]

#--------------------------------------------------------------------------
#-- extend_orbit_period: extend orbital period to fill up 30 day period   -
#--------------------------------------------------------------------------

def extend_orbit_period(time, alt, lon, lat):
    """
    extend orbital period to fill up 30 day period
    input:  time    --- a list of time
            alt     --- a list of altitude
            lon     --- a list of longitude
            lat     --- a list of latitude
    output: time    --- a list of time updated
            alt     --- a list of altitude updated
            lon     --- a list of longitude updated
            lat     --- a list of latitude updated
    """
#
#--- find indecies of last two nadirs
#
    [p1, p2] = find_orbit_nadir_times(alt)
#
#--- take the data values between these two periods
#
    dcnt   = p2 - p1
    t1     = time[p1]
    t2     = time[p2]
    tdiff  = t2 - t1
    tstep  = tdiff/ dcnt
    alt_a  = alt[p1:p2]
    lon_a  = lon[p1:p2]
    lat_a  = lat[p1:p2]
#
#--- drop the data after the last nadir point
#
    time   = time[:p2]
    alt    = alt[:p2]
    lon    = lon[:p2]
    lat    = lat[:p2]
#
#--- append the data values between two periods and extend the data
#
    for k in range(0, 8):
        for m in range(0, dcnt):
            time.append(time[-1] + tstep)
        alt = alt + alt_a
        lon = lon + lon_a
        lat = lat + lat_a

    return [time, alt, lon, lat]

#--------------------------------------------------------------------------
#-- find_orbit_nadir_times: find two indecies of the last two nadirs      -
#--------------------------------------------------------------------------

def find_orbit_nadir_times(alt):
    """
    find two indecies of the last two nadirs 
    input:  alt --- a list of altitude
    output: indecies of the last two nadir points
    """
    bot = []
    for k in range(0, len(alt)-2):
        v1 = alt[k]
        v2 = alt[k+1]
        v3 = alt[k+2]
        if (v2 <= v1) and (v2 <= v3):
            bot.append(k)

    return [bot[-2], bot[-1]]

#--------------------------------------------------------------------------
#-- create_prediction: create solar particle density and speed prediction models
#--------------------------------------------------------------------------

def create_prediction(adend, aspdd,  mdend, mspdd):
    """
    create solar particle density and speed prediction models
    input:  adend   --- a dictionary of ace particle density 
            aspdd   --- a dictionary of ace particle speed
            mdend   --- a dictionary of soho particle density
            mspdd   --- a dictionary of shoho particle speed
                    key is Chandra Time in hour unit
    output  dtime   --- a list of time in day of year  
            aspd0   --- a list of ace particle speed 0th order
            mspd0   --- a list of soho particle speed 0th order
            aspdu0  --- a list of ace particle speed uncertainty 0th order
            mspdu0  --- a list of soho particle speed uncertainty 0th order
            aden0   --- a list of ace particle density 0th order
            mden0   --- a list of soho particle density 0th order
            adenu0  --- a list of ace particle density uncertainty 0th order
            mdenu0  --- a list of soho particle density uncertainty 0th order
            aspd1   --- a list of ace particle speed 1st order
            mspd1   --- a list of soho particle speed 1st order
            aspdu1  --- a list of ace particle speed uncertainty 1st order
            mspdu1  --- a list of soho particle speed uncertainty 1st order
            aden1   --- a list of ace particle density 1st order
            mden1   --- a list of soho particle density 1st order
            adenu1  --- a list of ace particle density uncertainty 1st order
            mdenu1  --- a list of soho particle density uncertainty 1st order
            aspds
            adens
            mspds
            mdens
    the assumtion is  that the earth faces the same spot of the sun every 27 days and
    the pattern will repeat from the past. 
    """
#
#-- some initalizations
#
    aden0  = []
    aspd0  = []
    mden0  = []
    mspd0  = []
    aden1  = []
    aspd1  = []
    mden1  = []
    mspd1  = []
    adenu0 = []
    aspdu0 = []
    adenu1 = []
    aspdu1 = []
    mdenu0 = []
    mspdu0 = []
    mdenu1 = []
    mspdu1 = []
    dtime  = []
    adens0 = 0
    aspds0 = 0
    mdens0 = 0
    mspds0 = 0
    adens1 = 0
    aspds1 = 0
    mdens1 = 0
    mspds1 = 0

    nadens0 = 0
    naspds0 = 0
    nmdens0 = 0
    nmspds0 = 0
    nadens1 = 0
    naspds1 = 0
    nmdens1 = 0
    nmspds1 = 0
#
#--- convert current Chandra Time into hour unit
#
    key0 = int(current_chandra_time / 3600.0)
#
#--- create 30 day prediction in 1hr step
#
    for k in range(0, 720):
        key   = key0 + k
        stime = 3600 * key
#
#--- time is in day of year (fractional)
#
        dtime.append(convert_to_doy(stime))
#
#--- get the values from the past and put in lists of ace/soho density/speed
#
        key1  = key - 655           #--- 27.3 days ago
        key2  = key - 1309          #--- 54.5 days ago
        key3  = key - 1964          #--- 81.8 days ago
        key4  = key - 2618          #--- 109.1 days ago

        aden  = []
        aspd  = []
        mden  = []
        mspd  = []
        for ent in [key1, key2, key3, key4]:
            if ent in adend:
                val = adend[ent]
                if abs(val) < 9900:
                    aden.append(val)

            if ent in aspdd:
                val = aspdd[ent]
                if abs(val) < 9900:
                    aspd.append(val)

            if ent in mdend:
                val = mdend[ent]
                if abs(val) < 9900:
                    mden.append(val)

            if ent in mspdd:
                val = mspdd[ent]
                if abs(val) < 9900:
                    mspd.append(val)
#
#--- 0th order prediction; most of the case, the value from 27days ago is used
#
        aden0.append(-9999) if len(aden) < 1 else aden0.append(aden[0])
        aspd0.append(-9999) if len(aspd) < 1 else aspd0.append(aspd[0])
        mden0.append(-9999) if len(mden) < 1 else mden0.append(mden[0])
        mspd0.append(-9999) if len(mspd) < 1 else mspd0.append(mspd[0])
#
#--- 1st order prediction
#
        aden1.append(-9999) if len(aden) < 2 else aden1.append(aden[0] * 2 - aden[1])
        aspd1.append(-9999) if len(aspd) < 2 else aspd1.append(aspd[0] * 2 - aspd[1])
        mden1.append(-9999) if len(mden) < 2 else mden1.append(mden[0] * 2 - mden[1])
        mspd1.append(-9999) if len(mspd) < 2 else mspd1.append(mspd[0] * 2 - mspd[1])
#
#--- uncertainty is just a difference between two different data points
#
        adenu0.append(-9999) if len(aden) < 2 else adenu0.append(aden[1] - aden[0])
        aspdu0.append(-9999) if len(aspd) < 2 else aspdu0.append(aspd[1] - aspd[0])
        mdenu0.append(-9999) if len(mden) < 2 else mdenu0.append(mden[1] - mden[0])
        mspdu0.append(-9999) if len(mspd) < 2 else mspdu0.append(mspd[1] - mspd[0])

        adenu1.append(-9999) if len(aden) < 3 else adenu1.append(aden[1] * 2 - aden[2] - aden[0])
        aspdu1.append(-9999) if len(aspd) < 3 else aspdu1.append(aspd[1] * 2 - aspd[2] - aspd[0])
        mdenu1.append(-9999) if len(mden) < 3 else mdenu1.append(mden[1] * 2 - mden[2] - mden[0])
        mspdu1.append(-9999) if len(mspd) < 3 else mspdu1.append(mspd[1] * 2 - mspd[2] - mspd[0])

        if len(aden) > 1:
            adens0  += (aden[1] - aden[0])**2 
            nadens0 += 1
        if len(aspd) > 1:
            aspds0  += (aspd[1] - aspd[0])**2 
            naspds0 += 1
        if len(mden) > 1:
            mdens0  += (mden[1] - mden[0])**2 
            nadens0 += 1
        if len(mspd) > 1:
            mspds0  += (mspd[1] - mspd[0])**2 
            nmspds0 += 1

    nadens0 -= 1
    naspds0 -= 1
    nmdens0 -= 1
    nmspds0 -= 1
    nadens1 -= 1
    naspds1 -= 1
    nmdens1 -= 1
    nmspds1 -= 1
    try:
        adens = "%.1f,%.1f" % (math.sqrt(adens0/nadens0), math.sqrt(adens1/nadens1))
    except:
        adens = '0.0, 0.0'
    try:
        aspds = "%d,%d"     % (math.sqrt(aspds0/naspds0), math.sqrt(aspds1/naspds1))
    except:
        aspds = '0, 0'
    try:
        mdens = "%.1f,%.1f" % (math.sqrt(mdens0/nmdens0), math.sqrt(mdens1/nmdens1))
    except:
        mdens = '0.0, 0,0'
    try:
        mspds = "%d,%d"     % (math.sqrt(mspds0/nmspds0), math.sqrt(mspds1/nmspds1))
    except:
        mspds = '0, 0'

    return [dtime, aspd0, mspd0, aspdu0, mspdu0, aden0, mden0, adenu0, mdenu0,\
            aspd1, mspd1, aspdu1, mspdu1, aden1, mden1, adenu1, mdenu1,\
            aspds, adens, mspds, mdens]

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def create_plot(otime, alt, lon, lat, dtime,\
                aspd0, mspd0, aspdu0, mspdu0, aden0, mden0, adenu0, mdenu0, 
                aspd1, mspd1, aspdu1, mspdu1, aden1, mden1, adenu1, mdenu1, 
                adens, aspds, mdens, mspds):
    """
    input:  otime   --- a list of time related to orbits; in day of year
            alt     --- a list of altitude
            lon     --- a list of longitude
            lat     --- a list of latitude
            dtime   --- a list of time in day of year  
            aspd0   --- a list of ace particle speed 0th order
            mspd0   --- a list of soho particle speed 0th order
            aspdu0  --- a list of ace particle speed uncertainty 0th order
            mspdu0  --- a list of soho particle speed uncertainty 0th order
            aden0   --- a list of ace particle density 0th order
            mden0   --- a list of soho particle density 0th order
            adenu0  --- a list of ace particle density uncertainty 0th order
            mdenu0  --- a list of soho particle density uncertainty 0th order
            aspd1   --- a list of ace particle speed 1st order
            mspd1   --- a list of soho particle speed 1st order
            aspdu1  --- a list of ace particle speed uncertainty 1st order
            mspdu1  --- a list of soho particle speed uncertainty 1st order
            aden1   --- a list of ace particle density 1st order
            mden1   --- a list of soho particle density 1st order
            adenu1  --- a list of ace particle density uncertainty 1st order
            mdenu1  --- a list of soho particle density uncertainty 1st order
    putput: <orbit_dir>/Plots/solwin.png
    """
    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 8
    props = font_manager.FontProperties(size=8)
    plt.subplots_adjust(hspace=0.08)

    xmin  = min(dtime)
    xmax  = max(dtime)
    xtxt  = xmin + 0.05 * (xmax- xmin)
    xtxt1 = xmin + 0.35 * (xmax- xmin)
    xtxt2 = xmin + 0.50 * (xmax- xmin)
    xtxt3 = xmin + 0.65 * (xmax- xmin)
    xtxt4 = xmin + 0.80 * (xmax- xmin)

    ymin1 =  -220
    ymax1 =   235
    ytxt1 =   195
    ymin2 =     0
    ymax2 =  1000
    ytxt2 =   880
    ymin3 = -1000
    ymax3 =  1000
    ytxt3 =   800
    ymin4 =     0
    ymax4 =    40
    ytxt4 =    36
    ymin5 =   -40
    ymax5 =    40
    ytxt5 =    32
#
#--- orbital info
#
    ax0 = plt.subplot(511)
    ax0.set_autoscale_on(False)
    ax0.set_xbound(xmin, xmax)
    ax0.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax0.set_ylim(ymin=ymin1, ymax=ymax1, auto=False)
    ax0.set_facecolor('xkcd:black')

    plt.scatter(otime, alt, color='lime',  marker='.', s=0.3)
    plt.scatter(otime, lat, color='red',   marker='.', s=0.3)
    plt.scatter(otime, lon, color='white', marker='.', s=0.3)
    plt.plot([xmin, xmax], [0, 0], color='white', ls=':', lw=1)

    ax0.set_ylabel('degree/Mm', weight='heavy')
    ax0.text(xtxt,  ytxt1, 'GSM Coordinates', color='white')
    ax0.text(xtxt2, ytxt1, 'alt',             color='lime')
    ax0.text(xtxt3, ytxt1, 'lat',             color='red')
    ax0.text(xtxt4, ytxt1, 'lon',             color='white')
#
#--- no tick labeling 
#
    line = ax0.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- solar wind prediction
#
    ax1 = plt.subplot(512)
    ax1.set_autoscale_on(False)
    ax1.set_xbound(xmin, xmax)
    ax1.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax1.set_ylim(ymin=ymin2, ymax=ymax2, auto=False)
    ax1.set_facecolor('xkcd:black')

    plt.scatter(dtime, aspd0, color='lime',         marker='o', s=0.5)
    plt.scatter(dtime, aspd1, color='aqua',         marker='+', s=0.5)
    plt.scatter(dtime, mspd0, color='red',          marker='o', s=0.5)
    plt.scatter(dtime, mspd1, color='lightsalmon',  marker='+', s=0.5)

    ax1.set_ylabel('km/s', weight='heavy')
    ax1.text(xtxt,  ytxt2, 'Solar Wind Speed',  color='white')
    ax1.text(xtxt1, ytxt2, 'ACE (0th)',         color='lime',        size=6)
    ax1.text(xtxt2, ytxt2, 'ACE (1st)',         color='aqua',        size=6)
    ax1.text(xtxt3, ytxt2, 'SOHO (0th)',        color='red',         size=6)
    ax1.text(xtxt4, ytxt2, 'SOHO (1st)',        color='lightsalmon', size=6)
#
#--- no tick labeling 
#
    line = ax1.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- solar wind prediction diff
#
    ax2 = plt.subplot(513)
    ax2.set_autoscale_on(False)
    ax2.set_xbound(xmin, xmax)
    ax2.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax2.set_ylim(ymin=ymin3, ymax=ymax3, auto=False)
    ax2.set_facecolor('xkcd:black')

    plt.scatter(dtime, aspdu0, color='lime',        marker='o', s=0.5)
    plt.scatter(dtime, aspdu1, color='aqua',        marker='+', s=0.5)
    plt.scatter(dtime, mspdu0, color='red',         marker='o', s=0.5)
    plt.scatter(dtime, mspdu1, color='lightsalmon', marker='+', s=0.5)

    ax2.set_ylabel('km/s', weight='heavy')
    ax2.text(xtxt,  ytxt3, 'Solar wind Speed Uncertainty (Predicted- Measured)', color='white')
    #x2.text(xtxt1, ytxt2, aspds, color='lime')
    #x2.text(xtxt2, ytxt2, mspds, color='red')
#
#--- no tick labeling 
#
    line = ax2.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- solar wind density prediction
#
    ax3 = plt.subplot(514)
    ax3.set_autoscale_on(False)
    ax3.set_xbound(xmin, xmax)
    ax3.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax3.set_ylim(ymin=ymin4, ymax=ymax4, auto=False)
    ax3.set_facecolor('xkcd:black')

    plt.scatter(dtime, aden0, color='lime',         marker='o', s=0.5)
    plt.scatter(dtime, aden1, color='aqua',         marker='+', s=0.5)
    plt.scatter(dtime, mden0, color='red',          marker='o', s=0.5)
    plt.scatter(dtime, mden1, color='lightsalmon',  marker='+', s=0.5)

    ax3.set_ylabel('p/cc', weight='heavy')
    ax3.text(xtxt,  ytxt4, 'Solar Wind Proton Density', color='white')
    #ax3.text(xtxt1, ytxt2, aspdu, color='lime')
    #ax3.text(xtxt2, ytxt2, mspdu, color='red')
#
#--- no tick labeling 
#
    line = ax3.get_xticklabels()
    for label in line:
        label.set_visible(False)
#
#--- solar wind density prediction uncertainty
#
    ax4 = plt.subplot(515)
    ax4.set_autoscale_on(False)
    ax4.set_xbound(xmin, xmax)
    ax4.set_xlim(xmin=xmin,  xmax=xmax,  auto=False)
    ax4.set_ylim(ymin=ymin5, ymax=ymax5, auto=False)
    ax4.set_facecolor('xkcd:black')

    plt.scatter(dtime, adenu0, color='lime',        marker='o', s=0.5)
    plt.scatter(dtime, adenu1, color='aqua',        marker='+', s=0.5)
    plt.scatter(dtime, mdenu0, color='red',         marker='o', s=0.5)
    plt.scatter(dtime, mdenu1, color='lightsalmon', marker='+', s=0.5)

    ax4.set_ylabel('p/cc', weight='heavy')
    ax4.text(xtxt,  ytxt5, 'Solar Wind Proton Density Uncertainty (Predicted - Measured)', color='white')
    #ax4.text(xtxt1, ytxt5, adens, color='lime')
    #x4.text(xtxt2, ytxt5, mdens, color='red')
    ax4.set_xlabel('Day of Year (Year: ' + str(this_year) +')', weight='heavy')
#
#--- set the size of the plotting area in inch
#
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(5.0, 8.0)
#
#--- save the plot in png format
#
    outname = html_dir + 'Orbit/Plots/solwin.png'
    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')
#
#--- copy to SOHO directory
#
    cmd = 'cp -f ' + outname + ' ' + html_dir + 'SOHO/Plot/solwin.png'
    os.system(cmd)

#--------------------------------------------------------------------------
#-- convert_to_doy: convert to chandra time to day of year of this year  --
#--------------------------------------------------------------------------

def convert_to_doy(ctime):
    """
    convert to chandra time to day of year of this year
    input:  ctime   --- Chandra Time
    output: dtime   --- time in doy of this year
    note: see at the top for year_start value
    """
    dtime = (ctime - year_start) / 86400.0
    if dtime > 0:
        dtime += 1

    return dtime


#-------------------------------------------------------------------------

if __name__ == '__main__':

    create_predicted_solar_wind_plot()
