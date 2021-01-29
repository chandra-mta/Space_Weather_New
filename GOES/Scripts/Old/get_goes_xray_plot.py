#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#########################################################################################
#                                                                                       #
#               get_goes_xray_plot.py: download goes x-ray plot                         #
#                                                                                       #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                            #
#                                                                                       #
#               Last update: Jan 31, 2020                                               #
#                                                                                       #
#########################################################################################

import os
import sys
import re
import string
import random
import time
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
    exec("%s = %s" %(var, line))

web_dir    = html_dir + 'GOES/'
plot_dir   = web_dir  + 'Plots/'
#
#--- set ftp address and output name
#
ftp = 'https://services.swpc.noaa.gov/images/goes-xray-flux.gif'
out = plot_dir + 'GOES_xray.gif'

#
#--- get the plot
#
cmd = 'wget -q -O ' + out + ' ' + ftp
os.system(cmd)

