#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#       create_orbital_data_files.py: using the orbital elements data,                          #
#                                       create several orbital data files                       #
#                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                               #
#           last update: mar 16, 2021                                                           #
#                                                                                               #
#################################################################################################

import sys
import os
import string
import re
import time
import math
import numpy
import Chandra.Time
from datetime import datetime

sys.path.append('/data/mta4/Script/Python3.8/lib/python3.8/site-packages')
from geopack  import geopack
from sgp4.api import Satrec
from sgp4.api import jday
from astLib import astCoords
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
#--- a list of satellite names
#
sats   = ['cxo', 'xmm']
#
#--- earth
#
earth = 6371.0
#
#--- radian to degree conversion factor
#
r2d    = 180.0 / math.pi
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
#
#--- a list of satellite orbital data on web
#
tle_url = "http://www.celestrak.com/NORAD/elements/science.txt"
#
#--- coordinate system
#
coord_sys = '2000'          #---- J2000
#
#--- tle data dir
#
tel_data_dir = tle_dir + 'Data/'

#--------------------------------------------------------------------------
#-- create_orbital_data_files: using the orbital elements data, create several orbital data files
#--------------------------------------------------------------------------

def create_orbital_data_files():
    """
    using the orbital elements data, create several orbital data files
    input:  none, but read from:
        http://www.celestrak.com/NORAD/elements/science.txt
    output: <tle_dir>/Data/cxo.spctrk
            <tle_dir>/Data/xmm.spctrk
            <tle_dir>/Data/cxo.j2000
            <tle_dir>/Data/xmm.j2000
            <tle_dir>/Data/cxo.gsme
            <tle_dir>/Data/cxo.gsme_in_Re
            <tle_dir>/Data/xmm.gsme
            <tle_dir>/Data/xmm.gsme_in_Re
    """
#
#--- using the orbital element data, create *.spctrk files
#
    run_spctrk()

    for sat in ['cxo', 'xmm']:
#
#--- convert to *.j2000
#
        convert_tle(sat)
#
#--- convert to *gsme, *gsme_in_Re
#
        convert_to_gsm(sat)

#--------------------------------------------------------------------------
#-- run_spctrk: create spctrk files                                      --
#--------------------------------------------------------------------------

def run_spctrk():
    """
    create spctrk files
    input: none but use satellite orbital info from web
    output: <tle_dir>/Data/cox.spctrk
            <tle_dir>/Data/xmm.spctrk
    """
    [cxo_tle, xmm_tle]  = get_orbit_elements()

    day_before = 7
    day_after  = 7
    interval   = 300

    create_spctrk_file('cxo', cxo_tle, day_before, day_after, interval)
    create_spctrk_file('xmm', xmm_tle, day_before, day_after, interval)

    print_out_element('cxo', cxo_tle)
    print_out_element('xmm', xmm_tle)

#--------------------------------------------------------------------------
#-- create_spctrk_file: create spctrk file of the given satellite        --
#--------------------------------------------------------------------------

def create_spctrk_file(sat, tle, day_before, day_after, interval):
    """
    create spctrk file of the given satellite
    input:  sat     --- satellite name
            tle     --- two line tle data in a list
            day_before  --- starting time in how many day before today
            day_after   --- stopping time in how many day after today
            interval    --- time step in seconds
    output: <tle_dir>/Data/<sat>.spctrk

    tle has two line information something like:
    1 25989U 99066A   20059.86263969  .00000157  00000-0  00000+0 0  9990
    2 25989  71.1321 324.1739 7279617  93.7518   0.2501  0.50137597 25834

    ref: https://pypi.org/project/sgp4/
    """
#
#--- two line orbit ephemeris information
#
    s      = tle[0]
    t      = tle[1]

    print("Satellite: " + sat)
    print(s)
    print(t)
#
#--- convert epoch time into a few different format
#--- the third element of line 1
#
    atemp  = re.split('\s+', s)
    epoch  = float(atemp[3])                #--- <yy><ddd>.<frac day>
    out    = convert_igtime(epoch)          #--- <yyy>:<ddd>:<hh>:<mm>:<ss>
    btemp  = re.split(':', out)             
    eyear  = int(float(btemp[0]))
    yday   = int(float(btemp[1]))
    ehh    = int(float(btemp[2]))
    emm    = int(float(btemp[3]))
    ess    = int(float(btemp[4]))

    dout   = time.strftime('%m:%d', time.strptime(out, '%Y:%j:%H:%M:%S'))
    btemp  = re.split(':', dout)
    emon   = int(float(btemp[0]))
    eday   = int(float(btemp[1]))
#
#--- convert seconds from 1970.1.1
#
    ep_uts = ut_in_secs(eyear, emon, eday, ehh, emm, ess)
    lmon   = mcf.change_month_format(emon)
    ep_date = lmon + '%3d%5d%4d%3d%3d 0' % (eday, eyear, yday, ehh, emm)
#
#--- set the satellite orbit
#
    satellite = Satrec.twoline2rv(s, t)
#
#--- create time lists in a few different format between <day_before>/<day_after> with an <interval> step
#--- date_list  --- <yyyy>:<ddd>:<hh>:<mm>:<ss>
#--- jd_list    --- julian date intger part
#--- fr_list    --- julian date fraction part
#--- uts_list   --- time in seconds from 1970.1.1
#
    date_list, jd_list, fr_list, uts_list = create_time_list(day_before, day_after, interval)
#
#--- convert to numpy array
#
    jd_array  = numpy.array(jd_list)
    fr_array  = numpy.array(fr_list)
#
#--- compute the satellite positions
#
    e, r, v   = satellite.sgp4_array(jd_array, fr_array)
#
#--- out-file header part
#
    line = 'Based on python sgp4 2.4\n'
    line = line + date_list[0] + ' <--> ' + date_list[-1] + ' time interval: ' + str(interval) + 'sec\n'
    line = line + 'TLE EPOCH : ' + str(int(ep_uts)) + ' (UTS 1970) = ' + ep_date + '\n'
    line = line + '---- ' + sat.upper() + ' Data ----\n'
    line = line + 'SGP4    Time                      X (km)       Y (km)       Z (km)'
    line = line + '       VX (km/s)    VY (km/s)    VZ (km/s)\n'
#
#--- create the data table
#
    for k in range(0, len(date_list)):
        if e[k] != 0:
            continue

        line = line + '%12d' % uts_list[k]

        at   = re.split(':', date_list[k])
        line = line + '%5d%4d'             % (float(at[0]), float(at[1]))
        line = line + '%3d%3d  0'          % (float(at[2]), float(at[3]))
        line = line + '%13.4f%13.4f%13.4f' % (r[k][0], r[k][1], r[k][2])
        line = line + '%13.4f%13.4f%13.4f' % (v[k][0], v[k][1], v[k][2])
        line = line + '\n'
#
#--- print out the result
#
    ofile = tel_data_dir + sat +'.spctrk'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/" + os.path.basename(ofile)
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#-- print_out_element: print out two line orbital element data           --
#--------------------------------------------------------------------------

def print_out_element(satellite, idata):
    """
    print out two line orbital element data
    input:  satellite   --- either cxo or xmm
            idata       --- a list of data
    output: <tel_dir>/Data/<satellite>.tle
            <tel_dir>/Data/<satellite>.tle2
    """
    line  = idata[0] + '\n' + idata[1] + '\n'
    ofile = tle_dir + '/Data/' + satellite + '.tle'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/" + os.path.basename(ofile)
    with open(ofile, 'w') as fo:
        fo.write(line)

    line  = line + '0 0 0 0\n'
    ofile = tle_dir + '/Data/' + satellite + '.tle2'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/" + os.path.basename(ofile)
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#-- create_time_list: create lists of time in a few different format     --
#--------------------------------------------------------------------------

def create_time_list(day_before, day_after, interval):
    """
    create lists of time in a few different format
    input:  day_before  --- starting time in how many days before the current time
            day_after   --- stopping tine in how many days after the current time
            inteval     --- step interval in seconds
    output: date_list   --- a list in <yyyy>:<ddd>:<hh>:<mm>:<ss>
            jd_list     --- a list in integer part of julian date
            fr_list     --- a list in fraction part of julian date
            uts_list    --- a list in seconds from 1970.1.1
    """
#
#--- set starting and stopping time in seconds from 1998.1.1
#
    start     = current_chandra_time - day_before * 86400.0
    stop      = current_chandra_time + day_after  * 86400.0
    steps     = int((stop - start) / interval) + 1

    jd_list   = []
    fr_list   = []
    uts_list  = []
    date_list = []
    for k in range(0, steps):
        atime = start + interval * k
        atime = Chandra.Time.DateTime(atime).date
        atemp = re.split('\.', atime)       #--- remove fractional part of seconds
        atime = atemp[0]
        date_list.append(atime)

        atime = time.strftime('%Y:%m:%d:%H:%M:%S', time.strptime(atime, '%Y:%j:%H:%M:%S'))
        atime = re.split(':', atime)
        year  = int(float(atime[0]))
        mon   = int(float(atime[1]))
        day   = int(float(atime[2]))
        hh    = int(float(atime[3]))
        mm    = int(float(atime[4]))
        ss    = int(float(atime[5]))

        jd,fr = jday(year, mon, day, hh, mm, ss)

        jd_list.append(jd)
        fr_list.append(fr)

        uts   = ut_in_secs(year, mon, day, hh, mm, ss)
        uts_list.append(uts)

    return date_list, jd_list, fr_list, uts_list

#--------------------------------------------------------------------------
#-- convert_igtime: convert epoch time into <yyy>:<ddd>:<hh>:<mm>:<ss>   --
#--------------------------------------------------------------------------

def convert_igtime(gtime):
    """
    convert epoch time in the two line orbital info to <yyyy>:<jjj>:<hh>:<mm>:<ss>
    input:  gtime   --- epoch in <yy><ddd>.<time in fractional day>
    output: etime   --- <yyy>:<ddd>:<hh>:<mm>:<ss>
    """
    yr = int(gtime/1000)
    if yr >= 70:
        year = 1900 + yr
    else:
        year = 2000 + yr

    yday = int(gtime) - 1000 * yr

    fr   = gtime - int(gtime)
    fr   = 24 * fr
    hh   = int(fr)
    fr   = 60 * (fr - hh)
    mm   = int(fr)
    fr   = 60 * (fr - mm)
    ss   = int(fr)

    etime = str(year) + ':' + mcf.add_leading_zero(yday, 3) + ':' + mcf.add_leading_zero(hh)
    etime = etime     + ':' + mcf.add_leading_zero(mm)      + ':' + mcf.add_leading_zero(ss)

    return etime

#--------------------------------------------------------------------------
#-- get_orbit_elements: read orbital elements of cxo and xmm from NORAD   -
#--------------------------------------------------------------------------

def get_orbit_elements():
    """
    read orbital elements of cxo and xmm from NORAD
    input:  none, but read from:
                http://www.celestrak.com/NORAD/elements/science.txt
    output: cxo --- a list of two line elements something like:
                        1 25867U 99040B   20039.58323943  .00000620  00000-0  00000+0 0  9998
                        2 25867  64.5392 270.3470 7539653 229.8335   0.3303  0.37804574 19706
            xmm --- a list of two line elements for xmm
    """
#
#--- download the data and read it
#
    cmd = 'wget -O ' + zspace + ' -q ' + tle_url
    os.system(cmd)
    data = mcf.read_data_file(zspace, remove=1)
#
#--- find the data of cxo and xmm
#
    cxo  = []
    xmm  = []
    chk  = 0
    for k in range(0, len(data)):
        mc1 = re.search('CXO', data[k])
        mc2 = re.search('XMM', data[k])
#
#--- data part is the next two lines from the line with the satellite name
#
        if mc1 is not None:
            cxo.append(data[k+1])
            cxo.append(data[k+2])
            chk += 1
        if mc2 is not None:
            xmm.append(data[k+1])
            xmm.append(data[k+2])
            chk += 1

        if chk > 1:
            break

    return [cxo, xmm]

#--------------------------------------------------------------------------
#-- convert_tle: convert spctrk data into j2000 data                     --
#--------------------------------------------------------------------------

def convert_tle(sat):
    """
    convert spctrk data into j2000 data
    input:  sat --- 'cxo' or 'xmm' (data: <tle_dir>/Data/<sat>.spctrk)
    ouput:  <tle_dir>/Data/<sat>.j2000
    """
    ifile = tel_data_dir + sat + '.spctrk'
    ofile = tel_data_dir + sat + '.j2000'
    
    data  = mcf.read_data_file(ifile)
#
#--- find ephoch line in the header part and convert the time foramt in fractional year
#
    for ent in data[:6]:
        mc = re.search('TLE EPOCH', ent)
        if mc is not None:
            atemp = re.split('\s+', ent)
            year  = float(atemp[-5])
            mon   = mcf.change_month_format(atemp[-7])
            day   = float(atemp[-6])
            hh    = float(atemp[-4])
            mm    = float(atemp[-3])
            ss    = float(atemp[-2])
            yday  = convert_to_yday(year, mon, day)
            epoch = convert_to_fyear(year, yday, hh, mm, ss)
            break
#
#--- data reading starts here
#
    line = ''
    for ent in data[5:]:
        atemp = re.split('\s+', ent)
        if len(atemp) < 10:
            continue
        try:
            x  = float(atemp[6])
            y  = float(atemp[7])
            z  = float(atemp[8])
        except:
            continue
#
#--- compute input values of wcstool
#
        r   = math.sqrt(x * x + y * y )
        r3  = math.sqrt(x * x + y * y + z * z)
        ra  = math.atan2(y, x) * r2d
        if ra < 0:
            ra += 360.0
        dec = 90.0 - math.atan2(r, z) * r2d
#
#--- converting coordinates from  B1950 system to J200 system
#--- since there is no proper motion correction, "epoch" of convertCoords is set to 0.0
#--- http://astlib.sourceforge.net/docs/astLib/astLib.astCoords-module.html#convertCoords
#
        [ra, dec]  = astCoords.convertCoords('B1950', 'J2000', ra, dec, 0.0)
        ra         = float(ra)
        dec        = float(dec)
#
#--- convert back to x, y, z
#
        x = r3 * math.cos(dec / r2d) * math.cos(ra / r2d)
        y = r3 * math.cos(dec / r2d) * math.sin(ra / r2d)
        z = r3 * math.sin(dec / r2d)
        
        [mon, day] = convert_yday_to_mon_day(atemp[1], atemp[2])
        fyear      = convert_to_fyear(atemp[1], atemp[2], atemp[3], atemp[4], atemp[5])
#
#--- save the data line
#
        line = line + '%12s '   % atemp[0]
        line = line + '%12.4f ' % x
        line = line + '%12.4f ' % y
        line = line + '%12.4f ' % z
        line = line + '%10.6f'  % ra
        line = line + '%11.6f'  % dec   
        line = line + ' ' + coord_sys
        line = line + '%13.6f'  % fyear
        line = line + '%3d'     % mon
        line = line + '%3d'     % day
        line = line + '%3d'     % float(atemp[3])
        line = line + '%3d'     % float(atemp[4])
        line = line + '%3d\n'   % float(atemp[5])
#
#--- print out the results
#
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/" + os.path.basename(ofile)
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#-- convert_to_yday: convert year, mon, day into day of year             --
#--------------------------------------------------------------------------

def convert_to_yday(year, mon, day):
    """
    convert year, mon, day into day of year
    input:  year    --- year
            mon     --- month
            day     --- day of month
    output: yday    --- day of year
    """
    ttemp = str(int(year)) + ':' + str(int(mon)) + ':' + str(int(day))
    yday  = float(time.strftime('%j', time.strptime(ttemp, '%Y:%m:%d')))

    return yday

#--------------------------------------------------------------------------
#-- convert_yday_to_mon_day: convert  year and day of year to month and day 
#--------------------------------------------------------------------------

def convert_yday_to_mon_day(year, yday):
    """
    convert  year and day of year to month and day
    input:  year    --- year
            yday    --- day of year
    output: [mon, day] --- month and day of month
    """
#
#--- convert day of year to month and day of month
#
    ltime = str(int(float(year)))  + ':' + mcf.add_leading_zero(yday, 3) 
    out   = time.strftime('%m:%d', time.strptime(ltime, '%Y:%j'))
    [mon, day] = re.split(':', out)
    mon = int(float(mon))
    day = int(float(day))

    return [mon, day]

#--------------------------------------------------------------------------
#-- convert_to_fyear: convert date into fractional year                  --
#--------------------------------------------------------------------------

def convert_to_fyear(year, yday, hh, mm, ss):
    """
    convert date into fractional year
    input:  year    --- year
            yday    --- day of year
            hh      --- hours
            mm      --- minutes
            ss      --- seconds
    output: fyear   --- date in fractional year
    """
    year = float(year)
    yday = float(yday)
    hh   = float(hh)
    mm   = float(mm)
    ss   = float(ss)

    if mcf.is_leapyear(year):
        base = 366
    else:
        base = 365

    fyear = year + (yday + hh / 24.0 + mm / 1440.0 + ss / 86400.) / base

    return fyear

#--------------------------------------------------------------------------
#-- convert_to_gsm: convert gei coordinates to gsm/gse coordinates       --
#--------------------------------------------------------------------------

def convert_to_gsm(sat):
    """
    convert gei coordinates to gsm/gse coordinates
    input:  sat --- satellite name, either cxo, xmm
    output: <tle_dir>/Data/cxo.gsme
            <tle_dir>/Data/cxo.gsme_in_Re
            <tle_dir>/Data/xmm.gsme
            <tle_dir>/Data/xmm.gsme_in_Re
    """
#
#--- read input data
#
    ifile = tel_data_dir + sat + '.j2000'
    data  = mcf.read_data_file(ifile)
#
#--- there are two files to create
#
    line1 = ''
    line2 = ''
    for ent in data:
#
#--- find time in seconds from 1970.1.1 to set the environment
#
        atemp = re.split('\s+', ent)
        gtime = float(atemp[0])
        year  = float(atemp[-6])
        mon   = float(atemp[-5])
        day   = float(atemp[-4])
        hh    = float(atemp[-3])
        mm    = float(atemp[-2])
        ss    = float(atemp[-1])

        uts = ut_in_secs(year, mon, day, hh, mm, ss)
        psi = geopack.recalc(uts)
#
#--- get the satellite postion in x, y, z
#
        x     = float(atemp[1]) / 1.0e3
        y     = float(atemp[2]) / 1.0e3
        z     = float(atemp[3]) / 1.0e3
#
#--- converts equatorial inertial (gei) to geographical (geo) coords
#
        xgeo, ygeo, zgeo = geopack.geigeo(x, y, z, 1)
#
#--- converts geographic (geo) to geocentric solar magnetospheric (gsm) coordinates
#
        xgsm, ygsm, zgsm = geopack.geogsm(xgeo, ygeo, zgeo, 1)
#
#--- convert magnetosperic (gsm) to gse
#
        xgse, ygse, zgse = geopack.gsmgse(xgsm, ygsm, zgsm, 1)
#
#--- convert to spherical coordinates
#
        r, tgsm, pgsm    = geopack.sphcar(xgsm, ygsm, zgsm, -1)
        tgsm  *= r2d
        pgsm  *= r2d
        if pgsm > 180.0:
            pgsm -= 360.0

        r, tgse, pgse    = geopack.sphcar(xgse, ygse, zgse, -1)
        tgse  *= r2d
        pgse  *= r2d
        if pgse > 180.0:
            pgse -= 360.0
#
#--- convert them in the Earth radius unit
#
        xgsm /= earth
        ygsm /= earth
        zgsm /= earth
        xgse /= earth
        ygse /= earth
        zgse /= earth

        line1 = line1 + '%12.1f%10.2f%8.2f%8.2f%8.2f%8.2f%12.6f%3d%3d%3d%3d%3d\n' \
                        % (gtime, r, tgsm, pgsm, tgse, pgse, year, mon, day, hh, mm, ss)

        line2 = line2 + '%12.1f%11.6f%11.6f%11.6f%11.6f%11.6f%11.6f%12.6f%3d%3d%3d%3d%3d\n' \
                         % (gtime, xgsm, ygsm, zgsm, xgse, ygse, zgse, year, mon, day, hh, mm, ss)
#
#--- print out the results
#
    ofile1 = tel_data_dir + sat + '.gsme'
    ofile2 = tel_data_dir + sat + '.gsme_in_Re'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile1 = test_out + "/" + os.path.basename(ofile1)
        ofile2 = test_out + "/" + os.path.basename(ofile2)
    with open(ofile1, 'w') as fo:
        fo.write(line1)

    with open(ofile2, 'w') as fo:
        fo.write(line2)
    
#---------------------------------------------------------------------------------------
#-- ut_in_secs: onvert calendar date into univarsal time in sec                       --
#---------------------------------------------------------------------------------------

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
    
    uts  = (datetime(year, mon, day, hh, mm, ss)\
                - datetime(1970,1,1)).total_seconds()
    uts += 86400.0
    
    return uts

#--------------------------------------------------------------------------

if __name__ == "__main__":

    create_orbital_data_files()
