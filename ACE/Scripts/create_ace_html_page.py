#!/proj/sot/ska3/flight/bin/python

#####################################################################################################
#                                                                                                   #
#               create_ace_html_page.py: read ace data and update html page                         #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Nov 04, 2021                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import time
import numpy
import Chandra.Time
import argparse
#
#---Define Directory Pathing
#
HTTP_EPAM = "http://services.swpc.noaa.gov/images/ace-epam-7-day.gif"
HTTP_MAG = "http://services.swpc.noaa.gov/images/ace-mag-swepam-7-day.gif"
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
TEMPLATE_DIR = "/data/mta4/Space_Weather/ACE/Scripts/Template"
ACE_HTML_DIR = "/data/mta4/www/RADIATION_new/ACE"
ACE_PLOT_DIR = "/data/mta4/www/RADIATION_new/ACE/Plots"
HOUSE_KEEPING = "/data/mta4/Space_Weather/house_keeping"
TMP_DIR = "/tmp/mta"
#
#--- Defining other Globals
#
TESTMAIL = False

P5_P3_SCALE  = 7.           #--- scale P5 to P3 values, while P3 is broke
P6_P3_SCALE  = 36.          #--- scale P6 to P3 values, while P3 is broke
P7_P3_SCALE  = 110.         #--- scale P7 to P3 values, while P3 is broke
P5_P6_LIM = 1.0e10

#---------------------------------------------------------------------------------------------------
#-- create_ace_html_page: read ace data and update html page                                      ---
#---------------------------------------------------------------------------------------------------

def create_ace_html_page():
    """
    read ace data and update html page
    input:  none, but read from:
            http://services.swpc.noaa.gov/images/ace-epam-7-day.gif
            http://services.swpc.noaa.gov/images/ace-mag-swepam-7-day.gif
            <ace_dir>/Data/ace_12h_archive
    output: <html_dir>/ACE/ace.html
    """
#
#---- read 12h_archive data
#
    with open(f"{ACE_DATA_DIR}/ace_12h_archive") as f:
        cdata = [line.strip() for line in f.readlines()]
#
#--- cdata:     a list of lists of electron/proton flux data 
#--- l_vals:    a list of the 'last' entries of those electron/proton flux data
#--- data is also trimmed to the last 2 hours
#
    try:
        cdata_cols, l_vals = convert_to_col_data(cdata)
    except:
        exit(1)
#
#--- create data table for the html page
#
    ace_table = create_ace_data_table(cdata_cols, l_vals)
#
#--- download images and reverse the color:
#
    download_img(HTTP_EPAM)
    download_img(HTTP_MAG)
#
#--- update ace html page
#
    line = ''
    with open(f"{TEMPLATE_DIR}/header") as f:
        line += f"{f.read()}\n"

    with open(f"{TEMPLATE_DIR}/header1") as f:
        line += f"{f.read()}\n"

    line += f"{ace_table}\n"

    with open(f"{TEMPLATE_DIR}/image2") as f:
        line += f"{f.read()}\n"

    with open(f"{TEMPLATE_DIR}/footer") as f:
        line += f"{f.read()}\n"

    with open(f"{ACE_HTML_DIR}/ace.html", 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------------------
#-- create_ace_data_table: create data tables from a given data list                              --
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
            p5_p3_scaled[k] = p5dat[k] * P5_P3_SCALE

        if p6dat[k] > 0:
            p6_p3_scaled[k] = p6dat[k] * P6_P3_SCALE

        if p7dat[k] > 0:
            p7_p3_scaled[k] = p7dat[k] * P7_P3_SCALE
        append_data = [de1[k], de4[k], p2dat[k], p3dat[k],p5_p3_scaled[k], p6_p3_scaled[k], p5dat[k], p6dat[k], p7dat[k]]
        aline = f'{cdata[1][k]}'
        for i in append_data:
            if i < 0:
                aline += f" {-1e5:11.2e}"
            else:
                aline += f" {i:11.3f}"
        line += f"{aline}\n"

#
#--- the table part is done, compute other entries
#
#
#--- compute mean and find min of p5, p6, and p7
#
    ind    = p5dat > 0
    cdat   = p5dat[ind]
    if len(cdat) > 0:
        p337a  = numpy.mean(cdat)
        p337m  = min(cdat)
    else:
        p337a  = 0   
        p337m  = 0   

    ind    = p6dat > 0
    cdat   = p6dat[ind]
    if len(cdat) > 0:
        p761a  = numpy.mean(cdat)
        p761m  = min(cdat)
    else:
        p761a  = 0    
        p761m  = 0   

    ind    = p7dat > 0
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
    ind    = pchk == 0
    ind2   = echk == 0

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

    if (p5_p6 > P5_P6_LIM) or (p5_p6 < 1):
        speci     = "%12.1f" % p5_p6
        speci_lim = "%8.1f"  % P5_P6_LIM

        ace_invalid_spec(speci, speci_lim)
#
#--- create a summary table
#
    with open(f"{TEMPLATE_DIR}/header2") as f:
        line += f"\n{f.read()}"

    line  = line + "%7s %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f\n"\
                   % ("AVERAGE        ", e38a, e175a, p56a, p130a, p5_p3a, p6_p3a, p337a, p761a, p1073a)

    line  = line + "%7s %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f\n"\
                   % ("MINIMUM        ", e38m, e175m, p56m, p130m, p5_p3m, p6_p3m, p337m, p761m, p1073m)

    line  = line + "%7s %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e %11.4e\n\n"\
                   % ("FLUENCE        ", e38f, e175f, p56f, p130f, p5_p3f, p6_p3f, p337f, p761f, p1073f)

    line  = line + "%7s %11s %11.3f %11s %11.3f %11s %11.3f %11s %11.3f \n\n"\
                   % ("SPECTRA        ", "p3/p5", p3_p5, "p3/p6", p3_p6, "p5/p6", p5_p6, "p6/p7", p6_p7)

    line  = line + "%62s %4.1f\n"\
                   % ("*   This P3 channel is currently scaled from P5 data. P3* = P5 X ", P5_P3_SCALE)

    line  = line + "%62s %4.1f\n"\
                   % ("**  This P3 channel is currently scaled from P6 data. P3** = P6 X ", P6_P3_SCALE)

    line  = line + "%62s %4.1f\n"\
                   % ("*** This P3 channel (not shown) is currently scaled from P7 data. P3*** = P7 X ", P7_P3_SCALE)

    return line

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
    out = f'{TMP_DIR}/prot_spec_violate'
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
        line = line + 'This message sent to mtadude\n'

        send_mail('ACE_p5/p6', line, 'mtadude@cfa.harvard.edu')
#
#--- open a file indicating that the mail was sent
#
        with open(out, 'w') as fo:
            fo.write(line)

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def send_mail(subject, content, address):
    if TESTMAIL:
        print(f"Test Mode, interrupting following email.\n\
              Subject: {subject}\n\
              Address: {address}\n\
              Content: {content}\n")
    else:
        os.system(f"echo '{content}' | mailx -s '{subject}' {address}")

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def convert_to_stime(year, yday):

    atemp = re.split(r'\.', yday)
    frac  = float(f"0.{atemp[1]}") 
    val   = 24 * frac
    hh    = int(val)
    diff  = val - hh
    val   = 60 * diff
    mm    = int(val)
    diff  = val - mm
    ss    = int(60 *diff)

    htime = str(year).zfill(4) + ':' + atemp[0].zfill(3) + ':' + str(hh).zfill(2) + ':' + str(mm).zfill(2) + ':' + str(ss).zfill(2)
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
    ofile = os.path.basename(file)
    oimg = f"{ACE_PLOT_DIR}/{ofile}"
#
#--- download the img
#
    #cmd   = 'lynx -source ' + file + '>' + oimg
    try:
        cmd  = 'wget -q -O' + oimg + ' ' + file
        os.system(cmd)
    except:
        mc   = re.search('gif', oimg)
        if mc is not None:
            cmd = f"cp {HOUSE_KEEPING}/no_plot.gif {oimg}"
        else:
            cmd = f"cp {HOUSE_KEEPING}/no_data.png {oimg}"
        os.system(cmd)

        return
#
#--- reverse the color of the image
#
    if chg == 1:
        cmd   = 'convert -negate ' +  oimg + ' ' + oimg
        os.system(cmd)
    
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
    atemp   = re.split(r'\s+', data[-1])
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
        atemp = re.split(r'\s+', ent)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-d", "--data", required = False, help = "Directory path to determine input location of data.")
    parser.add_argument("-p", "--path", required = False, help = "Directory path to determine output location of plot.")
    parser.add_argument("-w", "--web", required = False, help = "Directory path to determine output location of html page.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
        print("Running In Test Mode.")
        TESTMAIL = True
#
#--- Path output to same location as unit tests
#
        TEMPLATE_DIR = f"{os.getcwd()}/Template"
        TMP_DIR =  f"{os.getcwd()}/test/_outTest"
        if args.data:
            ACE_DATA_DIR = args.data
        else:
            ACE_DATA_DIR = f"{os.getcwd()}/test/_outTest"

        if args.path:
            ACE_PLOT_DIR = args.path
        else:
            ACE_PLOT_DIR = f"{os.getcwd()}/test/_outTest/Plots"
        
        if args.web:
            ACE_HTML_DIR = args.web
        else:
            ACE_HTML_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(ACE_PLOT_DIR, exist_ok = True)
        os.makedirs(ACE_HTML_DIR, exist_ok = True)
        print(f"ACE_DATA_DIR: {ACE_DATA_DIR}")
        print(f"ACE_PLOT_DIR: {ACE_PLOT_DIR}")
        print(f"ACE_HTML_DIR: {ACE_HTML_DIR}")
        print(f"TEMPLATE_DIR: {TEMPLATE_DIR}")
        print(f"TMP_DIR: {TMP_DIR}")
        create_ace_html_page()
    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions.
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog.")
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")
        create_ace_html_page()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")
