#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#############################################################################
#                                                                           #
#   daemon_process_check.py: check whether EPHEM related daemon is running. #
#                                                                           #
#               author: t. isobe@cfa.harvard.edu                            #
#                                                                           #
#               last update Oct 29, 2020                                    #
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

admin  = 'tisobe@cfa.harvard.edu'

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

    text = 'daemon process of /data/mta4/Space_Weather/EPHEM/Scripts/ page is not running.\n'
    text = text + 'Please check mta/c3po-v daemon process.\n'

    with open(zspace, 'w') as fo:
        fo.write(text)

    cmd = 'cat ' + zspace + " | mailx -s'EPHEM Daemon Process Problem' " + admin
    os.system(cmd)

    cmd = 'rm -rf ' + zspace
    os.system(cmd)

#----------------------------------------------------------------------------

if __name__ == "__main__":

    daemon_process_check()
