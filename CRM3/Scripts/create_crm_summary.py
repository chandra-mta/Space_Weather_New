#!/proj/sot/ska3/flight/bin/python
"""
**create_crm_summary_table.py**: Summarize the CRM flux table into different data files.

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Aug 11, 2025

"""
import os
import json
import numpy as np
import argparse
import getpass
import signal
import warnings
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
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"
#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True), keep_trailing_newline=True) #: Old format has an additional newline character
_JINJA_ENV.filters['e_format'] = lambda v, p: f"{v:.{p}e}" #: Custom filter to format to scientific notation
_JINJA_ENV.filters['date_format'] = lambda v: f"{v.split('.')[0]}" #: Custom filter to remove cxotime fractional seconds
#
# --- Globals
#
GOES_P4_RADMON_FACTOR = 3.4 #: This factor converts the GOES-R P4 channel flux (already recorded in MeV) into the RADMON P4GM units.
GOES_P7_RADMON_FACTOR = 12 #: This factor converts the GOES-R P7 channel flux (already recorded in MeV) into the RADMON P41GM units
TDELTA = 300

CXONOW = CxoTime()
ISONOW = CXONOW.isot.split('.')[0] + "Z"
SOL_REGION = ['NULL', 'Solar_Wind', 'Magnetosheath', 'Magnetosphere'] #: Indexed according to the CRM solar region index marker

def create_crm_summary():
    """
    Read from the crm_flux_table.ecsv and generate summaries.
    """

    summary, summary_meta = read_crm_flux_table()
    summary['sol_region'] = SOL_REGION[summary['sol_region_idx']] #: Additional clarity
    summary['cxonow'] = CxoTime(summary['cxosecs']).date
    supp_data, supp_source_list = crm_supplementary_info()

    summary.update(supp_data)
    if isinstance(summary_meta.get('sources'), list):
        summary_meta['sources'] += supp_source_list
    else:
        warnings.warn("Couldn't assign CRM flux table metadata source")
        summary_meta['sources'] = supp_source_list
    summary_meta['description'] = "Summary of CRM data and related fluxes."

    summary = _coerce_json_serialize(summary)
    summary_meta = _coerce_json_serialize(summary_meta)
    summary['meta'] = summary_meta

    with open(f"{OUT_CRM_DATA_DIR}/CRMsummary.json", 'w') as f:
        json.dump(summary, f, indent = 4)

    crm_template = _JINJA_ENV.get_template('CRMsummary.jinja')
    crm_render = crm_template.render(data = summary)
    with open(f"{OUT_CRM_DATA_DIR}/CRMsummary.dat", 'w') as fo:
        fo.write(crm_render)

def read_crm_flux_table():
    """
    Read from the crm_flux_table.ecsv
    """
    crm_flux_table = ascii.read(f"{OUT_CRM_DATA_DIR}/crm_flux_table.ecsv")

    corrected_crm_fluence = sum(crm_flux_table['corrected_crm_flux'] * TDELTA)
    attenuated_crm_fluence = sum(crm_flux_table['attenuated_crm_flux'] * TDELTA)

    summary = {}
    last_entry = {col: crm_flux_table[-1][col].tolist() for col in crm_flux_table.columns}
    summary.update(last_entry)
    summary['corrected_crm_fluence'] = corrected_crm_fluence
    summary['attenuated_crm_fluence'] = attenuated_crm_fluence

    return summary, crm_flux_table.meta

def crm_supplementary_info():
    """
    Pulls the information included in the CRM summary data file, but isn't used to calculate CRM flux.
    """
    supp_data = {}
    _source_list = []
    goes_data, goes_source_list = read_goes()
    supp_data.update(goes_data)
    _source_list += goes_source_list

    ephem_data, ephem_source_list = read_ephem()
    supp_data.update(ephem_data)
    _source_list += ephem_source_list
    return supp_data, _source_list
    
def read_goes():
    """
    Read the most recent GOES flux data for P4, P7, and >= E2 
    """
    goes_data = {'goes_p4_flux': None,
                 'goes_p7_flux': None,
                 'goes_e2_flux': None,}
    diff_proton_table = ascii.read(f"{GOES_DATA_DIR}/goes_differential_protons.ecsv")
    intg_electron_table = ascii.read(f"{GOES_DATA_DIR}/goes_integral_electrons.ecsv")

    _source_list = []
    if isinstance(diff_proton_table.meta.get('sources'), list):
        _source_list += diff_proton_table.meta.get('sources')
    else:
        warnings.warn("Couldn't assign GOES diff table metadata source")
    if isinstance(intg_electron_table.meta.get('sources'), list):
        _source_list += intg_electron_table.meta.get('sources')
    else:
        warnings.warn("Couldn't assign GOES diff table metadata source")
    
    #: In case the most recent flux for the target channel is missing, record the last known values by iterating backwards.
    idx = -1
    while goes_data['goes_p4_flux'] is None:
        a = diff_proton_table['P4'][idx]
        if a == np.ma.masked:
            idx -= 1
        else:
            goes_data['goes_p4_flux'] = a * GOES_P4_RADMON_FACTOR
    idx = -1
    while goes_data['goes_p7_flux'] is None:
        b = diff_proton_table['P7'][idx]
        if b == np.ma.masked:
            idx -= 1
        else:
            goes_data['goes_p7_flux'] = b * GOES_P7_RADMON_FACTOR
    idx = -1
    while goes_data['goes_e2_flux'] is None:
        c = intg_electron_table['>=2 MeV'][idx]
        if c == np.ma.masked:
            idx -= 1
        else:
            goes_data['goes_e2_flux'] = c

    return goes_data, _source_list

def read_ephem():
    """
    Read the EPHEM file to determine orbit altitude and leg
    
    The EPHEM file records altitude in meters. This fetch returns in km.
    """
    with open(f"{EPHEM_DATA_DIR}/gephem.dat") as f:
        data = f.read().split() #: Located on the first and only line.
        alt = int(float(data[0]) / 1000)
        leg = data[1]
    stats = os.stat(f"{EPHEM_DATA_DIR}/gephem.dat")
    #: Format metadata of text file in style of table metadata
    meta_data = {
        'description': "Interpolation of the current Chandra ephemeris.",
        'sources': [
            {
                'origin_script': "/data/mta4/Space_Weather/EPHEM/Scripts/ephem_interpolate.py",
                'output_file': f"{EPHEM_DATA_DIR}/gephem.dat",
                'update_time': CxoTime(stats.st_mtime,format='unix').date,
                'mta_owned_origin': True
            }
        ]
    }
    return {'orbit_altitude': alt, 'orbit_leg': leg}, meta_data['sources']

def _coerce_json_serialize(obj):
    def _coerce(x):
        if x.__class__.__module__ == 'numpy':
            return x.tolist()
        elif isinstance(x, CxoTime):
            return x.date
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
        create_crm_summary()

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

        create_crm_summary()
        #: Make available on the web
        os.system(f"cp {OUT_CRM_DATA_DIR}/CRMsummary.json {OUT_CRM_WEB_DIR}/CRMsummary.json")
        os.system(f"cp {OUT_CRM_DATA_DIR}/CRMsummary.dat {OUT_CRM_WEB_DIR}/CRMsummary.dat")

        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")