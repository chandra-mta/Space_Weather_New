#!/usr/bin/env python
"""
**create_crm_summary_table.py**: Summarize the CRM flux table into different data files.

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Mar 11, 2026

# /// script
# requires-python = ">=3.12"
# ///

# /// testing
# tested-ska-release = "2026.1"
# ///
"""

import os
import json
import numpy as np
import argparse
import getpass
import signal
from astropy.io import ascii
from cxotime import CxoTime
from pathlib import Path
#
# --- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv('SPACE_WEATHER', "/data/mta4/Space_Weather"))
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))

CRM_DATA_DIR : Path = SPACE_WEATHER / "CRM3" / "Data"
CRM_WEB_DIR : Path = SPACE_WEATHER_WEB / "CRM3"
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"
EPHEM_DATA_DIR : Path = SPACE_WEATHER / "EPHEM" / "Data"
#
# --- Globals
#
#: This factor converts the GOES-R P4 channel flux (already recorded in MeV) into the RADMON P4GM units.
GOES_P4_RADMON_FACTOR = 3.4
#: This factor converts the GOES-R P7 channel flux (already recorded in MeV) into the RADMON P41GM units
GOES_P7_RADMON_FACTOR = 12
TDELTA = 300

CXONOW = CxoTime()
ISONOW = CXONOW.isot.split(".")[0] + "Z"
SOL_REGION = [
    "NULL",
    "Solar_Wind",
    "Magnetosheath",
    "Magnetosphere",
]  #: Indexed according to the CRM solar region index marker


def create_crm_summary():
    """
    Read from the crm_flux_table.ecsv and generate summaries.
    """

    summary, orbit_meta = read_crm_flux_table()
    #: Include solar region name for additional clarity.
    summary["sol_region"] = SOL_REGION[summary["sol_region_idx"]]
    summary["cxonow"] = CxoTime(summary["cxosecs"]).date
    supp_data = crm_supplementary_info()
    summary.update(supp_data)
    summary.update(orbit_meta)
    summary = _coerce_json_serialize(summary)

    _summary_json = CRM_DATA_DIR / "CRMsummary.json"
    with open(_summary_json, "w") as f:
        json.dump(summary, f, indent=4)

def read_crm_flux_table():
    """
    Read from the crm_flux_table.ecsv
    """
    _table_file = CRM_DATA_DIR / "crm_flux_table.ecsv"
    #: Astropy file format guesser can sometimes mistreat a Path() instance. Avoid by specifying format.
    crm_flux_table = ascii.read(_table_file, format="ecsv")

    corrected_crm_fluence = sum(crm_flux_table["corrected_crm_flux"] * TDELTA)
    attenuated_crm_fluence = sum(crm_flux_table["attenuated_crm_flux"] * TDELTA)

    summary = {}
    last_entry = {
        col: crm_flux_table[-1][col].tolist() for col in crm_flux_table.columns
    }
    summary.update(last_entry)
    summary["corrected_crm_fluence"] = corrected_crm_fluence
    summary["attenuated_crm_fluence"] = attenuated_crm_fluence

    return summary, crm_flux_table.meta


def crm_supplementary_info():
    """
    Pulls the information included in the CRM summary data file, but isn't used to calculate CRM flux.
    """
    supp_data = {}
    goes_data = read_goes()
    supp_data.update(goes_data)

    ephem_data = read_ephem()
    supp_data.update(ephem_data)
    return supp_data


def read_goes():
    """
    Read the most recent GOES flux data for P4, P7, and >= E2
    """
    goes_data = {
        "goes_p4_flux": None,
        "goes_p7_flux": None,
        "goes_e2_flux": None,
    }
    _diff_table = GOES_DATA_DIR / "goes_differential_protons.ecsv"
    _intg_table = GOES_DATA_DIR / "goes_integral_electrons.ecsv"
    #: Astropy file format guesser can sometimes mistreat a Path() instance. Avoid by specifying format.
    diff_proton_table = ascii.read(_diff_table, format="ecsv")
    intg_electron_table = ascii.read(_intg_table, format="ecsv")

    #: In case the most recent flux for the target channel is missing,
    #: record the last known values by iterating backwards.
    idx = -1
    while goes_data["goes_p4_flux"] is None:
        a = diff_proton_table["P4"][idx]
        if a == np.ma.masked:
            idx -= 1
        else:
            goes_data["goes_p4_flux"] = a * GOES_P4_RADMON_FACTOR
    idx = -1
    while goes_data["goes_p7_flux"] is None:
        b = diff_proton_table["P7"][idx]
        if b == np.ma.masked:
            idx -= 1
        else:
            goes_data["goes_p7_flux"] = b * GOES_P7_RADMON_FACTOR
    idx = -1
    while goes_data["goes_e2_flux"] is None:
        c = intg_electron_table[">=2 MeV"][idx]
        if c == np.ma.masked:
            idx -= 1
        else:
            goes_data["goes_e2_flux"] = c

    return goes_data


def read_ephem():
    """
    Read the EPHEM file to determine orbit altitude and leg

    The EPHEM file records altitude in meters. This fetch returns in km.
    """
    _gephem = EPHEM_DATA_DIR / "gephem.dat"
    with open(_gephem) as f:
        data = f.read().split()  #: Located on the first and only line.
        alt = int(float(data[0]) / 1000)
        leg = data[1]
    return {"orbit_altitude": alt, "orbit_leg": leg}


def _coerce_json_serialize(obj):
    def _coerce(x):
        if x.__class__.__module__ == "numpy":
            return x.tolist()
        elif isinstance(x, CxoTime):
            return x.date
        else:
            return x

    if isinstance(obj, dict):
        return {key: _coerce(obj[key]) for key in obj.keys()}
    elif isinstance(obj, list):
        return [_coerce(i) for i in obj]
    else:
        return _coerce(obj)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flight", "test"], required=True, help="Determine running mode.")
    parser.add_argument("-p", "--path", required=False, help="Directory path to determine output location of summary.")
    args = parser.parse_args()
    #
    # --- Determine if running in test mode and change pathing if so.
    #
    if args.mode == "test":
        #
        # --- Path output to same location as unit tests.
        #
        if args.path:
            CRM_DATA_DIR = Path(args.path)
        else:
            CRM_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        
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
            #: Kill old process if stalling.
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            os.system(
                f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock"
            )
        else:
            os.system(
                f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock"
            )

        create_crm_summary()
        #: Make available on the web.
        os.system(
            f"cp {OUT_CRM_DATA_DIR}/CRMsummary.json {OUT_CRM_WEB_DIR}/CRMsummary.json"
        )
        #
        # --- Remove lock file once process is completed.
        #
        os.system(f"rm /tmp/{user}/{name}.lock")
