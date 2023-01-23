#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

import sys
import os
from datetime import datetime
import re

#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec( "%s = %s" %(var, line))

#
#--- append paths to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.8/MTA/')
#
#-command line arguments for reading in different hours before alert
#
if (len(sys.argv) == 1):#if no arguments passed
    viol_hour = 8#defaults to alert after 8 hours
else:
    viol_hour = int(sys.argv[1]) #if arguments passed


if (viol_hour >= 13):
    raise Exception(f'Error: Violation hour until notification: {viol_hour}h: exceeds 12h.')

#
#---infile definition and setup of violation directory
#

ace12hfile = ace_dir + "Data/ace_12h_archive"
infile = ace_dir +  "Data/ace.archive"#read in full archive file to read most recent data in order
archive_length_lim = 12 * viol_hour # 12 five-min segments per hour.



lockdir = "/tmp/mta"

if (not os.path.exists(lockdir)):
    os.system(f'mkdir {lockdir}')

lockfile = lockdir + "/ace_viol.out"


#
#--Loop A: iterating over file lines
#

VALID_DATA_MARK = False

line_count = 0#count of lines in the While loop, one we exceed the archive limit of lines, we leave the While loop
with open(infile, 'r') as archive_file:
    while True:
        line = archive_file.readline()
        if not line:#end of file reached. This should never happen since the archive file spans years, hence the error warning
            raise Exception("File reading of ace.archive reaches end. Should stop after reading archive_length_limit number of lines.")
        if line[0] != "#": #Not a comment line in the archive file
            line_count += 1
            data = line.split()
            print(f'Count: {line_count} - Data: {data}')
            if (data[6] == "0" or data[9] == "0"):
                VALID_DATA_MARK = True
                print('VALID_DATA_MARK found')
                break
            if (line_count >= archive_length_lim):
                print('Archive_Length_Limit reached')
                break
archive_file.close()

#
#--Alert Check: Does not send alerts between midnight and 8 am
#
hour_now = int(datetime.now().strftime("%H"))#get current hour

if ((hour_now < 24) and (hour_now > 7)):

    if (not VALID_DATA_MARK):
        #No valid data for viol_hour hours, send out an alert if it has not been sent out yet
        #writing the lock file
        if (os.path.exists(lockfile)):
            os.system(f'date >> {lockfile}')#touch lockfile, updating the date
        else:
            lock_handle = open(lockfile,"w+")
            lock_handle.write(f'Alert Trigger Script: {os.path.realpath(os.path.dirname(__file__)) + "/" + os.path.basename(__file__)} \n')
            lock_handle.write(f'Alert in file: {infile}\n')
            lock_handle.write(f'No valid ACE data for at least {viol_hour}h\n')
            lock_handle.write("Radiation team should investigate\n")
            lock_handle.write("this message sent to sot_ace_alert\n")
            lock_handle.close()
            os.system(f'cat {lockfile} | mailx -s "ACE no valid data for >{viol_hour}h" sot_ace_alert')
            #os.system(f'cat {lockfile} | mailx -s "ACE no valid data for >{viol_hour}h" waaron')

            
            #store the 12h archive file that triggered the alert
            os.system(f'cp {ace12hfile} {lockdir+"/ace_12h_archive_alert"}')

            
