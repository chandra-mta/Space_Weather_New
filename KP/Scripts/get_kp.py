#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#####################################################################################
#                                                                                   #
#       get_kp.py:copy kp data and create a file to match in the required format    #
#                                                                                   #
#               author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                                   #
#               last updae: Mar 16, 2021                                            #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import time
from datetime import datetime
from time import gmtime, strftime, localtime
import Chandra.Time

head =        '# Prepared by Helmholtz Centre Potsdam.\n'
head = head + '# See: https://www.gfz-potsdam.de/en/kp-index/ \n'
head = head + '#\n'
head = head + '# Units: Predicted Index 0-9 in Kp units\n'
head = head + '#\n'
head = head + '# Solar Wind Source: See: ttps://www.gfz-potsdam.de/en/kp-index/\n'
head = head + '# The value -1 in the report indicates missing data.\n'
head = head + '#\n'
head = head + '#                      USAF 3 hours Wing Kp Geomagnetic Activity Index\n'
head = head + '#\n'
head = head + '#                        3-hour         3-hour        3-hour         3-hour     \n'
head = head + '# UT Date   Time      Predicted Time  Predicted    Predicted Time  Predicted   USAF Est.\n'
head = head + '# YR MO DA  HHMM      YR MO DA  HHMM    Index      YR MO DA  HHMM    Index        Kp    \n'
head = head + '#---------------------------------------------------------------------------------------\n'

#---------------------------------------------------------------------------------------
#-- get_kp: copy kp data and create a file to match in the required format            --
#---------------------------------------------------------------------------------------

def get_kp():
    """
    copy kp data and create a file to match in the required format
    input: none but read from: /data/mta4/Space_Weather/KP/Data/k_index_data_past
    output: ./kp.dat
    """

    ifile = '/data/mta4/Space_Weather/KP/Data/k_index_data_past'
    with open(ifile, 'r') as f:
        data  = [line.strip() for line in f.readlines()]

    atemp = re.split('\s+', data[-1])
    ltime = float(atemp[0])
    kval  = atemp[1]

    ltime = Chandra.Time.DateTime(ltime).date
    mc    = re.search('\.', ltime)
    if mc is not None:
        btemp = re.split('\.', ltime)
        ltime = btemp[0]

    ldate = datetime.strptime(ltime, '%Y:%j:%H:%M:%S').strftime("%Y %m %d %H%M")

    line  = ldate + '\t\t' + ldate + '\t\t' + kval + '\t\t\t' + ldate + '\t\t' + kval + '\t\t' + kval + '\n'
    line  = head + line

    with open('/data/mta4/Space_Weather/KP/Data/kp.dat', 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------

if __name__ == '__main__':

    get_kp()

