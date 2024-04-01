#!/proj/sot/ska3/flight/bin/python
import os
import sys
import datetime
import subprocess
import argparse
import traceback
import getpass

ARCHIVE_FILE = "/data/mta4/Space_Weather/GOES/Data/hrc_proxy.csv"
ADMIN = ['mtadude@cfa.harvard.edu']
#Due to the latest data from SWPC being 15 minutes behind, this data will always have at minimum a 15 minute delay.
TIME_DIFF = 1800 #30 minutes in seconds

def send_mail(content, subject, admin):
    """
    send out a notification email to admin
    """
    content += f'This message was send to {" ".join(admin)}'
    cmd = f'echo "{content}" | mailx -s "{subject}" {" ".join(admin)}'
    os.system(cmd)

def check_cadence():
    now = datetime.datetime.utcnow()
    out = subprocess.check_output(f"tail -n 1 {ARCHIVE_FILE}", shell=True, executable='/bin/csh').decode()
    last_time = datetime.datetime.strptime(out.split(",")[0], '%Y:%j:%H:%M')
    if (now - last_time).total_seconds() > TIME_DIFF:
        content = f"Time discrepancy in {ARCHIVE_FILE}\n{'-' * 40}\nTail of file: {out}Current Time: {now.strftime('%Y:%j:%H:%M')}\n"    
        send_mail(content, "Time Discrepancy in HRC Proxy Archive", ADMIN)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-e", '--email', nargs = '*', required = False, help = "List of emails to recieve notifications")
    parser.add_argument("-a", "--archive", help="Determine longterm record file path for HRC proxy")
    args = parser.parse_args()

    if args.mode == 'test':
#
#--- Redefine Admin for sending notification email in test mode
#
        if args.email != None:
            ADMIN = args.email
        else:
            ADMIN = [os.popen(f"getent aliases | grep {getpass.getuser()}").read().split(":")[1].strip()]

        OUT_DIR = f"{os.getcwd()}/test/outTest"
        os.makedirs(OUT_DIR, exist_ok = True)
        if args.archive:
            ARCHIVE_FILE = args.archive
        else:
            ARCHIVE_FILE = f"{OUT_DIR}/hrc_proxy.csv"

        try:
            check_cadence()
        except:
            traceback.print_exc()

    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions
#
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            notification = f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            send_mail(notification,f"Stalled Script: {name}", ADMIN)
            sys.exit(notification)
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        try:
            check_cadence()
        except:
            traceback.print_exc()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")