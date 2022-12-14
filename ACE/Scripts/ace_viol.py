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


infile = ace_dir +  "Data/ace_12h_archive"
archive_length_lim = 12 * viol_hour # 12 five-min segments per hour.



lockdir = "/tmp/mta"

if (not os.path.exists(lockdir)):
    os.system(f'mkdir {lockdir}')

lockfile = lockdir + "/ace_nh_viol.out"

bad_e_data = 0 # number of lines with e status != 0
bad_p_data = 0 # number of lines with p status != 0


#
#--Loop A: iterating over file lines
#

count = 0 #counter for 
for line in reversed(list(open(infile))):#iterating over the file lines in reverse
    data = line.split()
    

    if (count >= archive_length_lim):#break for loop after exceeding viol_hour
        break
    
    
    #electrons
    if (data[6] != "0"):
        bad_e_data = bad_e_data + 1
    #protons
    if (data[9] != "0"):
        bad_p_data = bad_p_data + 1
    
    count = count + 1 # final step, to increment counter



#
#--Alert Check: Does not send alerts between midnight and 8 am
#
hour_now = int(datetime.now().strftime("%H"))#get current hour

if ((hour_now < 24) and (hour_now > 7)):

    if ((bad_e_data == archive_length_lim) or (bad_p_data == archive_length_lim)):
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
            #os.system(f'cat {lockfile} | mailx -s "ACE no valid data for >{viol_hour}h" waaron malgosia swolk')

            
            #store the 12h archive file that triggered the alert
            os.system(f'cp {infile} {lockdir+"/ace_12h_archive_alert"}')

            
