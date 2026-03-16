#!/usr/bin/env python
"""
**collect_goes_long.py**: Collect GOES data for the long term use

:Author: t. isobe (tisobe@cfa.harvard.edu)
:Maintainer: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Feb 18, 2025

# /// script
# requires-python = ">3.12"
# dependencies = [
#   "file_readers>=0.1",
# ]
# ///

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
import sys
from cxotime import CxoTime
import json
import argparse
import traceback
from astropy.io import ascii
import file_readers as fr
#
# --- Define directory pathing
#
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"
OUT_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"

_ARCHIVE_COLS = (
    'P1',
    'P2A',
    'P2B',
    'P3',
    'P4',
    'P5',
    'P6',
    'P7',
    'P8A',
    'P8B',
    'P8C',
    'P9',
    'P10',
)


def collect_goes_long():
    """Collect GOES data for the long term use

    :Web Link: https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json
    :File Out: <data_dir>/goes_data_r.txt
                Time P1  P2A P2B P3  P4  P5  P6  P7  P8A P8B P8C P9  P10 HRC Proxy
    """
    #
    # --- find the last entry time
    #
    last_line = fr.get_last_text_line(f"{GOES_DATA_DIR}/goes_data_r.txt")
    cutoff = CxoTime(last_line.split()[0])
    #
    # --- extract proton data
    #
    goes_table = ascii.read(f"{GOES_DATA_DIR}/goes_differential_protons.ecsv")
    cxotime = CxoTime(goes_table['time_tag'].data)
    goes_table.add_column(cxotime, name = 'cxotime')
    #
    # --- Select new data lines
    #
    sel = goes_table['cxotime'] > cutoff
    subtable = goes_table[sel]
    #
    # --- compute hrc proxy
    #
    hrc_proxy = []
    for row in subtable:
        _ = compute_hrc(row)
        hrc_proxy.append(_)
    subtable.add_column(hrc_proxy, name = "HRC_Proxy")
    #
    # --- format archive addition
    #
    line =''
    for row in subtable:
        line += format_archive_line(row)
    
    with open(f"{OUT_DATA_DIR}/goes_data_r.txt", 'a') as f:
        f.write(line)


def compute_hrc(row):
    """
    :NOTE: The HRC Proxy was calculated based on GOES channel flux rates in MeV units.
        The MTA GOES data sets use MeV units accoridngly, but documentation of GOES uses KeV.
        This proxy equation for the GOES-R series was put in use as of 2021:125:06:05:00.
    
    P5 = 11.64 - 23.27 MeV
    P6 = 25.90 - 38.10 MeV
    P7 = 40.30 - 73.40 MeV
    """
    
    hrc_proxy = (143 * row['P5']) + (64738 * row['P6']) + (162505 * row['P7']) + 4127
    return hrc_proxy

def format_archive_line(row):
    """
    Format the astropy table into the goes_data_r.txt specific archive format.
    """
    line = f"{row['cxotime'].date.split('.')[0]}\t\t"
    line += "\t".join([f"{i:1.3e}" for i in row[_ARCHIVE_COLS]])
    line += f"\t{row['HRC_Proxy']:5.0f}\t\n"
    
    return line

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
        help="Directory path to determine output location of data file.",
    )
    args = parser.parse_args()

    if args.mode == "test":
        OUT_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(OUT_DATA_DIR, exist_ok=True)
        collect_goes_long()
    else:
        #
        # --- Create a lock file and exit strategy in case of race conditions
        #
        import getpass

        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(
                f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            )
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        try:
            collect_goes_long()
        except json.decoder.JSONDecodeError:
            traceback.print_exc() #: Record issue with downloaded JSON and finish.
        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")
