#!/proj/sot/ska3/flight/bin/python
"""
**create_crm_summary_table.py**: update the CRMsummary.dat data summary table

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Jul 18, 2025

"""
import os
import re
import json
import argparse
import getpass
import signal
from numpy.ma import masked #: Marker for missing data in reading astropy tables
from astropy.io import ascii
from cxotime import CxoTime
from jinja2 import Environment, FileSystemLoader

#
# --- Define Directory Pathing
#
CRM_WEB_DIR = "/data/mta4/www/RADIATION/CRM"
CRM_DATA_DIR = "/data/mta4/Space_Weather/CRM3/Data"
OUT_CRM_WEB_DIR = "/data/mta4/www/RADIATION/CRM"
OUT_CRM_DATA_DIR = "/data/mta4/Space_Weather/CRM3/Data"
EPHEM_DATA_DIR = "/data/mta4/Space_Weather/EPHEM/Data"
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"
KP_DATA_DIR = "/data/mta4/Space_Weather/KP/Data"
ACIS_FLUENCE_DATA_DIR = "/proj/sot/acis/FLU-MON"
#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True), keep_trailing_newline=True) #: Old format has an additional newline character
_JINJA_ENV.filters['e_format'] = lambda v, p: f"{v:.{p}e}" #: Custom filter to format to scientific notation
CRM_DATA_COL_NAMES = ('cxosecs', 'sol_region_idx', 'proton_flux', 'x', 'y', 'z') #: Column names possibly inaccurate
#
# --- Globals
#
GOES_P4_RADMON_FACTOR = 3.4 #: This factor converts the GOES-R P4 channel flux (already recorded in MeV) into the RADMON P4GM units.
GOES_P7_RADMON_FACTOR = 12 #: This factor converts the GOES-R P7 channel flux (already recorded in MeV) into the RADMON P41GM units
SW_FACTOR  = [0, 1, 2, 0.5] #: Indexed according to the CRM solar region index marker
CRM_FACTOR = [0, 0, 1, 1] #: Indexed according to the CRM solar region index marker
TDELTA = 300

CXONOW = CxoTime()
ISONOW = CXONOW.isot.split('.')[0] + "Z"
SOL_REGION = ['NULL', 'Solar_Wind', 'Magnetosheath', 'Magnetosphere'] #: Indexed according to the CRM solar region index marker

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
    with open(f"{OUT_CRM_DATA_DIR}/CRMsummary.json") as f:
        old_summary = json.load(f)
#
#--- read all needed data
#
    crm_summary = read_goes()
    crm_summary.update(read_ephem())
    crm_summary.update(read_kp())

    kp = crm_summary['kp']
    ace = read_ace_data() #: Kept as legacy version since ACE will be replaced with SWFO-L1 in September 2025.
    crm_summary['ace_p3'] = ace
    crm_summary.update(read_crm_dat(kp,ace))
    crm_summary.update(read_inst_config())
    crm_summary['attenuated_crm_flux'] = crm_summary['attenuation_factor'] * crm_summary['crm_flux']

#
# --- Determine orbit specific values
#
    old_fluence = old_summary['crm_fluence']
    old_attenuated_fluence = old_summary['attenuated_crm_fluence']
    fluence = old_fluence + crm_summary['crm_flux'] * TDELTA
    attenuated_fluence = old_attenuated_fluence + crm_summary['attenuated_crm_flux'] * TDELTA
    orbit_start = old_summary['orbit_start']

    if old_summary['orbit_leg'] == 'D' and crm_summary['orbit_leg'] == 'A':
        #: When the orbit changes from descending to ascending, 
        #: write the data into an archive and reset orbit starting time (ostart) fluence and afluence
        orbit_end = CXONOW.date.split('.')[0]
        #: old archive write of fluence
        with open(f"{CRM_DATA_DIR}/CRMarchive.dat", 'a') as fo:
            fo.write(f"{orbit_start}   {orbit_end}   {fluence}   {attenuated_fluence}\n")
        orbit_start = orbit_end
        fluence = 0
        attenuated_fluence = 0
    
    crm_summary['orbit_start'] = orbit_start
    crm_summary['crm_fluence'] = fluence
    crm_summary['attenuated_crm_fluence'] = attenuated_fluence
    crm_summary['cxonow'] = CXONOW.date.split('.')[0]
#
# --- Once all data is gathered. Write the new summary data sets.
#
    crm_summary = coerce_json_serialize(crm_summary)
    with open(f"{OUT_CRM_DATA_DIR}/CRMsummary.json", 'w') as f:
        json.dump(crm_summary, f, indent = 4)
    with open(f"{OUT_CRM_WEB_DIR}/CRMsummary.json", 'w') as f:
        json.dump(crm_summary, f, indent = 4)

    crm_template = _JINJA_ENV.get_template('CRMsummary.jinja')
    crm_render = crm_template.render(data = crm_summary)
    with open(f"{OUT_CRM_DATA_DIR}/CRMsummary.dat", 'w') as fo:
        fo.write(crm_render)
    with open(f"{OUT_CRM_WEB_DIR}/CRMsummary.dat", 'w') as fo:
        fo.write(crm_render)

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
    kp_data = {'kp': subset['kp'][-1], 'kp_update_time': subset['time_tag'][-1]}
    return kp_data

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
        atemp = re.split(r'\s+', data[-3])
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
            atemp = re.split(r'\s+', data[-3])
            ace_n = float(atemp[11])
            if ace_n != ace:
                ace = ace_n
    except:
#
#--- the data is bad. use the last good data
#
        with open(acegood) as f:
            data = [line.strip() for line in f.readlines()]
        atemp = re.split(r'\s+', data[-3])
        ace_n = float(atemp[11])
        if ace_n != ace:
            ace = ace_n

    return ace

def read_crm_dat(kp, ace):
    """Read the CRM data file generated by runcrm as determined by
    the current best estimate for the KP index.

    :param kp: KP index
    :type kp: float
    :param ace: ACE P3 Flux
    :type ace: float
    """
    
    #: runcrm stores data for each KP under a specific file name format
    kpi = f"{kp:.1f}".replace('.', '')
    file = f"{CRM_DATA_DIR}/CRM3_p.dat{kpi}"
    crm_data_table = ascii.read(file, names = CRM_DATA_COL_NAMES)
    
    sel = crm_data_table['cxosecs'] < CXONOW
    current_row = crm_data_table[sel][-1]
    
    sol_region_idx = current_row['sol_region_idx']
    #: The CRM flux is calculated as a sum of the region-factored CRM flux plus
    #: the space-weather-factored flux.
    crm_flux = CRM_FACTOR[sol_region_idx] * current_row['proton_flux'] + SW_FACTOR[sol_region_idx] * ace
    
    crm_data = {
        'crm_data_update_time': CxoTime(current_row['cxosecs']).isot.split('.')[0] + 'Z',
        'sol_region_idx': sol_region_idx,
        'sol_region': SOL_REGION[sol_region_idx],
        'crm_flux': crm_flux
    }
    return crm_data
    

def read_inst_config():
    """
    Read the Science Instrument Configuration (SIM and OTG)
    """
    
    fp_table = ascii.read(f"{ACIS_FLUENCE_DATA_DIR}/FPHIST-2001.dat",
                          names = ('cxcdate', 'inst', 'obsid'),
                          data_start = -50)
    grat_table = ascii.read(f"{ACIS_FLUENCE_DATA_DIR}/GRATHIST-2001.dat",
                          names = ('cxcdate', 'hetg', 'letg', 'obsid'),
                          data_start = -50)
    
    sel_fp = fp_table['cxcdate'] < CXONOW
    sel_grat = grat_table['cxcdate'] < CXONOW
    current_fp_row = fp_table[sel_fp][-1]
    current_grat_row = grat_table[sel_grat][-1]
    
    time = max(CxoTime(current_fp_row['cxcdate']), CxoTime(current_grat_row['cxcdate']))
    inst = current_fp_row['inst']
    hetg, letg = current_grat_row['hetg'], current_grat_row['letg']
    
    otg = "NONE"
    if hetg == 'HETG-IN' and letg == 'LETG-OUT':
        otg = 'HETG'
    elif hetg == 'HETG-OUT' and letg == 'LETG-IN':
        otg = 'LETG'
    elif hetg == 'HETG-IN' and letg == 'LETG-IN':
        otg = 'BAD'
    else:
        otg = 'NONE'
    
    attenuation_factor = 0

    if inst in ('ACIS-I', 'ACIS-S'):
        if otg == 'LETG':
            attenuation_factor = 0.5
        elif otg == 'HETG':
            attenuation_factor = 0.2

    inst_config_data = {
        'isntrument_update_time': time.isot.split('.')[0] + "Z",
        'instrument': inst,
        'grating': otg,
        'attenuation_factor': attenuation_factor
    }
    return inst_config_data

def coerce_json_serialize(obj):
    def _coerce(x):
        if x.__class__.__module__ == 'numpy':
            return x.tolist()
        else:
            return x
    if isinstance(obj,dict):
        return {key:_coerce(obj[key]) for key in obj.keys()}
    elif isinstance(obj,list):
        return [_coerce(i) for i in obj]
    else:
        return _coerce(obj)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-m",
        "--mode",
        choices=["flight", "test"],
        required=True,
        help="Determine running mode.",
    )
    parser.add_argument(
        "-p",
        "--path",
        required=False,
        help="Directory path to determine output location of plot.",
    )
    args = parser.parse_args()
    #
    # --- Determine if running in test mode and change pathing if so
    #
    if args.mode == "test":
        #
        # --- Path output to same location as unit tests
        #
        OUT_CRM_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        if args.path:
            OUT_CRM_DATA_DIR = args.path
        os.makedirs(OUT_CRM_DATA_DIR, exist_ok=True)
        OUT_CRM_WEB_DIR = OUT_CRM_DATA_DIR
        
        create_crm_summary_table()

    elif args.mode == "flight":
        #
        # --- Create a lock file and exit strategy in case of race conditions
        #

        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            with open(f"/tmp/{user}/{name}.lock") as f:
                pid = int(f.readlines()[-1].strip())
            #: Kill old process if stalling
            try:
                os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")
        else:
            os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")

        create_crm_summary_table()
        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")