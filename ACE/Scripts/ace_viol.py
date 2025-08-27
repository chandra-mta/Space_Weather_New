#!/proj/sot/ska3/flight/bin/python
"""
**ace_viol.py**: Alert if missing too much ACE data.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 03, 2025

"""
import os
import sys
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from astropy.io import ascii
from astropy.table import Column, unique
from cxotime import CxoTime
from datetime import datetime, timedelta
import numpy as np
import argparse
#
#--- Define Globals
#
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data" #: Directory for ACE Data.
HOURS_MISSING = 12 #: Count of consecutive hours missing valid ACE data.
#: Sporadically valid data might be available. Send alert if number of valid point's doesn't exceed LEEWAY
LEEWAY = 5
_ADMIN = "mtadude@cfa.harvard.edu" #: Admin email address
_ALERT = "sot_ace_alert@cfa.harvard.edu" #: Alert email address
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
]  #: For reading in ACE data file with astropy.io.ascii.
_TESTMAIL = False #: Boolean to test mail
_NOW = datetime.now()

def _read_ace_file():
    """
    Read in the ACE Data file and format into astropy table.
    """
    data_file = f"{ACE_DATA_DIR}/ace_12h_archive"
    ace_table = unique(ascii.read(data_file,names=_INPUT_ACE_COLUMNS))
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

def check_viol():
    """
    Emails admins alert if ace data invalid for period of time

    input:	<ace_dir>/Data/ace_12h_archive
        <ace_dir>/Data/ace.archive
    output:	Admin Email
        /tmp/mta/ace_viol.out
    """
    ifile = f"{ACE_DATA_DIR}/ace_12h_archive"
    if not os.path.isfile(ifile):
        content = f"Error: {ifile} not found\n"
        content += f"by script {__file__}.\n"
        content += f"Alerts depend on this file. Please Investigate.\n"
        content += f"This message was sent to {ADMIN}"
        send_mail("Missing ACE archive",content, ADMIN)
    else:
        with open(f"{ACE_DATA_DIR}/ace_12h_archive") as f:
            file_data = [line.strip() for line in f.readlines() if line != '']
            file_data.reverse()
#
#--- Check only the time subsection of data which corresponds to
#--- an ARCHIVE_LENGTH_LIM number of 5-min increments
#
        data = [line.split() for line in file_data[:ARCHIVE_LENGTH_LIM]]
#
#--- If the entire data set is invalid, then email alert, otherwise proceed as normal
#
        valid_marker = False
        for entry in data:
            if (entry[6] == "0" or entry[9] == "0"):
                valid_marker = True
                break
        if not valid_marker:
            lockfile = f"{TMP_DIR}/ace_viol.out"
            if (os.path.exists(lockfile)):
                os.system(f'date >> {lockfile}')
            else:
                content = f'Alert Trigger Script: {__file__} \n'
                content += f'Alert in file: {ifile}\n'
                content += f'No valid ACE data for at least {VIOL_HOUR} hours.\n'
                content += f"Radiation team should investigate.\n"
                content += f"This message was sent to {ALERT}\n"
                send_mail(f"ACE no valid data for >{VIOL_HOUR}h", content, ALERT)
                os.system(f"cp {ifile} {lockfile}")

def send_mail(subject, content, address):
    if TESTMAIL:
        print(f"Test Mode, interrupting following email.\n\
              Subject: {subject}\n\
              Address: {address}\n\
              Content: {content}\n")
    else:
        os.system(f"echo '{content}' | mailx -s '{subject}' {address}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", required = False, help = "Directory path to determine input data location.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
        print("Running In Test Mode.")
        TESTMAIL = True
#
#--- Path output to same location as unit tests
#
        if args.path:
            ACE_DATA_DIR = args.path
        else:
            ACE_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        TMP_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(f"{ACE_DATA_DIR}", exist_ok = True)
        os.makedirs(f"{TMP_DIR}", exist_ok = True)
        print(f"ACE_DATA_DIR: {ACE_DATA_DIR}")
        print(f"TMP_DIR: {TMP_DIR}")
        check_viol()

    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions.
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog.")
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")
        check_viol()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")
