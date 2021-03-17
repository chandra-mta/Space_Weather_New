#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#           update_xmm_rad_data.py: update xmm radiation flux database                          #
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
import numpy
from subprocess import Popen, PIPE
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
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs

m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#
#--- xmm data html
#
xmm_file = 'https://xmm-tools.cosmos.esa.int/external/xmm_obs_info/radmon/plots/radmon_02h.dat'

#--------------------------------------------------------------------------
#-- update_xmm_rad_data: update xmm radiation flux database              --
#--------------------------------------------------------------------------

def update_xmm_rad_data():
    """
    update xmm radiation flux database
    input: none, but read from:
            /stage/xmmops_ftp/radmon_02h.dat
    output: <xmm_dir>/Data/xmm_7day.archive2
    """
#
#--- current time and 7 day ago boundary in Chandra Time
#
    current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
    d7ago                = current_chandra_time - 7 * 86400.0
#
#--- backup the data file
#
    ifile = xmm_dir + 'Data/xmm_7day.archive2'
    ofile = ifile + '~'
    cmd   = 'rm -rf ' + ofile
    os.system(cmd)
    cmd   = 'cp ' + ifile + ' ' + ofile
    os.system(cmd)
#
#--- read the data set and remove older data
#
    data  = mcf.read_data_file(ifile)
    line  = ''
    for ent in data:
        atemp = re.split('\s+', ent)
        stime = float(atemp[0])
        if stime < d7ago:
            continue
        line = line + ent + '\n'
#
#--- read the current data and append the data
#
    ofile = xmm_dir + '/Data/radmon_02h.dat'
    cmd   = 'rm -rf ' + ofile
    os.system(cmd)

    cmd = 'wget -q -O' + ofile + ' ' + xmm_file
    os.system(cmd)
    data  = mcf.read_data_file(ofile)

    save = [0, 0, 0, 0, 0, 0, 0, 0]
    chk  = 0
    dcnt = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        ltime = atemp[0].replace('-', ':')
        ctime = Chandra.Time.DateTime(ltime).secs
        if ctime <= stime:
            continue

        if chk == 0:
            start = ctime
            chk = 1
        diff = ctime - start
        if diff < 300:
            for k in range(0, 7):
                save[k] += float(atemp[k+1])
            dcnt += 1
        else:
            line  = line + '%1.8e'  % (ctime - 0.5 * diff)
            line  = line + '%13.3f' % (save[0] / dcnt)
            line  = line + '%13.3f' % (save[1] / dcnt)
            line  = line + '%13.3f' % (save[2] / dcnt)
            line  = line + '%13.3f' % (save[3] / dcnt)
            line  = line + '%13.3f' % (save[4] / dcnt)
            line  = line + '%13.3f' % (save[5] / dcnt)
            line  = line + '%13.3f' % (save[6] / dcnt) + '\n'

            start = ctime
            save  = [0, 0, 0, 0, 0, 0, 0, 0]
            for k in range(0, 7):
                save[k] += float(atemp[k+1])
            dcnt  = 1
#
#--- update the data
#
    if line != '':
        with open(ifile, 'w') as fo:
            fo.write(line)

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def update_mta_xmm_db():
#
#--- find the last entry time
#
    ifile = xmm_dir + 'Data/mta_xmm_db.dat'
    ltime = find_the_last_entry_time(ifile)
#
#--- read xmm flux data
#
    [ftime, flines] = read_xmm_flux()
#
#--- read xmm orbital data
#
    [otime, olines] = read_xmm_orbit()

    flen  = len(ftime)
    olen  = len(otime)
    start = 0
    line  = ''
    bchk  = 0
#
#--- skip the data till the new data part of the flux data
#
    for k in range(0, flen):
        if ftime[k] <= ltime:
            continue

        if bchk > 0:
            line = line + '\n'
            break
        line = line + flines[k] + ' ' 

        for m in range(start, olen):
#
#--- if there is more flex data than orbital data, stop there
#
            if m+1 >= olen:
                bchk = 1
                break
#
#--- flex time and orbital time are about same; append the orbital info to the flux data
#
            if ftime[k] >= otime[m] and ftime[k] < otime[m+1]:
                line = line + olines[m] + '\n'

                start = m - 5
                if start < 0:
                    start = 0
#
#--- write out the data
#
    with open(ifile, 'a') as fo:
        fo.write(line)
            
#--------------------------------------------------------------------------
#-- find_the_last_entry_time: find the last entry time                   --
#--------------------------------------------------------------------------

def find_the_last_entry_time(ifile):
    """
    find the last entry time
    input:  ifile   --- data file name. assume that the time is the first entry
    output: stime   --- the last entry time
    """
    p = Popen(['tail', '-1', ifile],shell=False, stderr=PIPE, stdout=PIPE)
    res, err = p.communicate()
    if err:
        print(err.decode())
        stime = current_chandra_time - 1440.0
    else:
        last_line = res.decode().strip()
        atemp = re.split('\s+', last_line)
        try:
            stime = float(atemp[0])
        except:
            stime = current_chandra_time - 1440.0

    return stime

#--------------------------------------------------------------------------
#-- read_xmm_flux: read xmm flux data                                    --
#--------------------------------------------------------------------------

def read_xmm_flux():
    """
    read xmm flux data
    input:  none, but read from <xmm_dir>/Data/xmm_7day.archive2'
    output: atime   --- a list of time in seconds from 1998.1.1
            fdata   --- a list of data
    """
    ifile = xmm_dir + 'Data/xmm_7day.archive2'
    data  = mcf.read_data_file(ifile)

    atime = []
    fdata = []
    for ent in data:
        atemp = re.split('\s+', ent)
        atime.append(float(atemp[0]))
        fdata.append(ent)

    return [atime, fdata]

#--------------------------------------------------------------------------
#-- read_xmm_orbit: read xmm orbital data                                --
#--------------------------------------------------------------------------

def read_xmm_orbit():
    """
    read xmm orbital data
    input: none, but read from <tle_dir>/Data/xmm.spctrk
    output: xtime   --- a list of time in seconds from 1998.1.1
            xdata   --- a list of data lines: r, x, y, z, vx, vy, vz
                        where r is the altitude
    """
    ifile = tle_dir + 'Data/xmm.spctrk'
    data  = mcf.read_data_file(ifile)

    xtime = []
    xdata = []

    for ent in data[5:]:
        atemp = re.split('\s+', ent)
        try:
            year  = atemp[1]
            yday  = mcf.add_leading_zero(atemp[2], 3)
            hh    = mcf.add_leading_zero(atemp[3])
            mm    = mcf.add_leading_zero(atemp[4])
            ltime = year + ':' + yday + ':' + hh + ':' + mm + ':00'
            stime = Chandra.Time.DateTime(ltime).secs
        except:
            continue

        xtime.append(stime)

        x     = float(atemp[6])
        y     = float(atemp[7])
        z     = float(atemp[8])
        r     = math.sqrt(x*x + y*y + z*z)
        vx    = float(atemp[9])
        vy    = float(atemp[10])
        vz    = float(atemp[11])
        line  = '%16.7f' % r
        line  = line + '%16.4f' % x
        line  = line + '%16.4f' % y
        line  = line + '%16.4f' % z
        line  = line + '%16.4f' % vx 
        line  = line + '%16.4f' % vy 
        line  = line + '%16.4f' % vz
        xdata.append(line)

    return [xtime, xdata]

#--------------------------------------------------------------------------
#-- update_xmm_archive: update xmm_archive data file                     --
#--------------------------------------------------------------------------

def update_xmm_archive():
    """
    update xmm_archive data file
    input: none, but read from:
            <xmm_dir>/Data/xmm.archive
            <xmm_dir>/Data/xmm_7day.archive2
    output: <xmm_dir>/Data/xmm.archive
    """
#
#--- copy the old data file
#
    ifile = xmm_dir + 'Data/xmm.archive'
    cmd   = 'rm -rf ' + ifile + '~'
    os.system(cmd)
    cmd   = 'cp ' + ifile + ' ' + ifile + '~'
    os.system(cmd)
#
#--- find the last entry time of xmm.archive
#
    stime = find_the_last_entry_time(ifile)
#
#--- read xmm_7day data
#
    sfile = xmm_dir + 'Data/xmm_7day.archive2'
    data  = mcf.read_data_file(sfile)
#
#--- append the new part 
#
    line  = ''
    for ent in data:
        atemp = re.split('\s+', ent)
        atime = float(atemp[0])
        if atime > stime:
            line = line + ent + '\n'

    with open(ifile , 'a') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#-- create_data_table_for_html: create a table for xmm html page         --
#--------------------------------------------------------------------------

def create_data_table_for_html():
    """
    create a table for xmm html page
    input: none but read from:
            <xmm_dir>/Data/xmm_7day.archive2
    output: <html_dir>/XMM/xmm_2day.dat
    """
#
#--- read xmm flux data
#
    ifile = xmm_dir + 'Data/xmm_7day.archive2'
    data  = mcf.read_data_file(ifile)
#
#--- make the last one hour interval time table for the last 24 hours.
#--- disp_time cnotains time in a display format at 30 min mark
#
    [disp_time, cstart, cstop] = make_time_interval()
#
#--- now make one hour average data in that intervals
#
    line   = ''
    dstart = 0
    le1    = 0
    le2    = 0
    hes1   = 0
    hes2   = 0
    hesc   = 0
    dcnt   = 0
    for k in range(0, len(cstart)):
        for m in range(dstart,len(data)):
            atemp = re.split('\s+',data[m])
            dtime = float(atemp[0])
            if dtime < cstart[k]:
                continue
            elif dtime >= cstart[k] and dtime < cstop[k]:
                le1  += float(atemp[2])
                le2  += float(atemp[3])
                hes1 += float(atemp[5])
                hes2 += float(atemp[6])
                hesc += float(atemp[7])
                dcnt += 1
            else:
#
#--- sometime, the data are totally missing; if so, display 'na'
#
                line = line + '' + disp_time[k] 
                if dcnt == 0:
                    line = line + '           na'
                    line = line + '           na'
                    line = line + '           na'
                    line = line + '           na'
                    line = line + '           na\n'
                else:
#
#---- take an average and prep for the next interval
#
                    le1  /= dcnt
                    le2  /= dcnt
                    hes1 /= dcnt
                    hes2 /= dcnt
                    hesc /= dcnt
                    line = line + '%13.3f' % le1
                    line = line + '%13.3f' % le2
                    line = line + '%13.3f' % hes1
                    line = line + '%13.3f' % hes2
                    line = line + '%13.3f' % hesc + '\n'

                le1    = 0
                le2    = 0
                hes1   = 0
                hes2   = 0
                hesc   = 0
                dcnt   = 0

                dstart = m - 5
                if dstart < 0:
                    dstart = 0
                break
#
#--- update the data  table
#
    ofile = html_dir + 'XMM/xmm_2day.dat'
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def make_time_interval():
    """
    make one hour time interval list
    input: none
    output: disp_time   --- a list of display time in the format of <yyyy>-<Mmm><dd>-<hh>:<mm>
            cstart      --- a list of the interval starting time in seconds from 1998.1.1
            cstop       --- a list of the interval stopping time in seconds from 1998.1.1
    """
#
#--- find starting time; set them to start at every hour
#
    start = current_chandra_time -86400.0
    start = Chandra.Time.DateTime(start).date
    atemp = re.split(':', start)
    year  = int(float(atemp[0]))
#
#--- check whether it is a leap year
#
    if mcf.is_leapyear(year):
        base = 366
    else:
        base = 365
#
#--- starting date and hour
#
    yday  = int(float(atemp[1]))
    hour  = int(float(atemp[2]))

    disp_time = []
    cstart    = []
    cstop     = []
#
#---- start creating the time inteval in seconds from 1998.1.1
#
    for k in range(0, 24):
#
#--- if the hour goes over to the next day, change the data and possibly year
#
        hour += 1 
        if hour > 23:
            yday += 1
            hour = 0
            if yday > base:
                year += 1 
                yday  = 1 
#
#--- starting time
#
        ttop  = str(year) + ':' + mcf.add_leading_zero(yday, 3) + ':'
        start = ttop      + mcf.add_leading_zero(hour) + ':00:00'
#
#--- display time
#
        mtime = ttop      + mcf.add_leading_zero(hour) + ':30:00'
        mtime = convert_to_display_time(mtime)
        disp_time.append(mtime)
#
#--- in Chandra Time
#
        start = int(Chandra.Time.DateTime(start).secs)
        cstart.append(start)
        stop  = start + 3600.0
        cstop.append(stop)

    return [disp_time, cstart, cstop]

#--------------------------------------------------------------------------
#-- convert_to_display_time: convert time into the foramt used in the table 
#--------------------------------------------------------------------------

def convert_to_display_time(ltime):
    """
    convert time into the foramt used in the table
    input:  ltime   --- time in <yyyy>:<jjj>:<hh>:<mm>:<ss>
    output: ldate   --- time in <yyyy>-<Mmm><dd>-<hh>:<mm>
    """

    out   = time.strftime('%Y-xxx%d-%H:%M', time.strptime(ltime, '%Y:%j:%H:%M:%S'))
    mon   = int(float(time.strftime('%m', time.strptime(ltime, '%Y:%j:%H:%M:%S'))))
    lmon  = m_list[mon-1]
    ldate = out.replace('xxx', lmon)

    return ldate

#--------------------------------------------------------------------------

if __name__ == "__main__":

    update_xmm_rad_data()
    update_mta_xmm_db()
    update_xmm_archive()
    create_data_table_for_html()
  




