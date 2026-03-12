#! /usr/bin/env python
"""
**compute_fluence_cxo70.py**: create a html page displaying ace fluence when cxo is above 70kkm

:Author: t. isobe  (tisobe@cfa.harvard.edu)
:Maintainer: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 16, 2021

# /// script
# requires-python = ">3.12"
# ///

# /// testing
# tested-ska-release = "2026.1"
# ///

"""
import os
import signal
from cxotime import CxoTime
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import psutil

#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True))

#
#--- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv("Space_Weather", "/data/mta4/Space_Weather"))
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))
ACE_DATA_DIR : Path = SPACE_WEATHER / "ACE" / "Data"
ACE_HTML_DIR : Path = SPACE_WEATHER_WEB / "ACE"
EPHEM_DATA_DIR : Path = SPACE_WEATHER / "EPHEM" / "Data"
#
#--- current time
#
CURRENT_CHANDRA_TIME = CxoTime().secs

#-----------------------------------------------------------------------------
#-- compute_fluence_cxo70: create a html page displaying ace fluence when cxo is above 70kkm
#-----------------------------------------------------------------------------

def compute_fluence_cxo70():
    """
    create a html page displaying ace fluence when cxo is above 70km
    input:  none but read from:
            <ephem_dir>/Data/PE.EPH.gsme_spherical
            <ace_dir>/Data/ace_7day_archive
    output: <html_dir>/ACE/ace_flux_dat.html
    """
#
#--- read orbital info
#
    _spherical = EPHEM_DATA_DIR / "PE.EPH.gsme_spherical"
    with open(f"{_spherical}") as f:
        data = [line.strip() for line in f.readlines()]
    data  = data[::-1]
    start = 0
#
#--- find the latest time span when cxo is above 70kkm
#
    stop  = 0
    for ent in data:
        atemp = ent.split()
        stime = float(atemp[0])
#
#--- make sure that the span is before the curren time
#
        if stime > CURRENT_CHANDRA_TIME:
            continue

        alt   = float(atemp[1])
        if stop == 0:
            if alt > 70.0:
                stop = stime
        else:
            if alt < 70.0:
                start = stime
                break
#
#--- read ace data
#
    _archive = ACE_DATA_DIR / "ace_7day_archive"
    with open(f"{_archive}") as f:
        data = [line.strip() for line in f.readlines()]
    ftime  = "NA"
    e1     = 0.0
    e2     = 0.0
    p1     = 0.0
    p2     = 0.0
    p3     = 0.0
    p4     = 0.0
    p5     = 0.0
    cstart = 0.0
    cstop  = 0.0
    for ent in data:
        atemp = ent.split()
        #: convert time in Chandra Time   
        stime = CxoTime(f"{atemp[0]}-{atemp[1]}-{atemp[2]}T{atemp[3][0]}{atemp[3][1]}:{atemp[3][2]}{atemp[3][3]}:00").secs #: isot format input.
#
#--- compute fluence between the span
#
        if stime < start:
            continue
        elif stime > stop:
            break
        else:
            ind1 = float(atemp[6])
            ind2 = float(atemp[9])
#
#--- use only good data
#
            if (ind1 != 0) or (ind2 != 0):
                continue

            if cstart == 0.0:
                cstart = stime
            cstop = stime

            ftime = f"{atemp[0]} {atemp[1]} {atemp[2]}  {atemp[3]}{float(atemp[4]):8.0f}{float(atemp[5]):8.0f}"

            ve1 = float(atemp[7])
            ve2 = float(atemp[8])
            vp1 = float(atemp[10])
            vp2 = float(atemp[11])
            vp3 = float(atemp[12])
            vp4 = float(atemp[13])
            vp5 = float(atemp[14])
#
#--- sometime, some of the values are still show up negative. drop that set of the data
#
            if (ve1 < 0) or (ve2 < 0):
                continue
            if (vp1 < 0) or (vp2 < 0) or (vp3 < 0) or (vp4 < 0) or (vp5 < 0):
                continue
#
#--- the values are given every 5 mins
#
            e1 +=  ve1 * 300
            e2 +=  ve2 * 300
            p1 +=  vp1 * 300
            p2 +=  vp2 * 300
            p3 +=  vp3 * 300
            p4 +=  vp4 * 300
            p5 +=  vp5 * 300
#
# --- Render ace_flux jinja template
#
    ace_flux = data[-1]
    ace_flux_70kkm = f"{ftime}  -{e1:10.2e}{e2:10.2e}  -{p1:10.2e}{p2:10.2e}{p3:10.2e}{p4:10.2e}{p5:10.2e}{cstop - cstart:8.0f}"

    template = _JINJA_ENV.get_template('ace_flux.jinja')
    render = template.render(ace_flux = ace_flux, ace_flux_70kkm = ace_flux_70kkm)
    _flux = ACE_HTML_DIR / "ace_flux.dat"
    with open(f"{_flux}", 'w') as fo:
        fo.write(render)
#
#--- create the html page
#
    web_template = _JINJA_ENV.get_template('ace_flux_data.jinja')
    web_render = web_template.render(ace_flux_render = render)

    _html = ACE_HTML_DIR / "ace_flux_data.html"
    with open(f"{_html}" , 'w') as fo:
            fo.write(web_render)

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-d", "--data", required = False, help = "Directory path to determine input location of data.")
    parser.add_argument("-w", "--web", required = False, help = "Directory path to determine output location of html page.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
        if args.data:
            ACE_DATA_DIR = Path(args.data)
        else:
            ACE_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        if args.web:
            ACE_HTML_DIR = Path(args.web)
        else:
            ACE_HTML_DIR = Path(os.getcwd(), "test", "_outTest")
        os.makedirs(ACE_HTML_DIR, exist_ok = True)
        compute_fluence_cxo70()
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

        compute_fluence_cxo70()

        #: Remove lock file once process is completed
        os.remove(lock)