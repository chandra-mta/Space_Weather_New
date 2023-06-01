#!/proj/sot/ska3/flight/bin/python

#####################################################################################
#                                                                                   #
#       collect_comm_data.py: read comm data and extract data for +/- 10 days       #
#                                                                                   #
#           author: t. isobe (tiosbe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Mar 16, 2021                                               #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
import random
import Chandra.Time
import codecs
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
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- append path to a private folder
#
sys.path.append('/data/mta4/Script/Python3.10/MTA/')
import mta_common_functions     as mcf
#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

comm_data_dir = ifot_dir +'/comm/'

col_names = ['Type Description', 'TStart (GMT)','TStop (GMT)', 'DSN_COMM.bot', 'DSN_COMM.eot',\
             'DSN_COMM.station', 'DSN_COMM.config', 'DSN_COMM.site', 'DSN_COMM.sched_support_time',\
             'DSN_COMM.activity', 'DSN_COMM.lga', 'DSN_COMM.soe']

#---------------------------------------------------------------------------------
#-- collect_comm_data: read comm data and extract data for +/- 10 days         ---
#---------------------------------------------------------------------------------

def collect_comm_data():
    """
    read comm data and extract data for +/- 10 days
    input: none, but read from '/proj/sot/ska/data/arc/iFOT_events/comm/*.rdb'
    output: comm_data   --- a data file containing comm data for +/- 10 days
    """
#
#--- set +/- 10 days time interval
#
    [tbegin, tend] = set_collection_interval(iday=10)
#
#--- collect comm data file names
#
    cmd    = 'ls ' + comm_data_dir + '*.rdb > ' + zspace
    os.system(cmd)

    f_list = mcf.read_data_file(zspace, remove=1)

#
#--- read the last file
#
    line = '#Support Time (GMT)                     '
    line = line + 'Contact Time (GMT)                      '
    line = line + 'Chandra Time (sec)      Year DOY    '
    line = line + 'Year DOY        Station/Site\n'
    line = line + '#' +  '-' * 140 + '\n'

    dline = ''

    with codecs.open(f_list[-1], 'r', encoding='utf-8', errors='ignore') as f:
        data = [line.strip() for line in f.readlines()]
#
#--- skip the header part
#
    for ent in data[2:]:
        atemp  = re.split('\s+', ent)
        tstart = atemp[3]
        tstop  = atemp[4]
#
#--- select data in the selection time interval
#
        sstart = Chandra.Time.DateTime(tstart).secs
        sstop  = Chandra.Time.DateTime(tstop).secs
        if sstop < tbegin:
            continue

        elif sstart > tend:
            break

        btemp  = re.split(':', tstart)
        cstart = btemp[0] + ':' + btemp[1] + ':'
        cstart = cstart + atemp[5][0] + atemp[5][1] + ':' + atemp[5][2] + atemp[5][3] + ':00'

        dtemp  = re.split(':', tstop)
        cstop  = dtemp[0] + ':' + dtemp[1] + ':'
        cstop  = cstop + atemp[6][0] + atemp[6][1] + ':' + atemp[6][2] + atemp[6][3] + ':00'

        stime1 = Chandra.Time.DateTime(cstart).secs
        stime2 = Chandra.Time.DateTime(cstop).secs
#
#--- sometime contact does not start till the following day; make sure the starting time is correct
#
        diff   = stime2 - stime1
        if diff > 7200.0:
            cstart = dtemp[0] + ':' + dtemp[1] + ':'
            cstart = cstart + atemp[5][0] + atemp[5][1] + ':' + atemp[5][2] + atemp[5][3] + ':00'


        ctemp = re.split('\.', tstart)
        dtemp = re.split('\.', tstop)
        line = line + ctemp[0] + '\t' + dtemp[0]  + '\t' + cstart + '\t' + cstop + '\t'
        line = line + str(int(Chandra.Time.DateTime(cstart).secs)) + '\t'
        line = line + str(int(Chandra.Time.DateTime(cstop).secs))  + '\t'
        line = line + change_to_fday(cstart)        + '\t'
        line = line + change_to_fday(cstop)         + '\t\t'
        line = line + atemp[7] + '/' + atemp[9]     + '\n'

        dline = dline + change_to_fday(cstart)      + '\t\t'
        dline = dline + change_to_fday(cstop)       + '\t\t'
        dline = dline + atemp[7] + '/' + atemp[9]   + '\n'

    out = comm_dir + 'Data/comm_data'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        out = test_out + '/comm_data'
    with open(out, 'w') as fo:
        fo.write(line)

    out = comm_dir + 'Data/DSN.sch'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        out = test_out + '/DSN.sch'
    with open(out, 'w') as fo:
        fo.write(dline)


#---------------------------------------------------------------------------------
#-- set_collection_interval: set the time interval for +/- iday around today's date 
#---------------------------------------------------------------------------------

def set_collection_interval(iday=3.0):
    """
    set the time interval for +/- iday around today's date
    input:  iday    --- time inteval in days
    output: tbegin  --- starting time in seconds from 1998.1.1
            tend    --- stopping time in seconds from 1998.1.1
    """
    today  = time.strftime("%Y:%j:00:00:00", time.gmtime())
    today  = Chandra.Time.DateTime(today).secs
    tbegin = today - iday * 86400.0
    tend   = today + iday * 86400.0

    return [tbegin, tend]

#---------------------------------------------------------------------------------
#-- change_to_fday: changing date format from <yyyy>:<ddd>:<hh>:<mm>:<ss> to <yyyy> <ddd.ddd>
#---------------------------------------------------------------------------------

def change_to_fday(idate):
    """
    changing date format from <yyyy>:<ddd>:<hh>:<mm>:<ss> to <yyyy> <ddd.ddd>
    input:  idate   date in <yyyy>:<ddd>:<hh>:<mm>:<ss>
    output: line    date in <yyyy> <ddd.ddd>
    """
    atemp = re.split(':', idate)
    year  = atemp[0]
    yday  = int(atemp[1])
    hh    = int(atemp[2])
    mm    = int(atemp[3])
    ss    = int(float(atemp[4]))
    yday += hh / 24.0 + mm / 1440.0 + ss /86400.0

    line  = year + ' ' + "%3.3f" % yday

    return line


#----------------------------------------------------------------------------------

if __name__ == "__main__":

    collect_comm_data()
