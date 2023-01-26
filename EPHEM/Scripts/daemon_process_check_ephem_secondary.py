#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#############################################################################
#                                                                           #
#   daemon_process_check.py: check whether EPHEM related daemon is running. #
#                                                                           #
#               author: t. isobe@cfa.harvard.edu                            #
#                                                                           #
#               last update Oct 12, 2022                                    #
#                                                                           #
#############################################################################

import sys
import os
import string
import re
import time
import random

#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

#
#--- Passes in extra emails from sys args
#
ADMIN  = ['mtadude@cfa.harvard.edu']
for i in range(1,len(sys.argv)):
    if sys.argv[i][:6] == 'email=':
        ADMIN.append(sys.argv[i][6:])

#----------------------------------------------------------------------------
#--- daemon_process_check: check whether EPHEM related daemon is running   --
#----------------------------------------------------------------------------

def  daemon_process_check():
    """
    check whether EPHEM related daemon is running
    input: none
    output: email sent to admin, if the script found non-active daemon process
            Note: this must be run on the same cpu where the daemon processes
                  are running. (currently c3po-v)
    """
#
#--- check SOH daemon processes
#
    cmd = 'ps aux|grep daemonize > ' + zspace
    os.system(cmd)

    with open(zspace, 'r') as f:
        out = f.read();

    cmd = 'rm -rf ' + zspace
    os.system(cmd)
    line = ''
#
#---    check the process is still running
#
    mc1  = re.search('interpolate_daemonize', out)
#
#---- if the process is not running, send out email to admin
#
    if mc1 is None:
        send_email()

#----------------------------------------------------------------------------
#-- send_email: send out email to admin                                    --
#----------------------------------------------------------------------------

def send_email():
    """
    send out email to admin
    input:  none
    output: email sent to admin
    """

    text = 'daemon process of /data/mta4/Script/Space_Weather/EPHEM/Scripts/ page is not running.\n'
    text = text + 'Please check mta/r2d2-v daemon process.\n'

    with open(zspace, 'w') as fo:
        fo.write(text)

    cmd = 'cat ' + zspace + " | mailx -s'EPHEM Daemon Process Problem' " + ' '.join(ADMIN)
    os.system(cmd)

    cmd = 'rm -rf ' + zspace
    os.system(cmd)

#----------------------------------------------------------------------------

if __name__ == "__main__":

    daemon_process_check()
