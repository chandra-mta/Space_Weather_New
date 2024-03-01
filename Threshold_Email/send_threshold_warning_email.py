#!/proj/sot/ska3/flight/bin/python

import sys
import os
import datetime
import Chandra.Time
import argparse
import getpass
import traceback

#Define directory Pathing

ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
GOES_DATA_DIR = "/data/mta4/Space_Weather/GOES/Data"

#TODO which email group to send for ACE and which to send for HRC Prox using GOES?
ACE_ADMIN = ['sot_ace_alert@cfa.harvard.edu']
HRC_ADMIN = ['sot_red_alert@cfa.harvard.edu']

#Reset for testing right now
ACE_ADMIN = ['william.aaron@cfa.harvard.edu']
HRC_ADMIN = ['william.aaron@cfa.harvard.edu']

#----------------------------------------------------------------------------------
#-- send_email_to_admin: send out a notification email to admin                  --
#----------------------------------------------------------------------------------
def send_mail(content, subject, admin):
    """
    send out a notification email to admin
    input:  admin --- list of emails
    output: email to admin
    """
    cmd = f'echo "{content}" | mailx -s "{subject}" {" ".join(admin)}'
    os.system(cmd)

def check_data_for_viol():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-e", '--email', nargs = '*', required = False, help = "list of emails to recieve notifications")
    args = parser.parse_args()

    if args.mode == 'test':

#
#--- Redefine Admin for sending notification email in test mode
#
        if args.email != None:
            ACE_ADMIN = args.email
            HRC_ADMIN = args.email
        else:
            ADMIN = [os.popen(f"getent aliases | grep {getpass.getuser()} ").read().split(":")[1].strip()]
        check_data_for_viol()
    else:
        check_data_for_viol()