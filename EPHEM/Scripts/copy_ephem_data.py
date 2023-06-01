#!/proj/sot/ska3/flight/bin/python

#############################################################################
#                                                                           #
#       copy_ephem_data.py: copy ephem data from another site               #
#                                                                           #
#               author: t. isobe (tisobe@@cfa.harvard.edu)                  #
#                                                                           #
#                   last update: Mar 16, 2021                               #
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
import datetime
import Chandra.Time
path = '/data/mta4/Space_Weather/EPHEM/house_keeping/dir_list_py'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]
for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" % (var, line))
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'
#
#--- append  pathes to private folders to a python directory
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)
#
#--- import several functions
#
import mta_common_functions as mcf  #---- contains other functions commonly used in MTA scripts
import convert_coord        as cnvc #---- converting coordinate systems
#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

#----------------------------------------------------------------------------------
#-- copy_ephem_data: copy ephem data from /data/mta/Script/Ephem/EPH_Data/       --
#----------------------------------------------------------------------------------

def copy_ephem_data():
    """
    copy ephem data from /data/mta/Script/Ephem/EPH_Data/
    input:  none, but read from <input_data>/DE*.EPH.dat0
    output: <data_dir>/EPH.dat
            <data_dir>/EPH.gsme
            <data_dir>/EPH.gsme_in_Re
    """
#
#--- read the list of the previously copied data files
#
    sfile  = house_keeping  + 'prev_data'
    p_list = mcf.read_data_file(sfile)
#
#--- read the current data files
#
    cmd = 'ls -rt /data/mta/Script/Ephem/EPH_Data/DE*.EPH.dat0 > ' + zspace
    os.system(cmd)

    c_list = mcf.read_data_file(zspace, remove=1)
#
#--- find the names of new files
#
    n_list = list(numpy.setdiff1d(c_list, p_list))

    if len(n_list):
        line = ''
        for ent in n_list:
            line = line + ent + '\n'
#
#--- append the data to the longterm data
#
            cmd = 'cat ' + ent + '>>' + data_dir + 'longterm/dephem.dat'
            #for writing out files in test directory
            if (os.getenv('TEST') == 'TEST'):
                cmd = 'touch' + test_out + '/dephem.dat ; ' + 'cat' + ent + '>>' + test_out + "/dephem.dat"
            os.system(cmd)
#
#--- copied the last entry
#
        cmd = 'rm -rf ' + data_dir + 'PE.EPH*'
        os.system(cmd)
        ofile = data_dir + 'PE.EPH.dat'
        if (os.getenv('TEST') == 'TEST'):
            ofile = test_out + "/" + os.path.basename(ofile)
        cmd = 'cp  '  + ent + ' ' + ofile
        os.system(cmd)
#
#--- update the list of copied files
#
        #for writing out files in test directory
        if (os.getenv('TEST') == 'TEST'):
            sfile = test_out + "/" + os.path.basename(sfile)
        with open(sfile, 'a') as fo:
            fo.write(line)
#
#--- gsme files updated a few times a day as a new kp data comes in
#
    cmd = 'ls -rt /data/mta/Script/Ephem/EPH_Data/DE*.EPH.dat00 > ' + zspace
    os.system(cmd)
    c_list = mcf.read_data_file(zspace, remove=1)
#
#---- create a data file with gsm and gse in the earth radius
#
    data  = cnvc.cocochan(c_list[-1])
#
#--- print out the results
#
    out   = data_dir + 'PE.EPH.gsme'
    #for writing out files in test directory
    if (os.getenv('TEST') == 'TEST'):
        out = test_out + "/" + os.path.basename(out)
    with open(out, 'w') as fo:
        for ent in data[0]:
            fo.write(ent)

    out   = data_dir + 'PE.EPH.gsme_in_Re'
    if (os.getenv('TEST') == 'TEST'):
        out = test_out + "/" + os.path.basename(out)
    with open(out, 'w') as fo:
        for ent in data[1]:
            fo.write(ent)
        

    out   = data_dir + 'PE.EPH.gsme_spherical'
    if (os.getenv('TEST') == 'TEST'):
        out = test_out + "/" + os.path.basename(out)
    with open(out, 'w') as fo:
        for ent in data[2]:
            fo.write(ent)
        
#------------------------------------------------------------------------------

if __name__ == '__main__':

    copy_ephem_data()
#
#---- create a data file with gsm and gse in the earth radius
#
#    ofile2 = data_dir + 'PE.EPH.gsme'
#    dline = cnvc.cocochan(ofile2)
#    out   = data_dir + 'PE.EPH.gsme_in_Re'
#    with open(out, 'w') as fo:
#        fo.write(dline)
