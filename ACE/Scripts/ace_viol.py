#!/proj/sot/ska3/flight/bin/python
import os
import sys
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
            ACE_DATA_DIR = f"{os.getcwd()}/test/outTest"
        TMP_DIR = f"{os.getcwd()}/test/outTest"
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
