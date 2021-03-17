#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################
#                                                                               #
#       update_goes_integrate_page.py: create goes integrated html page         #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: mar 16, 2021                                           #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import math
import time
import datetime
import Chandra.Time
import urllib.request
import json
import random
import numpy

path = '/data/mta4/Space_Weather/house_keeping/dir_list'
with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append path to a private folder
#
sys.path.append(goes_dir)
sys.path.append('/data/mta4/Script/Python3.8/MTA/')

#import mta_common_functions     as mcf
#
#--- set a temporary file name
#
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- json data locations proton and electron
#
plink = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json'
elink = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json'
#
#--- protone energy designations and output file names
#
proton_list = ['>=1 MeV', '>=5 MeV', '>=10 MeV', '>=30 MeV', '>=50 MeV',\
               '>=60 MeV', '>=100 MeV', '>=500 MeV']
#
#--- electron energy designation and output file name
#
elec_list   = ['>=2 MeV',]
#
#--- goes data directory
#
data_dir  = goes_dir + 'Data/'
templ_dir = goes_dir + 'Scripts/Template/'
#
#--- current goes satellite #
#
satellite = "Primary"
#----------------------------------------------------------------------------
#-- update_goes_integrate_page: update the GOES integrated page            --
#----------------------------------------------------------------------------

def update_goes_integrate_page():
    """
    update the GOES integrated page
    input:  none but read from:
                'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json'
                'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json'
    output: <html_dir>/GOES/goes_part_p.html 
    """
#
#--- read the header template
#
    hfile = templ_dir + 'G_header'
    with open(hfile, 'r') as f:
        line = f.read()
#
#--- add the table
#
    line = line + '<pre>\n'
    line = line + make_two_hour_table()
    line = line + '</pre>\n'
    line = line + '<br />\n'
#
#--- add the image link
#
    hfile = templ_dir + 'Gp_image_int'
    with open(hfile, 'r') as f:
        line = line + f.read()
#
#---- add footer
#
    hfile = templ_dir + 'G_footer'
    with open(hfile, 'r') as f:
        line = line + f.read()
#
#--- substitute a couple of lines
#
    line = line.replace('#GNUM#', str(satellite))
    line = line.replace('#SELECT#', 'Integrated')
#
#--- update the page
#
    ####outfile = html_dir + 'GOES/goes16_part_p.html'
    outfile = html_dir + 'GOES/goes_part_p.html'
    with open(outfile, 'w') as fo:
        fo.write(line)

#----------------------------------------------------------------------------
#-- make_two_hour_table: create two hour table of goes proton/electron flux 
#----------------------------------------------------------------------------

def make_two_hour_table():
    """
    create two hour table of goes proton/electron flux
    input: none, but read from web
    output: <data_dir>/<out file>
    """
#
#--- proton data: [[<time list>, <data1 list>], [<time list>,<data2 list>], ...]
#
    p_save = extract_goes_data(plink, proton_list)
#
#--- electron data
#
    e_save = extract_goes_data(elink, elec_list)
#
#--- combine the data
#
    p_save = p_save + e_save
#
#--- start writing the table
#
    line = '\t' * 10
    line = line + 'Most Recent GOES #GNUM# Observations\n'
    line = line + '\t' * 8
    line = line + 'Solar Particle and Electron Flux particles/cm2-s-ster\n\n'
    line = line + '\tTime\t\t\t>1Mev\t\t>5MeV\t\t>10MeV\t\t>30MeV\t\t>50MeV\t\t'
    line = line + '>60MeV\t\t>100MeV\t\t>500MeV\t\tElectron\n'
    line = line + '\t' + '-'*150 +'\n'
#
#--- aline will save the text output of the table which is used by CRM
#
    aline = ''
#
#--- data length
#
    flen = len(p_save[0][0])
    for k in range(0, flen):
#
#--- print time data 
#
        tout  = str(p_save[0][0][k]).strip()
        line  = line + '\t' + tout + '\t\t'
#
#--- data file has a different time format
#
        aline = aline + time.strftime('%Y %m %d %H%M', time.strptime(tout, '%Y:%j:%H:%M'))
        aline = aline + ' 99999 99999\t'    #--- adding dummy julian time
#
#--- print flax data
#
        for m in range(0, len(p_save)):
            try:
                out  = adjust_format(p_save[m][1][k])
            except:
                continue
            line = line   +  out +"\t\t" 
            #line = line   + "%1.5f\t\t" % (p_save[m][1][k]) 
            aline = aline + "%2.3e\t\t" % (p_save[m][1][k])
        line = line + '\n'
#
#--- electron does not have distinction fo 0.8 2.8 or 4.0; so fake with all E>2.0
#
        try:
            aline = aline  + "%2.3e\t%2.3e\n" % (p_save[m][1][k], p_save[m][1][k])
        except:
            aline = aline  + "na\t%na\n" % (p_save[m][1][k], p_save[m][1][k])
#
#--- table break
#
    line = line + '\n'
    line = line + '\t' + '-'*150 +'\n\n'
#
#--- add average and sum of the data
#
    line = line + '\tAVERAGE\t\t\t'
    for m in range(0, len(p_save)):
        #line = line + "%1.5f\t\t" % (numpy.mean(p_save[m][1]))
        out = adjust_format(numpy.mean(p_save[m][1]))
        line  = line + out + '\t\t'

    line = line + '\n'

    line = line + '\tFLUENCE\t\t\t'
    for m in range(0, len(p_save)):
        #line = line + "%5.0f\t\t" % (numpy.sum(p_save[m][1]) * 7200.0)
        out = adjust_format(numpy.sum(p_save[m][1]) * 7200.0)
        line = line + out + '\t\t'
#
#--- set data file 
#
    bline = ':This file contains data used by CRM scripts\n:Created: Unknown\n'
    for k in range(0, 22):
        bline = bline + '#\n'
    bline = bline + '#\tTime\t\t\t\t\t>1Mev\t\t>5MeV\t\t>10MeV\t\t>30MeV\t\t>50MeV\t\t'
    bline = bline + '>60MeV\t\t>100MeV\t\t>500MeV\t\tElectron\n'
    bline = bline + '\t' + '-'*150 +'\n'
    bline = bline + aline

    outfile = data_dir + 'Gp_part_5m.txt'
    with open(outfile, 'w') as fo:
        fo.write(bline)

    return line

#----------------------------------------------------------------------------
#-- extract_goes_data: extract GOES satellite flux data                    --
#----------------------------------------------------------------------------

def extract_goes_data(dlink, energy_list):
    """
    extract GOES satellite flux data
    input: dlink        --- json web address
            energy_list --- a list of energy designation 
    output: <data_dir>/<out file>
    """
#
#--- read json file from the web
#
    try:
        with urllib.request.urlopen(dlink) as url:
            data = json.loads(url.read().decode())
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
#
#--- check the last entry time  and select only last 2 hrs
#
        try:
            ltime  = check_last_entry_time(data)
        except:
            exit(1)
        ctime  = ltime - 3600.0 * 2
        for ent in data:
#
#--- get the data from a specified satellite
#
#            if ent['satellite'] != satellite:
#                continue
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
                flux  = float(ent['flux'])
                if flux < 0.0:
                    flux = 0.0
#
#--- convert time into seconds from 1998.1.1
#
                otime = ent['time_tag']
                dtime = time.strftime('%Y:%j:%H:%M',    time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
                stime = int(Chandra.Time.DateTime(otime).secs)

                if stime <= ctime:
                    continue

                t_list.append(dtime)
                f_list.append(flux)

        d_save.append([t_list, f_list])

    return d_save

#----------------------------------------------------------------------------
#-- check_last_entry_time: check the last data entry time of the given data file 
#----------------------------------------------------------------------------

def check_last_entry_time(data):
    """
    check the last data entry time of the given data file
    input:  data    --- data
    output: ltime   --- the last entry time in seconds from 1998.1.1
    """

    ent = data[-1]
    otime = ent['time_tag']
    otime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(otime, '%Y-%m-%dT%H:%M:%SZ'))
    stime = int(Chandra.Time.DateTime(otime).secs)

    return stime

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def adjust_format(val):
    
    val = float(val)
    if val < 10:
        out = "%1.5f" % (val)
    elif val < 100:
        out = "%2.4f" % (val)
    elif val < 1000:
        out = "%3.3f" % (val)
    elif val < 10000:
        out = "%4.2f" % (val)
    elif val < 100000:
        out = "%5.1f" % (val)
    else:
        out = "%5.0f" % (val)

    return out
                                                                                           
#----------------------------------------------------------------------------

if __name__ == "__main__":

    update_goes_integrate_page()
