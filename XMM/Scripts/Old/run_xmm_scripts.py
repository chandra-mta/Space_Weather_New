#!/usr/bin/env /proj/sot/ska/bin/python

#############################################################################
#                                                                           #
#       run_xmm_scripts.py: run all xmm related scripts                     #
#                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                       #
#                                                                           #
#           last update: Feb 19, 2020                                       #
#                                                                           #
#############################################################################
import os
import sys
import re
import string
import random
import operator
import time
from Ska.Shell import getenv, bash

ascdsenv = getenv('setenv IDL_PATH "/home/mta/IDL"; setenv IDL_DLM_PATH "/home/mta/IDL/CXFORM:<IDL_DEFAULT>";', shell='tcsh')
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

s_dir    = xmm_dir + 'Scripts/'
data_dir = xmm_dir + 'Data/'

#----------------------------------------------------------------------------------
#-- run_xmm_scripts: run all xmm related scripts                                 --
#----------------------------------------------------------------------------------

def run_xmm_scripts():
    """
    run all xmm related scripts
    input: none but copied from:
                <tle_dir>/*gsme_in_Re
                /stage/xmmops_ftp/radmon_02h.dat
    output: <data_dir>/crmreg_cxo.dat
            <data_dir>/crmreg_xmm.dat
            <data_dir>/mta_xmm_db.dat
            <data_dir>/xmm_7day.archive2
            <data_dir>/xmm.archive
            <web_dir>/xmm_2day.dat
            <web_dir>/Plots/mta_xmm_plot.gif
            <web_dir>/Plots/mta_xmm_plot_gsm.gif
            <web_dir>/Plots/mta_xmm_plot_comp.gif

    """
#
#--- save last xmm.archive
#
    cmd = 'cp -f ' + data_dir + 'xmm.archive ' + data_dir + 'xmm.archive~'
    os.system(cmd)
#
#--- copy data into the current direcotry
#
    copy_cxo_data()
    
    cmd = 'cp /stage/xmmops_ftp/radmon_02h.dat ./radmon_02h_curr.dat'
    os.system(cmd)
#
#--- run fortran scripts
#
###    cmd = s_dir + 'crmreg_cxo'
###    os.system(cmd)
###    
###    cmd = s_dir + 'crmreg_xmm'
###    os.system(cmd)
#
#--- run idl scripts
#
###    try:
###        cmd1 = "/usr/bin/env PERL5LIB= "
###        cmd2 = ' idl ' + s_dir + 'update'
###        cmd  = cmd1 + cmd2
###        bash(cmd, env=ascdsenv)
###    except:
###        cmd = 'setenv IDL_PATH "/home/mta/IDL"; setenv IDL_DLM_PATH "/home/mta/IDL/CXFORM:<IDL_DEFAULT>"; idl ' + s_dir +'update'
###        os.system(cmd)
#
#--- remove copied data
#
###    rm_file('./radmon_02h_curr.dat')
###    rm_file('./cxo.gsme_in_Re')
###    rm_file('./xmm.gsme_in_Re')
###    rm_file('./mta_xmm_db.dat')
#
#--- check whether something happened and lost data; if so, use the original xmm.archive
#
    orig = data_dir + 'xmm.archive~'
    crrt = data_dir + 'xmm.archive'
    out1 = os.stat(orig)
    out2 = os.stat(crrt)
    if out1.st_size > out2.st_size:
        cmd = 'mv -f ' + orig + ' ' + crrt
        os.system(cmd)

#----------------------------------------------------------------------------------
#-- copy_cxo_data: copying cxo and xmm gsme data                                 --
#----------------------------------------------------------------------------------

def copy_cxo_data():
    """
    copying cxo and xmm gsme data
    input: none but read from TLE directory
    output: <data_dir>/cxo.gsme_in_Re
            <data_dir>/xmm.gsme_in_Re
    """
#
#--- cxo data
#
    ifile = 'cxo.gsme_in_Re'
    dfile = tle_dir + 'Data/cxo.gsme_in_Re'

    check_data(ifile, dfile)
#
#--- xmm data
#
    ifile = 'xmm.gsme_in_Re'
    dfile = tle_dir + 'Data/xmm.gsme_in_Re'

    check_data(ifile, dfile)

#----------------------------------------------------------------------------------
#-- check_data: read data and drop data line which are nan or starting from non digit 
#----------------------------------------------------------------------------------

def check_data(ifile, dfile):
    """
    read data and drop data line which are nan or starting from non digit
    input:  dfile   --- data file name
    output: ifile   --- output file name
    """

    data  = read_data_file(dfile)

    fo    = open(ifile, 'w')
    for ent in data:
        mc = re.search('nan', ent)
        if mc is not None:
            continue
        else:
            try:
                test = float(ent[0])

                fo.write(ent)
                fo.write('\n')
            except:
                continue

    fo.close()

    cmd =  'chmod 755 ' + ifile
    os.system(cmd)

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    f    = open(ifile, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    if remove > 0:
        cmd = 'rm -rf ' + ifile 
        os.system(cmd)

    return data

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

def rm_file(ifile):

    if os.path.isfile(ifile):
        cmd = 'rm -f ' + ifile
        os.system(cmd)

#---------------------------------------------------------------------------------

if __name__ == '__main__':
    
    run_xmm_scripts()
