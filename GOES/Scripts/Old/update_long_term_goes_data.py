#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################################
#                                                                                                   #
#       update_long_term_goes_data.py: update long term goes data                                   #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Nov 06, 2018                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import string
import random
import operator
import time
import datetime
import numpy
import Chandra.Time
import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')

from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines

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
#
#--- temp writing file name
#
rtail  = int(time.time())
zspace = '/tmp/zspace' + str(rtail)
#
#--- set direcotries
#
data_dir   = goes_dir + 'Data/'

#---------------------------------------------------------------------------------------------------
#-- update_long_term_goes_data: update long term goes data                                       ---
#---------------------------------------------------------------------------------------------------

def update_long_term_goes_data():
    """
    update long term goes data
    input:  none but read from ftp://ftp.swpc.noaa.gov/pub/lists/pchan/<date>_Gp_pchan_5m.txt
    output: <data_dir>/goes_data.txt
    """
#
#--- read the current data
#
    ifile = data_dir + 'goes_data.txt'
    data  = read_data_file(ifile)
    atemp = re.split('\s+', data[-1])
#
#--- time stamp of the last read data set
#
    ltime = int(atemp[0] + atemp[1] + atemp[2])
    lhr   = int(atemp[3])
#
#--- find Gp pchan data list from ftp site
#
    cmd = "/usr/bin/lynx -source  ftp://" + noaa_ftp + "pchan/ > " + zspace
    #cmd = 'wget -q -O' + zspace + ' ftp://' + noaa_ftp + "pchan/"

    os.system(cmd)

    fdata = read_data_file(zspace, remove=1)
#
#--- find the data files which have not been read
#
    chk  = 0
    for ent in fdata:
        mc = re.search('Gp_pchan_5m.txt', ent)
        if mc is None:
            continue
        mc = re.search('A HREF=', ent)
        if mc is None:
            continue

        atemp = re.split('pchan\/', ent)
        fname = atemp[1].replace('"', '')
        btemp = re.split('_', fname)
        try:
            test  = int(btemp[0])
        except:
            continue

        if test >=  ltime:
#
#--- download data
#
            cmd = "/usr/bin/lynx -source  ftp://" + noaa_ftp + "pchan/" + fname + ' > ' + zspace
            #cmd = 'wget -q -O' + zspace + " ftp://" + noaa_ftp + "pchan/" + fname
            os.system(cmd)
#
#---- get the data part
#
            gdata = read_data_file(zspace, remove=1)
            gdata = gdata[26:]

            if test == ltime:
                save = []
                for ent in gdata:
                    atemp = re.split('\s+', ent)
                    if int(atemp[3]) < lhr:
                        continue
                    else:
                        save.append(ent)

                data = data + save
            else:
                data  = data + gdata

            chk   = 1
#
#--- if there are new data, add to the data
#
    if chk > 0:
        cmd = 'mv ' + ifile + ' ' + ifile + '~'
        os.system(cmd)

        fo  = open(ifile, 'w')
        for ent in data:
            fo.write(ent)
            fo.write('\n')

        fo.close()

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    f    = open(ifile, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    if remove > 0:
        if os.path.isfile(ifile):
            cmd = 'rm ' + ifile
            os.system(cmd)

    return data
    
#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    update_long_term_goes_data()
