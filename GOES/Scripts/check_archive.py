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
from datetime import datetime, timezone
import subprocess
import argparse
import traceback
import getpass
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from pathlib import Path
import file_readers as fr
#
# --- Define Directory Pathing
#
SPACE_WEATHER = Path(os.getenv('SPACE_WEATHER', "/data/mta4/Space_Weather"))
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"
HRC_PROXY_ARCHIVE : Path= GOES_DATA_DIR / "hrc_proxy.csv"
#
# --- Due to the latest data from SWPC being 15 minutes behind, this data will always have at minimum a 15 minute delay.
#
TIME_DIFF = 2700  #: 45 minutes in seconds


def send_mail(content, subject, admin):
    """Send warning message to the admins

    :param content: Content of the email.
    :type content: str
    :param subject: Subject line of the email.
    :type subject: str
    :param admin: List of email recipients.
    :type admin: list
    """
    content += f'This message was send to {" ".join(admin)}'
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["To"] = ",".join(admin)
    p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    (out, error) = p.communicate(msg.as_bytes())


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
            content = f"Time discrepancy in {ARCHIVE_FILE} has ended.\n{'-' * 40}\nTail of file: {out}Current Time: {now.strftime('%Y:%j:%H:%M')}\n"
            send_mail(content, "HRC Proxy Archive Resumed", ADMIN)
            os.remove(f"{DATA_DIR}/check_archive.viol")
    #
    # --- If we have no record of a time violation, but then find one, write the viol file and send email
    #
    elif (now - last_time).total_seconds() > TIME_DIFF:
        content = f"Time discrepancy in {ARCHIVE_FILE}\n{'-' * 40}\nTail of file: {out}Current Time: {now.strftime('%Y:%j:%H:%M')}\n"
        content += "Discrepancy likely due to interrupted service from SWPC NOAA.\n"
        with open(f"{DATA_DIR}/check_archive.viol", "w") as f:
            f.write(content)
        send_mail(content, "Time Discrepancy in HRC Proxy Archive", ADMIN)


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
        #
        # --- Create a lock file and exit strategy in case of race conditions
        #
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            notification = f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            send_mail(notification, f"Stalled Script: {name}", ADMIN)
            sys.exit(notification)
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        try:
            check_cadence()
        except:  # noqa: E722
            traceback.print_exc()
        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")
