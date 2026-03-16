#!/usr/bin/env python
"""
**alert_hrc.py**: Send alerts to the HRC team in case the HRC proxy violates

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Feb 20, 2025

:TODO: Consider adapting the hrc proxy violation archive into an astropy ECSV file in order to make use of table metadata

# /// testing
# tested-ska-release = "2026.1"
# ///
"""

from email.mime.text import MIMEText
import os
import shutil
import signal
import argparse
from subprocess import PIPE, Popen
from datetime import datetime, timezone
import json
import csv
from astropy.io import ascii
from pathlib import Path
import psutil
#
# --- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv("SPACE_WEATHER", "/data/mta4/Space_Weather"))
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"

NAMES = (
    "time",
    "p1",
    "p2a",
    "p2b",
    "p3",
    "p4",
    "p5",
    "p6",
    "p7",
    "p8a",
    "p8b",
    "p8c",
    "p9",
    "p10",
    "hrc_proxy",
    "hrc_proxy_legacy",
)
CSV_HEADER = ["time", "hrc_proxy", "hrc_proxy_legacy"]
HRC_THRESHOLD = {"Warning": 3.2e4}  #: Based on HRC Proxy differential values
PROXIES = ["hrc_proxy", "hrc_proxy_legacy"]
HRC_ADMIN = [
    "rkraft@cfa.harvard.edu",
    "6172756031@vtext.com",
    "dpatnaude@cfa.harvard.edu",
    "6173726105@vtext.com",
    "gtremblay@cfa.harvard.edu",
    "2075044862@vtext.com",
    "gerrit.schellenberg@cfa.harvard.edu",
    "6178750424@vtext.com",
    "mtadude@cfa.harvard.edu",
]  #: Alert Email Addresses
ADMIN = ["mtadude@cfa.harvard.edu"]
TESTMAIL = True

def alert_hrc():
    """Read the GOES differential proton data for the calculated hrc proxy value

    :File Out: <goes_dir>/hrc_proxy.csv

    """
    _goes_data_file = GOES_DATA_DIR / "Gp_pchan_5m.txt"
    dat = ascii.read(_goes_data_file, data_start=5, delimiter="\t", guess=False, names=NAMES)
    time, hrc_proxy, hrc_proxy_legacy = dat[-1]["time", "hrc_proxy", "hrc_proxy_legacy"]
    recent_data = {
        "time": str(time),
        "hrc_proxy": int(hrc_proxy),
        "hrc_proxy_legacy": int(hrc_proxy_legacy),
    }  #: Cast astropy table data into json serializable types
    #
    # --- Check current status of HRC proxy violations.
    # --- If one has been found very recently, do not email about the violation again.
    #
    _violation_record = GOES_DATA_DIR / "hrc_proxy_viol.json"
    with open(_violation_record) as f:
        curr_viol = json.load(f)

    content = ""
    for kind in (
        HRC_THRESHOLD.keys()
    ):  #: Iterate over kinds of threshold and versions each proxy
        for proxy in PROXIES:
            if recent_data[proxy] > HRC_THRESHOLD[kind]:
                if viol_time_check(
                    curr_viol, kind, proxy
                ):  #: check if there was a similar kind of violation withing the last 24 hours
                    content += f"{kind}: {proxy}\n"
                    content += f"Limit: {HRC_THRESHOLD[kind]:.3e} counts/sec.\n"
                    content += f"Time: {time}\n"
                    content += f"{'-' * 20}\n"
                    for p in PROXIES:
                        content += f"{p}: {recent_data[p]:.5e}\n"
                    curr_viol[f"{kind}_{proxy}"] = recent_data

    if content != "" and len(HRC_ADMIN) > 0:
        send_mail("HRC Proxy Violation", content, HRC_ADMIN)
    with open(_violation_record, "w") as f:
        json.dump(curr_viol, f, indent=4)

    _proxy_data_file = GOES_DATA_DIR / "hrc_proxy.csv"
    add_to_archive(recent_data, _proxy_data_file)


def send_mail(subject, content, address):
    """Send Emails

    :param subject: Subject line
    :type subject: str
    :param content: Email content as string
    :type content: str
    :param address: Email address of the recipient, or a list/tuple or recipients
    :type address: str, list, tuple
    """
    msg = MIMEText(content)
    msg['Subject'] = subject
    if isinstance(address,(list,tuple)):
        msg['To'] = ','.join(address)
    elif isinstance(address,str):
        msg['To'] = address
    else:
        raise Exception("Please provide an address string or a lsit of address strings")

    if TESTMAIL:
        print(msg)
    else:
        p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())


def viol_time_check(curr_viol, kind, proxy):
    """
    Prevents spamming violation emails if the data is in violation,
    opting to send out a email if the specific violation was last warned more than 24 hours ago.
    """
    time_string = curr_viol[f"{kind}_{proxy}"]["time"]
    last = datetime.strptime(time_string, "%Y:%j:%H:%M")
    now = datetime.now(timezone.utc)
    last = last.replace(tzinfo=timezone.utc)
    return (now - last).days > 1


def add_to_archive(recent_data, outfile):
    with open(outfile, "a") as f:
        writer = csv.DictWriter(
            f, dialect="unix", fieldnames=CSV_HEADER, quoting=csv.QUOTE_NONE
        )
        writer.writerow(recent_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flight", "test"], required=True, help="Determine running mode.")
    parser.add_argument("-d", "--data", help="Determine directory path for GOES Data")
    args = parser.parse_args()

    if args.mode == "test":
        TESTMAIL = True
        #
        # --- Redefine pathing for GOES and HRC PROXY data files
        #
        _old = GOES_DATA_DIR
        if args.data:
            GOES_DATA_DIR = Path(args.data)
        else:
            GOES_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        #: GOES Data directory not created in test case, because it should already be created to read the hrc proxy data.
        _violation_record = GOES_DATA_DIR / "hrc_proxy_viol.json"
        if not _violation_record.is_file():
            #: Creates a default violation record file.
            #: Manually copy from the live running version to test triggers for current version.
            _default_dict ={
                "Warning_hrc_proxy": {
                    "time": "2020:077:17:10",
                    "hrc_proxy": 0,
                    "hrc_proxy_legacy": 0,
                },
                "Warning_hrc_proxy_legacy": {
                    "time": "2020:077:17:10",
                    "hrc_proxy": 0,
                    "hrc_proxy_legacy": 0,
                }
            }
            with open(_violation_record, "w") as f:
                json.dump(_default_dict, f, indent=4)
        
        _proxy_data_file = GOES_DATA_DIR / "hrc_proxy.csv"
        if not _proxy_data_file.is_file():
            shutil.copyfile(_old / "hrc_proxy.csv", _proxy_data_file)

        alert_hrc()

    elif args.mode == "flight":
        TESTMAIL = False
        #: Create a lock file and exit strategy in case of stall.
        name = os.path.basename(__file__).split(".")[0]
        user = os.getenv("USER", "mta")
        lock = Path("/tmp", user, f"{name}.lock")

        #: If lock file exists, read the pid and kill the process, then remove the lock file
        if os.path.isfile(lock):
            notification = f"Lock file exists as {lock} Process already running/errored out. Check calling scripts/cronjob/cronlog. Killing old process." 
            send_mail(f"Stalled Script: {name}", notification, ADMIN)
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
        alert_hrc()
        #: Remove lock file once process is completed
        os.remove(lock)