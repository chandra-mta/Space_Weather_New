#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

#############################################################################################################
#                                                                                                           #
#                   extract_radiation_data.py: extract radiation related data                               #
#                                                                                                           #
#                   author: t. isobe (tisobe@cfa.harvard.edu)                                               #
#                                                                                                           #
#                   last update: Mar 16, 2021                                                               #
#                                                                                                           #
#############################################################################################################

import os
import sys
import re
import string
import random
import operator
import math
import numpy
import astropy.io.fits  as pyfits
import time
import Chandra.Time
import unittest
#
#--- from ska
#
from Ska.Shell import getenv, bash

#ascdsenv = getenv('source /home/ascds/.ascrc -r release; source /home/mta/bin/reset_param', shell='tcsh')
ascdsenv = getenv('source /home/ascds/.ascrc -r release', shell='tcsh')
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
sys.path.append(acis_dir)
#
#--- temp writing file name
#
rtail  = int(time.time())
zspace = '/tmp/zspace' + str(rtail)
#
#---- the testing period
#
test_start = 531187196       #--- 2014:305:00:00:00 (Nov  1, 2014)
test_stop  = 532483196       #--- 2014:320:00:00:00 (Nov 15, 2014)

#-------------------------------------------------------------------------------------------
#-- find_sim_position: extract sim position realated data for a given time span         ----
#-------------------------------------------------------------------------------------------

def find_sim_position(start, stop):
    """
    extract sim position realated data for a given time span
    input   start   --- starting time
            stop    --- stopping time
            data are in: /data/mta_www/mta_temp/mta_states/MJ/<yyyy>//comprehensive_data_summary<yyyy>
    output: acis_i_start/ acis_i_stop     --- acis i starting and stopping time 
            acis_s_start/ acis_s_stop     --- acis s starting and stopping time
            hrc_i_start/  hrc_i_stop      --- hrc i starting and stopping time
            hrc_s_start/  hrc_s_stop      --- hrc s starting and stopping time
            hetg_start/   hetg_stop       --- hetg starting and stopping time
            letg_start/   letg_stop       --- letg starting and stopping time
            radmon_start/ radmon_stop     --- radmon starting and stopping time
            fmt                           --- fmt format list
            time                          --- time list
    """
#
#--- find year of starting and stopping time. this will be used to fine which data set we need to use
#
    ntime = Chandra.Time.DateTime(start).date
    atemp = re.split(':', ntime)
    syear = int(atemp[0])

    ntime = Chandra.Time.DateTime(stop).date
    atemp = re.split(':', ntime)
    lyear = int(atemp[0])
#
#-- read all data sets contain the appropriate data
#
    data  = []
    for year in range(syear, lyear+1):
        #file = '/data/mta_www/mta_temp/mta_states/MJ/' + str(year) + '/comprehensive_data_summary' + str(year)
        ifile = '/data/mta_www/mta_temp/mta_states/Data/MJ/comprehensive_data_summary' + str(year)
        with open(ifile, 'r') as f:
            dtmp = [line.strip() for line in f.readlines()]

        data  = data + dtmp

    acis_i_start = []
    acis_i_stop  = []
    acis_s_start = []
    acis_s_stop  = []
    hrc_i_start  = []
    hrc_i_stop   = []
    hrc_s_start  = []
    hrc_s_stop   = []
    hetg_start   = []
    hetg_stop    = []
    letg_start   = []
    letg_stop    = []
    radmon_start = []
    radmon_stop  = []
    fmt          = []
    time         = []
    acis_i_in    = 0
    acis_s_in    = 0
    hrc_i_in     = 0
    hrc_s_in     = 0
    hetg_in      = 0
    letg_in      = 0
    radmon_on    = 0

    for ent in data:
#
#--- use only data line starting with year (which should be a digits)
#
        try:
            val = float(ent[0])
        except:
            continue

        atemp = re.split('\s+', ent)

        stime = int(Chandra.Time.DateTime(atemp[0]).secs)

        if stime < start:
            continue
        if stime > stop:
            break

        scpos = float(atemp[1])             #--- 3TSCPOS
        hpos  = float(atemp[9])             #--- 4HPOSARO
        lpos  = float(atemp[11])            #--- 4LPOSARO

        time.append(stime)

#
#--- ACIS I
#
        if scpos > 89000 and acis_i_in == 0:
            acis_i_start.append(stime)
            acis_i_in = 1
        elif scpos < 89000 and acis_i_in == 1:
            acis_i_stop.append(stime)
            acis_i_in = 0
#
#--- ACIS S
#
        elif scpos < 80000 and scpos > 71000 and acis_s_in == 0:
            acis_s_start.append(stime)
            acis_s_in = 1
        elif (scpos > 80000 or scpos < 71000) and acis_s_in == 1:
            acis_s_stop.append(stime)
            acis_s_in = 0
#
#--- HRC I
#
        elif scpos < -45000 and scpos > -55000 and hrc_i_in == 0:
            hrc_i_start.append(stime)
            hrc_i_in = 1
        elif (scpos > -45000 or scpos < -55000) and hrc_i_in == 1:
            hrc_i_stop.append(stime)
            hrc_i_in = 0
#
#--- HRC S
#
        elif scpos < -90000 and hrc_s_in == 0:
            hrc_s_start.append(stime)
            hrc_s_in = 1
        elif scpos > -90000 and hrc_s_in == 1:
            hrc_s_stop.append(stime)
            hrc_s_in = 0
#
#--- HETIG
#
        if hpos < 20 and hetg_in == 0:
            hetg_start.append(stime)
            hetg_in = 1
        elif hpos > 60 and hetg_in == 1:
            hetg_stop.append(stime)
            hetg_in = 0
#
#--- LETG
#
        if lpos  < 20 and letg_in == 0:
            letg_start.append(stime)
            letg_in = 1
        elif lpos > 60 and letg_in == 1:
            letg_stop.append(stime)
            letg_in = 0
#
#--- RADMON
#
        if atemp[5] == 'DISA' and radmon_on == 0:
            radmon_start.append(stime)
            radmon_on = 1
        elif atemp[5] == 'ENAB' and radmon_on == 1:
            radmon_stop.append(stime)
            radmon_on = 0
#
#--- FMT Format
#
        fmt.append(atemp[7])
#
#--- for the case the period is not closed during the time interval given
#--- add "stop" time to close the period
#
    if len(acis_i_stop) < len(acis_i_start):
        acis_i_stop.append(stop)

    if len(acis_s_stop) < len(acis_s_start):
        acis_s_stop.append(stop)

    if len(hrc_i_stop) < len(hrc_i_start):
        hrc_i_stop.append(stop)

    if len(hrc_s_stop) < len(hrc_s_start):
        hrc_s_stop.append(stop)

    if len(hetg_stop) < len(hetg_start):
        hetg_stop.append(stop)

    if len(letg_stop) < len(letg_start):
        letg_stop.append(stop)

    if radmon_on == 1:
        radmon_stop.append(stop)


    return[acis_i_start, acis_i_stop, acis_s_start, acis_s_stop, hrc_i_start, hrc_i_stop, \
           hrc_s_start,  hrc_s_stop,  hetg_start,   hetg_stop,   letg_start,  letg_stop,  \
           radmon_start, radmon_stop, fmt, time]


#-------------------------------------------------------------------------------------------
#-- read_ccd_data: extract acis cti measurement time periods                             ---
#-------------------------------------------------------------------------------------------

def read_ccd_data(start, stop):
    """
    extract acis cti measurement time periods
    input   start       ---- starting time
            stop        ---- stopping time
            the data is read from /data/mta4/www/DAILY/mta_rad/cti_data.txt
    output  cti_start   ---- cti measurement starting time
            cti_stop    ---- cti measurement stopping time
    """

    with  open('/data/mta4/www/DAILY/mta_rad/cti_data.txt', 'r') as f:
        data = [line.strip() for line in f.readlines()]

    cti_start = []
    cti_stop  = []
    for ent in data:
        atemp  = re.split('\s+', ent)
        cstart = float(atemp[11])
        cstop  = float(atemp[12])
        if cstart >= start and cstart < stop:
            cti_start.append(float(atemp[11]))
            cti_stop.append(float(atemp[12]))
        elif cstart >= stop:
            break
        else:
            continue


    return [cti_start, cti_stop]

#-------------------------------------------------------------------------------------------
#-- read_orbit_data: extract orbit and magnetic environment information                  ---
#-------------------------------------------------------------------------------------------

def read_orbit_data(start, stop):
    """
    extract orbit and magnetic environment information for a given time span
    input:  start       --- starting time
            stop        --- stopping time
            data are read from /data/mta/DataSeeker/data/repository/dephem.rdb
    output: time        --- a list of time
            alt         --- altitude
            magx        --- magnetic component x
            magy        --- magnetic component y
            magz        --- magnetic component z
            crm         --- crm
    """

#    with open('/data/mta4/Script/Ephem/Exc/zclean', 'r')
#    with  open('/data/mta/DataSeeker/data/repository/dephem.rdb', 'r') as f:
    with  open('/data/mta4/Space_Weather/ACIS_Rad/Data/dephem.rdb', 'r') as f:
        data = [line.strip() for line in f.readlines()]

    data.sort()

    time = []
    alt  = []
    magx = []
    magy = []
    magz = []
    crm  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            stime = float(atemp[0])
        except:
            continue

        if stime >=start and stime < stop: 
            time.append(stime)
            alt.append(float(atemp[1]) / 1000.0)
            magx.append(float(atemp[5]))
            magy.append(float(atemp[6]))
            magz.append(float(atemp[7]))
            crm.append(float(atemp[8]))
        elif stime >= stop:
            break
        else:
            continue


    return [time, alt, magx, magy, magz, crm]


#-------------------------------------------------------------------------------------------
#-- read_alt_data: extract altitude data                                                ----
#-------------------------------------------------------------------------------------------

def read_alt_data(start, stop):
    """
    extract extract altitude data
    input:  start       --- starting time
            stop        --- stopping time
            data are read from /data/mta/DataSeeker/data/repository/aorbital.rdb
    output: time        --- a list of time
            alt         --- altitude
    """

    with open('/data/mta/DataSeeker/data/repository/aorbital.rdb', 'r') as f:
        data = [line.strip() for line in f.readlines()]

    time = []
    alt  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            stime = float(atemp[0])
        except:
            continue

        if stime >=start and stime < stop: 
            time.append(stime)
            x   = float(atemp[1])
            y   = float(atemp[2])
            z   = float(atemp[3])
            dist = math.sqrt(x * x + y * y + z * z) /1000.0
            alt.append(dist)
        elif stime >= stop:
            break
        else:
            continue


    return [time, alt]

#-------------------------------------------------------------------------------------------
#-- read_rad_zone_data: extract radiation zone information for a given time span         ---
#-------------------------------------------------------------------------------------------

def read_rad_zone_data(start, stop):
    """
    extract radiation zone information for a given time span
    input:  start       --- starting time
            stop        --- stopping time
            data are read from /data/mta4/Script/Interrupt/house_keeping/rad_zone_info
    output: rad_start   --- a list of radiation zone starting time
            rad_stop    --- a list of radiation zone stopping time
    """

    #with  open('/data/mta4/Script/Interrupt/house_keeping/rad_zone_info', 'r') as f:
    with  open('/data/mta4/Space_Weather/Rad_zone/rad_zone_info', 'r') as f:
        data  =  [line.strip() for line in f.readlines()]

    rad_start = []
    rad_stop  = []
    rad_in    = 0

    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            val = float(atemp[1])       #---- check time is in digit (dom)
        except:
            continue 

        [year, ydate] = DOMtoYdate(float(atemp[1]))
#
#--- convert time to sec from 1998.1.1
#
        day_part = int(ydate)
        rest     = ydate - day_part
        hour     = int(24 * rest)
        rest     = 24 * rest - hour
        minutes  = int(60 * rest)

        ltime = str(year) + ':' + str(day_part) + ':' + str(hour) + ':' + str(minutes) + ':00'
        stime = int(Chandra.Time.DateTime(ltime).secs)

        if stime >= start and stime < stop:
            if atemp[0] == 'ENTRY' and rad_in == 0:
                rad_start.append(stime)
                rad_in = 1
            elif atemp[0] == 'EXIT' and rad_in == 1:
                rad_stop.append(stime)
                rad_in = 0
        elif stime >=stop:
            break
        else:
            continue

    if len(rad_stop) < len(rad_start):
        rad_stop.append(stop)

    return [rad_start, rad_stop]

#-------------------------------------------------------------------------------------------
#-- read_ace_data: extract ace data for a given time span: NOT USED ANYMORE              ---
#-------------------------------------------------------------------------------------------

def read_ace_data(start, stop):
    """
    extract ace data for a given time span
    input:  start       --- starting time
            stop        --- stopping time
            data are read from /data/mta4/www/DAILY/mta_rad/ace_data.txt
    output: time        --- time in sec from 1998.1.1
            ch1         --- ch1
            ch2         --- ch2
            ch3         --- ch3
            ch4         --- ch4
            ch5         --- ch5

    """

    with  open('/data/mta4/www/DAILY/mta_rad/ace_data.txt', 'r') as f:
        data = [line.strip() for line in f.readlines()]

    time = []
    ch1  = []
    ch2  = []
    ch3  = []
    ch4  = []
    ch5  = []

    for ent in data:
        atemp = re.split('\s+', ent)
        jd    = float(atemp[4])
        sec   = float(atemp[5])
        stime = (jd - 50814.0) * 86400.0 + sec
        if stime >= start and stime < stop:
            time.append(stime)
            ch1.append(float(atemp[10]))
            ch2.append(float(atemp[11]))
            ch3.append(float(atemp[12]))
            ch4.append(float(atemp[13]))
            ch5.append(float(atemp[14]))
        elif stime >= stop:
            break
        else:
            continue

    return [time, ch1, ch2, ch3, ch4, ch5]

#-------------------------------------------------------------------------------------------
#-- read_goes_data: extract goes data for a given time span: NOT USED ANYMORE            ---
#-------------------------------------------------------------------------------------------

def read_goes_data(start, stop):

    """
    extract goes data for a given time span
    input:  start       --- starting time
            stop        --- stopping time
            data are read from /data/mta4/www/DAILY/mta_rad/goes_data.txt
    output: time        --- time in sed from 1998.1.1
            p1          --- p1 rate
            p2          --- p2 rate
            p5          --- p5 rate
    """
    with open('/data/mta4/www/DAILY/mta_rad/goes_data.txt', 'r') as f:
        data = [line.strip() for line in f.readlines()]
    
    time = []
    p1   = []
    p2   = []
    p5   = []

    for ent in data:
        atemp = re.split('\s+', ent)
        jd    = float(atemp[4])
        sec   = float(atemp[5])
        stime = (jd - 50814.0) * 86400.0 + sec
        if stime >= start and stime < stop:
            time.append(stime)
            p1.append(float(atemp[6]))
            p2.append(float(atemp[7]))
            p5.append(float(atemp[10]))
        elif stime >= stop:
            break
        else:
            continue

    return[time, p1, p2, p5]


#-------------------------------------------------------------------------------------------
#-- read_hrc_data: extract hrc sheild rate for a given time span                         ---
#-------------------------------------------------------------------------------------------

def read_hrc_data(start, stop):
    """
    extract hrc sheild rate for a given time span
    input:  start       --- starting time
            stop        --- stopping time
            vito.fits   --- this fits file must exist, created by get_hrc_veto.perl
    output: time        --- time in sec from 1998.1.1
            rate        --- hrc shield rate
    """
#
#--- create a dammy file
#
    t_file =  acis_dir + '/Scripts/Template/empty_command'
    if not os.path.isfile(t_file):
        cmd = 'touch ' + t_file
        os.system(cmd)
#
#--- call dataseeker
#
    os.system('touch test')
    cmd1 = '/usr/bin/env PERL5LIB="" '

    cmd2 = ' /home/ascds/DS.release/bin/dataseeker.pl '
    cmd2 = cmd2 + 'infile=' +  t_file + ' outfile=ztemp.fits  '
    cmd2 = cmd2 + 'search_crit="columns=_shevart_avg timestart=' + str(start)
    cmd2 = cmd2 + ' timestop=' + str(stop) +'" loginFile='+ house_keeping + 'loginfile'
    cmd  = cmd1 + cmd2
    bash(cmd,  env=ascdsenv)
    os.system('rm -rf test')
#
#--- read the data
#
    try:
        data  = pyfits.getdata('./ztemp.fits')
        stime = data.field('time')
        shd   = data.field('shevart_avg')
    except:
        return [[], []]

    time  = []
    rate  = []
    for i in range(0, len(stime)):
        if stime[i] >= start and stime[i] < stop:
            time.append(stime[i])
            rate.append(shd[i])
        elif stime[i] >= stop:
            break
        else:
            continue

    rm_file('./test')
    rm_file('./ztemp.fits')

    return [time, rate]


#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------

def rm_file(ifile):

    if os.path.isfile(ifile):
        cmd = 'rm  -rf ' + ifile
        os.system(cmd)

#-----------------------------------------------------------------------------------------
#-- DOMtoYdate: change time fromat from DOM to Year and Ydate                          ---
#-----------------------------------------------------------------------------------------

def DOMtoYdate(dom):
    """
    change time fromat from DOM to Year and Ydate
    input:  dom     --- day of mission
    output: year    --- year
            ydate   --- year date
    """

    dom += 202
    year = 1999
    found = 0
    while (found == 0):
        chk = 4.0 * int(0.25 * year)
        if chk == year:
            base = 366
        else:
            base = 365
    
        dom -= base
        if dom < 0:
            ydate = dom + base
            found = 1
            break
    
        year += 1
    
    return (year, ydate)

#-----------------------------------------------------------------------------------------
#-- TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST    ---
#-----------------------------------------------------------------------------------------

class TestFunctions(unittest.TestCase):


    def test_find_sim_position(self):

        out = find_sim_position(test_start, test_stop)
        acis_i_start  = out[0]
        acis_s_start  = out[2]
        hrc_i_start   = out[4]
        hrc_s_start   = out[6]
        hetg_start    = out[8]
        letg_start    = out[10]
        radmon_start  = out[12]
        fmt           = out[14]

        comp_acis_i = [531198205, 531248643, 531473454, 531703054, 531930325, 532157826, 532389033]
        comp_hrc_s  = [531198426, 531425140, 531656577, 531883225, 532110824, 532342293]
        comp_hetg   = [531359532, 531485049, 532439580]

        self.assertEquals(acis_i_start, comp_acis_i)
        self.assertEquals(hrc_s_start,  comp_hrc_s)
        self.assertEquals(hetg_start,   comp_hetg)

#------------------------------------------------------------------------

    def test_read_ccd_data(self):

        [ccd_start, ccd_stop] = read_ccd_data(test_start, test_stop)

        comp_start = [531199219.0, 531237122.0, 531425631.0, 531461735.0, 531657085.0, 531692247.0]
        comp_stop  = [531208467.0, 531248588.0, 531435179.0, 531473393.0, 531666671.0, 531703034.0]

        self.assertEquals(ccd_start[0:6], comp_start)
        self.assertEquals(ccd_stop[0:6],  comp_stop)

#------------------------------------------------------------------------

#    def test_read_orbit_data(self):
#
#        [time, alt, magx, magy, magz, crm] = read_orbit_data(test_start, test_stop)
#
#        print alt
#        print crm

#------------------------------------------------------------------------

    def test_read_alt_data(self):

        [time, alt] = read_alt_data(test_start, test_stop)
        comp_alt = [93109.52610634398, 92658.06568676967, 92203.77986699861, 91746.64745831782, 91286.64694519126]
        self.assertEquals(alt[0:5], comp_alt)

#------------------------------------------------------------------------

    def test_read_rad_zone_data(self):

        [rad_start, rad_stop] = read_rad_zone_data(test_start, test_stop)

        comp_start = [531198540, 531425220, 531656700, 531883320, 532110960, 532342380]
        comp_stop  = [531248340, 531475020, 531702780, 531933840, 532159980, 532388700]

        self.assertEquals(rad_start, comp_start)
        self.assertEquals(rad_stop,  comp_stop)

#------------------------------------------------------------------------

    def test_read_hrc_data(self):

        [time, rate] = read_hrc_data(test_start, test_stop)

        comp_rate = [3109.9443359375, 3098.166748046875, 3086.27783203125, 3069.421142578125, 3078.73681640625]

        self.assertEquals(rate[0:5], comp_rate)

#------------------------------------------------------------------------

    def test_read_ace_data(self):

        [time, ch1, ch2, ch3, ch4, ch5] = read_ace_data(test_start, test_stop)

        comp_ch1 = [2250.0, 2280.0, 2210.0, 2170.0, 2130.0, 2170.0, 2150.0, 2300.0, 2310.0, 2050.0]
        comp_ch2 = [38.3, 38.9, 36.1, 32.4, 33.6, 30.7, 30.4, 37.1, 26.4, 30.0]

        self.assertEquals(ch1[0:10], comp_ch1)
        self.assertEquals(ch2[0:10], comp_ch2)

#------------------------------------------------------------------------

    def test_read_goes_data(self):

        [time, p1, p2, p5] = read_goes_data(test_start, test_stop)

        comp_p1 = [0.239, 0.201, 0.448, 0.364, 0.347, 0.287, 0.254, 0.287, 0.19, 0.3]
        comp_p2 = [0.0363, 0.109, 0.0484, 0.121, 0.0726, 0.0484, 0.0484, 0.0484, 0.0363, 0.0484]

        self.assertEquals(p1[0:10], comp_p1)
        self.assertEquals(p2[0:10], comp_p2)


#-------------------------------------------------------------------------------------------

if __name__ == "__main__":

    unittest.main()



