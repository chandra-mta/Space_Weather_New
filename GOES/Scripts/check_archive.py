#!/usr/bin/env python
"""
**check_archive.py**: Verify the HRC Proxy Archive is being updated.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Feb 20, 2025

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
import shutil
import signal
from datetime import datetime, timezone
import argparse
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from pathlib import Path
import psutil
import file_readers as fr
#
# --- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv('SPACE_WEATHER', "/data/mta4/Space_Weather"))
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"
HRC_PROXY_ARCHIVE : Path= GOES_DATA_DIR / "hrc_proxy.csv"

ADMIN = "mtadude@cfa.harvard.edu"
#
# --- Due to the latest data from SWPC being 15 minutes behind, this data will always have at minimum a 15 minute delay.
#
TIME_DIFF = 2700  #: 45 minutes in seconds
TESTMAIL = False

def send_mail(subject, content, address):
    """Send Emails

    :param subject: Subject line
    :type subject: str
    :param content: Email content as string
    :type content: str
    :param address: Email address of the recipient
    :type address: str
    """
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['To'] = address

    if TESTMAIL:
        print(msg)
    else:
        p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())


def check_cadence():
    """Reads the hrc_proxy.csv archive file to check if there is a delay in the calculation, likely due to missing data."""
    now = datetime.now(timezone.utc)
    _archive_file = GOES_DATA_DIR / "hrc_proxy.csv"
    out = fr.get_last_text_line(_archive_file) 
    last_time = datetime.strptime(out.split(",")[0], "%Y:%j:%H:%M")
    last_time = last_time.replace(tzinfo=timezone.utc)
    _archive_viol = GOES_DATA_DIR / "check_archive.viol"
    if _archive_viol.is_file():
        #
        # --- if we are in violation with a time discrepancy, do nothing until we are no longer in violation, then send email
        #
        if (now - last_time).total_seconds() < TIME_DIFF:
            content = f"Time discrepancy in {_archive_file} has ended.\n{'-' * 40}\nTail of file: {out}Current Time: {now.strftime('%Y:%j:%H:%M')}\n"
            send_mail("HRC Proxy Archive Resumed", content, ADMIN)
            os.remove(_archive_viol)
    #
    # --- If we have no record of a time violation, but then find one, write the viol file and send email
    #
    elif (now - last_time).total_seconds() > TIME_DIFF:
        content = f"Time discrepancy in {_archive_file}\n{'-' * 40}\nTail of file: {out}Current Time: {now.strftime('%Y:%j:%H:%M')}\n"
        content += "Discrepancy likely due to interrupted service from SWPC NOAA.\n"
        with open(_archive_viol, "w") as f:
            f.write(content)
        send_mail("Time Discrepancy in HRC Proxy Archive", content, ADMIN)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flight", "test"], required=True, help="Determine running mode.")
    parser.add_argument("-p", "--path", help="Determine GOES data directory containing long-term record file for HRC proxy")
    args = parser.parse_args()

    if args.mode == "test":

        _old = GOES_DATA_DIR
        TESTMAIL = True
        if args.path:
            GOES_DATA_DIR = Path(args.path)
        else:
            GOES_DATA_DIR = Path(os.getcwd(), "test", "_outTest")
        os.makedirs(GOES_DATA_DIR, exist_ok=True)
        
        if not (GOES_DATA_DIR / "hrc_proxy.csv").is_file():
            shutil.copyfile(_old / "hrc_proxy.csv", GOES_DATA_DIR / "hrc_proxy.csv")

        check_cadence()

    elif args.mode == "flight":
    #: Create a lock file and exit strategy in case of stall.
        name = os.path.basename(__file__).split(".")[0]
        user = os.getenv("USER", "mta")
        lock = Path("/tmp", user, f"{name}.lock")

        #: If lock file exists, read the pid and kill the process, then remove the lock file
        if os.path.isfile(lock):
            notification = f"Lock file exists as {lock}. Process already running/errored out. Check calling scripts/cronjob/cronlog."
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

        check_cadence()

        #: Remove lock file once process is completed
        os.remove(lock)