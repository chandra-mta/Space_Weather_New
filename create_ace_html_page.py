#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#####################################################################################################
#                                                                                                   #
#               create_ace_html_page.py: read ace data and update html page                         #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Jan 13, 2021                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import string
import random
import operator
import time
import datetime
import numpy
import Chandra.Time
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
sys.path.append('/data/mta4/Script/Python3.6/MTA/')
#
#--- import several functions
#
import mta_common_functions as mcf
#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- set direcotries
#
data_dir   = ace_dir + 'Data/'
templ_dir  = ace_dir + 'Scripts/Template/'
web_dir    = html_dir + 'ACE/'
plot_dir   = web_dir  + 'Plots/'
#
#--- ftp, html site setting
#
http_epam = 'http://' + noaa_site + 'images/ace-epam-7-day.gif'
http_mag  = 'http://' + noaa_site + 'images/ace-mag-swepam-7-day.gif'
#
#--- set parameters
#
p5_p3_scale  = 7.           #--- scale P5 to P3 values, while P3 is broke
p6_p3_scale  = 36.          #--- scale P6 to P3 values, while P3 is broke
p7_p3_scale  = 110.         #--- scale P7 to P3 values, while P3 is broke

#---------------------------------------------------------------------------------------------------
#-- create_ace_html_page: read ace data and update html page                                      ---
#---------------------------------------------------------------------------------------------------

def create_ace_html_page():
    """
    read ace data and update html page
    input:  none, but read from:
            http://services.swpc.noaa.gov/images/ace-epam-7-day.gif
            http://services.swpc.noaa.gov/images/images/ace-mag-swepam-7-day.gif
            <ace_dir>/Data/ace_12h_archive
    output: <html_dir>/ACE/ace.html
    """
#
#---- read 12h_archive data
#
    ifile          = data_dir + 'ace_12h_archive'
    cdata          = mcf.read_data_file(ifile)
#
#--- cdata:     a list of lists of electron/proton flux data 
#--- l_vals:    a list of the 'last' entries of those electron/proton flux data
#--- data is also trimmed to the last 2 hours
#
    cdata_cols, l_vals = convert_to_col_data(cdata)
#
#--- create data table for the html page
#
    ace_table = create_ace_data_table(cdata_cols, l_vals)
#
#--- download images and reverse the color:
#
    download_img(http_epam)
    download_img(http_mag)
#
#--- update ace html page
#
    ifile = templ_dir + 'header'
    line  = read_file(ifile)
    line  = line + '\n'

    ifile = templ_dir + 'header1'
    line  = line + read_file(ifile)

    line  = line + ace_table
    line  = line + '\n'

    ifile = templ_dir + 'image2'
    line  = line + read_file(ifile)
    line  = line + '\n'

    ifile = templ_dir + 'footer'
    line  = line + read_file(ifile)
    line  = line + '\n'

    out   = web_dir + 'ace.html'
    with open(out, 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------------------
#-- create_ace_data_table: craete data tables from a given data list                              --
#---------------------------------------------------------------------------------------------------

def create_ace_data_table(cdata, l_vals):
    """
    craete data tables from a given data list
    input:  cdata   --- a list of lists of data
                        [atime, jtime, echk, ech1, ech2, pchk, pch2, pch3, pch5, pch6, pch7]
            l_vals  --- a list of the 'last'entry values
                        [ech1_last, ech2_last, pch2_last, pch3_last, pch5_last, pch6_last, pch7_last]]
    output: line    --- table

    """
    c_len = len(cdata[0])
#
#--- last valid entry records --- these are values just outside of the current data period
#
    p2_last  =  l_vals[2]
    p3_last  =  l_vals[3]
    p5_last  =  l_vals[4]
    p6_last  =  l_vals[5]
    p7_last  =  l_vals[6]
#
#--- initialize scaled lists
#
    p5_p3_scaled = []
    p6_p3_scaled = []
    p7_p3_scaled = []
    for k in range(0, c_len):
        p5_p3_scaled.append(-10000)
        p6_p3_scaled.append(-10000)
        p7_p3_scaled.append(-10000)
#
#--- for ease of read...
#
    ctime = cdata[0]                #--- Chandra Time
    jtime = cdata[1]                #--- display time
    echk  = numpy.array(cdata[2])   #--- whether electron data is good 
    de1   = numpy.array(cdata[3])
    de4   = numpy.array(cdata[4])
    pchk  = numpy.array(cdata[5])   #--- whether proton data is good
    p2dat = numpy.array(cdata[6])
    p3dat = numpy.array(cdata[7])
    p5dat = numpy.array(cdata[8])
    p6dat = numpy.array(cdata[9])
    p7dat = numpy.array(cdata[10])
#
#--- go through the data
#
    line = ''
    for k in range(0, c_len):
#
#--- pchk and p3
#
        if pchk[k] == 0:
            plast   = p3_last
            p3_diff = p3dat[k] - p3_last
            if p3dat[k] > 0 and p3_diff > 500000:
                p3dat[k] = -999
                pchk[k]  = 1

        if p3dat[k] > 0:
            p3_last = p3dat[k]
#
#---- p2
#
        p2_diff = p2dat[k] - p2_last
        if p2dat[k]  > 0 and p2_diff > 1000000:
            p2dat[k] = -999
            pchk[k]  = 1

        if p2dat[k] > 0:
            p2_last = p2dat[k]
#
#--- p5
#
        p5_diff = p5dat[k] -  p5_last
        if p5dat[k] and p5_diff  > 40000:
            p5dat[k] = -999
            pchk[k]  = 1
            p5_p3_scaled[k] = -999

        if p5dat[k] > 0:
            p5_last = p5dat[k]
#
#--- p6
#
        p6_diff = p6dat[k] - p6_last
        if p6dat[k] and  p6_diff > 20000:
            p6dat[k] = -999
            pchk[k]  = 1
            p6_p3_scaled[k] = -999

        if p6dat[k] > 0:
            p6_last = p6dat[k]
#
#--- p7
#
        p7_diff = p7dat[k] - p7_last
        if p7dat[k] > 0 and p7_diff> 10000:
            p7dat[k] = -999
            pchk[k]  = 1
            p7_p3_scaled[k] = -999

        if p7dat[k] > 0:
            p7_last = p7dat[k]
#
#---  replace the scaled data with valid data if the original values are good
#
        if p5dat[k] > 0:
            p5_p3_scaled[k] = p5dat[k] * p5_p3_scale

        if p6dat[k] > 0:
            p6_p3_scaled[k] = p6dat[k] * p6_p3_scale

        if p7dat[k] > 0:
            p7_p3_scaled[k] = p7dat[k] * p7_p3_scale
#
#--- if data is ok, add the line to the table data
#
        if pchk[k] == 0:
            aline = "%s%11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f\n"\
                    % (cdata[1][k], de1[k], de4[k], p2dat[k], p3dat[k],\
                       p5_p3_scaled[k], p6_p3_scaled[k], p5dat[k], p6dat[k], p7dat[k])

            line  = line + aline
#
#--- the table part is done, compute other entries
#
#
#--- compute mean and find min of p5, p6, and p7
#
    ind    = [p5dat > 0]
    cdat   = p5dat[ind]
    if len(cdat) > 0:
        p337a  = numpy.mean(cdat)
        p337m  = min(cdat)
    else:
        p337a  = 0   
        p337m  = 0   

    ind    = [p6dat > 0]
    cdat   = p6dat[ind]
    if len(cdat) > 0:
        p761a  = numpy.mean(cdat)
        p761m  = min(cdat)
    else:
        p761a  = 0    
        p761m  = 0   

    ind    = [p7dat > 0]
    cdat   = p7dat[ind]
    if len(cdat) > 0:
        p1073a = numpy.mean(cdat)
        p1073m = min(cdat)
    else:
        p1073a = 0   
        p1073m = 0   
#
#---  do the same for the scaled data
#
    p5_p3_scaled  = numpy.array(p5_p3_scaled)
    p6_p3_scaled  = numpy.array(p6_p3_scaled)
    p7_p3_scaled  = numpy.array(p5_p3_scaled)
    p5_p3_scaled  = p5_p3_scaled[p5_p3_scaled >0]
    p6_p3_scaled  = p6_p3_scaled[p6_p3_scaled >0]
    p7_p3_scaled  = p7_p3_scaled[p7_p3_scaled >0]

    if len(p5_p3_scaled) > 0:
        p5_p3a = numpy.mean(p5_p3_scaled)
        p5_p3m = numpy.min(p5_p3_scaled)
    else:
        p5_p3a = 0
        p5_p3m = 0

    if len(p6_p3_scaled) > 0:
        p6_p3a = numpy.mean(numpy.array(p6_p3_scaled))
        p6_p3m = numpy.min(numpy.array(p6_p3_scaled))
    else:
        p6_p3a = 0
        p6_p3m = 0

    if len(p7_p3_scaled) > 0:
        p7_p3a = numpy.mean(numpy.array(p7_p3_scaled))
        p7_p3m = numpy.min(numpy.array(p7_p3_scaled))
    else:
        p7_p3a = 0
        p7_p3m = 0
#
#--- index to find good data
#
    ind    = [pchk == 0]
    ind2   = [echk == 0]

#
#--- check whether there are any good data left after removing bad ones
#
    chk    = len(echk[ind])
    chk2   = len(echk[ind2])

    if (chk == 0) or (chk2 == 0):
        line = line + '<p style="padding-top:40px;padding-bottom:40px;">'
        line = line + " No Valid data for last 2 hours."
        line = line + '</p>\n'
        return  line
#
#--- there are good data
#
    p56    = p2dat[ind]
    p56    = p56[p56 >0]
    p130   = p3dat[ind]
    p130   = p130[p130 > 0]
    if len(p56) > 0:
        p56a   = numpy.mean(p56)
        p56m   = min(p56)
    else:
        p56a   = 0
        p56m   = 0

    if len(p130) > 0:
        p130a  = numpy.mean(p130)
        p130m  = min(p56)
    else:
        p130a  = 0
        p130m  = 0

    e38    = de1[ind2]
    e38    = e38[e38 > 0]
    e175   = de4[ind2]
    e175   = e175[e175 >0]

    if len(e38) > 0:
        e38a   = numpy.mean(e38)
        e38m   = min(e38)
    else:
        e38a   = 0
        e38m   = 0
    if len(e175) > 0:
        e175a  = numpy.mean(e175)
        e175m  = min(e175)
    else:
        e175a  = 0
        e175m  = 0
#
#--- compute fluence of 2 hours
#
    e38f   = e38a   * 7200.
    e175f  = e175a  * 7200.
    p56f   = p56a   * 7200.
    p130f  = p130a  * 7200.
    p337f  = p337a  * 7200.
    p761f  = p761a  * 7200.
    p1073f = p1073a * 7200.
    p5_p3f = p5_p3a * 7200.
    p6_p3f = p6_p3a * 7200.
    p7_p3f = p7_p3a * 7200.
#
#--- compute spectral indcies
#
    if p337a > 0:
        p3_p5  = p130a / p337a
    else:
        p3_p5  = 0
    if p761a > 0:
        p3_p6  = p130a / p761a
    else:
        p3_p6 = 0
    if p761a > 0:
        p5_p6  = p337a / p761a
    else:
        p5_p6 = 0
    if p1073a > 0:
        p6_p7  = p761a / p1073a
    else:
        p6_p7 = 0
    if p1073a > 0:
        p5_p7  = p337a / p1073a
    else:
        p337a = 0
#
#--- violation check
#
    if p130f > 360000000:
        val = "%.4e" % p130f
        ace_violation_protons(val)

    p5_p6_lim = 1.0                 #----????? this is what given in the original, but use below
    p5_p6_lim = 1.0e10

    if (p5_p6 > p5_p6_lim) or (p5_p6 < 1):
        speci     = "%12.1f" % p5_p6
        speci_lim = "%8.1f"  % p5_p6_lim

        ace_invalid_spec(speci, speci_lim)
#
#--- crate a summary table
#
    hfile = templ_dir + 'header2'
    line  = line + "\n" +  read_file(hfile)

    line  = line + "%7s %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f\n"\
                   % ("AVERAGE        ", e38a, e175a, p56a, p130a, p5_p3a, p6_p3a, p337a, p761a, p1073a)

    line  = line + "%7s %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f\n"\
                   % ("MINIMUM        ", e38m, e175m, p56m, p130m, p5_p3m, p6_p3m, p337m, p761m, p1073m)

    line  = line + "%7s %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e\n\n"\
                   % ("FLUENCE        ", e38f, e175f, p56f, p130f, p5_p3f, p6_p3f, p337f, p761f, p1073f)

    line  = line + "%7s %11s %11.3f %11s %11.3f %11s %11.3f %11s %11.3f \n\n"\
                   % ("SPECTRA        ", "p3/p5", p3_p5, "p3/p6", p3_p6, "p5/p6", p5_p6, "p6/p7", p6_p7)

    line  = line + "%62s %4.1f\n"\
                   % ("*   This P3 channel is currently scaled from P5 data. P3* = P5 X ", p5_p3_scale)

    line  = line + "%62s %4.1f\n"\
                   % ("**  This P3 channel is currently scaled from P6 data. P3** = P6 X ", p6_p3_scale)

    line  = line + "%62s %4.1f\n"\
                   % ("*** This P3 channel (not shown) is currently scaled from P7 data. P3*** = P7 X ", p7_p3_scale)

    return line

#---------------------------------------------------------------------------------------------------
#-- ace_violation_protons: send out a warning email                                               --
#---------------------------------------------------------------------------------------------------

def ace_violation_protons(val):
    """
    send out a warning email
    input:  val --- value
    output: email sent out
    """
    line = 'A Radiation violation of P3 (130KeV) has been observed by ACE\n'
    line = line + 'Observed = ' + val + '\n'
    line = line + '(limit = fluence of 3.6e8 particles/cm2-ster-MeV within 2 hours)\n'
    line = line + 'see http://cxc.harvard.edu/mta/ace.html\n'
#
#--- add current spacecraft info
#
    line = line + curr_state()
#
#--- read alert case
#
    if os.path.isfile('/data/mta4/www/Snapshot/.scs107alert'):
        line = line + 'The ACIS on-call person should review the data and call a telecon if necessary.\n'
        line = line + 'This message sent to sot_ace_alert\n'
        send_mail('ACE_p3', line, 'sot_ace_alert@cfa.harvard.edu')
#
#--- yellow alert case
#
    else:
        line = line + 'This message sent to sot_yellow_alert\n'
        send_mail('ACE_p3', line, 'sot_yellow_alert@cfa.harvard.edu')

#---------------------------------------------------------------------------------------------------
#-- ace_invalid_spec: sending out a warning email                                                 --
#---------------------------------------------------------------------------------------------------

def ace_invalid_spec(speci, speci_lim):
    """
    sending out a warning email 
    input:  speci       --- the value reported
            speci_lim   --- the limit of the vluae
    output: email sent out
    """
#
#--- check whether the mail is recently sent out
#
    out = '/tmp/mta/prot_spec_violate'
    if os.path.isfile(out):
        cmd = 'date >> ' + out
        os.system(cmd)
#
#--- if not, send the warning email
#
    else:
        line = " A spectral index violation of P5/P6 has been observed by ACE, "
        line = line + "indicating a possibly invalid P5 channel.\n"
        line = line + 'Observed = ' + speci
        line = line + '(limit = ' + speci_lim + ')\n'
        line = line + 'see http://cxc.harvard.edu/mta/ace.html\n'
        line = line + 'This message sent to sot_yellow_alert\n'

        send_mail('ACE_p5/p6', line, 'sot_yellow_alert@cfa.harvard.edu')
#
#--- open a file indicating that the mail was sent
#
        with open(out, 'w') as fo:
            fo.write(line)

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def send_mail(subject, content, address):

    fo = open(zspace, 'w')
    fo.write(content)
    fo.close()

#---- REMOVE the line below after test finished!!!!-------------------
    address = 'tisobe@cfa.harvard.edu'
#---------------------------------------------------------------------

    cmd = 'cat ' + zspace + '|mailx -s "' + subject + '" ' + address
    os.system(cmd)
    
    cmd = 'rm ' + zspace
    os.system(cmd)

#---------------------------------------------------------------------------------------------------
#-- curr_state: extract some satellite related information                                        --
#---------------------------------------------------------------------------------------------------

def curr_state():
    """
    extract some satellite related information
    input:  none
    output: line    --- lines which display the satellite information
    """
#
#--- read CRM file to get some information
#
    sfile = crm_dir + 'CRMsummary.dat'
    data  = mcf.read_data_file(sfile)

    dirct = 'NA'
    dist  = 'NA'
    if len(data) < 1:
        dline = ''
    else:
        dline = data[0]
    for ent in data:
        mc = re.search('Geocentric Distance', ent)
        if mc is not None:
            atemp = re.split(':', ent)
            btemp = re.split('\s+', atemp[1].strip())
            dist  = btemp[0]
            if btemp[1] == 'A':
                dirct = 'Ascending'
            else:
                dirct = 'Descending'

    line  = 'Currently ' + dirct + ' through ' + dist + 'km with ' + dline + '\n\n'
#
#-- get DSN contact info from ephem data
#
    ctime = time.trftime("%Y:%j:%H:%M:%S", time.gmtime())
    start = Chandra.Time.DateTime(ctime).secs 
    stop  = start + 3.0 * 86400.

    ifile = ephem_dir + 'dsn_summary.dat'
    data  = read_file_data(ifile)
    data  = data[2:]
    line  = line + data[0] + '\n' + data[1] + '\n'
    for ent in data:
        atemp = re.split('\s+', ent)
        year  = atemp[10]
        yday  = atemp[11]
        stime = convert_to_stime(year, yday)
        if stime >= start and stime < stop:
            line = line + ent + '\n'

    line = line + '\n'

    return line

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def convert_to_stime(year, yday):

    atemp = re.split('\.', yday)
    frac  = float(atemp[1]) 
    val   = 24. * frac
    hh    = int(val)
    diff  = val - hh
    val   = 60 * diff
    mm    = int(val)
    diff  = val - mm
    ss    = int(60 *diff)

    htime = str(year) + ':' + atemp[0] + ':' + str(hh) + ':' + str(mm) + ':' + str(ss)
    
    stime = Chandra.Time.DateTime(htime).secs 

    return stime

#---------------------------------------------------------------------------------------------------
#-- download_img: down load an image from web site                                                --
#---------------------------------------------------------------------------------------------------

def download_img(file, chg=1):
    """
    down load an image from web site
    input:  file    --- image file address
            chg     --- if >0, reverse the color
    output: <plot_dir>/<name of the image>
    """
#
#--- get the name of output img file name
#
    atemp = re.split('\/', file)
    ofile = atemp[-1]
    oimg  =  plot_dir + ofile
#
#--- download the img
#
    #cmd   = 'lynx -source ' + file + '>' + oimg
    cmd   = 'wget -q -O' + oimg + ' ' + file
    os.system(cmd)
#
#--- reverse the color of the image
#
    if chg == 1:
        cmd   = 'convert -negate ' +  oimg + ' ' + oimg
        os.system(cmd)


#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_file(ifile):

    f    = open(ifile, 'r')
    data = f.read()
    f.close()

    return data

    
#-----------------------------------------------------------------------------
#-- convert_to_col_data: read  data into a list of lists                    --
#-----------------------------------------------------------------------------

def convert_to_col_data(data):
    """
    convert the list of row data into column data
    input:  a list of lists
    output: a list of lists of:
            atime   --- a time in seconds from 1998.1.1
            jtime   --- a string time
            echk    --- data quality of electron data
            ech1    --- electron 38-53
            ech2    --- electron 175-315
            pchk    --- data quality of proton
            pch2    --- proton 47-68
            pch3    --- proton 115-195
            pch5    --- proton 310-580
            pch6    --- proton 795-1193
            pch7    --- proton 1060-1900

            [ech1_last, ech2_last, pch2_last, pch3_last, pch5_last, pch6_last, pch7_last]
                --- this is a list of the last valid flux data before the current data set
    """
#
#--- find the most recent entry time and set the cutting time to 2 hrs before that
#
    atemp   = re.split('\s+', data[-1])
    ltime = atemp[0] + ':' + atemp[1] + ':' + atemp[2] + ':' + atemp[3][0] + atemp[3][1] + ':'
    ltime = ltime    + atemp[3][2] + atemp[3][3] + ':00' 
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%Y:%m:%d:%H:%M:%S'))
    cut   = int(Chandra.Time.DateTime(ltime).secs) - 2 * 3600.0 - 60.0

    atime = []
    jtime = []
    echk  = []
    ech1  = []
    ech2  = []
    pchk  = []
    pch2  = []
    pch3  = []
    pch5  = []
    pch6  = []
    pch7  = []
    ptime = 0
    for ent in data:
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
#--- sometime, there are double entries; so remove those
#
        if stime == ptime:
            continue
        else:
            ptime = stime
#
#--- keep the record of 'previous' entry; only valid data
#
        if stime < cut:
            chk1 = int(float(atemp[6]))
            chk2 = int(float(atemp[9]))
            if chk1 == 0 and chk2 == 0:
                ech1_last = float(atemp[7])
                ech2_last = float(atemp[8])
                pch2_last = float(atemp[10])
                pch3_last = float(atemp[11])
                pch5_last = float(atemp[12])
                pch6_last = float(atemp[13])
                pch7_last = float(atemp[14])
            continue
#
#--- save time part in a string format (YR MO DA  HHMM    Day    Day)
#
        ftime = atemp[0] + ' '  + atemp[1] + ' ' + atemp[2] + '  ' + atemp[3]
#        ftime = ftime    + '%8d%8d' % (float(atemp[4]), float(atemp[5]))

        atime.append(stime)
        jtime.append(ftime)
        echk.append(int(float(atemp[6])))
        ech1.append(float(atemp[7]))
        ech2.append(float(atemp[8]))
        pchk.append(int(float(atemp[9])))
        pch2.append(float(atemp[10]))
        pch3.append(float(atemp[11]))
        pch5.append(float(atemp[12]))
        pch6.append(float(atemp[13]))
        pch7.append(float(atemp[14]))

    return [atime, jtime, echk, ech1, ech2, pchk, pch2, pch3, pch5, pch6, pch7],\
                [ech1_last, ech2_last, pch2_last, pch3_last, pch5_last, pch6_last, pch7_last]

#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    create_ace_html_page()

