#!/proj/sot/ska3/flight/bin/python

#################################################################################
#                                                                               #
#       update_goes_integrate_page.py: create goes integrated html page         #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#           last update: Aug 07, 2024                                           #
#                                                                               #
#################################################################################

import os
import time
import Chandra.Time
import datetime
import urllib.request
import json
import numpy
import traceback
import argparse

#
#--- Define Directory Pathing
#
GOES_DIR = '/data/mta4/Space_Weather/GOES'
GOES_DATA_DIR = f"{GOES_DIR}/Data"
GOES_TEMPLATE_DIR = f"{GOES_DIR}/Scripts/Template"
HTML_GOES_DIR = '/data/mta4/www/RADIATION_new/GOES'

#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- json data locations proton and electron
#
PLINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json'
ELINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json'
#
#--- protone energy designations and output file names
#
PROTON_LIST = ['>=1 MeV', '>=5 MeV', '>=10 MeV', '>=30 MeV', '>=50 MeV',\
               '>=60 MeV', '>=100 MeV', '>=500 MeV']
#
#--- electron energy designation and output file name
#
ELEC_LIST   = ['>=2 MeV',]

#
#--- current goes satellite #
#
SATELLITE = "Primary"
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
    with open(f"{GOES_TEMPLATE_DIR}/G_header", 'r') as f:
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
    with open(f"{GOES_TEMPLATE_DIR}/Gp_image_int", 'r') as f:
        line = line + f.read()
#
#---- add footer
#
    with open(f"{GOES_TEMPLATE_DIR}/G_footer", 'r') as f:
        line = line + f.read()
#
#--- substitute a couple of lines
#
    line = line.replace('#GNUM#', SATELLITE)
    line = line.replace('#SELECT#', 'Integrated')
#
#--- update the page
#
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        outfile = test_out + "/" + os.path.basename(outfile)
    with open(f"{HTML_GOES_DIR}/goes_part_p.html", 'w') as fo:
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
    p_save = extract_goes_data(PLINK, PROTON_LIST)
#
#--- electron data
#
    e_save = extract_goes_data(ELINK, ELEC_LIST)
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

    if (os.getenv('TEST') == 'TEST'):
        outfile = test_out + "/" + os.path.basename(outfile)
    with open(f"{GOES_DATA_DIR}/Gp_part_5min.txt", 'w') as fo:
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
#--- read json file from a file or the web
#
    if os.path.isfile(dlink):
        try:
            with open(dlink) as f:
                data = json.load(f)
        except:
            traceback.print_exc()
            data = []
    else:
        try:
            with urllib.request.urlopen(dlink) as url:
                data = json.loads(url.read().decode())
        except:
            traceback.print_exc()
            data = []

    if len(data) < 1:
        exit(1)
#
#--- go through all energy ranges
#
    elen   = len(energy_list)
    d_save = []
    ctime = datetime.datetime.strptime(data[-1]['time_tag'], '%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(hours=2)
    for k in range(0, elen):
        t_list = []
        f_list = []
        energy = energy_list[k]
        last_time = datetime.datetime.strptime(data[0]['time_tag'], '%Y-%m-%dT%H:%M:%SZ')
#
#--- check the last entry time and select only last 2 hrs
#
        for ent in data:
#
#--- read time and flux of the given energy range
#
            if ent['energy'] == energy:
                flux  = float(ent['flux'])
                otime =  datetime.datetime.strptime(ent['time_tag'], '%Y-%m-%dT%H:%M:%SZ')
                #If the otime is more than five minutes after the last_time
                #then that means the data set is missing an entry for this energy band and zero values should be appened.
                diff = (otime - last_time).seconds
                if diff > 300:
                    #All times should be in divisions of 5 minutes/300 seconds.
                    for i in range(300,int(diff),300):
                        missing_time = last_time + datetime.timedelta(seconds=i)
                        if missing_time > ctime:
                            t_list.append(missing_time.strftime('%Y:%j:%H:%M'))
                            #Mark missing data with the invalid data marker (-1e5)
                            f_list.append(-1e5)
                if otime > ctime:
                    t_list.append(otime.strftime('%Y:%j:%H:%M'))
                    f_list.append(flux)
                    last_time = otime

        d_save.append([t_list, f_list])
#
#--- Check if there is a missing energy at the beginning or ending of a band.
#
    for i in range(len(d_save)):
        #Find a channel with all 24 needed data points and use those time values
        if len(d_save[i][0]) == 24:
            start = d_save[i][0][0]
            stop = d_save[i][0][-1]
            break

    for i in range(len(d_save)):
        if len(d_save[i][0]) < 24:
            #if there is still not 24 data points, then we are missing the start or end of this channel
            if d_save[i][0][0] != start:
                d_save[i][0].insert(0,start)
                d_save[i][1].insert(0,-1e5)
                
            if d_save[i][0][-1] != stop:
                d_save[i][0].append(stop)
                d_save[i][1].append(-1e5)
    return d_save

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def adjust_format(val):

    val = float(val)
    if val < 0: #Missing entry
        out = f"{val:5.0f}"
    elif val < 10:
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
