#!/usr/bin/env /proj/sot/ska/bin/python

#################################################################################
#                                                                               #
#   extract_next_three_days.py: extract gse/gsm data for the next two days      #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Aug 24, 2018                                           #
#                                                                               #
#################################################################################

import sys
import os
import string
import re
import numpy
import getopt
import time
import time
import Chandra.Time

#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

f= open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)

data_dir = gsm_plot_dir + 'Data/'
#
#---- read PE.EPH.gsme_in_Re and select out the potion that contains the
#---- data from today to the end of 2nd day from today
#---- output: ./gs_data_3_day
#

stday = time.strftime("%Y:%j", time.gmtime())
chk   = float(time.strftime("%H", time.gmtime()))
if chk < 12:
    stday = stday + ':00:00:00'
else:
    stday = stday + ':12:00:00'

start = Chandra.Time.DateTime(stday).secs
stop  = start + 2.0 * 86400.0

ifile = ephem_dir + 'Data/PE.EPH.gsme_in_Re_short'
f     = open(ifile, 'r')
data  = [line.strip() for line in f.readlines()]
f.close()

out = data_dir + 'gs_data_2_day'
fo = open(out, 'w')

for ent in data:
    atemp = re.split('\s+', ent)
    atime = float(atemp[0])
    if atime < start:
        continue
    elif atime > stop:
        break
    else:
        line = ent + '\n'
        fo.write(line)

fo.close()
