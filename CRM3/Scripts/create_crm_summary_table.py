#!/proj/sot/ska3/flight/bin/python

#############################################################################################
#                                                                                           #
#       create_crm_summary_table.py: update CRMsummary.dat data summary table               #
#                                                                                           #
#               author: t. isobe (tiosbe@cfa.harvard.edu)                                   #
#                                                                                           #
#               last update: Oct 07, 2021                                                   #
#                                                                                           #
#############################################################################################

import os
import sys
import re
import string
import math
import time
import datetime
import Chandra.Time
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

sys.path.append('/data/mta4/Script/Python3.8/MTA/')
import mta_common_functions     as mcf
#
#--- set a temporary file name
#
rtail  = int(time.time()*random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- setting dir path
#
root_dir    = '/data/mta4/proj/rac/ops/'
web_dir     = html_dir  + 'CRM/'
crmdat_root = crm3_dir  + '/Data/CRM3_p.dat'
sumdat      = crm3_dir  + '/Data/CRMsummary.dat'
arcdat      = crm3_dir  + '/Data/CRMarchive.dat'
ephdat      = ephem_dir + '/Data/gephem.dat'
kpdat       = ace_dir   + '/Data/kp.dat'
acedat      = ace_dir   + '/Data/fluace.dat'
gp_dat      = goes_dir  + '/Data/Gp_pchan_5m.txt'
#gs_dat      = goes_dir  + '/Data/Gs_pchan_5m.txt'
gpe_dat     = goes_dir  + '/Data/Gp_part_5m.txt'
#
#--- data files
#
sim_file = "/proj/sot/acis/FLU-MON/FPHIST-2001.dat"
otg_file = "/proj/sot/acis/FLU-MON/GRATHIST-2001.dat"
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- other settings
#
delta      = 300
sw_factor  = [0, 1, 2, 0.5]
crm_factor = [0, 0, 1, 1]
#
#--- crm file category according to kp value
#
crm_n_list = ['00', '03', '07', '10', '13', '17', '20', '23', '27','30', '33', '37',\
              '40', '43', '47', '50', '53', '57', '60', '63', '67','70', '73', '77',\
              '80', '83', '87', '90']

gp_p4_c_factor = 3.4            #---- factor to correct p2 to p4gm 
gp_p7_c_factor = 12.0           #---- facotr to correct p5 to p41gm
#
#--- satellite location regarded to the solar wind environment
#
sol_region     = ['NULL', 'Solar_Wind', 'Magnetosheath', 'Magnetosphere']
#
#--- current time  in <yyyy>:<ddd>:<hh>:<mm>:<ss> and in seconds from 1998.1.1
#
cl_time      = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_time = Chandra.Time.DateTime(cl_time).secs

#-------------------------------------------------------------------------------
#-- create_crm_summary_table: update CRMsummary.dat data summary table        --
#-------------------------------------------------------------------------------

def create_crm_summary_table():
    """
    update CRMsummary.dat data summary table
    input:  none, but read several input data table
    output: <html_dir>/GOES/Data/CRMsummary.dat
            <html_dir>/GOES/Data/CRMarchive.dat
    """
#
#--- read all needed data
#
    [gp_p4, gp_p7]  = read_goes_p_data(gp_dat)
   #[gs_p2, gs_p5]  = read_goes_p_data(gs_dat)
    gp_e2           = read_goes_e_data(gpe_dat)
    [alt, leg]      = read_ephem_data()
    [kp, kpi]       = read_kp_data() 
    ace             = read_ace_data()
    [region, flux, summary] = read_crm_fluence(kpi, ace)
    si              = read_sim()
    otg             = read_otg()
    aflux           = find_attenuate_flux(flux, si, otg)
#
#--- supply missing data
#
    if gp_p4 == '': gp_p4 = float(summary[-11])
    if gp_p7 == '': pg_p5 = float(summary[-9])
    ostart   = summary[-7]
    fluence  = float(summary[-2])
    afluence = float(summary[-1])
#
#--- when the orbit changes from decending to acending, write the data into an archive
#--- and reset orbit starting time (ostart) fluence and afluence
#
    if leg == 'A' and summary[-6] == 'D':
        oend = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
        outfile = arcdat
        #for writing out files in test directory
        if (os.getenv('TEST') == 'TEST'):
            outfile = test_out + "/" + os.path.basename(arcdat)
            os.system(f"touch {outfile}")
        with open(outfile, 'a') as fo:
            line = str(ostart) + '  ' +   oend   + '  ' + str(fluence) + '  ' + str(afluence) + '\n'
            fo.write(line)
            ostart = oend
            fluence  = 0.0
            afluence = 0.0

    fluence  += (flux  * delta)
    afluence += (aflux * delta)
#
#--- print out the data
#
    line = ''
    line = line + "                    Currently scheduled FPSI, OTG : " + si + ' ' + otg + '\n'
    line = line + "                                     Estimated Kp : " + str(kp) + '\n'
    line = line + "        ACE EPAM P3 Proton Flux (p/cm^2-s-sr-MeV) : %.2e\n" % (check_val(ace))
    line = line + "            GOES-R P4 flux, in RADMON P4GM  units : %.2e\n" % (check_val(gp_p4))
   #line = line + "            GOES-S P2 flux, in RADMON P4GM  units : %.2f\n" % (check_val(ps_p2))
    line = line + "            GOES-R P7 flux, in RADMON P41GM units : %.2e\n" % (check_val(gp_p7))
   #line = line + "            GOES-S P5 flux, in RADMON P41GM units : %.2f\n" % (gp_p7)
    line = line + "            GOES-R E > 2.0 MeV flux (p/cm^2-s-sr) : %.2e\n" % (check_val(gp_e2))
    line = line + "                                 Orbit Start Time : " + ostart + '\n'
    line = line + "              Geocentric Distance (km), Orbit Leg : " + str(alt) + ' ' + leg + '\n'
    line = line + "                                       CRM Region : " + str(region) 
    line = line + "(" + sol_region[region] + ")\n"
    line = line + "           External Proton Flux (p/cm^2-s-sr-MeV) : %.4e\n" % (flux)
    line = line + "         Attenuated Proton Flux (p/cm^2-s-sr-MeV) : %.4e\n" % (aflux)
    line = line + "  External Proton Orbital Fluence (p/cm^2-sr-MeV) : %.4e\n" % (fluence)
    line = line + "Attenuated Proton Orbital Fluence (p/cm^2-sr-MeV) : %.4e\n" % (afluence)
    line = line + '\n\n'
    line = line + 'Last Data Update: ' + cl_time + ' (UT)'
    line = line + '\n\n'
    #line = line + 'Due to transition to GOES-16, what used to be P2 is now P4\n'
    #line = line + 'and what used to be P5 is now P7 This message will dissappear\n'
    #line = line + 'in 01/31/2021'

    outfile = sumdat
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        outfile = test_out + "/" + os.path.basename(sumdat)
    with open(outfile, 'w') as fo:
        fo.write(line)
#
#--- back up the data files
#
    cmd = 'cp -f ' + sumdat + ' ' + web_dir + 'CRMsummary.dat'
    os.system(cmd)
    cmd = 'cp -f ' + arcdat + ' ' + web_dir + 'CRMarchive.dat'
    os.system(cmd)
#
#--- update web page
#
    update_crm_html()
#
#--- plot data (moved to plot_crm_flux_data.py Mar 05, 2020)
#
#    cmd = '/usr/local/bin/idl  ' + crm3_dir + '/Scripts/CRM_plots.idl > /dev/null 2>&1'
#    os.system(cmd)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def check_val(val):
    try:
        val = float(val)
    except:
        val = 0.0

    return val

#-------------------------------------------------------------------------------
#-- read_goes_p_data: read the current GOES proton fluxes                     --
#-------------------------------------------------------------------------------

def read_goes_p_data(ifile):
    """
    read the current GOES proton fluxes
    input:  ifile   --- file name
    output: gp_p4   --- p4 flux
            pg_p7   --- p7 flux
                note: p2 p5 definition may be different from a satellite to another
    """
    data  = mcf.read_data_file(ifile)
    gp_p4 = ''
    gp_p7 = ''
    if len(data) > 0:
        if data[-2][0] != '#':
            atemp = re.split('\s+', data[-2])
            try:
                gp_p4 = float(atemp[5]) * gp_p4_c_factor
                gp_p7 = float(atemp[8]) * gp_p7_c_factor
            except:
                pass

    return [gp_p4, gp_p7]

#-------------------------------------------------------------------------------
#-- read_goes_e_data: read the current GOES electron data                     --
#-------------------------------------------------------------------------------

def read_goes_e_data(ifile):
    """
    read the current GOES electron data
    input:  ifile   --- file name
    output: gp_e2   --- flux > 2kev
    """

    gp_e2 = ''
    data  = mcf.read_data_file(ifile)
    for ent in data:
        if ent[0] == '#':
            continue
        atemp = re.split('\s+', ent)
        try:
            val = float(atemp[14])
            if val > 4.0:   #--- it seems 4.0 is the 'null' value
                gp_e2 = val
        except:
            pass

    return gp_e2

#-------------------------------------------------------------------------------
#-- read_ephem_data: read the current ephem data                              --
#-------------------------------------------------------------------------------

def read_ephem_data():
    """
    read the current ephem data
    input:  none but read from <ephdata>
    output: alt --- altitude
            leg --- A (acending) or D (decending)
    """
    data = mcf.read_data_file(ephdat)
    alt  = []
    leg  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        alt = int(float(atemp[0])/1000.)
        leg = atemp[1]

    return [alt, leg]

#-------------------------------------------------------------------------------
#-- read_kp_data: read the current kp value                                   --
#-------------------------------------------------------------------------------

def read_kp_data():
    """
    read the current kp value
    input:  none, but read from <kpdat>
    ouput:  kp  --- kp value
            kpi --- indicator of wihc CRM file to be used
    """
    kp     = -1.0
    kpi    = '00'
    kpgood = kpdat + '.good'
    try:
        data = mcf.read_data_file(kpdat)
        atemp = re.split('\s+', data[-1])
        kp    = float(atemp[-2])
#
#--- if the data is good, copy it to kp.dat.good for future use
#
        cmd   = 'cp -f ' +  kpdat + ' ' + kpgood
        os.system(cmd)
    except:
#
#--- the data is bad. use the last good data
#
        data = mcf.read_data_file(kpgood)
        atemp = re.split('\s+', data[-1])
        kp    = float(atemp[-2])

    kpi = "%3.1f" % kp
    kpi = kpi.replace('.', '')

    return [kp, kpi]

#-------------------------------------------------------------------------------
#-- read_ace_data: read current ace value                                     --
#-------------------------------------------------------------------------------

def read_ace_data():
    """
    read current ace value
    input:  none, but read from <acedata>
    output: ace --- ace value
    """
    ace     = 0
    acegood = acedat + '.good'
    try:
        data = mcf.read_data_file(acedat)
        atemp = re.split('\s+', data[-3])
        ace_n = float(atemp[11])
        if ace_n != ace:
            ace = ace_n
#
#--- if the data is good, copy it to kp.dat.good for future use
#
            cmd   = 'cp -f ' + acedat + ' ' + acegood
            os.system(cmd)
        else:
            data = mcf.read_data_file(acegood)
            atemp = re.split('\s+', data[-3])
            ace_n = float(atemp[11])
            if ace_n != ace:
                ace = ace_n
    except:
#
#--- the data is bad. use the last good data
#
        data = mcf.read_data_file(acegood)
        atemp = re.split('\s+', data[-3])
        ace_n = float(atemp[11])
        if ace_n != ace:
            ace = ace_n

    return ace

#-------------------------------------------------------------------------------
#-- read_crm_fluence: read the last CRMsummary data and compute flux          --
#-------------------------------------------------------------------------------

def read_crm_fluence(kpi, ace):
    """
    read the last CRMsummary data and compute flux
    input:  kpi --- crm file indicator
            ace --- ace vluae
            it also reads  data from <sumdat>= CRMsummary.dat
    output: flux
            summary --- a list of values of:
                Currently scheduled FPSI, OTG
                Estimated Kp
                ACE EPAM P3 Proton Flux (p/cm^2-s-sr-MeV)
                GOES-P P2 flux, in RADMON P4GM  units
                GOES-S P2 flux, in RADMON P4GM  units
                GOES-P P5 flux, in RADMON P41GM units
                GOES-S P5 flux, in RADMON P41GM units
                GOES-P E > 2.0 MeV flux (p/cm^2-s-sr)
                Orbit Start Time
                Geocentric Distance (km), Orbit Leg :
                CRM Region
                External Proton Flux (p/cm^2-s-sr-MeV)
                Attenuated Proton Flux (p/cm^2-s-sr-MeV)
                External Proton Orbital Fluence (p/cm^2-sr-MeV)
                Attenuated Proton Orbital Fluence (p/cm^2-sr-MeV)
    """

    data    = mcf.read_data_file(sumdat)
    summary = []
    for ent in data:
        mc = re.search(':', ent)
        if mc is None:
            continue
        mc = re.search('Last', ent)
        if mc is not None:
            break

        atemp = re.split('\s+', ent)
        try:
            val = flat(atemp[-1])
        except:
            val = atemp[-1].strip()

        summary.append(val)

    ifile = crmdat_root + kpi
    data  = mcf.read_data_file(ifile)

    chk = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        time  = float(atemp[0])
        if time > current_time:
            comp = atemp
            chk =1
            break
        else:
            stime = time
            save  = atemp
#
#--- find data closest to the current time
#
    if chk == 0:
        crm = save
    else:
        if abs(time - current_time) > abs(current_time - stime):
            crm = save
        else:
            crm = comp
#
#--- find flux with correction
#
    region = int(float(crm[1]))     
    flux   = crm_factor[region] * float(crm[2]) + sw_factor[region] * ace

    return [region, flux, summary]

#-------------------------------------------------------------------------------
#-- read_sim: find the current instrument                                     --
#-------------------------------------------------------------------------------

def read_sim():
    """
    find the current instrument
    input: none but read from <sim_file>
    output: si
    """
    si   = 'NA'

    data = mcf.read_data_file(sim_file)
    for ent in data:
        atemp = re.split('\s+', ent)
        btemp = re.split('\.',  atemp[0])
        try:
            ctime = Chandra.Time.DateTime(btemp[0]).secs
        except:
            continue
        if ctime > current_time:
            break
        si    = atemp[1]

    return si

#-------------------------------------------------------------------------------
#-- read_otg: find which grating is used                                     ---
#-------------------------------------------------------------------------------

def read_otg():
    """
    find which grating is used
    input: nont but read from <otg_file>
    output: otg --- HETG/LETG/NONE/BAD
    """
    convert_grathist_format()
    data = mcf.read_data_file(otg_file)
    hetg = ''
    letg = ''
    for ent in data:
        cols  = re.split('\s+', ent)
        btemp = re.split('\.', cols[0])
        try:
            ctime = Chandra.Time.DateTime(btemp[0]).secs
        except:
            continue
        if ctime > current_time:
            break
        else:
            hetg  = cols[1]
            letg  = cols[2]

    otg = 'NONE'
    if   hetg == 'HETG-IN'  and letg == 'LETG-OUT':
        otg = 'HETG'
    elif hetg == 'HETG-OUT' and letg == 'LETG-IN':
        otg = 'LETG'
    elif hetg == 'HETG-IN'  and letg == 'LETG-IN':
        otg = 'BAD'
    else:
        otg = 'NONE'

    return otg

#-------------------------------------------------------------------------------
#-- find_attenuate_flux: compute attenuated flux                              --
#-------------------------------------------------------------------------------

def find_attenuate_flux(flux, si, otg):
    """
    compute attenuated flux
    input:  flux    --- flax
            si      --- instrument
            otg     --- grating 
    output: aflux   --- attenudated flux
    """

    aflux = flux
    mc = re.search('HRC', si)
    if mc is not None:
        aflux = 0.0
    elif otg == 'LETG':
        aflux *= 0.5
    elif otg == 'HETG':
        aflux *= 0.2

    return aflux
    
#-------------------------------------------------------------------------------
#-- current_yday: get the current tim in day of the year with year           ---
#-------------------------------------------------------------------------------

def current_yday():
    """
    get the current tim in day of the year with year: ex: 2020001.12343
    input: none
    output: ydoy ---- year date with year at the front
    """

    out   = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    atemp = re.split(':', out)
    year  = float(atemp[0])
    yday  = float(atemp[1])
    hh    = float(atemp[2])
    mm    = float(atemp[3])
    ss    = float(atemp[4])
    ydoy  = 1000 * year + yday + hh / 24.0 + mm /1400.0 + ss / 86400.0

    return ydoy

#-------------------------------------------------------------------------------
#-- update_crm_html: update crm web site----------------------------------------
#-------------------------------------------------------------------------------

def update_crm_html():
    """
    update crm web site
    input none but read from <data_dir>/CRMsummary.dat
    output: <html_dir>/CRMsummary.html
    """
    ifile = crm3_dir + '/Data/CRMsummary.dat'
    with  open(ifile, 'r') as f:
        line = f.read()
    
    ifile = house_keeping + 'top_page_template'
    with open(ifile, 'r') as f:
        html = f.read()
    
    html = html.replace("#TEXT#", line)
    
    ofile = html_dir + 'index.html'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/index.html"
    with open(ofile, 'w') as fo: 
        fo.write(html)

#-------------------------------------------------------------------------------
#-- convert_grathist_format: convert GRATHIST format                          --
#-------------------------------------------------------------------------------

def convert_grathist_format():
    """
    convert GRATHIST format
    input: none but read from: /proj/sot/acis/FLU-MON/GRATHIST-2001.dat
    output: <crm3_dir>/Data/grathist.dat
    """

    ifile = '/proj/sot/acis/FLU-MON/GRATHIST-2001.dat'
    data  = mcf.read_data_file(ifile)
    line  = ''
    for ent in data:
        atemp = re.split('\s+', ent)
        line  = line + atemp[0].replace(':', ' ') + '  '
        if atemp[1] == 'HETG-IN':
            line = line + '1' + '  '
        else:
            line = line + '0' + '  '
        if atemp[2] == 'LETG-IN':
            line = line + '1' + '  '
        else:
            line = line + '0' + '  '
        line = line + atemp[3] + '\n'

    ofile = crm3_dir + 'Data/grathist.dat'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/grathist.dat"
    with open(ofile, 'w') as fo:
        fo.write(line)


#-------------------------------------------------------------------------------
#---THIS IS NOT USED....                                                     ---
#-------------------------------------------------------------------------------

def read_crm_data():
    file1 = crmdat_root + '87'
    file2 = crmdat_root + '90'
    if os.path.isfile(file2):
        if os.stat(file1).st_size == os.stat(file2).st_size:
            new_crm = []
            for ent in crm_n_list:
                ifile = crmdat_root + ent
                data  = mcf.read_data_file(ifile)
                new_crm.append(data)

        return new_crm
    else:
        return False


#-------------------------------------------------------------------------------

if __name__ == "__main__":

    create_crm_summary_table()
    
