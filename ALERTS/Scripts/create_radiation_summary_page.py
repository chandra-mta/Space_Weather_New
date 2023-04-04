#!/proj/sot/ska3/flight/bin/python

#########################################################################################
#                                                                                       #
#   create_radiation_summary_page.py: create Chandra Radiation Environment Summary page #
#                                                                                       #
#               author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                       #
#               last updae: mar 16, 2021                                                #
#                                                                                       #
#########################################################################################

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
    exec( "%s = %s" %(var, line))
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.8/MTA/')
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
pool     = '/pool14/chandra/chandra_psi.snapshot'
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

mon_list  = ['Non', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
week_list = ['Sun', 'Mon', 'Tus', 'Wed', 'Thu', 'Fri', 'Sat']

#-----------------------------------------------------------------------------
#-- create_radiation_summary_page: create Chandra Radiation Environment Summary page
#-----------------------------------------------------------------------------

def create_radiation_summary_page():
    """
    create Chandra Radiation Environment Summary page
    input:  none but read from:
                /pool14/chandra/chandra_psi.snapshot
                <crm3_dir>/Data/CRMsummary.dat
                <alerts_dir>/Data/goes_fluence.dat
                <ace_dir>/Data/fluace.dat.good
                <comm_dir>/Data/comm_data
                /data/mta4/Space_Weather/Rad_zone/rad_zone_info
                /proj/sot/acis/FLU-MON/FPHIST-2001.dat
    output: <html_dir>/Alerts/rad_comm.html
    """
#
#--- read CRM summary table and extract data
#
    [inst, orb_start, alt, crm_flx, crm_flx_att, crm_flu, crm_flu_att] = read_crm_summary()
#
#--- read goes data
#
    try:
        out = read_goes_data()
    except:
        exit(1)
    [goes_p4_flx, goes_p7_flx, goes_e2_flx, goes_p4_flu, goes_p7_flu, goes_e2_flu] = out
#
#--- read ace data
#
    #[ace_p3_flx, ace_p3_flu] = read_ace_data()
    [ace_p3_flx, ace_p3_flu, ace_p3_flx_att, ace_p3_flu_att] = read_ace_data()
#
#--- find comm contact times of the next and one after that
#
    [contact_start, next_contact] = read_contact_data()
#
#--- find the next rad zone entry time
#
    rad_time = get_radzone_info()
    if rad_time == False:
        print("something is wrong at rad zone info: existing\n")
        exit(1)
#
#--- find how long into this orbital period
#
    o_period = current_chandra_time - Chandra.Time.DateTime(orb_start).secs
    o_period /= 1.e3
#
#--- compute times till the next comm contact and rad zone entry:
#--- in hours
#
    comspan  = (contact_start - current_chandra_time) / 3600.0
    radspan  = (rad_time - current_chandra_time) / 3600.0
#
#--- in sec
#
    rad_p    = rad_time      - current_chandra_time
    comm1_p  = contact_start - current_chandra_time
    comm2_p  = next_contact  - current_chandra_time
#
#--- next comm and rad zone time in readble format
#
    out      = Chandra.Time.DateTime(contact_start).date
    atemp    = re.split('\.', out)
    next_cmm = time.strftime('%Y:%j:%H:%M:00', time.strptime(atemp[0], '%Y:%j:%H:%M:%S'))

    out      = Chandra.Time.DateTime(rad_time).date
    atemp    = re.split('\.', out)
    next_rad = time.strftime('%Y:%j:%H:%M:00', time.strptime(atemp[0], '%Y:%j:%H:%M:%S'))
#
#--- use these for attenuated cases: cumulative time periods where acis was in use
#
    att_rad_time  = calc_acis_att_time(current_chandra_time, rad_time)
    att_com_time1 = calc_acis_att_time(current_chandra_time, contact_start)
    att_com_time2 = calc_acis_att_time(current_chandra_time, next_contact)
#
#--- convert the current time into the display time
#
    #disp_time = convert_chandra_time_to_display(current_chandra_time)
    out = Chandra.Time.DateTime(current_chandra_time).date
    atemp = re.split('\.', out)
    disp_time = time.strftime('%Y:%j:%H:%M:00', time.strptime(atemp[0], '%Y:%j:%H:%M:%S'))

#
#--- compute instrument attenuation factors
#
    att_factor     = crm_flx_att/crm_flx
    att_flu_factor = crm_flu_att/crm_flu
#
#--- start writing the html page (rad_comm.html)
#
#--- intro part  --------------------
#
    tline = read_file(alerts_dir + 'Scripts/Template/page_top')
    tline = tline.replace('#ORBSTART#',     orb_start)
    tline = tline.replace('#OPERIOD#',      '%.1f' % o_period)
    tline = tline.replace('#ALT#',          alt)
    tline = tline.replace('#INST_OTG#',     inst)
    tline = tline.replace('#NEXT_COMM#',    next_cmm)
    tline = tline.replace('#COMM_SPAN#',    '%.1f' % comspan)
    tline = tline.replace('#NEXT_RAD#',     next_rad)
    tline = tline.replace('#RAD_SPAN#',     '%.1f' % radspan)
    tline = tline.replace('#CURRENT_TIME#', disp_time)
    tline = tline.replace('#NEXT_RAD_SEC#', '%.1f' % (att_rad_time  /1.e3))
    tline = tline.replace('#NEXT_COMM_SEC#','%.1f' % (att_com_time1 /1.e3))
#
#--- insturment attenuated fluence part --------------
#
#--- crm part
#
    rad_flu1 =      crm_flx_att * att_rad_time  + crm_flu_att
    rad_flu2 = 2  * crm_flx_att * att_rad_time  + crm_flu_att
    rad_flu3 = 10 * crm_flx_att * att_rad_time  + crm_flu_att
    cmm_flu1 =      crm_flx_att * att_com_time1 + crm_flu_att
    cmm_flu2 =      crm_flx_att * att_com_time2 + crm_flu_att

    tline = tline + '<tr><td>CRM</td>\n'
    tline = tline + '<td>'  + "%.3e" % crm_flx_att + '</td>\n'
    tline = tline + '<td>'  + "%.3e" % crm_flu_att + '</td>\n'
    tline = tline + '<td>'
    tline = tline + "%.3e" % rad_flu1 + '<br/>(' + "%.3e" % rad_flu2 + ')<br/>*' + "%.3e" % rad_flu3
    tline = tline + '*</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>working yellow limit:<br />1.000E+09 (fluence)</td></tr>\n'
#
#--- ace part
#
#    ace_p3_flx_att = att_factor     * ace_p3_flx
#    ace_p3_flu_att = att_flu_factor * ace_p3_flu

    rad_flu1 =      ace_p3_flx_att * att_rad_time  + ace_p3_flu_att
    rad_flu2 = 2  * ace_p3_flx_att * att_rad_time  + ace_p3_flu_att
    rad_flu3 = 10 * ace_p3_flx_att * att_rad_time  + ace_p3_flu_att
    cmm_flu1 =      ace_p3_flx_att * att_com_time1 + ace_p3_flu_att
    cmm_flu2 =      ace_p3_flx_att * att_com_time2 + ace_p3_flu_att

    tline = tline + '<tr><td>ACE P3</td>\n'
    tline = tline + '<td>' + "%.3e" % ace_p3_flx_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % ace_p3_flu_att + '</td>\n'
    tline = tline + '<td>'
    tline = tline + "%.3e" % rad_flu1 + '<br/>(' + "%.3e" % rad_flu2 + ')<br/>*' + "%.3e" % rad_flu3
    tline = tline + '*</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>alert trigger: 1.000E+09 (fluence)</td></tr>\n'
#
#--- goes p4 part
#
    goes_p4_flx_att = att_factor     * goes_p4_flx
    goes_p4_flu_att = att_flu_factor * goes_p4_flu
    rad_flu1 = goes_p4_flx_att * att_rad_time  + goes_p4_flu_att
    cmm_flu1 = goes_p4_flx_att * att_com_time1 + goes_p4_flu_att
    cmm_flu2 = goes_p4_flx_att * att_com_time2 + goes_p4_flu_att

    tline = tline + '<tr><td>GOES-R (P4)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p4_flx_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p4_flu_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>&#160;</td></tr>\n'
#
#--- goes p7 part
#
    goes_p7_flx_att = att_factor     * goes_p7_flx
    goes_p7_flu_att = att_flu_factor * goes_p7_flu
    rad_flu1 = goes_p7_flx_att * att_rad_time  + goes_p7_flu_att
    cmm_flu1 = goes_p7_flx_att * att_com_time1 + goes_p7_flu_att
    cmm_flu2 = goes_p7_flx_att * att_com_time2 + goes_p7_flu_att

    tline = tline + '<tr><td>GOES-R (P7)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p7_flx_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p7_flu_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>&#160;</td></tr>\n'
#
#--- goes e2 part
#
    goes_e2_flx_att = att_factor     * goes_e2_flx
    goes_e2_flu_att = att_flu_factor * goes_e2_flu
    rad_flu1 = goes_e2_flx_att * att_rad_time  + goes_e2_flu_att
    cmm_flu1 = goes_e2_flx_att * att_com_time1 + goes_e2_flu_att
    cmm_flu2 = goes_e2_flx_att * att_com_time2 + goes_e2_flu_att

    tline = tline + '<tr><td>GOES-R (E>2.0MeV)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_e2_flx_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_e2_flu_att + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>&#160;</td></tr>\n'
#
#---- exteral fluxes etc ---------
#
    tline = tline + read_file(alerts_dir + 'Scripts/Template/second_table_head')
#
#--- crm part
#
    rad_flu1 =      crm_flx * rad_p   + crm_flu
    cmm_flu1 =      crm_flx * comm1_p + crm_flu
    cmm_flu2 =      crm_flx * comm2_p + crm_flu

    tline = tline + '<tr><td>CRM</td>\n'
    tline = tline + '<td>'  + "%.3e" % crm_flx + '</td>\n'
    tline = tline + '<td>'  + "%.3e" % crm_flu + '</td>\n'
    tline = tline + '<td>'
    tline = tline + "%.3e" % rad_flu1
    tline = tline + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>&#160;</td</tr>'
#
#--- ace part
#
    rad_flu1 =      ace_p3_flx * rad_p   + ace_p3_flu
    cmm_flu1 =      ace_p3_flx * comm1_p + ace_p3_flu
    cmm_flu2 =      ace_p3_flx * comm2_p + ace_p3_flu

    tline = tline + '<tr><td>ACE P3</td>\n'
    tline = tline + '<td>' + "%.3e" % ace_p3_flx + '</td>\n'
    tline = tline + '<td>' + "%.3e" % ace_p3_flu + '</td>\n'
    tline = tline + '<td>'
    tline = tline + "%.3e" % rad_flu1
    tline = tline + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>3.6e8 (2 hr fluence, red)</td></tr>\n'
#
#--- goes p4 part
#
    rad_flu1 = goes_p4_flx * rad_p   + goes_p4_flu
    cmm_flu1 = goes_p4_flx * comm1_p + goes_p4_flu
    cmm_flu2 = goes_p4_flx * comm2_p + goes_p4_flu

    tline = tline + '<tr><td>GOES-R (P4)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p4_flx + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p4_flu + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>30.0/90.9 (flux, yellow/red)</td></tr>\n'
#
#--- goes p7 part
#
    rad_flu1 = goes_p7_flx * rad_p   + goes_p7_flu
    cmm_flu1 = goes_p7_flx * comm1_p + goes_p7_flu
    cmm_flu2 = goes_p7_flx * comm2_p + goes_p7_flu

    tline = tline + '<tr><td>GOES-R (P7)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p7_flx + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_p7_flu + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>0.25/0.70 (flux, yellow/red)</td></tr>\n'
#
#--- goes e2 part
#
    rad_flu1 = goes_e2_flx * rad_p   + goes_e2_flu
    cmm_flu1 = goes_e2_flx * comm1_p + goes_e2_flu
    cmm_flu2 = goes_e2_flx * comm2_p + goes_e2_flu

    tline = tline + '<tr><td>GOES-R (E>2.0MeV)</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_e2_flx + '</td>\n'
    tline = tline + '<td>' + "%.3e" % goes_e2_flu + '</td>\n'
    tline = tline + '<td>' + "%.3e" % rad_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu1 + '</td>\n'
    tline = tline + '<td>' + "%.3e" % cmm_flu2 + '</td>\n'
    tline = tline + '<td>&#160;</td></tr>\n'
#
#--- close the page
#
    tline = tline + read_file(alerts_dir + 'Scripts/Template/bottom_part')

    snptime = get_snapshot_time()
    tline = tline.replace('#LAST_SUPPORT#', snptime)
#
#--- update the page
#
    ofile = html_dir + 'Alerts/rad_summ.html'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out +'/rad_summ.html'
    with open(ofile, 'w') as fo:
        fo.write(tline)

#-----------------------------------------------------------------------------
#-- read_crm_summary: read CRM model data                                  ---
#-----------------------------------------------------------------------------

def read_crm_summary():
    """
    read CRM model data
    input: none but read from
            <crm3_dir>/Data/CRMsummary.dat
    output: inst    --- instrument + otg
            orb_start   --- orbit starting time 
            alt         --- altitude
            crm_flx     --- crm flux
            crm_flx_att --- instrument attenuated crm flux
            crm_flu     --- crm fluence of this period
            crm_flu_att --- instrument attenuated crm fluence
    """
    ifile = crm3_dir + '/Data/CRMsummary.dat'
    data  = mcf.read_data_file(ifile)

    atemp = re.split(':', data[0])
    inst        = atemp[1].strip()

#    atemp = re.split(':', data[3])
#    goes_p4_flx = float(atemp[1].strip())
#
#    atemp = re.split(':', data[4])
#    goes_p7_flx = float(atemp[1].strip())
#
#    atemp = re.split(':', data[5])
#    goes_e2_flx = float(atemp[1].strip())

    atemp = re.split(' : ', data[6])
    orb_start   = atemp[1].strip()

    atemp = re.split(':', data[7])
    alt         = atemp[1].strip()

    atemp = re.split(':', data[9])
    try:
        crm_flx     = float(atemp[1].strip())
    except:
        crm_flx     = 0.0

    atemp = re.split(':', data[10])
    try:
        crm_flx_att = float(atemp[1].strip())
    except:
        crm_flx_att = 0.0

    atemp = re.split(':', data[11])
    try:
        crm_flu     = float(atemp[1].strip())
    except:
        crm_flu     = 0.0

    atemp = re.split(':', data[12])
    try:
        crm_flu_att = float(atemp[1].strip())
    except:
        crm_flu_att = 0.0


    return  [inst, orb_start, alt, crm_flx, crm_flx_att, crm_flu, crm_flu_att]

#-----------------------------------------------------------------------------
#-- read_goes_data: read goes current fluxes and fluence                    --
#-----------------------------------------------------------------------------

def read_goes_data():
    """
    read goes current fluxes and fluences
    input:  none, but read from:
            <alerts_dir>/Data/goes_fluence.dat
    output: goes_p4_flx     --- current goes p4 flux
            goes_p7_flx     --- current goes p7 flux
            goes_e2_flx     --- current goes e>2.0MeV flx
            goes_p4_flu     --- goes p4 fluence of this orbit
            goes_p7_flu     --- goes p7 fluence of this orbit
            goes_e2_flu     --- goes e2 fluence of this orbit
    """
    ifile = alerts_dir + 'Data/goes_fluence.dat'
    data  = mcf.read_data_file(ifile)

    atemp = re.split('\s+', data[1])
    goes_p4_flx = check_value(atemp[1])
    goes_p7_flx = check_value(atemp[2])
    goes_e2_flx = check_value(atemp[3])

    atemp = re.split('\s+', data[2])
    goes_p4_flu = check_value(atemp[1])
    goes_p7_flu = check_value(atemp[2])
    goes_e2_flu = check_value(atemp[3])

    return [goes_p4_flx, goes_p7_flx, goes_e2_flx, goes_p4_flu, goes_p7_flu, goes_e2_flu]

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def check_value(val):

    try:
        out = float(val)
    except:
        out = 0.0

    return out

#-----------------------------------------------------------------------------
#-- read_ace_data: read ace data                                            --
#-----------------------------------------------------------------------------

def read_ace_data():
    """
    read ace data
    input:  none but read from:
                <ace_dir>/Data/fluace.dat.good
    output: ace_p3_flx      --- ace p3 flux
            ace_p3_flu      --- ace p3 flluence
    """
#    ifile = ace_dir + 'Data/fluace.dat.good'
#    data  = mcf.read_data_file(ifile)
#
#    atemp = re.split('\s+', data[4])
#    ace_p3_flx = float(atemp[11])
#
#    atemp = re.split('\s+', data[6])
#    ace_p3_flu = float(atemp[11])
#
#    ifile = alerts_dir + 'Data/current.dat'
    ifile = '/proj/web-cxc/htdocs/acis/Fluence/current.dat'
    data  = mcf.read_data_file(ifile)

    atemp = re.split('\s+', data[7])
    ace_p3_flx     = float(atemp[9])
    
    atemp = re.split('\s+', data[9])
    ace_p3_flu     = float(atemp[9])
    
    atemp = re.split('\s+', data[-3])
    ace_p3_flx_att = float(atemp[9])

    atemp = re.split('\s+', data[-1])
    ace_p3_flu_att = float(atemp[9])

    return [ace_p3_flx, ace_p3_flu, ace_p3_flx_att, ace_p3_flu_att]
#    return [ace_p3_flx, ace_p3_flu]

#-----------------------------------------------------------------------------
#-- read_contact_data: read DSN contact information                         --
#-----------------------------------------------------------------------------

def read_contact_data():
    """
    read DSN contact information
    input:  none but read from:
    <comm_dir>/Data/coom_data
    output: dsn_start   --- a list of contact start time
    dsn_stop--- a list of contact end time
    """
    infile = comm_dir + '/Data/comm_data'
    data   = mcf.read_data_file(infile)
    dsn_start = []
    for  ent in data[2:]:
        atemp = re.split('\s+', ent)
        if mcf.is_neumeric(atemp[4]):
            dsn_start.append(float(atemp[4]))

    dlen = len(dsn_start)
    for k in range(0, dlen-1):
        if (dsn_start[k] < current_chandra_time) and (dsn_start[k+1] > current_chandra_time):
            contact_start = dsn_start[k+1]
            next_contact  = dsn_start[k+2]
            break
    
    return  [contact_start, next_contact]

#--------------------------------------------------------------------------------
#-- convert_to_ctime: convert <yyyy> <doy>.<fractional doy> to Chandra Time    --
#--------------------------------------------------------------------------------

def convert_to_ctime(year, fyday):
    """
    convert <yyyy> <doy>.<fractional doy> to Chandra Time
    input:  year--- year
    fyday   --- fractional day of year
    output: time in seconds from 1998.1.1
    """
    year  = str(year)
    
    ydate = float(fyday)
    yday  = int(ydate)
    frc   = 24 * (ydate - yday)
    hh= int(frc)
    frc   = 60 *(frc - hh)
    mm= int(frc)
    ss= 60 *(frc - mm)
    ss= int(ss)
    
    ltime = year  + ':' + mcf.add_leading_zero(yday, 3) + ':' + mcf.add_leading_zero(hh)
    ltime = ltime + ':' + mcf.add_leading_zero(mm)  + ':' + mcf.add_leading_zero(ss)
    
    ctime = Chandra.Time.DateTime(ltime).secs
    ctime = int(ctime)
    
    return ctime

#-----------------------------------------------------------------------------
#-- get_radzone_info: find out the next rad zone entry time                ---
#-----------------------------------------------------------------------------

def get_radzone_info():
    """
    find out the next rad zone entry time
    input:  none, but read from:
            /data/mta4/Space_Weather/Rad_zone/rad_zone_info
    output: rtime   --- next rad zone entry time
    """
    ifile = '/data/mta4/Space_Weather/Rad_zone/rad_zone_info'
    data  = mcf.read_data_file(ifile)

    dlen  = len(data)
    for k in range(0, dlen-1):
        atemp = re.split('\s+', data[k])
        if atemp[0] == 'ENTRY':
            atime = Chandra.Time.DateTime(atemp[2]).secs
            if atime <= current_chandra_time:
                continue
            else:
                return atime


    return False

#-----------------------------------------------------------------------------
#-- calc_acis_att_time: compute time period where acis was in use           --
#-----------------------------------------------------------------------------

def calc_acis_att_time(start, stop):
    """
    compute time period where acis was in use
    input:  start   --- data colleciton starting time in seconds from 1998.1.1
            stop    --- data collection stopping time in seconds from 1998.1.1
    output: att_time    --- total acis operation time during the given period
    """
#
#--- read the instrument in use list
#
    ifile = '/proj/sot/acis/FLU-MON/FPHIST-2001.dat'
    data  = mcf.read_data_file(ifile)
    
#
#--- create lists of starting time and stopping time for ACIS-I, ACIS-S, HRC-I, HRC-S 
#--- set their positional index to 0, 1, 2, and 3, respectively
#
    inst_start = [[], [], [], []]
    inst_stop  = [[], [], [], []]
#
#--- dummy instrument indicator
#
    pinst = -999
    pchk  = 0

    klen = len(data)
    for k in range(0, klen):
        atemp = re.split('\s+', data[k])
        try:
            ctime = Chandra.Time.DateTime(atemp[0]).secs
        except:
            continue

        if atemp[1] == 'ACIS-I':
            pos = 0
        elif atemp[1] == 'ACIS-S':
            pos = 1
        elif atemp[1] == 'HRC-I':
            pos = 2
        elif atemp[1] == 'HRC-S':
            pos = 3
        else:
            continue
#
#--- if the time is before the collecting period, just keep which instrument is used
#
        if ctime < start:
            pinst = pos
            continue
#
#--- if the time is after the collecting period, add the stop time to the previous instrument
#--- before breaking the loop unless there is no starting time yet; then also add starting time
#
        if ctime > stop:
            if pchk == 0:
                inst_start[pinst].append(start)
            inst_stop[pinst].append(stop)
            break 
#
#--- the time is in the period first time, add the time to previous instrument
#
        if pchk == 0:
            inst_start[pinst].append(start)
            pchk = 1
#
#--- close the previous instrument and start the period of the new instrument
#
        inst_stop[pinst].append(ctime)
        inst_start[pos].append(ctime)
        pinst = pos
#
#--- accumulate time periods when acis is in use
#
    att_time = 0.0
    for k in range(0, len(inst_start[0])):
        istart = inst_start[0][k]
        try:
            istop  = inst_stop[0][k]
        except:
            istop  = stop

        if istart < start:
            istart = start
        if istop > stop:
            istop = stop

        att_time += istop - istart

    for k in range(0, len(inst_start[1])):
        istart = inst_start[1][k]
        try:
            istop  = inst_stop[1][k]
        except:
            istop  = stop
        if istart < start:
            istart = start
        if istop > stop:
            istop = stop

        att_time += istop - istart

    return att_time
            

#-----------------------------------------------------------------------------
#--get_snapshot_time: find the current snapshot time                        --
#-----------------------------------------------------------------------------

def get_snapshot_time():
    """
    find the current snapshot time
    input:  none but read from:
            '/pool14/chandra/chandra_psi.snapshot
    output: sn_time --- snapshot tie
    """
    ifile = '/pool14/chandra/chandra_psi.snapshot'
    data  = mcf.read_data_file(ifile)
    atemp = re.split('\s+', data[1])
    snp_time = atemp[1]

    atemp = re.split('\s+', data[0])
    dday  = atemp[2].replace('\(', '')
    dday  = dday.replace('\)', '')

    snp_time = snp_time + ' ' + dday

    return snp_time

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def read_file(ifile):

    with open(ifile, 'r') as f:
        data = f.read()

    return data

#-----------------------------------------------------------------------------
#-- convert_chandra_time_to_display: convert chandra time to human readable time format
#-----------------------------------------------------------------------------

def convert_chandra_time_to_display(ctime):
    """
    convert chandra time to human readable time format
    input:  ctime   --- time in seconds from 1998.1.1
    output: line    --- <wday> <Mmm> <dd> <hh>:<mm>:<ss> <yyyy>
    """

    out = Chandra.Time.DateTime(ctime).date
    atemp = re.split('\.', out)
    ltime = atemp[0]
    ltime = time.strftime("%Y:%m:%d:%H:%M:%S:%w", time.strptime(ltime, '%Y:%j:%H:%M:%S'))

    atemp = re.split(':', ltime)
    wday  = week_list[int(float(atemp[-1]))]
    mon   = mon_list[int(float(atemp[1]))]

    line  = wday + ' ' + mon + ' ' + atemp[2] + ' ' + atemp[3] + ':'
    line  = line + atemp[4] + ':' + atemp[5] + ' ' + atemp[0]

    return line

#-----------------------------------------------------------------------------

if __name__ == "__main__":

    create_radiation_summary_page()
