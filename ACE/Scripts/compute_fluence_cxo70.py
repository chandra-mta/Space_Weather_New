#!/proj/sot/ska3/flight/bin/python

#####################################################################################
#                                                                                   #
#   compute_fluence_cxo70.py: create a html page displaying ace fluence             #
#                               when cxo is above 70kkm                             #
#                                                                                   #
#               author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                                   #
#               last updae: Mar 16, 2021                                            #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import numpy
import time
from datetime import datetime
import Chandra.Time
import copy 
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
    exec( "%s = %s" %(var, line))
#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.10/MTA/')
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
#--- set paths to the files
#
ephem_file       = ephem_dir + 'Data/PE.EPH.gsme_spherical'
ace_file         = ace_dir   + 'Data/ace_7day_archive'
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#-----------------------------------------------------------------------------
#-- compute_fluence_cxo70: create a html page displaying ace fluence when cxo is above 70kkm
#-----------------------------------------------------------------------------

def compute_fluence_cxo70():
    """
    create a html page displaying ace fluence when cxo is above 70kkm
    input:  none but read from:
            <ephem_dir>/Data/PE.EPH.gsme_spherical
            <ace_dir>/Data/ace_7day_archive
    output: <html_dir>/ACE/ace_flux_dat.html
    """
#
#--- read orbital info
#
    data  = mcf.read_data_file(ephem_file)
    data  = data[::-1]
    start = 0
#
#--- find the latest time span when cxo is above 70kkm
#
    stop  = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        stime = float(atemp[0])
#
#--- make sure that the span is before the curren time
#
        if stime > current_chandra_time:
            continue

        alt   = float(atemp[1])
        if stop == 0:
            if alt > 70.0:
                stop = stime
        else:
            if alt < 70.0:
                start = stime
                break
#
#--- read ace data
#
    data   = mcf.read_data_file(ace_file)
    e1     = 0.0
    e2     = 0.0
    p1     = 0.0
    p2     = 0.0
    p3     = 0.0
    p4     = 0.0
    p5     = 0.0
    cstart = 0.0
    cstop  = 0.0
    for ent in data:
        atemp = re.split('\s+', ent)
#
#--- convert time in Chandra Time
#
        ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' + atemp[3][0] + atemp[3][1] + ':'
        ltime = ltime    + atemp[3][2] + atemp[3][3] + ':00'
        ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
        stime = int(Chandra.Time.DateTime(ltime).secs)
#
#--- compute fluence between the span
#
        if stime < start:
            continue
        elif stime > stop:
            break
        else:
            ind1 = float(atemp[6])
            ind2 = float(atemp[9])
#
#--- use only good data
#
            if (ind1 != 0) or (ind2 != 0):
                continue

            if cstart == 0.0:
                cstart = stime
            cstop = stime

            ftime = atemp[0] + ' '  + atemp[1] + ' ' + atemp[2] + '  ' + atemp[3]
            ftime = ftime    + '%8d%8d' % (float(atemp[4]), float(atemp[5]))

            ve1 = float(atemp[7])
            ve2 = float(atemp[8])
            vp1 = float(atemp[10])
            vp2 = float(atemp[11])
            vp3 = float(atemp[12])
            vp4 = float(atemp[13])
            vp5 = float(atemp[14])
#
#--- sometime, some of the values are still show up negative. drop that set of the data
#
            if (ve1 < 0) or (ve2 < 0):
                continue
            if (vp1 < 0) or (vp2 < 0) or (vp3 < 0) or (vp4 < 0) or (vp5 < 0):
                continue
#
#--- the values are given every 5 mins
#
            e1 +=  ve1 * 300
            e2 +=  ve2 * 300
            p1 +=  vp1 * 300
            p2 +=  vp2 * 300
            p3 +=  vp3 * 300
            p4 +=  vp4 * 300
            p5 +=  vp5 * 300
#
#-- print out a text data
#
    aline = 'Latest valid ACE flux data...\n'
    aline = aline + '# UT Date   Time  Julian  of the  ----- Electron -----   '
    aline = aline + '------------------- Protons keV -------------------   Anis.\n'
    aline = aline + '# YR MO DA  HHMM    Day    Day    S    38-53   175-315   '
    aline = aline + 'S    47-68   115-195   310-580   795-1193 1060-1900   Index\n'
    aline = aline + '#' + '-'* 114 + '\n'
    aline = aline + data[-1] + '\n'
    aline = aline + 'Latest ACE fluence when CXO is above 70kkm' + ' '*67
    aline = aline + 'Int Time (s)\n'
    try:
        aline = aline + ftime 
        aline = aline + '  -'
        aline = aline + '%10.2e' % e1
        aline = aline + '%10.2e' % e2
        aline = aline + '  -'
        aline = aline + '%10.2e' % p1
        aline = aline + '%10.2e' % p2
        aline = aline + '%10.2e' % p3
        aline = aline + '%10.2e' % p4
        aline = aline + '%10.2e' % p5
        aline = aline + '%8d\n' % (cstop - cstart)
    except:
        aline = aline + '              N/A\n'

    ofile = html_dir + 'ACE/ace_flux.dat'
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + '/ace_flux.dat'
    with open(ofile, 'w') as fo:
        fo.write(aline)
#
#--- create the html page
#
    line = '<!DOCTYPE html>\n'
    line = line + '<html>\n'
    line = line + '<head>\n'
    line = line + '   <meta charset="UTF-8">\n'
    line = line + '   <title>ACE Fluence when CXO is above 70kkm</title>\n'
    line = line + '</head>\n'
    line = line + '<body style="width:95%;margin-left:10px; '
    line = line + 'margin-right;10px;background-color:#FAEBD7;font-family:Georgia, '
    line = line + '"Times New Roman", Times, serif">\n'
    line = line + '<h3>Most Recent ACE Fluxes and Fluences When CXO Is Above 70kkm</h3>\n'
    line = line + '<div style="text-align:right;">\n'
    line = line + '<a href="../index.html">Back to Radiation Monitoring Central Page.</a>\n'
    line = line + '</div>\n'
    line = line + '<pre>\n'
    line = line + aline
    line = line + '</pre>\n'
    line = line + '<p style="padding-top:30p;">'

    line = line + '<a href="https://' + main_web + 'ACE/ace.html">'
    line = line + 'Go to ACE page</a><br />'

    line = line + '<a href="https://' + main_web + 'Orbit/orbit.html">'
    line = line + 'See the current CXO orbital information</a></p>'
    line = line + '</body>\n'
    line = line + '<html>\n'


    ofile = html_dir + 'ACE/ace_flux_dat.html'
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + '/ace_flux_data.html'
    with open(ofile , 'w') as fo:
        fo.write(line)


#-----------------------------------------------------------------------------

if __name__ == '__main__':
    compute_fluence_cxo70()
