#!/proj/sot/ska3/flight/bin/python

#############################################################################################
#                                                                                           #
#           create_short_ephdata.py: create short PE.EPH.gsme(_in_Re) data                  #
#                                                                                           #
#               author: t. isobe (tiosbe@cfa.harvard.edu)                                   #
#                                                                                           #
#               last update: Mar 16, 2021                                                   #
#                                                                                           #
#############################################################################################

import os
import sys
import re
import string
import math
import time
import datetime
import Chandra.Time
import random
import numpy

path = '/data/mta4/Space_Weather/house_keeping/dir_list'
with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var   = atemp[1].strip()
    line  = atemp[0].strip()
    exec("%s = %s" %(var, line))
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'

sys.path.append('/data/mta4/Script/Python3.10/MTA/')
import mta_common_functions     as mcf

current = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current = Chandra.Time.DateTime(current).secs - 2.0 * 86400.
#start   = current - 2.0 * 86400

for ifile in ['PE.EPH.gsme', 'PE.EPH.gsme_in_Re','PE.EPH.gsme_spherical']:
    ifile   = ephem_dir + 'Data/' + ifile
    data    = mcf.read_data_file(ifile)

    line    = ''
    cnt     = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        stime = float(atemp[0])
        if stime > current:
            if cnt >= 3500:
                break
    
            #ent  = ent.replace('\t', '  ')
            line = line + ent + '\n'
            cnt += 1
    
    ofile = ifile + '_short'
    if (os.getenv('TEST') == 'TEST'):
        ofile = test_out + "/" + os.path.basename(ofile)
    with open(ofile, 'w') as fo:
        fo.write(line)
