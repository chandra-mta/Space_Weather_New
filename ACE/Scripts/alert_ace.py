#!/usr/bin/env python
"""
**alert_ace.py**: Run ACE alerts.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jan 21, 2026

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
from email.mime.text import MIMEText
import shutil
from subprocess import Popen, PIPE
from astropy.io import ascii
from astropy.table import Column, unique, Table
import argparse
from cxotime import CxoTime
from datetime import timedelta
import numpy as np
import json
import signal
from pathlib import Path
from urllib.parse import urljoin
import psutil

#
# --- Define Directory Pathing and Globals
#
SPACE_WEATHER = Path(os.getenv("Space_Weather", "/data/mta4/Space_Weather"))
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))
SPACE_WEATHER_URL = os.environ.get('SPACE_WEATHER_URL', "https://cxc.cfa.harvard.edu/mta/RADIATION")

ACE_DATA_DIR : Path = SPACE_WEATHER / "ACE" / "Data"
ACE_HTML_DIR : Path = SPACE_WEATHER_WEB / "ACE"
ACE_URL = urljoin(SPACE_WEATHER_URL, "ACE/ace.html")

SNAPSHOT_DIR = Path("/data/mta4/www/Snapshot") #: Use primary run across instances
_ADMIN = "mtadude@cfa.harvard.edu"
_INPUT_ACE_COLUMNS = [
    "year",
    "month",
    "day",
    "hhmm",
    "mjd",
    "daysecs",
    "electron_status",
    "electron38-53",
    "electron175-315",
    "proton_status",
    "proton47-68",
    "proton115-195",
    "proton310-580",
    "proton795-1193",
    "proton1060-1900",
    "aniso",
]  #: For reading in ACE data file.
_P3_CHANNEL = "proton115-195"  #: Channel selection for P3 alert.
ACE_P3_LIMIT = 3.6e8  #: Fluence of 3.6e8 particles/cm2-ster-MeV within 2 hours.
_DEFAULT_VIOLATION = {
    "ace_p3": {"cxotime": 0, "val": 0},
    "ace_invalid": {"cxotime": 0, "val": False},
}  #: If cannot find file of previous violations, then assume issue involving them not being sent and rebuild file. Built for multiple alert types
_TESTMAIL = False
_BOGUS_P3 = 500000

HOURS_MISSING = 12 #: Count of consecutive hours missing valid ACE data.
_ALERT = "sot_ace_alert@cfa.harvard.edu" #: Alert email address
_NOW = CxoTime()

def _read_ace_file(file):
    """
    Read in the ACE Data file and format into astropy table.
    """
    ace_table = unique(ascii.read(file,names=_INPUT_ACE_COLUMNS))
    cxotime_col = Column(
        _convert_time_format(
            ace_table["year"], ace_table["month"], ace_table["day"], ace_table["hhmm"]
        ),
        name="cxotime",
    )
    ace_table.add_column(cxotime_col)
    return ace_table

@np.vectorize
def _convert_time_format(year, month, day, hhmm):
    """Converts separated ``numpy.ndarray`` containing date information into an array of ``CxoTime`` objects.

    :param year: Four digit year
    :type year: int
    :param month: Month
    :type month: int
    :param day: Day
    :type day: int
    :param hhmm: Integer Combining Hours and Minutes
    :type hhmm: int
    :return: ``numpy.ndarray`` of ``CxoTime`` objects.
    :rtype: ``numpy.ndarray(dtype = 'object')``

    """
    hh = hhmm // 100  #: Hours in hundreds and thousands place.
    mm = hhmm % 100  #: Minutes in tens and ones place.
    #: CxoTime accepts ISOT format
    time = f"{year:04}-{month:02}-{day:02}T{hh:02}:{mm:02}:00"
    return CxoTime(time)

def send_mail(subject, recipients, text_body, cc=""):
    """Send MIMEText Email

    :param subject: Subject of email
    :type subject: str
    :param recipients: Intended recipients
    :type recipients: list or str
    :param text_body:Email contents
    :type text_body: str
    :param cc:Carbon Copy recipients, defaults to ''
    :type cc: str or list, optional
    """
    #
    # --- Construct message in MIMEText
    #
    msg = MIMEText(text_body)
    msg["Subject"] = subject
    if type(recipients).__name__ == "list":
        recipients = ",".join(recipients)
    if type(cc).__name__ == "list":
        cc = ",".join(cc)
    msg["To"] = recipients
    msg["CC"] = cc
    #
    # --- Send Email
    #
    if not _TESTMAIL:
        p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        (out, error) = p.communicate(msg.as_bytes())
    else:
        print(msg)

def parse_p3(ace_table):
    """
    Parse ACE P3 data and return alert information if fluence over limit.
    """
    no_outlier = Table(names = ace_table.colnames, dtype=ace_table.dtype)
    no_outlier.add_row(ace_table[0])
    for i in range(1,len(ace_table)):
        if ace_table[i][_P3_CHANNEL] - no_outlier[-1][_P3_CHANNEL] < _BOGUS_P3:
            no_outlier.add_row(ace_table[i])
    
    two_hours_ago = no_outlier["cxotime"][-1] - timedelta(hours=2)
    sel = np.logical_and(
        no_outlier["cxotime"].data >= two_hours_ago, no_outlier[_P3_CHANNEL] > 0
    )
    sel = np.logical_and(
        sel, no_outlier['proton_status'] == 0
    )
    data_select = no_outlier[sel]
    if len(data_select) > 0:
        p130f = (
            np.mean(data_select[_P3_CHANNEL].data) * 7200
        )  #: Calculates the fluence with available data.
        _cxotime = data_select[-1]["cxotime"]
    else:
        p130f = -1e5 #: No valid data to send alert.
        _cxotime = _NOW
    
    ace_p3 = {
        "cxotime": _cxotime,
        "val": p130f,
    }
    return ace_p3

def parse_invalid(ace_table):
    """
    Parse ACE data for invalid data and return alert information if over limit.
    """
    #: Slice table to search for consecutive data points for a set
    #: number of hours ago. Number of hours is HOURS_MISSING variable.
    _start = ace_table['cxotime'][-1] - timedelta(hours=HOURS_MISSING)
    ace_table = ace_table[ace_table['cxotime'] >= _start]
    
    #: Select missing table values.
    missing_selection = ace_table['proton_status'] == -1
    #: If all consecutive data points minus the leeway (5) are less than those missing,
    #: then check for sending notification.
    #: Sporadically valid data might be available. Send alert if number of valid point's doesn't exceed the leeway
    invalid = False
    if len(ace_table) - 5 <= sum(missing_selection):
        if 8 <= _NOW.datetime.hour <= 22:
            invalid = True
    return {'cxotime': _NOW, 'val': invalid}

def check_alert_triggers():

    _12h_file = ACE_DATA_DIR / "ace_12h_archive"
    ace_table = _read_ace_file(_12h_file)
    #: Pull Alert information
    ace_p3 = parse_p3(ace_table)
    ace_invalid = parse_invalid(ace_table)
    #: Pull current violation information
    alert_file = ACE_DATA_DIR / "ace_alert.json"
    if not alert_file.is_file():
        curr_viol = _DEFAULT_VIOLATION
    else:
        with open(alert_file) as f:
            curr_viol = json.load(f)

    #: Check for P3 alert trigger
    if ace_p3["val"] > ACE_P3_LIMIT:
        #: P3 triggered. Check to prevent repeat alerting.
        if (ace_p3.get("cxotime").datetime - CxoTime(curr_viol["ace_p3"]["cxotime"]).datetime).days > 1:
            #: New triggering instance. Send alert and update violation file.
            curr_viol['ace_p3'] = {
                "cxotime": int(ace_p3["cxotime"].secs),
                "val": ace_p3["val"]
            }
            p3_message = (
                "A Radiation violation of P3 (130KeV) has been observed by ACE\n"
            )
            p3_message += f"Observed = {ace_p3['val']:.4e}\n"
            p3_message += (
                "(limit = fluence of 3.6e8 particles/cm2-ster-MeV within 2 hours)\n"
            )
            p3_message += f"see {ACE_URL}\n"
            _snap_file = SNAPSHOT_DIR / ".scs107alert"
            if _snap_file.is_file():
                recipients = "sot_yellow_alert@cfa.harvard.edu"
                p3_message += "SCS107 is listed as alerted.\n"
            else:
                recipients = "sot_ace_alert@cfa.harvard.edu"
                p3_message += "The ACIS on-call person should review the data and call a telecon if necessary.\n"
            p3_message += f"This message sent to {recipients.split('@')[0]}"
            send_mail("ACE_p3", recipients, p3_message)
    
    #: Check for invalid data alert trigger
    if ace_invalid['val']:
        #: Invalid triggered. Check to prevent repeat alerting
        if (ace_invalid.get("cxotime").datetime - CxoTime(curr_viol["ace_invalid"]["cxotime"]).datetime).days > 1:
            curr_viol['ace_invalid'] = {
                "cxotime": int(ace_invalid["cxotime"].secs),
                "val": ace_invalid["val"]
            }
            invalid_message = f'Alert in file: {_12h_file}\n'
            invalid_message += f'No valid ACE data for at least {HOURS_MISSING} hours.\n'
            invalid_message += "Radiation team should investigate.\n"
            invalid_message += f"This message was sent to {_ALERT}\n"
            send_mail(f"ACE no valid data for >{HOURS_MISSING}h", _ALERT, invalid_message)
    
    #: Update the current violation information
    with open(alert_file, "w") as f:
        json.dump(curr_viol, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        choices=["flight", "test"],
        required=True,
        help="Determine running mode.",
    )
    parser.add_argument("-p", "--path", help="Determine path to ACE Data.")
    args = parser.parse_args()

    if args.mode == "test":
        _TESTMAIL = True
        _copy_of_old = Path(str(ACE_DATA_DIR))
        if args.path:
            ACE_DATA_DIR = Path(args.path)
        else:
            ACE_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        os.makedirs(ACE_DATA_DIR, exist_ok=True)
        _12h_archive = ACE_DATA_DIR / "ace_12h_archive"
        if not _12h_archive.is_file():
            shutil.copyfile(_copy_of_old / "ace_12h_archive" , ACE_DATA_DIR / "ace_12h_archive")
        
        check_alert_triggers()

    elif args.mode == "flight":
        #: Create a lock file and exit strategy in case of race conditions.
        name = os.path.basename(__file__).split(".")[0]
        user = os.getenv("USER", "mta")
        lock = Path("/tmp", user, f"{name}.lock")

        #: If lock file exists, read the pid and kill the process, then remove the lock file
        if os.path.isfile(lock):
            #: Notify stall in alerting process
            notification = f"Lock file exists as {str(lock)} Process already running/errored out. Check calling scripts/cronjob/cronlog."
            send_mail(notification, f"ACE ALERT: Stalled Script: {name}", _ADMIN)
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

        check_alert_triggers()

        #: Remove lock file once process is completed
        os.remove(lock)
