#!/usr/bin/env python
"""
**create_crm_dat_file.py**: Use the CRMsummary.json to write the CRMsummary.dat file for Snapshot

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Mar 18, 2026

# /// script
# requires-python = ">=3.12"
# ///

# /// testing
# tested-ska-release = "2026.1"
# ///

"""
import os
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import psutil
import shutil
import argparse
import signal
#
# --- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv('SPACE_WEATHER', "/data/mta4/Space_Weather"))
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))

CRM_DATA_DIR : Path = SPACE_WEATHER / "CRM3" / "Data"
CRM_WEB_DIR : Path = SPACE_WEATHER_WEB / "CRM3"
#
# --- Template Globals
#
#: Keep trailing newline as old format has an additional newline character.
_JINJA_ENV = Environment(
    loader=FileSystemLoader("Template", followlinks=True), keep_trailing_newline=True
)
#: Custom filter to format to scientific notation.
_JINJA_ENV.filters["e_format"] = lambda v, p: f"{v:.{p}e}"
#: Custom filter to remove cxotime fractional seconds
_JINJA_ENV.filters["date_format"] = lambda v: f"{v.split('.')[0]}"

def main():
    _summary_json = CRM_DATA_DIR / "CRMsummary.json"
    with open(_summary_json) as f:
        summary = json.load(f)

    crm_template = _JINJA_ENV.get_template("CRMsummary.jinja")
    crm_render = crm_template.render(data=summary)
    _summary_dat = CRM_DATA_DIR / "CRMsummary.dat"
    with open(_summary_dat, "w") as fo:
        fo.write(crm_render)

def get_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flight", "test"], required=True, help="Determine running mode.")
    parser.add_argument("-p", "--path", required=False, help="Directory path to determine output location of summary.")
    return parser.parse_args(args)

if __name__ == "__main__":
    args = get_args()
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
        
        main()

    elif args.mode == "flight":
        #: Create a lock file and exit strategy in case of race conditions.
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
        os.makedirs(os.path.dirname(lock), exist_ok = True)
        with open(lock, 'w') as f:
            f.write(str(pid))

        main()
        #: Make data available on the web.
        shutil.copyfile(CRM_DATA_DIR / "CRMsummary.dat", CRM_WEB_DIR / "CRMsummary.dat")

        #: Remove lock file once process is completed
        os.remove(lock)