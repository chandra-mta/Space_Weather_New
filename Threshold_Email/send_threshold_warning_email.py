#!/proj/sot/ska3/flight/bin/python

import os
import argparse
import getpass
import traceback
import json
import urllib.request
from astropy.table import Table

#Define data source pathing
ACE_DATA_SOURCE = 'https://services.swpc.noaa.gov/json/ace/epam/ace_epam_5m.json'
GOES_DATA_SOURCE = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-6-hour.json'

#TODO which email group to send for ACE and which to send for HRC Prox using GOES?
#ACE_ADMIN = ['sot_ace_alert@cfa.harvard.edu']
#HRC_ADMIN = ['sot_red_alert@cfa.harvard.edu']

#Reset for testing right now
ACE_ADMIN = ['william.aaron@cfa.harvard.edu']
HRC_ADMIN = ['william.aaron@cfa.harvard.edu']

#
#--- Determine HRC proxy linear combination parameters.
#

#TODO - Move this proxy combination info into a JSON file for use across all Space_Weather scripts

#In use for old generation GOES-1 to GOES-15
#DOES NOT MAP DIRECTLY TO NEW GOES CHANNELS
OLD_GEN_HRC_PROXY = {'CHANNELS': {'P4': 6000,
                                  'P5': 270000,
                                  'P6': 100000},
                     'CONSTANT': 0}

#In use for transition period between GOES-15 and GOES-16+ (2020)
HRC_PROXY_V1 = {'CHANNELS': {'P5': 6000,
                             'P7': 270000,
                             'P8A': 100000},
                'CONSTANT': 0}

#In use for new generation GOES-16+ (post 2020)
HRC_PROXY_V2 = {'CHANNELS': {'P5': 143,
                             'P6': 64738,
                             'P7': 162505}, 
                'CONSTANT': 4127}
#
#--- Determine thresholds for ACE and HRC proxy violations
#

#TODO - Move these thresholds into the future MTA limits combined SQLite database

#Based on Fluence calculated over time
ACE_THRESHOLD = {'Warning': 3.6e8}

#Based on HRC Proxy value as specific time
HRC_THRESHOLD = {'Warning': 6.2e4,
                 'Violation': 1.95e5}

def check_data_for_viol():
    ace_table = extract_data_table(ACE_DATA_SOURCE)
    goes_table = extract_data_table(GOES_DATA_SOURCE)

    ace_violation(ace_table)
    hrc_violation(goes_table)


def extract_data_table(jlink):
    """
    extract satellite data
    input: jlink--- JSON web address or file
    output: table--- astropy table of the data.
    """
#
#--- read json file from a file or the web
#
    if os.path.isfile(jlink):
        try:
            with open(jlink) as f:
                data = json.load(f)
        except:
            traceback.print_exc()
            data = []
    else:
        try:
            with urllib.request.urlopen(jlink) as url:
                data = json.loads(url.read().decode())
        except:
            traceback.print_exc()
            data = []

    if len(data) < 1:
        exit(1)
    data = Table(data)
    return data

def ace_violation(table):
    """
    input: table --- astropy table of ace data in reverse time order
    output: none, but sends a warning email to ACE admin if the P3 fluence is in violation.
    """
#
#--- Average over the past 2 hour timeframe.
#
    stop = table['time_tag'][0]
    start = table['time_tag'][24]
    p130a = table['p3'][:24].data.mean()
    # Compute fluence over two hours from the averaged rate
    p130f = p130a * 7200
    print(f"p130f: {p130f}")
    print(f"start: {start}")
    print(f"stop: {stop}")

    if p130f > ACE_THRESHOLD['Warning']:
        content = f"WARNING: A Radiation violation of P3 (130Kev) has been observed by ACE.\n"
        content = f"Occuring between {start} and {stop}\.n"
        content += f"Observed: {p130f} \n"
        content += f"Limit: {ACE_THRESHOLD['Warning']} particles/cm2-ster-MeV within 2 hours.\n"
        content += f"see http://cxc.harvard.edu/mta/ace.html or https://cxc.harvard.edu/mta/RADIATION_new/ACE/ace.html\n"
        content += f"The ACIS on-call person should review the data and call a telecon if necessary.\n"

        subject = f"[sot_ace_alert] ACE_p3"
        send_mail(content, subject, ACE_ADMIN)
        
def hrc_violation(table):
    """
    input: table --- astropy table of GOES data
    output: none, but send a warning email to HRC admin if the HRC proxy is in violation
    """

    #TODO Send email for multiple proxies? Current just run for v2
    proxy = 0
#
#--- select the latest data point
#
    time = table['time_tag'][-1]
    sel = table['time_tag'] == time
    table = table[sel]

    for chan in HRC_PROXY_V2['CHANNELS'].keys():
        proxy += HRC_PROXY_V2['CHANNELS'][chan] * table[table['channel'] == chan]['flux'].data[0]
    proxy += HRC_PROXY_V2['CONSTANT']
    print(f"proxy: {proxy}")
    print(f"time: {time}")
    content = ''
    subject = ''
    if proxy > HRC_THRESHOLD['Warning']:
        content = f"WARNING: A HRC GOES proxy violation has been observerd by GOES at {time}\n"
        content += f"Observed: {proxy} \n"
        content += f"LIMIT:{HRC_THRESHOLD['Warning']} counts/sec.\n"

        subject = f"[sot_red_alert] Warning: HRC proxy"
    
    if proxy > HRC_THRESHOLD['Violation']:
        content = f"VIOLATION: A HRC GOES proxy violation has been observerd by GOES at {time}\n"
        content += f"Observed: {proxy} \n"
        content += f"LIMIT:{HRC_THRESHOLD['Violation']} counts/sec.\n"

        subject = f"[sot_red_alert] Violation: HRC proxy"
    
    if content != '':
        send_mail(content, subject, HRC_ADMIN)
        
#----------------------------------------------------------------------------------
#-- send_email_to_admin: send out a notification email to admin                  --
#----------------------------------------------------------------------------------
def send_mail(content, subject, admin):
    """
    send out a notification email to admin
    input:  admin --- list of emails
    output: email to admin
    """
    content += f'This message was send to {" ".join(admin)}'
    cmd = f'echo "{content}" | mailx -s "{subject}" {" ".join(admin)}'
    os.system(cmd)

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