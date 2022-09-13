#! /usr/bin/python3

#python version of ace_12h_viol.pl

import sys
import os
from datetime import datetime

#
#--Creates file to store log of steps
#
path = "/tmp/mta/ace_nh_alert"#path for testing this on the mta user of desktop machine scrapper. change with more info

trackdir = path + "/tracker"
if (not os.path.exists(trackdir)):
    os.system(f'mkdir {trackdir}')


log_handle = open(trackdir + "/ace_nh_viol.log","w+")#opens a log file to record steps of the script


#
#-command line arguements for reading in different hours before alert
#


if (len(sys.argv) == 1):#if no arguements passed
    viol_hour = 8#defaults to alert after 8 hours
    log_handle.write("No Arg Passed: viol_hour=8\n")
else:
    viol_hour = int(sys.argv[1]) #if arguements passed
    log_handle.write(f'Arg Passed: viol_hour={viol_hour}\n')
    #TODO: error handling of non-int arguement of multiple arguements


if (viol_hour >= 13):
    log_handle.write(f'Error:Violation hour until notification: {viol_hour}h: exceeds 12h.\n')
    raise Exception(f'Error: Violation hour until notification: {viol_hour}h: exceeds 12h.')

#
#---infile definition and setup of violation directory
#


infile = "/data/mta4/Space_Weather/ACE/Data/ace_12h_archive"#change post testing and with more info
archive_length_lim = 12 * viol_hour # 12 five-min segments per hour.



lockdir = path + "/viol"#change post testing and with more info

if (not os.path.exists(lockdir)):
    os.system(f'mkdir {lockdir}')
    log_handle.write(f'{lockdir} dir does not exist. Creating.\n')

lockfile = lockdir + "/ace_nh_viol.out"

bad_e_data = 0 # number of lines with e status != 0
bad_p_data = 0 #number of lines with p status != 0


#
#--Loop A: iterating over file lines
#

count = 0 #counter for 
for line in reversed(list(open(infile))):#iterating over the file lines in reverse
    data = line.split()
    
    log_handle.write(f'Reverse Line iterating: Line: {count}, Time: {data[3]}\n')#lines incoporated such that the time should step in reverse

    if (count >= archive_length_lim):#break for loop after exceeding viol_hour
        log_handle.write(f'Iterated till viol_hour: Breaking Loop A\n')
        break
    
    
    #electrons
    if (data[6] != "0"):
        bad_e_data = bad_e_data + 1
        log_handle.write(f'Data[6]: {data[6]} :Increment bad_e_data\n')
    #protons
    if (data[9] != "0"):
        bad_p_data = bad_p_data + 1
        log_handle.write(f'Data[9]: {data[9]} :Increment bad_p_data\n')
    
    count = count + 1 # final step, to increment counter


log_handle.write(f'Total bad data count: E: {bad_e_data}, P: {bad_p_data}\n')
#
#--Alert Check: Does not send alerts between midnight and 7 am
#
hour_now = int(datetime.now().strftime("%H"))#get current hour
log_handle.write(f'Current Hour: {hour_now}\n')
if ((hour_now < 24) and (hour_now > 7)):
    log_handle.write(f'Within Alert Time\n')

    if ((bad_e_data == archive_length_lim) or (bad_p_data == archive_length_lim)):
        #No valid data for viol_hour hours, send out an alert if it has not been sent out yet
        log_handle.write(f'Enough Bad Data Found: Uh-Oh. \n')
        #writing the lock file
        if (os.path.exists(lockfile)):
            os.system(f'date >> {lockfile}')#touch lockfile, updating the date
        else:
            lock_handle = open(lockfile,"w+")
            lock_handle.write(f'No valid ACE data for at least {viol_hour}h\n')
            lock_handle.write("Radiation team should investigate\n")
            lock_handle.write("this message sent to sot_ace_alert\n")
            lock_handle.close()
            #os.system(f'cat {lockfile} | mailx -s "ACE no valid data for >{viol_hour}h" sot_ace_alert')
            os.system(f'cat {lockfile} | mailx -s "ACE no valid data for >{viol_hour}h" waaron malgosia swolk')

            log_handle.write(f'Alert Triggered: mail should be sent.\n')
            
            #store the 12h archive file that triggered the alert
            os.system(f'cp {infile} {lockdir+"/ace_12h_archive_alert"}')

            
log_handle.close(), #closes log operations file
