#!/proj/sot/ska3/flight/bin/python
"""
**create_crm_summary_table.py**: update the CRMsummary.dat data summary table

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Jul 18, 2025

"""
import os
import re
import time
import json
from numpy.ma import masked #: Marker for missing data in reading astropy tables
from astropy.io import ascii
from cxotime import CxoTime
from jinja2 import Environment, FileSystemLoader

#
# --- Define Directory Pathing
#
CRM_WEB_DIR = "/data/mta4/www/RADIATION/CRM"
CRM_DATA_DIR = "/data/mta4/Space_Weather/CRM3/Data"
EPHEM_DATA_DIR = "/data/mta4/Space_Weather/EPHEM/Data"
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"
KP_DATA_DIR = "/data/mta4/Space_Weather/KP/Data"
ACIS_FLUENCE_DATA_DIR = "/proj/sot/acis/FLU-MON"
#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True))
_JINJA_ENV.filters['e_format'] = lambda v, p: f"{v:.{p}e}" #: Custom filter to format to scientific notation
#
# --- Globals
#
GOES_P4_RADMON_FACTOR = 3.4 #: This factor converts the GOES-R P4 channel flux (already recorded in MeV) into the RADMON P4GM units.
GOES_P7_RADMON_FACTOR = 12 #: This factor converts the GOES-R P7 channel flux (already recorded in MeV) into the RADMON P41GM units.

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
#
#--- satellite location regarded to the solar wind environment
#
sol_region     = ['NULL', 'Solar_Wind', 'Magnetosheath', 'Magnetosphere']
#
#--- current time  in <yyyy>:<ddd>:<hh>:<mm>:<ss> and in seconds from 1998.1.1
#
cl_time      = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
CXONOW = CxoTime()
ISONOW = CXONOW.isot.split('.')[0] + "Z"

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
# --- Read old summary for certain uses.
#
    with open(f"{CRM_DATA_DIR}/CRMsummary.json") as f:
        old_summary = json.load(f)

#
#--- read all needed data
#
    crm_summary = read_goes()
    crm_summary.update(read_ephem())
    crm_summary.update(read_kp())

#
# --- Once all data is gathered. Write the new summary data sets.
#
    with open(f"{CRM_DATA_DIR}/CRMsummary.json", 'w') as f:
        json.dump(crm_summary, f, indent = 4)

    ace             = read_ace_data()
    [region, flux, summary] = read_crm_fluence(kpi, ace)
    si              = read_sim()
    otg             = read_otg()
    aflux           = find_attenuate_flux(flux, si, otg)
#
#--- supply missing data
#
    ostart   = summary[-7]
    fluence  = float(summary[-2])
    afluence = float(summary[-1])
#
#--- when the orbit changes from descending to ascending, write the data into an archive
#--- and reset orbit starting time (ostart) fluence and afluence
#
    if leg == 'A' and summary[-6] == 'D':
        oend = time.strftime("%Y:%j:%H:%M:%S", time.gmtime())
        with open(f"{CRM_DATA_DIR}/CRMarchive.dat", 'a') as fo:
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

    with open(f"{CRM_DATA_DIR}/CRMsummary.dat", 'w') as fo:
        fo.write(line)
#
#--- back up the data files
#
    os.system(f"cp -f {CRM_DATA_DIR}/CRMsummary.dat {CRM_WEB_DIR}/CRMsummary.dat")
    os.system(f"cp -f {CRM_DATA_DIR}/CRMarchive.dat {CRM_WEB_DIR}/CRMarchive.dat")

def check_val(val):
    try:
        val = float(val)
    except:
        val = 0.0

    return val

def read_goes():
    """
    Read the most recent GOES flux data for P4, P7, and >= E2 
    """
    goes_data = {'goes_p4': None,
                 'goes_p7': None,
                 'goes_e2': None,}
    diff_proton_table = ascii.read(f"{GOES_DATA_DIR}/goes_differential_protons.ecsv")
    intg_electron_table = ascii.read(f"{GOES_DATA_DIR}/goes_integral_electrons.ecsv")
    
    #: In case the most recent flux for the target channel is missing, record the last known values by iterating backwards.
    idx = -1
    while goes_data['goes_p4'] is None:
        a = diff_proton_table['P4'][idx]
        if a == masked:
            idx -= 1
        else:
            goes_data['goes_p4'] = a * GOES_P4_RADMON_FACTOR
            goes_data['goes_p4_update_time'] = diff_proton_table['time_tag'][idx]
    idx = -1
    while goes_data['goes_p7'] is None:
        b = diff_proton_table['P7'][idx]
        if b == masked:
            idx -= 1
        else:
            goes_data['goes_p7'] = b * GOES_P7_RADMON_FACTOR
            goes_data['goes_p7_update_time'] = diff_proton_table['time_tag'][idx]
    idx = -1
    while goes_data['goes_e2'] is None:
        c = intg_electron_table['>=2 MeV'][idx]
        if c == masked:
            idx -= 1
        else:
            goes_data['goes_e2'] = c
            goes_data['goes_e2_update_time'] = intg_electron_table['time_tag'][idx]

    return goes_data

def read_ephem():
    """
    Read the EPHEM file to determine orbit altitude and leg
    
    The EPHEM file records altitude in meter. This fetch returns in km.
    """
    with open(f"{EPHEM_DATA_DIR}/gephem.dat") as f:
        data = f.read().split() #: Located on the first and only line.
        alt = int(float(data[0]) / 1000)
        leg = data[1]
    stats = os.stat(f"{EPHEM_DATA_DIR}/gephem.dat")
    time = CxoTime(stats.st_mtime,format='unix').isot.split('.')[0] + "Z"
    return {'orbit_altitude': alt, 'orbit_leg': leg, 'orbit_update_time': time}

def read_kp():
    """
    Read the most recent observed / estimated value for the KP index.
    """
    kp_forecast_table = ascii.read(f"{KP_DATA_DIR}/kp_forecast.ecsv")
    #: Note that the kp_forecast_table is fetched every 3 hours, so sometimes the estimates are outdated.
    subset = kp_forecast_table[kp_forecast_table['time_tag'] <= ISONOW]
    kp_data = {'kp': subset['kp'][-1].data, 'kp_update_time': subset['time_tag'][-1].data}
    return kp_data

#-------------------------------------------------------------------------------
#-- read_ace_data: read current ace value                                     --
#-------------------------------------------------------------------------------

def read_ace_data():
    """
    read current ace value
    input:  none, but read from <ace_data_dir>/fluace.dat
    output: ace --- ace value
    """
    ace     = 0
    acefile = f"{ACE_DATA_DIR}/fluace.dat"
    acegood = f"{ACE_DATA_DIR}/fluace.dat.good"
    try:
        with open(acefile) as f:
            data = [line.strip() for line in f.readlines()]
        atemp = re.split('\s+', data[-3])
        ace_n = float(atemp[11])
        if ace_n != ace:
            ace = ace_n
#
#--- if the data is good, copy it to kp.dat.good for future use
#
            os.system(f"cp -f {acefile} {acegood}")
        else:
            with open(acegood) as f:
                data = [line.strip() for line in f.readlines()]
            atemp = re.split('\s+', data[-3])
            ace_n = float(atemp[11])
            if ace_n != ace:
                ace = ace_n
    except:
#
#--- the data is bad. use the last good data
#
        with open(acegood) as f:
            data = [line.strip() for line in f.readlines()]
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
            it also reads  data from CRMsummary.dat
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
    with open(f"{CRM_DATA_DIR}/CRMsummary.dat") as f:
        data = [line.strip() for line in f.readlines()]
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
            val = float(atemp[-1])
        except:
            val = atemp[-1].strip()

        summary.append(val)

    with open(f"{CRM_DATA_DIR}/CRM3_p.dat{kpi}") as f:
        data = [line.strip() for line in f.readlines()]

    chk = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        time  = float(atemp[0])
        if time > CXONOW:
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
        if abs(time - CXONOW) > abs(CXONOW - stime):
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
    input: none but read from <acis_fluence_data_dir>/FPHIST-2001.dat
    output: si
    """
    si   = 'NA'
    with open(f"{ACIS_FLUENCE_DATA_DIR}/FPHIST-2001.dat") as f:
        data = [line.strip() for line in f.readlines()]
    for ent in data:
        atemp = re.split('\s+', ent)
        btemp = re.split('\.',  atemp[0])
        try:
            ctime = CxoTime(btemp[0])
        except:
            continue
        if ctime > CXONOW:
            break
        si    = atemp[1]

    return si

#-------------------------------------------------------------------------------
#-- read_otg: find which grating is used                                     ---
#-------------------------------------------------------------------------------

def read_otg():
    """
    find which grating is used
    input: none but read from <acis_fluence_data_dir>/GRATHIST-2001.dat
    output: otg --- HETG/LETG/NONE/BAD
    """
    convert_grathist_format()
    with open(f"{ACIS_FLUENCE_DATA_DIR}/GRATHIST-2001.dat") as f:
        data = [line.strip() for line in f.readlines()]
    hetg = ''
    letg = ''
    for ent in data:
        cols  = re.split('\s+', ent)
        btemp = re.split('\.', cols[0])
        try:
            ctime = CxoTime(btemp[0])
        except:
            continue
        if ctime > CXONOW:
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
#-- convert_grathist_format: convert GRATHIST format                          --
#-------------------------------------------------------------------------------

def convert_grathist_format():
    """
    convert GRATHIST format
    input: none but read from: <acis_fluence_data_dir>/GRATHIST-2001.dat
    output: <crm3_dir>/Data/grathist.dat
    """

    with open(f"{ACIS_FLUENCE_DATA_DIR}/GRATHIST-2001.dat") as f:
        data = [line.strip() for line in f.readlines()]
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

    with open(f"{CRM_DATA_DIR}/grathist.dat", 'w') as fo:
        fo.write(line)

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    create_crm_summary_table()
    
