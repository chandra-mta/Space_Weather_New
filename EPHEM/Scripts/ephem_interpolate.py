#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#############################################################################
#                                                                           #
#           ephem_interpolate.py: interpolate the current epheris data      #
#                                                                           #
#               author: t. isobe (tisobe@cfa.harvard.edu)                   #
#                                                                           #
#                   last update: Feb 02, 2020                               #
#                                                                           #
#############################################################################

import os
import sys
import re
import string
import random
import math
import numpy
import time
import Chandra.Time
path = '/data/mta4/Space_Weather/EPHEM/house_keeping/dir_list_py'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]
for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" % (var, line))
#
#--- append  pathes to private folders to a python directory
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)
#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

e_file = data_dir + 'PE.EPH.dat'
o_file = data_dir + 'gephem.dat'

#----------------------------------------------------------------------------------
#-- ephem_interpolate: interpolate the current epheris data                      --
#----------------------------------------------------------------------------------

def ephem_interpolate():
    """
    interpolate the current epheris data
    input:  <data_dir>/PE.EPH.dat
    output: <data_dir>/gephem.dat
    """
#
#--- find the current time
#
    out = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    now = Chandra.Time.DateTime(out).secs
#
#--- read epherims data
#
    data = read_data_file(e_file)

    t_list = []
    d_list = []
    for ent in data:
        atemp = re.split('\s+', ent)
        t_list.append(float(atemp[0]))
        d_list.append(ent)
#
#--- if the current data is outside of the data, stop
#
    t_len = len(t_list)
    if now < t_list[0]:
        print("Outside of the data range")
        exit(1)
    if now > t_list[-1]:
        print("Outside of the data range")
        exit(1)
#
#--- find the time interval that the current time drops between
#
    for  k in range(1, t_len):
        if (now >= t_list[k-1]) and (now <= t_list[k]):
#
#--- interpolate the postion
#
            ratio = (now - t_list[k-1]) / (t_list[k] - t_list[k-1])

            atemp = re.split('\s+', d_list[k-1])
            btemp = re.split('\s+', d_list[k])

            line  = ''
            dsum1 = 0
            dsum2 = 0
#
#--- go through x, y, z and vx, vy, vz
#
            for m in range(1, 7):
                sval = float(atemp[m])
                tval = float(btemp[m])
                est  = sval + (tval - sval) * ratio
                line = line + "%16.3f" % est
                if m in [1, 2, 3]:
                    dsum1 += sval * sval
                    dsum2 += tval * tval
#
#--- compute the distrance from the center and ditermine whether the satellite is going up or down
#
            dist1 = math.sqrt(dsum1)
            dist2 = math.sqrt(dsum2)
            dist  = dist1 +(dist2 - dist1) * ratio
            ###print("I AM HERE: " + str(dist1) + '<-->' + str(dist2) + '<-->' + str(dist) +'<-->' + str(ratio))
            if dist1 <= dist2:
                direct = 'A'
            else:
                direct = 'D'
            sline = "%7d" % dist + ' ' +  direct + line + '\n'
#
#--- print out the result
#
            with open(o_file, 'w') as fo:
                fo.write(sline)
            
            break
                
#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    if remove > 0:
        cmd = 'rm -rf ' + ifile
        os.system(cmd)

    return data

#-------------------------------------------------------------------------------------

if __name__ == "__main__":

    ephem_interpolate()
