#!/usr/bin/env python
"""
**collect_goes_long.py**: Collect GOES data for the long term use

:Author: t. isobe (tisobe@cfa.harvard.edu)
:Maintainer: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Feb 18, 2025

# /// script
# requires-python = ">3.12"
# dependencies = [
#   "file_readers=0.1",
# ]
# ///

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
import signal
from cxotime import CxoTime
import argparse
from astropy.io import ascii
import file_readers as fr
from pathlib import Path
import psutil
#
# --- Define directory pathing
#
SPACE_WEATHER = Path(os.getenv('SPACE_WEATHER', "/data/mta4/Space_Weather"))
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"
OUT_GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"

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

    :File In: <goes_data_dir>/goes_data_r.txt
    :File Out: <out_goes_data_dir>/goes_data_r.txt
                Time P1  P2A P2B P3  P4  P5  P6  P7  P8A P8B P8C P9  P10 HRC Proxy
    """
    #
    # --- find the last entry time
    #
    archive_file = GOES_DATA_DIR / "goes_data_r.txt"
    last_line = fr.get_last_text_line(str(archive_file)) # type: ignore
    cutoff = CxoTime(last_line.split()[0])
    #
    # --- extract proton data
    #
    proton_data_file = GOES_DATA_DIR / "goes_differential_protons.ecsv"
    goes_table = ascii.read(str(proton_data_file))
    cxotime = CxoTime(goes_table['time_tag'].data) # type: ignore
    goes_table.add_column(cxotime, name = 'cxotime') # type: ignore
    #
    # --- Select new data lines
    #
    sel = goes_table['cxotime'] > cutoff # type: ignore
    subtable = goes_table[sel] # type: ignore
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
    out_archive_file = OUT_GOES_DATA_DIR / "goes_data_r.txt"
    with open(out_archive_file, 'a') as f:
        f.write(line)


def compute_hrc(row):
    """
    :NOTE: The HRC Proxy was calculated based on GOES channel flux rates in MeV units.
        The MTA GOES data sets use MeV units accordingly, but documentation of GOES uses KeV.
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
        
        if args.path:
            OUT_GOES_DATA_DIR = Path(args.path)
        else:
            OUT_GOES_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        os.makedirs(OUT_GOES_DATA_DIR, exist_ok=True)
        collect_goes_long()
    else:
        #: Create a lock file and exit strategy in case of stall.
        name = os.path.basename(__file__).split(".")[0]
        user = os.getenv("USER", "mta")
        lock = Path("/tmp", user, f"{name}.lock")

        #: If lock file exists, read the pid and kill the process, then remove the lock file
        if os.path.isfile(lock):
            with open(lock) as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGTERM)
            os.remove(lock)
        
        #: Lock file with current pid
        pid = os.getpid()
        os.makedirs(lock.parent, exist_ok = True)
        with open(lock, 'w') as f:
            f.write(str(pid))

        collect_goes_long()

        #: Remove lock file once process is completed
        os.remove(lock)