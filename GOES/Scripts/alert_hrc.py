#!/proj/sot/ska3/flight/bin/python
import os
import sys
import argparse
import getpass
import traceback
import datetime
import json
import subprocess
from astropy.io import ascii

#
#--- Define Directory Pathing
#
GOES_DIR = "/data/mta4/Space_Weather/GOES/Data"
GOES_DATA_FILE = f"{GOES_DIR}/Gp_pchan_5m.txt"
HRC_PROXY_DATA_FILE = f"{GOES_DIR}/hrc_proxy.txt"
VIOL_RECORD_FILE = f"{GOES_DIR}/hrc_proxy_viol.json"

NAMES = ('time', 'p1', 'p2a', 'p2b', 'p3', 'p4', 'p5',
         'p6', 'p7', 'p8a', 'p8b', 'p8c', 'p9', 'p10',
         'hrc_proxy', 'hrc_proxy_legacy')

#Based on HRC Proxy differential values
HRC_THRESHOLD = {'Warning': 6.2e4,
                'Violation': 1.95e5}

#Alert Email Addresses
HRC_ADMIN = ['sot_ace_alert@cfa.harvard.edu']
ADMIN = ['mtadude@cfa.harvard.edu']


def alert_hrc():
    dat = ascii.read(GOES_DATA_FILE, data_start=5, delimiter='\t', guess=False, names=NAMES)
    time, hrc_proxy, hrc_proxy_legacy = dat[-1]['time','hrc_proxy', 'hrc_proxy_legacy']
    #Cast astropy table data into json serializable types
    recent_data = {'time': str(time),
                   'hrc_proxy': int(hrc_proxy),
                   'hrc_proxy_legacy': int(hrc_proxy_legacy)}

    #Check current status of HRC proxy violations.
    #If one has been found very recently, do not email about the violation again
    with open(VIOL_RECORD_FILE) as f:
        curr_viol = json.load(f)
    
    #Iterate over kinds of threshold and versions each proxy
    content = ''
    for kind in HRC_THRESHOLD.keys():
        for proxy in ['hrc_proxy', 'hrc_proxy_legacy']:
            if recent_data[proxy] > HRC_THRESHOLD[kind]:
                #check if there was a similar kind of violation withing the last 24 hours
                if viol_time_check(curr_viol, kind, proxy):
                    content += f"{kind}: {proxy}\n"
                    content += f"Observed: {recent_data[proxy]:.5e} at Time: {time}\n"
                    content += f"Limit: {HRC_THRESHOLD[kind]:.3e} counts/sec.\n"
                    content += f"{'-' * 20}\n"
                    curr_viol[f"{kind}_{proxy}"] = recent_data
    
    if content != '' and HRC_ADMIN != []:
        send_mail(content, "HRC Proxy Violation", HRC_ADMIN)
    with open(VIOL_RECORD_FILE, 'w') as f:
        json.dump(curr_viol, f, indent = 4)
    
    add_to_archive(recent_data, HRC_PROXY_DATA_FILE)

def send_mail(content, subject, admin):
    """
    send out a notification email to admin
    """
    content += f'This message was send to {" ".join(admin)}'
    cmd = f'echo "{content}" | mailx -s "{subject}" {" ".join(admin)}'
    os.system(cmd)

def viol_time_check(curr_viol, kind, proxy):
    """
    Prevents spamming violation emails if the data is in violation, 
    opting to send out a email if the specific violation was last warned more than 24 hours ago.
    """
    time_string = curr_viol[f"{kind}_{proxy}"]['time']
    last = datetime.datetime.strptime(time_string, '%Y:%j:%H:%M')
    now = datetime.datetime.utcnow()
    return (now - last).days > 1    

def add_to_archive(recent_data, outfile):
    #data_line = f"{recent_data['time']:<13}\t{recent_data['hrc_proxy']:<9}\t{recent_data['hrc_proxy_legacy']:<16}\n"
    data_line = f"{recent_data['time']}\t{recent_data['hrc_proxy']}\t{recent_data['hrc_proxy_legacy']}\n"
    if os.path.isfile(outfile):
        mode = 'a'
        #Secondary check in appending to the archive in case there is a time discrepancy.
        append_time = datetime.datetime.strptime(recent_data['time'], '%Y:%j:%H:%M')
        out = subprocess.check_output(f"tail -n 1 {outfile}", shell=True, executable='/bin/csh').decode()
        last_time = datetime.datetime.strptime(out.split()[0], '%Y:%j:%H:%M')
        #Send alert if the archive has not been recording for 15 minutes
        if (append_time - last_time).total_seconds() > 900:
            content = f"Time discrepancy in {HRC_PROXY_DATA_FILE}\n{'-' * 40}\nTail: {out}New Data: {data_line}Investigate {__file__}\n"    
            send_mail(content, "Time Discrepancy in HRC Proxy Archive", ADMIN)

    else:
        #data_line = f"{'time':<13}\t{'hrc_proxy':<9}\t{'hrc_proxy_legacy':<16}\n{'-' * 48}\n{data_line}"
        data_line = f"{'time'}\t{'hrc_proxy'}\t{'hrc_proxy_legacy'}\n{'-' * 40}\n{data_line}"
        mode = 'w'
    with open(outfile, mode) as f:
        f.write(data_line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-e", '--email', nargs = '*', required = False, help = "List of emails to recieve notifications")
    parser.add_argument("-g", "--goes", help = "Determine GOES data file path")
    parser.add_argument("-a", "--archive_hrc", help="Determine lonterm record file path for HRC proxy")
    parser.add_argument("-j", "--json", help = "Pass in record for current state of HRC proxy violations.")
    args = parser.parse_args()

    if args.mode == 'test':
#
#--- Redefine Admin for sending notification email in test mode
#
        if args.email != None:
            HRC_ADMIN = args.email
            ADMIN = args.email
        else:
            HRC_ADMIN = [os.popen(f"getent aliases | grep {getpass.getuser()}").read().split(":")[1].strip()]
            ADMIN = HRC_ADMIN

#
#--- Redefine pathing for GOES and HRC PROXY data files
#
        OUT_DIR = f"{os.getcwd()}/test/outTest"
        os.makedirs(OUT_DIR, exist_ok = True)
        if args.goes:
            GOES_DATA_FILE = args.goes

        if args.json:
            VIOL_RECORD_FILE = args.json
        else:
            #while roundabout, writing this empty test violation record to a separate file and reading it again test's 
            #a typical script run more directly.
            temp_dict = {"time": '2020:077:17:10',
                         "hrc_proxy": 0,
                         "hrc_proxy_legacy": 0}
            import copy
            check_viol = {"Warning_hrc_proxy": copy.copy(temp_dict),
                          "Violation_hrc_proxy": copy.copy(temp_dict),
                          "Warning_hrc_proxy_legacy": copy.copy(temp_dict),
                          "Violation_hrc_proxy_legacy": copy.copy(temp_dict)}
            
            VIOL_RECORD_FILE = f"{OUT_DIR}/hrc_proxy_viol.json"
            with open(VIOL_RECORD_FILE,'w') as f:
                json.dump(check_viol, f, indent = 4)

        if args.archive_hrc:
            HRC_PROXY_DATA_FILE = args.archive_hrc
        else:
            HRC_PROXY_DATA_FILE = f"{OUT_DIR}//hrc_proxy.txt"

        try:
            alert_hrc()
        except:
            traceback.print_exc()
    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            notification = f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            send_mail(notification,f"Stalled Script: {name}", ADMIN)
            sys.exit(notification)
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        try:
            alert_hrc()
        except:
            traceback.print_exc()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")