#!/usr/bin/env /data/mta4/Script/Python3.6/envs/ska3/bin/python

#################################################################################
#                                                                               #
#       runcrm.py: calculate CRM proton flux for Chandra ephemeris              #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last upate: Feb 02, 2021                                            #
#                                                                               #
#       converted from Robert Cameron's runcrm.f (2002)                         #
#                                                                               #
#################################################################################

import sys
import os
import re
import string
import math
#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec( "%s = %s" %(var, line))
#
#--- append  pathes to private folders to a python directory
#
sys.path.append('/data/mta4/Script/Python3.6/MTA/')
sys.path.append('/data/mta4/Space_Weather/CRMFLX/CRMFLX_PYTHON/')
#
#--- import several functions
#
import mta_common_functions as mcf
import crmflx               as cflx

tail = ['00','03','07','10','13','17','20','23','27',\
        '30','33','37','40','43','47','50','53','57',\
        '60','63','67','70','73','77','80','83','87','90']

#----------------------------------------------------------------------------
#-- runcrm: calculate CRM proton flux for Chandra ephemeris                --
#----------------------------------------------------------------------------

def runcrm(ifile=''):
    """
    calculate CRM proton flux for Chandra ephemeris
    read from a file, for all 28 possible values of Kp.

    input:  ifile   --- input ephemeris file, e.g., 'PE.EPH.gsme_in_Re_short'
    output: <crm3_dir>/Data/CRM3_p.dat<#>
    """
    if ifile == '':
        ifile = ephem_dir + 'Data/PE.EPH.gsme_in_Re_short'
#
#--- set parameters (see crmflx for definitions)
#
    ispeci  = 1
    iusesw  = 1
    iusemsh = 2
    iusemsp = 0
    smooth1 = 4
    nflxget = 10
    ndrophi = 2
    ndroplo = 2
    logflg  = 2
    rngtol  = 4.0
    fpchi   = 80
    fpclo   = 20

    fswimn  = 0.0
    fswi95  = 0.0
    fswi50  = 0.0
    fswisd  = 0.0
#
#--- read solar wind database
#
    xflux1, yflux1, zflux1, flxbin1, numbin1, numdat1 = cflx.swinit(ispeci)
#
#--- read magnetosheath databas
#
    xflux2, yflux2, zflux2, flxbin2, numbin2, numdat2 = cflx.mshinit(ispeci)
#
#--- read magnetosphere database
#
    xflux3, yflux3, zflux3, flxbin3, numbin3, numdat3,imapindx3,\
          nsphvol3, ioffset3,joffset3,koffset3  = cflx.mspinit(ispeci)
#
#--- read the ephemeris data
#
    data  = mcf.read_data_file(ifile)
    if len(data) < 1:
        exit(1)
    cdata = mcf.separate_data_to_arrays(data)
    tlist = cdata[0]
    xgsm  = cdata[1]
    ygsm  = cdata[2]
    zgsm  = cdata[3]

    for i in range(0, 28):
        xkp   = i / 3.0
        line  = ''
        for j in range(0, len(tlist)):
            idloc,fluxmn,flux95,flux50,fluxsd =\
                cflx.crmflx(xkp,xgsm[j],ygsm[j],zgsm[j],ispeci,iusesw,\
                    fswimn,fswi95,fswi50,fswisd,iusemsh,iusemsp,smooth1,\
                    nflxget,ndrophi,ndroplo,logflg,rngtol,fpchi,fpclo,\
                    xflux1, yflux1, zflux1, flxbin1, numbin1, numdat1,\
                    xflux2, yflux2, zflux2, flxbin2, numbin2, numdat2,\
                    xflux3, yflux3, zflux3, flxbin3, numbin3, numdat3,\
                    nsphvol3, ioffset3,joffset3,koffset3,imapindx3)

            line = line + '%13.1f\t' % tlist[j]
            line = line + '%2d\t'    % idloc
            line = line + '%13.6e\t' % fluxmn
            line = line + '%13.6e\t' % flux95
            line = line + '%13.6e\t' % flux50
            line = line + '%13.6e\n' % fluxsd

        ofile = crm3_dir +  'Data/CRM3_p.dat' + tail[i]
        with open(ofile, 'w') as fo:
            fo.write(line)

#---------------------------------------------------------------------

if __name__ == '__main__': 

    if len(sys.argv) > 1:
        ifile = sys.argv[1].strip()
    else:
        ifile = ''

    runcrm(ifile)
