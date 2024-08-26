#!/proj/sot/ska3/flight/bin/python
import os
import argparse
#
#--- Define Globals
#
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
TESTMAIL = False
VIOL_HOUR = 8
ARCHIVE_LENGTH_LIM = 12 * VIOL_HOUR
ADMIN = 'mtadude@cfa.harvard.edu'
ALERT = 'sot_ace_alert@cfa.harvard.edu'
TMP_DIR = "/tmp/mta"

def check_viol():
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