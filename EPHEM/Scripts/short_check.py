#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#####################################################################################
#                                                                                   #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last updae: Apr 08, 2020                                                #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string

cmd = 'ls /data/mta4/Space_Weather/EPHEM/Data/PE* > ./zstest'
os.system(cmd)

with open('zstest', 'r') as f:
    data = [line.strip() for line in f.readlines()]

cmd = 'rm -rf ./zstest'
os.system(cmd)

chk = 0
for ent in data:
    mc = re.search('short', ent)
    if mc is not None:
        chk = 1

if chk == 0:
    line = '*_short files are missing in /data/mta4/Space_Weather/EPHEM/Data/.\n'
    with open('./zstest', 'w') as fo:
        fo.write(line)

    cmd = 'cat ./zstest | mailx -s "Subject: ephem short file missing!" tisobe@cfa.harvard.edu'
    os.system(cmd)

    cmd = 'rm -rf ./zstest'
    os.system(cmd)
