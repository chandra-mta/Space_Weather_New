#!/proj/sot/ska3/flight/bin/python
import os
import sys
import argparse
import getpass
import traceback
import subprocess
import datetime
import json
import numpy as np
from astropy.io import misc, ascii
from astropy.table import Table, vstack, unique

#
#--- Define Directory Pathing
#
GOES_DIR = "/data/mta4/Space_Weather/GOES/Data"
GOES_DATA_FILE = f"{GOES_DIR}/Gp_pchan_5m.txt"
HRC_PROXY_DATA_FILE = f"{GOES_DIR}/hrc_proxy.h5"
VIOL_RECORD_FILE = f"{GOES_DIR}/hrc_proxy_viol.json"

NAMES = ('time', 'p1', 'p2a', 'p2b', 'p3', 'p4', 'p5',
         'p6', 'p7', 'p8a', 'p8b', 'p8c', 'p9', 'p10',
         'hrc_proxy', 'hrc_proxy_legacy')

#Alert Email Addresses
HRC_ADMIN = ['sot_ace_alert@cfa.harvard.edu']


def alert_hrc():
    dat = ascii.read(GOES_DATA_FILE, data_start=5, delimiter='\t', guess=False, names=NAMES)
    time, hrc_proxy, hrc_proxy_legacy = dat[-1]['time','hrc_proxy', 'hrc_proxy_legacy']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-e", '--email', nargs = '*', required = False, help = "List of emails to recieve notifications")
    parser.add_argument("-g", "--goes", help = "Determine GOES + HRC data file path")
    parser.add_argument("-p", "--hrc_proxy", help = "Determine realtime HRC proxy data file path")
    parser.add_argument("-j", "--json", help = "Pass in custom data record for current state of HRC proxy violations.")
    args = parser.parse_args()

    if args.mode == 'test':
#
#--- Redefine Admin for sending notification email in test mode
#
        if args.email != None:
            HRC_ADMIN = args.email
        else:
            HRC_ADMIN = [os.popen(f"getent aliases | grep {getpass.getuser()}").read().split(":")[1].strip()]

#
#--- Redefine pathing for GOES and HRC PROXY data files
#
        if args.goes:
            GOES_DATA_FILE = args.goes
        if args.hrc_proxy:
            HRC_PROXY_DATA_FILE = args.hrc_proxy
        else:
            OUT_DIR = f"{os.getcwd()}/test/outTest"
            os.makedirs(OUT_DIR, exist_ok = True)
            HRC_PROXY_DATA_FILE = f"{OUT_DIR}/hrc_proxy.h5"        
        if args.json:
            VIOL_RECORD_FILE = args.json
        else:
            #while roundabout, writing this empty test violation record to a separate file and reading it again test's 
            #a typical script run more directly.
            OUT_DIR = f"{os.getcwd()}/test/outTest"
            os.makedirs(OUT_DIR, exist_ok = True)
            temp_dict = {'in_viol': False,
                         'last_viol_time': '2020:077:17:10:00',
                         'content': '',
                         'notified': True}
            import copy
            check_viol = {"warn_V1": copy.copy(temp_dict),
                          "viol_V1": copy.copy(temp_dict),
                          "warn_V2": copy.copy(temp_dict),
                          "viol_V2": copy.copy(temp_dict)}
            
            VIOL_RECORD_FILE = f"{OUT_DIR}/hrc_proxy_viol.json"
            with open(VIOL_RECORD_FILE,'w') as f:
                json.dump(check_viol, f, indent = 4)


        try:
            alert_hrc()
        except:
            traceback.print_exc()
    else:
        try:
            alert_hrc()
        except:
            traceback.print_exc()