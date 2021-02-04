#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#           update_ace_data_files.py: update ace related data files                 #
#                                                                                   #
#               author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                                   #
#               last updae: feb 04, 2021                                            #
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
sys.path.append('/data/mta4/Script/Python3.6/MTA/')
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
race_file        = ace_dir   + 'Data/ace.archive'
fluence_file     = ace_dir   + 'Data/fluace.dat'
fluence_file_bak = ace_dir   + 'Data/fluace.dat.good'
fluence_archive  = ace_dir   + 'Data/fluace.arc'
falert_file      = ace_dir   + 'Data/falert.dat'
ace_web          = html_dir  + 'ACE/'
ace_data         = ace_dir   + 'Data/'
#
#--- ftp address
#
noaa_file       = 'https://services.swpc.noaa.gov/text/ace-epam.txt'
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs
#
#--- other consts
#
ace_delt = 3 * 86400    #--- the depth of ACE archive in seconds
sampl    = 300          #--- ACE sample time (seconds)

#-----------------------------------------------------------------------------
#-- update_ace_data_files: update ace related data files                    --
#-----------------------------------------------------------------------------

def update_ace_data_files():
    """
    update ace related data files
    input: none but read from:
            ftp://ftp.swpc.noaa.gov/pub/lists/ace/ace_epam_5m.txt
            <ephem_dir>/Data/gephem.dat
            <kp_dir>/Data/k_index_data_past
    output: <ace_dir>/Data/ace.archive
            <ace_dir>/Data/ace_12h_archive
            <ace_dir>/Data/ace_7day_archive
            <ace_dir>/Data/longterm/ace_data.txt
            <ace_dir>/Data/fluace.dat
            <ace_dir>/Data/kp.dat
    """
#
#--- data is a list of lists of (see definitions in read_current_ace_data):
#--- [atime, jtime, echk, ech1, ech2, pchk, pch1, pch2, pch3, pch4, pch5, anis, ipol, fluence]
#--- the last two of current_ace_data are dummy lists
#
    [current_ace_data, chead] = read_current_ace_data()
    [past_ace_data,    head]  = read_past_ace_data()
#
#--- create one continuous data set
#
    combined_data             = combine_data(current_ace_data, past_ace_data)
#
#--- estimate bad data part and replace ipol data list. ipol data is based on pch2
#
    filled_data               = fill_missing_data(combined_data)
#
#--- fluence data collection time spans based on orbital period (at nadirs the periods start)
#
    [collection_start, collection_stop] = set_fluence_collection_span()
#
#--- compute fluence and update fluence list
#
    updated_data  = compute_fluence(filled_data, collection_start, collection_stop)
#
#--- update ace.archive file
#
    update_ace_archive(updated_data, head)
#
#--- update ace_12h_archive and ace_7day_archive data file
#
    update_secondary_archive_files(current_ace_data)
#
#--- update long term data
#
    update_long_term_data(current_ace_data)
#
#---- update fluace.dat
#
    updat_fluace_data_file(combined_data, chead, collection_start)
#
#--- update kp.dat
#
    update_kp_data_file()

#-----------------------------------------------------------------------------
#-- read_current_ace_data: read current ace data from a ftp site            --
#-----------------------------------------------------------------------------

def read_current_ace_data():
    """
    read current ace data from a ftp site
    input:  none, but read from ftp site: 
                ftp://ftp.swpc.noaa.gov/pub/lists/ace/ace_epam_5m.txt
    output: a list of lists of:
            atime   --- a time in seconds from 1998.1.1
            jtime   --- a string time
            echk    --- data quality of electron data
            ech1    --- electron 38-53
            ech2    --- electron 175-315
            pchk    --- data quality of proton
            pch1    --- proton 47-68
            pch2    --- proton 115-195
            pch3    --- proton 310-580
            pch4    --- proton 795-1193
            pch5    --- proton 1060-1900
            anis    --- anti-iso index (inactive and all of them are -1.0)
            ipol    --- estimated good data (112-187) --- -999 for all: computed later
            fluen   --- fluence                       --- -999 for all: computed later
            head    --- a list of header part
    """
#
#--- read the current data file
#
    cmd = 'wget -q -O' + zspace + ' ' + noaa_file
    os.system(cmd)

    data = mcf.read_data_file(zspace, remove=1)
#
#--- [atime, jtime, echk, ech1, ech2, pchk, pch1, pch2, pch3, pch4, pch5, anis, fluen, head]
#
    out  = read_ace_table_data(data)
#
#--- the last list contains header lines
#
    return [out[:-1], out[-1]]

#-----------------------------------------------------------------------------
#-- read_past_ace_data: read the past ace data                             ---
#-----------------------------------------------------------------------------

def read_past_ace_data():
    """
    read the past ace data
    input:  none, but read from <ace_dir>/Data/ace.archive
    output: a list of lists of:
            atime   --- a time in seconds from 1998.1.1
            jtime   --- a string time
            echk    --- data quality of electron data
            ech1    --- electron 38-53
            ech2    --- electron 175-315
            pchk    --- data quality of proton
            pch1    --- proton 47-68
            pch2    --- proton 115-195
            pch3    --- proton 310-580
            pch4    --- proton 795-1193
            pch5    --- proton 1060-1900
            anis    --- anti-iso index (inactive and all of them are -1.0)
            ipol    --- estimated good data (112-187)
            fluen   --- fluence
            head    --- a list of header part
    """
    ifile = ace_data + 'ace.archive'
    data  = mcf.read_data_file(ifile)
#
#--- [atime, jtime, echk, ech1, ech2, pchk, pch1, pch2, pch3, pch4, pch5, anis, ipol,fluen, head]
#
    out   = read_ace_table_data(data)
#
#--- reverse the data order to the oldest to the newest
#
    save  = []
    dlen  = len(out[:-1])
    for k in range(0, dlen):
        dtemp = out[k][::-1]
        save.append(dtemp)
#
#--- the last list contains the header lines
#
    return [save, out[-1]]

#-----------------------------------------------------------------------------
#-- read_ace_table_data: read  data into a list of lists                    --
#-----------------------------------------------------------------------------

def read_ace_table_data(data):
    """
    read  data into a list of lists
    input:  a list of list or either 16 or 18 entries
    output: a list of lists of:
            atime   --- a time in seconds from 1998.1.1
            jtime   --- a string time
            echk    --- data quality of electron data
            ech1    --- electron 38-53
            ech2    --- electron 175-315
            pchk    --- data quality of proton
            pch1    --- proton 47-68
            pch2    --- proton 115-195
            pch3    --- proton 310-580
            pch4    --- proton 795-1193
            pch5    --- proton 1060-1900
            anis    --- anti-iso index (inactive and all of them are -1.0)
            ipol    --- estimated good data (112-187)
            fluen   --- fluence (if flu > 0)
            head    --- a list of header part
    """
    atime = []
    jtime = []
    echk  = []
    ech1  = []
    ech2  = []
    pchk  = []
    pch1  = []
    pch2  = []
    pch3  = []
    pch4  = []
    pch5  = []
    anis  = []
    ipol  = []
    fluen = []
    head  = []
    for ent in data:
#
#--- keep header
#
        if ent[0] == "#":
            head.append(ent)
            continue
        elif mcf.is_neumeric(ent[0]) == False:
            continue

        atemp = re.split('\s+', ent)
        clen  = len(atemp)
#
#--- convert time in Chandra Time
#
        ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' + atemp[3][0] + atemp[3][1] + ':'
        ltime = ltime    + atemp[3][2] + atemp[3][3] + ':00' 
        ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
        stime = int(Chandra.Time.DateTime(ltime).secs)
#
#--- save time part in a string format (YR MO DA  HHMM    Day    Day)
#
        ftime = atemp[0] + ' '  + atemp[1] + ' ' + atemp[2] + '  ' + atemp[3]
        ftime = ftime    + '%8d%8d' % (float(atemp[4]), float(atemp[5]))

        atime.append(stime)
        jtime.append(ftime)
        echk.append(int(float(atemp[6])))
        ech1.append(float(atemp[7]))
        ech2.append(float(atemp[8]))
        pchk.append(int(float(atemp[9])))
        pch1.append(float(atemp[10]))
        pch2.append(float(atemp[11]))
        pch3.append(float(atemp[12]))
        pch4.append(float(atemp[13]))
        pch5.append(float(atemp[14]))
        anis.append(float(atemp[15]))
        if clen > 16:
            ipol.append(float(atemp[16]))
            fluen.append(float(atemp[17]))
        else:
            ipol.append(-999)
            fluen.append(-999)

    return [atime, jtime, echk, ech1, ech2, pchk, pch1, pch2, pch3, pch4, pch5, anis, ipol, fluen, head]

#-----------------------------------------------------------------------------
#-- set_fluence_collection_span: set fluence data collection span           --
#-----------------------------------------------------------------------------

def set_fluence_collection_span():
    """
    set fluence data collection span
    input: none
    output: start   --- a list of fluence data collection starting time in seconds from 1998.1.1
            stop    --- a list of fluence data collection stopping time in seconds from 1998.1.1
    """
    reset_time = find_reset_time()

    start = [0.0]
    stop  = []
    for ent in reset_time:
        start.append(ent)
        stop.append(ent)

    stop.append(6374591994.0)            #--- 2200:001:00:00
    
    return [start, stop]

#-----------------------------------------------------------------------------
#-- find_reset_time: find fluence reset time (at the nadir of the orbit)    --
#-----------------------------------------------------------------------------

def find_reset_time():
    """
    find fluence reset time (at the nadir of the orbit)
    input: none but read from:
            <ephem_dir>/Data/gephem.dat
    output: reset_time  --- a list of reset times in seconds from 1998.1.1
    """
    data = mcf.read_data_file(ephem_file)
    stime = []
    alt   = []
    for ent in data:
        atemp = re.split('\s+', ent)
        stime.append(float(atemp[0]))
        alt.append(float(atemp[1]))

    alen = len(alt)
    reset_time = []
    for k in range(0, alen-2):
        if (alt[k] >= alt[k+1]) and (alt[k+1] <= alt[k+2]):
            reset_time.append(stime[k+1])

    return reset_time

#-----------------------------------------------------------------------------
#-- combine_data: combine two data set                                      --
#-----------------------------------------------------------------------------

def combine_data(current_ace_data, past_ace_data):
    """
    combine two data set
    input:  current_ace_data    --- the list of 15 lists of data
            past_ace_data       --- the list of 15 lists of data
                atime   --- a time in seconds from 1998.1.1
                jtime   --- a string time
                echk    --- data quality of electron data
                ech1    --- electron 38-53
                ech2    --- electron 175-315
                pchk    --- data quality of proton
                pch1    --- proton 47-68
                pch2    --- proton 115-195
                pch3    --- proton 310-580
                pch4    --- proton 795-1193
                pch5    --- proton 1060-1900
                anis    --- anti-iso index (inactive and all of them are -1.0)
                ipol    --- estimated good data (112-187)
                fluen   --- fluence (if flu > 0)
    output: ndata       --- combined data set
    """
    dlen   = len(current_ace_data)
    clen   = len(current_ace_data[0])
    plen   = len(past_ace_data[0])
#
#--- there is no new data; return past data
#
    if clen < 1:
        return past_ace_data

    nstart = current_ace_data[0][0]
#
#--- initialize a list of lists
#
    ndata  = []
    for k in range(0, dlen):
        ndata.append([])
#
#--- the past data; stop at nstart (when the new data starts)
#
    for m in range(0, plen):
        if past_ace_data[0][m] >= nstart:
            break

        for k in range(0, dlen):
            ndata[k].append(past_ace_data[k][m])
#
#--- the current data
#
    for m in range(0, clen):
        for k in range(0, dlen):
            ndata[k].append(current_ace_data[k][m])

    return ndata

#-----------------------------------------------------------------------------
#-- fill_missing_data: update missing data proton flux list with interporation 
#-----------------------------------------------------------------------------

def fill_missing_data(combined_data):
    """
    update missing data proton flux list with interporation
    input:  combined_data   --- a list of lists of data. 7th list will be used for estimate
    output: combined_data   --- a list of lists of dta. 12th list will be replaced with a new estimate
    """
#
#--- set a list of estimated proton flux
#
    dlen = len(combined_data[0])
    est  = copy.deepcopy(combined_data[7])
    for k in range(0, dlen):
#
#--- find bad data
#
        if combined_data[5][k] != 0:
#
#--- find the most recent good data
#
            m = k -1
            while combined_data[5][m] != 0:
                m -= 1
#
#--- find the next good data
#
            n   = k + 1
            chk = 0
#
#--- if there is no good data after the current spot, use the last good data
#
            if n >= dlen:
                est[k] = est[m]
                chk = 1
            else:    
                while combined_data[5][n] != 0:
                    n += 1
                    if n >= dlen:
                        est[k] = est[m]
                        chk = 1
                        break
            if chk == 1:
                continue
#
#--- extrapolate linierly
#
            est[k] = est[m] + (est[m] - est[n]) * (k - m) / (n - m)
#
#--- replace the old one with the new estimate
#
    combined_data[12] = est

    return combined_data

#-----------------------------------------------------------------------------
#-- compute_fluence: upate fluence data list                                --
#-----------------------------------------------------------------------------

def compute_fluence(data, collection_start, collection_stop):
    """
    upate fluence data list
    input:  data                --- a list of lists of data 
                                    data[0] ---time/data[17] --- fluence
            collection_start    --- a list of fluence collection starting time
            collection_stop     --- a list of fluence collection stopping time
    output: data                --- fluecne updated data
    """
#
#--- start from the last estimated fluence value at the beginning
#
    fluence = [data[-1][0]]
    dlen    = len(data[0])
    clen    = len(collection_start)
#
#--- find which orbital period the first data set is in
#
    for n in range(0, clen):
        if (collection_start[n] <= data[0][0]) and (collection_stop[n] > data[0][0]):
            nperiod = n+1
            break
#
#--- fill the fluence based previously computed fluence between the first data and
#--- the new orbital period starts
#
    for k in range(0, dlen):
        if data[0][k] < collection_start[nperiod]:
            fluence.append(fluence[-1] + sampl * data[-2][k])
        else:
            fluence.append(sampl * data[-2][k-1])
            kstart = k
            break

    for k in range(kstart, dlen):
#
#--- compute the current fluence by adding the estimated flux to the previous fluence
#
        if (data[0][k] >= collection_start[nperiod]) and (data[0][k] < collection_stop[nperiod]):
                fluence.append(fluence[-1] + sampl * data[-2][k])
#
#--- new period starts
#
        else:
            nperiod += 1
            fluence.append(sampl * data[-2][k])
#
#--- replace the fluence list
#
    data[-1] = fluence
    
    return data

#-----------------------------------------------------------------------------
#-- update_ace_archive: update ace.archive data file                        --
#-----------------------------------------------------------------------------

def update_ace_archive(updated_data, head):
    """
    update ace.archive data file
    input:  updated_data    --- a list of lists of data
            head            --- a list of header lines
    output: <ace_dir>/Data/ace.archive
    """
#
#--- prep to update the table
#
    line = ''
    for ent in head: 
        line = line + ent + '\n'
#
#--- cutting time 
#
    cut = updated_data[0][0] - ace_delt
#
#--- reverse the line: newest to oldeest
#-- atime, jtime, echk, ech1, ech2, pchk, pch1, pch2, pch3, pch4, pch5, anis, fluen
#
    dlen = len(updated_data[0])
    for k in range(0, dlen):
        m = dlen - k -1
        if updated_data[0][m] > cut:
            line = line + updated_data[1][m]
            line = line + '%3d'   % updated_data[2][m]
            line = line + line_adjust(updated_data[3][m])
            line = line + line_adjust(updated_data[4][m])
            line = line + '%3d'   % updated_data[5][m]
            line = line + line_adjust(updated_data[6][m])
            line = line + line_adjust(updated_data[7][m])
            line = line + line_adjust(updated_data[8][m])
            line = line + line_adjust(updated_data[9][m])
            line = line + line_adjust(updated_data[10][m])
            line = line + '%7.2f' % updated_data[11][m]
            line = line + line_adjust(updated_data[12][m])
            line = line + line_adjust(updated_data[13][m])
            line = line + '\n'

    ofile = ace_data + 'ace.archive'

    with open(ofile, 'w') as fo:
        fo.write(line)

#-----------------------------------------------------------------------------
#-- update_secondary_archive_files: update ace_12h_archive, ace_7day_archive and long tem data files
#-----------------------------------------------------------------------------

def update_secondary_archive_files(ndata):
    """
    update ace_12h_archive, ace_7day_archive data files
    input:  ndata   --- a list of lists of the newest data
    output: <ace_dir>/Data/ace_12h_archive
            <ace_dir>/Data/ace_7day_archive
    """
#
#--- the start and stop time of the newest ace data table
#
    tstart = ndata[0][0]
    tstop  = ndata[0][-1]
#
#--- 12hr data set
#
    dfile  = ace_data + 'ace_12h_archive'
    cut    = tstop  - 43200.0
    create_new_table(dfile, ndata, tstart, cut)
#
#--- 7 day data set
#
    dfile  = ace_data + 'ace_7day_archive'
    cut    = tstop  - 7 * 86400.0
    create_new_table(dfile, ndata, tstart, cut)

#-----------------------------------------------------------------------------
#-- update_long_term_data: update long term data                           ---
#-----------------------------------------------------------------------------

def update_long_term_data(ndata):
    """
    update long term data
    input:  ndata   --- a list of lists of new data
    output: <ace_dir>/Data/longterm/ace_data.txt
    """
    dfile = ace_data + 'longterm/ace_data.txt'
    data  = mcf.read_data_file(dfile)
    atemp = re.split('\s+', data[-1])
#
#--- convert time in Chandra Time
#
    ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' + atemp[3][0] + atemp[3][1] + ':'
    ltime = ltime    + atemp[3][2] + atemp[3][3] + ':00' 
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
    stime = int(Chandra.Time.DateTime(ltime).secs)

    dlen  = len(ndata[0])
    line  = ''
    for m in range(0, dlen):
        if ndata[0][m] > stime:
#
#--- record only good data
#
            if ndata[2][m] != 0 or ndata[5][m] != 0:
                continue

        line = line + ndata[1][m]
        line = line + '%3d'   % ndata[2][m]
        line = line + line_adjust(ndata[3][m])
        line = line + line_adjust(ndata[4][m])
        line = line + '%3d'   % ndata[5][m]
        line = line + line_adjust(ndata[6][m])
        line = line + line_adjust(ndata[7][m])
        line = line + line_adjust(ndata[8][m])
        line = line + line_adjust(ndata[9][m])
        line = line + line_adjust(ndata[10][m])
        line = line + '%7.2f' % ndata[11][m]
        line = line + '\n'

    with open(dfile, 'a') as fo:
        fo.write(line)

#-----------------------------------------------------------------------------
#-- create_new_table: update the data table file with the newest data       --
#-----------------------------------------------------------------------------

def create_new_table(dfile, ndata, tstart, cut):
    """
    update the data table file with the newest data
    input:  dfile   --- data file name
            ndata   --- a list of lists of data
            tstart  --- the time of ndata start
            cut     --- the time to drop older data part
    ouptput dfile   --- updated data file
    """
#
#--- read the previous data
#
    odata  = mcf.read_data_file(dfile)

    line = ''
    for ent in odata:
        atemp = re.split('\s+', ent)
#
#--- convert time in Chandra Time
#
        ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' + atemp[3][0] + atemp[3][1] + ':'
        ltime = ltime    + atemp[3][2] + atemp[3][3] + ':00' 
        ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
        stime = int(Chandra.Time.DateTime(ltime).secs)
        if stime < cut:
            continue
        elif stime > tstart:
            break
        else:
            line = line + ent + '\n'
#
#--- append the newest data 
#
    for m in range(0, len(ndata[0])):
        line = line + ndata[1][m]
        line = line + '%3d'   % ndata[2][m]
        line = line + line_adjust(ndata[3][m])
        line = line + line_adjust(ndata[4][m])
        line = line + '%3d'   % ndata[5][m]
        line = line + line_adjust(ndata[6][m])
        line = line + line_adjust(ndata[7][m])
        line = line + line_adjust(ndata[8][m])
        line = line + line_adjust(ndata[9][m])
        line = line + line_adjust(ndata[10][m])
        line = line + '%7.2f' % ndata[11][m]
        line = line + '\n'

    with open(dfile, 'w') as fo:
        fo.write(line)
    
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def line_adjust(ent):
    if ent < 0.0:
        line = ' %.2e' % ent
    else:
        line = '  %.2e' % ent
    return line

#-----------------------------------------------------------------------------
#-- compute_latest_fluence: compute the fluence of the last period         ---
#-----------------------------------------------------------------------------

def compute_latest_fluence(data_set, c_start):
    """
    compute the fluence of the last period
    input:  data_set---  a list of lists of data
            c_start --- a list of fluence reset time
    output: a list of fluence of each channel and integreation time in seconds
    """
#
#--- find the fluence period starting time
#
    r_start = c_start[::-1]
    for ent in r_start:
        if data_set[0][-1] > ent:
            f_start = ent
            break

    fech1 = 0.0
    fech2 = 0.0
    fpch1 = 0.0
    fpch2 = 0.0
    fpch3 = 0.0
    fpch4 = 0.0
    fpch5 = 0.0
    dlen  = len(data_set[0])
    for k in range(0, dlen):
#
#--- drop bad data
#
        if (data_set[2][k] != 0) or (data_set[5][k] != 0):
            continue
     
        if data_set[0][k] < f_start:
            continue
#
#--- drop all negative values
#
        chk = 0
        for n in range(3, 11):
            if data_set[n][k] < 0.0:
                chk = 1
                continue
        if chk  > 0:
            continue

        fech1 += data_set[3][k]  * sampl
        fech2 += data_set[4][k]  * sampl
        fpch1 += data_set[6][k]  * sampl
        fpch2 += data_set[7][k]  * sampl
        fpch3 += data_set[8][k]  * sampl
        fpch4 += data_set[9][k]  * sampl
        fpch5 += data_set[10][k] * sampl
    
    tacc = data_set[0][-1] - f_start

    return [fech1, fech2, fpch1, fpch2, fpch3, fpch4, fpch5, tacc]

#-----------------------------------------------------------------------------
#-- updat_fluace_data_file: fluace data file                                --
#-----------------------------------------------------------------------------

def updat_fluace_data_file(data_set, header,  c_start):
    """
    update fluace data file
    input:  data_set---  a list of lists of data
            header  --- a list of header lines
            c_start --- a list of fluence reset time
    output: <ace_dir>/Data/fluace.dat
    """
#
#--- compute the latest fluence
#
    [fech1, fech2, fpch1, fpch2, fpch3, fpch4, fpch5, tacc] = compute_latest_fluence(data_set, c_start)
#
#--- start writing data table --- the header part first
# 
    line = 'Latest valid ACE flux data...\n'
    line = line + header[-3] + '\n' + header[-2] + '\n' + header[-1] + '\n'
#
#--- find the latest valid flux data line
#
    for m in range(len(data_set[0])-1, 0, -1):
        chk = 0
        for n in range(3, 11):
            if data_set[n][m] < 0.0:
                chk = 1
                continue
        if chk  > 0:
            continue

        if data_set[2][m] == 0:
            line = line + data_set[1][m]
            line = line + '%3d'   % data_set[2][m]
            line = line + line_adjust(data_set[3][m])
            line = line + line_adjust(data_set[4][m])
            line = line + '%3d'   % data_set[5][m]
            line = line + line_adjust(data_set[6][m])
            line = line + line_adjust(data_set[7][m])
            line = line + line_adjust(data_set[8][m])
            line = line + line_adjust(data_set[9][m])
            line = line + line_adjust(data_set[10][m])
            line = line + '%7.2f' % data_set[11][m]
            line = line + '\n'
            break
#
#--- then fluence data part
#
    line = line + 'Fluence data...' + ' '* 95 + 'Int Time(s)\n'
    line = line + data_set[1][-1]
    line = line + '  -'
    line = line + line_adjust(fech1)
    line = line + line_adjust(fech2)
    line = line + '  -'
    line = line + line_adjust(fpch1)
    line = line + line_adjust(fpch2)
    line = line + line_adjust(fpch3)
    line = line + line_adjust(fpch4)
    line = line + line_adjust(fpch5)
    line = line + '%10d' % tacc
    line = line + '\n'
    
    ofile = ace_data + 'fluace.dat'
    with open(ofile, 'w') as fo:
        fo.write(line)

#-----------------------------------------------------------------------------
#-- update_kp_data_file: copy kp data and create a file to match in the required format
#-----------------------------------------------------------------------------

def update_kp_data_file():
    """
    copy kp data and create a file to match in the required format
    input: none but read from: <kp_dir>/Data/k_index_data_past
    output: <ace_dir>/Data/kp.dat
    """
#
#--- header part
#
    head =        '# Prepared by Helmholtz Centre Potsdam.\n'
    head = head + '# See: https://www.gfz-potsdam.de/en/kp-index/ \n'
    head = head + '#\n'
    head = head + '# Units: Predicted Index 0-9 in Kp units\n'
    head = head + '#\n'
    head = head + '# Solar Wind Source: See: ttps://www.gfz-potsdam.de/en/kp-index/\n'
    head = head + '# The value -1 in the report indicates missing data.\n'
    head = head + '#\n'
    head = head + '#                      USAF 3 hours Wing Kp Geomagnetic Activity Index\n'
    head = head + '#\n'
    head = head + '#                        '
    head = head + '3-hour         3-hour        3-hour         3-hour     \n'
    head = head + '# UT Date   Time      Predicted Time  Predicted    '
    head = head + 'Predicted Time  Predicted   USAF Est.\n'
    head = head + '# YR MO DA  HHMM      YR MO DA  HHMM    Index      '
    head = head + 'YR MO DA  HHMM    Index        Kp    \n'
    head = head + '#' + '-'*87 + '\n'
#
#--- read kp data   
#
    ifile = kp_dir + 'Data/k_index_data_past'
    data  = mcf.read_data_file(ifile)
    
    atemp = re.split('\s+', data[-1])
    ltime = float(atemp[0])
    kval  = atemp[1]
    
    ltime = Chandra.Time.DateTime(ltime).date
    mc= re.search('\.', ltime)
    if mc is not None:
        btemp = re.split('\.', ltime)
        ltime = btemp[0]
    
    ldate = datetime.strptime(ltime, '%Y:%j:%H:%M:%S').strftime("%Y %m %d %H%M")
    
    line  = ldate + '\t\t' + ldate + '\t\t' + kval + '\t\t\t' 
    line  = line  + ldate + '\t\t' + kval + '\t\t' + kval + '\n'
    line  = head + line
    
    ofile = ace_data + 'kp.dat'
    
    with open(ofile, 'w') as fo:
        fo.write(line)

#-----------------------------------------------------------------------------

if __name__ == "__main__":

    update_ace_data_files()

