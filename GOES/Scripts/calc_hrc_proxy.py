#!/proj/sot/ska3/flight/bin/python

import os
import sys
import argparse
import getpass
import traceback
import subprocess
import datetime
import numpy as np
from astropy.io import misc, ascii
from astropy.table import Table, vstack, unique

#
#--- Define Directory Pathing
#
GOES_DIR = "/data/mta4/Space_Weather/GOES/Data"
GOES_DATA_FILE = f"{GOES_DIR}/goes_data_r.txt"
HRC_PROXY_DATA_FILE = f"{GOES_DIR}/hrc_proxy.h5"


#Alert Email Addresses
HRC_ADMIN = ['sot_ace_alert@cfa.harvard.edu']

#TODO, following testing, replace alert email with red alert email
#HRC_ADMIN = ['sot_red_alert@cfa.harvard.edu']

#
#--- Determine HRC Proxy Linear Combination parameters
#

#In use for transition period between GOES-15 and GOES-16+ (2020)
HRC_PROXY_V1 = {'CHANNELS': {'P5P6': 6000,
                             'P7': 270000,
                             'P8ABC': 100000},
                'CONSTANT': 0}

#In use for new generation GOES-16+ (post 2020)
HRC_PROXY_V2 = {'CHANNELS': {'P5': 143,
                             'P6': 64738,
                             'P7': 162505}, 
                'CONSTANT': 4127}

#Based on HRC Proxy value as specific time
HRC_THRESHOLD = {'Warning': 6.2e4,
                'Violation': 1.95e5}

# GOES-16+ Energy bands (keV) and combinations
DE = {'P1': [1860., 1020.],
      'P2A': [2300., 1900.],
      'P2B': [3340., 2310.],
      'P3': [6480., 3400.],
      'P4': [11000., 5840.],
      'P5': [23270., 11640.],
      'P6': [38100., 25900.],
      'P7': [73400., 40300.],
      'P8A': [98500., 83700.],
      'P8B': [118000., 99900.],
      'P8C': [143000., 115000.],
      'P9': [242000., 160000.],
      'P5P6': [23270., 11640.],
      'P8ABC': [143000., 83700.],
      'P8ABCP9': [242000., 83700.]}

# Add delta_e to each list
for key in DE.keys():
    de = DE[key]
    de.append(de[0] - de[1])

#Based on HRC Proxy value at specific time
HRC_THRESHOLD = {'Warning': 6.2e4,
                 'Violation': 1.95e5}

#For fixing the format in importing goes_data_r.txt
COLNAMES = ['Time',
            'P1',
            'P2A',
            'P2B',
            'P3',
            'P4',
            'P5',
            'P6',
            'P7',
            'P8A',
            'P8B',
            'P8C',
            'P9',
            'P10',
            'HRC_Proxy']

ALERT_HOURS = 6

def combine_rates(dat, chans):
    """
    Return combined rates for multiple channels
    """
    combined = 0
    for chan in chans:
        combined = combined + dat[chan] * DE[chan][2]
        
    delta_e = DE[chans[-1]][0] - DE[chans[0]][1]
    return combined / delta_e


def pull_GOES(cutoff = ''):
    """
    Pull data from MTA GOES DATA directory
    """
    if cutoff == '':
        t = ascii.read(GOES_DATA_FILE)
    else:
        #cutoff provides a time stamp to slice the file towards. 
        try:
            linecut = int(subprocess.check_output(f'grep -n "{cutoff}" {GOES_DATA_FILE}', shell=True, executable='/bin/csh').decode().split(":")[0])
        except:
            traceback.print_exc()
            sys.exit(f"Error: Possible that the latest HRC Proxy time point exceeds latest GOES time point.\nInvestigate at {GOES_DATA_FILE}\nand {HRC_PROXY_DATA_FILE}.")
        data = subprocess.check_output(f"tail -n +{linecut+1} {GOES_DATA_FILE}", shell=True, executable='/bin/csh').decode()
        if data == '':
            #No goes data past desired cutoff. Stop process
            sys.exit()
        t = ascii.read(data, delimiter ="\s")
    
    #rename columns to names found at top
    for i, col in enumerate(t.colnames):
        t.rename_column(col,COLNAMES[i])
    #Extra calculation of comined channels for use in V1 proxy
    t['P5P6'] = combine_rates(t,('P5','P6'))
    t['P8ABC'] = combine_rates(t,('P8A','P8B', 'P8A'))
    return t

def pull_HRC_proxy():
    """
    Pull current data table for HRC proxy in MTA GOES DATA directory
    """
    if os.path.isfile(HRC_PROXY_DATA_FILE):
        hrc_proxy_table = misc.hdf5.read_table_hdf5(HRC_PROXY_DATA_FILE)
    else:
        hrc_proxy_table = Table(names = ['Time', 'Proxy_V1', 'Proxy_V2'],
                                dtype = ['<U17', 'int64', 'int64'])
    return hrc_proxy_table

def find_proxy_values(goes_table, hrc_proxy_table):
    """
    Use all of the imported goes table to calculate the HRC proxy values
    """
    prox_v1 = np.empty(len(goes_table))
    prox_v1 = HRC_PROXY_V1['CONSTANT']
    for chan,coef in HRC_PROXY_V1['CHANNELS'].items():
        prox_v1 += goes_table[chan] * coef
    prox_v1 = prox_v1.astype(np.int64)
    prox_v1._name = "Proxy_V1"

    prox_v2 = np.empty(len(goes_table))
    prox_v2 = HRC_PROXY_V2['CONSTANT']
    for chan,coef in HRC_PROXY_V2['CHANNELS'].items():
        prox_v2 += goes_table[chan] * coef
    prox_v2 = prox_v2.astype(np.int64)
    prox_v2._name = "Proxy_V2"

    append_table = Table([goes_table['Time'], prox_v1, prox_v2])
    hrc_viol(append_table)

    if len(hrc_proxy_table) == 0:
        hrc_proxy_table = append_table
    else:
        hrc_proxy_table = vstack([hrc_proxy_table, append_table])
    return unique(hrc_proxy_table)

def hrc_viol(hrc_proxy_table):
    """
    determine if hrc proxy is in violation adn then send a warning email
    """
    #Once the start of a violation has been found in the data, record a boolean that one has been found6 and the message content of when the violation occured.
    check_viol = {"warn_V1": [False, ''],
                  "viol_V1": [False, ''],
                  "warn_V2": [False, ''],
                  "viol_V2": [False, '']}
    
    string_v1 = ' + '.join([f'({v} * {k})' for k,v in HRC_PROXY_V1['CHANNELS'].items()]) + f" + {HRC_PROXY_V1['CONSTANT']}"
    string_v2 = ' + '.join([f'({v} * {k})' for k,v in HRC_PROXY_V2['CHANNELS'].items()]) + f" + {HRC_PROXY_V2['CONSTANT']}"
    now = datetime.datetime.utcnow()

    for row in hrc_proxy_table:
        #Only evaluate for times in the last ALERT_HOURS of data.
        if (now - datetime.datetime.strptime(row['Time'], '%Y:%j:%H:%M:%S')).seconds < ALERT_HOURS * 3600:
            #Proxy 1
            if row["Proxy_V1"] > HRC_THRESHOLD['Warning'] and not check_viol["warn_V1"][0]:
                content = f"Warning: Proxy V1 [{string_v1}]\n"
                content += f"Observed: {row["Proxy_V1"]:.5e} at Time: {row['Time']}\n"
                content += f"Limit: {HRC_THRESHOLD['Warning']:.3e} counts/sec.\n"
                content += f"{'-' * 20}\n"
                check_viol["warn_V1"] = [True, content]

            if row["Proxy_V1"] > HRC_THRESHOLD['Violation'] and not check_viol["viol_V1"][0]:
                content = f"Violation: Proxy V1 [{string_v1}]\n"
                content += f"Observed: {row["Proxy_V1"]:.5e} at Time: {row['Time']}\n"
                content += f"Limit: {HRC_THRESHOLD['Violation']:.3e} counts/sec.\n"
                content += f"{'-' * 20}\n"
                check_viol["viol_V1"] = [True, content]
            
            #Proxy 2
            if row["Proxy_V2"] > HRC_THRESHOLD['Warning'] and not check_viol["warn_V2"][0]:
                content = f"Warning: Proxy V2 [{string_v2}]\n"
                content += f"Observed: {row["Proxy_V2"]:.5e} at Time: {row['Time']}\n"
                content += f"Limit: {HRC_THRESHOLD['Warning']:.3e} counts/sec.\n"
                content += f"{'-' * 20}\n"
                check_viol["warn_V2"] = [True, content]

            if row["Proxy_V2"] > HRC_THRESHOLD['Violation'] and not check_viol["viol_V2"][0]:
                content = f"Violation: Proxy V2 [{string_v1}]\n"
                content += f"Observed: {row["Proxy_V2"]:.5e} at Time: {row['Time']}\n"
                content += f"Limit: {HRC_THRESHOLD['Violation']:.3e} counts/sec.\n"
                content += f"{'-' * 20}\n"
                check_viol["viol_V2"] = [True, content]

    email_content = ''
    for v in check_viol.values():
        if v[0]:
            email_content += v[1]
    #If there is formatted email contnet, then a violation or warnign ahs been found.
    if email_content != '':
        email_content = "A HRC proxy violation has been observered.\n" + email_content
        send_mail(email_content, "HRC Proxy Violation", HRC_ADMIN)


def send_mail(content, subject, admin):
    """
    send out a notification email to admin
    """
    content += f'This message was send to {" ".join(admin)}'
    cmd = f'echo "{content}" | mailx -s "{subject}" {" ".join(admin)}'
    os.system(cmd)

def calc_hrc_proxy():
    """
    Pull MTA GOES DATA and calculate the HRC proxy, alert if in violation, then store calculated proxy
    """
    hrc_proxy_table = pull_HRC_proxy()
    #Determine cut off time for pulling in new data from GOES. If no HRC proxy data, calculate the last 24 hrs
    if len(hrc_proxy_table) == 0:
        #new table
        now = datetime.datetime.utcnow()
        cut_struct = now - datetime.timedelta(days = 1, minutes = now.minute % 5, seconds = now.second, microseconds = now.microsecond)
        cutoff = cut_struct.strftime('%Y:%j:%H:%M:%S')
    else:
        cutoff = hrc_proxy_table['Time'][-1]
    goes_table = pull_GOES(cutoff = cutoff)

    hrc_proxy_table = find_proxy_values(goes_table, hrc_proxy_table)

    misc.hdf5.write_table_hdf5(hrc_proxy_table, HRC_PROXY_DATA_FILE, overwrite = True)
    
    return hrc_proxy_table, goes_table

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-e", '--email', nargs = '*', required = False, help = "List of emails to recieve notifications")
    parser.add_argument("-g", "--goes", help = "Determine GOES data file path")
    parser.add_argument("-p", "--hrc_proxy", help = "Determine HRC PROXY data file path")
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

        try:
            calc_hrc_proxy()
        except:
            traceback.print_exc()
    else:
        try:
            calc_hrc_proxy()
        except:
            traceback.print_exc()