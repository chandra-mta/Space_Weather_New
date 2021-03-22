#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python 
# cython: profile=True

#################################################################################
#                                                                               #
#       crmflx.py: calculate CRM proton flux for Chandra ephemeris              #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last upate: Mar 22, 2021                                            #
#                                                                               #
#           baseed on Robert Cameron's crmflx.f (2001)                          #
#                                                                               #
#################################################################################

import sys
import os
import re
import string
import math
import numpy
import time
from datetime import datetime
import Chandra.Time
import copy
import unittest
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
sys.path.append('/data/mta/Script/Python3.8/MTA/')
#
#--- import several functions
#
import mta_common_functions as mcf
#
#--- temp writing file name
#
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- directory where sol wind model data etc are kept (abbriviated data files)
#
mdat_dir = '/data/mta4/Space_Weather/CRMFLX/CRMFLX_PYTHON/Data/'
#
#--- set the kp tolerance variable.  if the kp value for which output
#--- is desired changes by more than this value, the kp scaling
#--- parameters are recalculated
#
xkptol  = 0.3
#
#--- global variables
#
blendx1 = -8.0      #--- xGSM (xTAIL) limit for *not* using z-layers (if xTAIL >= BLENDx1, no z-layers used)
blendx2 = -10.0     #--- xGSM (xTAIL) limit for *only* using z-layers (if xTAIL >= BLENDx1, no z-layers used)
maxcell = 1000      #--- maximum number of near-neighbor cells used in calculating the average flux at this location
maxkp   = 9         #--- number of kp bins in the data file
maxnsphvol = 100000 #--- maximum number of sub-volume elements stores in the streamline mapping search volume
maxnum  = 65        #--- maximum number of volume elements along an axis used in datafile
maxpnt  = 250000    #--- maximum number of points used in datafile
nsave   = 10        #--- the number of range sorted data cells to save before removing the highest & lowest flux values
numsec  = 10        #--- number of spatila sectors: max nused in magnetosphere, magnetosheath, or solar wind
pi      = 3.14159265359
xinc    = 1.0       #--- Chandra Volume Element Database Parameters: length of volume element in x-direction (Re)
yinc    = 1.0       #--- Chandra Volume Element Database Parameters: length of volume element in y-direction (Re)
zinc    = 1.0       #--- Chandra Volume Element Database Parameters: length of volume element in z-direction (Re
xmin    = -30.0     #--- Chandra Volume Element Database Parameters: minimum x-value of volume element (Re)
ymin    = -30.0     #--- Chandra Volume Element Database Parameters: minimum y-value of volume element (Re)
zmin    = -30.0     #--- Chandra Volume Element Database Parameters: minimum z-value of volume element (Re)
xmax    = +30.0     #--- Chandra Volume Element Database Parameters: maximum x-value of volume element (Re)
ymax    = +30.0     #--- Chandra Volume Element Database Parameters: maximum y-value of volume element (Re)
zmax    = +30.0     #--- Chandra Volume Element Database Parameters: maximum z-value of volume element (Re)
num2    = 6         #--- Sub-Volume Element Database Parameters: number of sub-volume elements in each direction
xinc2   = 0.1666666 #--- Sub-Volume Element Database Parameters: length of sub-volume element in x-direction (Re)
yinc2   = 0.1666666 #--- Sub-Volume Element Database Parameters: length of sub-volume element in y-direction (Re)
zinc2   = 1.0       #--- Sub-Volume Element Database Parameters: length of sub-volume element in z-direction (Re)

#----------------------------------------------------------------------------
#-- crmflx: calculates the ion flux as a function of the magnetic activity kp index
#----------------------------------------------------------------------------

def crmflx(xkp,xgsm,ygsm,zgsm,ispeci,iusesw,fswimn,fswi95,fswi50,fswisd,\
           iusemsh,iusemsp,smooth1,nflxget,ndrophi,ndroplo,logflg,rngtol,fpchi,fpclo,\
           xflux1, yflux1, zflux1, flxbin1, numbin1, numdat1, \
           xflux2, yflux2, zflux2, flxbin2, numbin2, numdat2, \
           xflux3, yflux3, zflux3, flxbin3, numbin3, numdat3, \
           nsphvol3, ioffset3,joffset3,koffset3,imapindx3):
    """
    this routine calculates the ion flux as a function of the
    magnetic activity kp index.
    
    input:  xkp     --- kp index user desires output for.
            xgsm    --- satellite's x-coordinate (re).
            ygsm    --- satellite's y-coordinate (re).
            zgsm    --- satellite's z-coordinate (re).
            ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno.
#            iusesw  --- flag for control of solar wind flux calculation:
#                        iusesw = 0 if (uniform flux) analytic solar wind model used.
#                        iusesw = 1 if user supplied uniform solar wind flux value used.
#                        iusesw = 2 if solar wind database used.
#                        iusesw = 3 if sum of solar wind database value and user
#                                    supplied uniform solar wind flux value used.
#                        iusesw = 4 if sum of (uniform flux) analytic solar wind model
                            and user supplied uniform solar wind flux value used.
            fswimn  --- user supplied mean uniform solar wind flux for the
                        selected species (#/[cm^2-sec-sr-mev]).
            fswi95  --- user supplied 95% level uniform solar wind flux for
                        the selected species (#/[cm^2-sec-sr-mev]).
            fswi50  --- user supplied 50% level uniform solar wind flux for
                        the selected species (#/[cm^2-sec-sr-mev]).
            fswisd  --- user supplied std. dev. of uniform solar wind flux
                        for the selected species (#/[cm^2-sec-sr-mev]).
#            iusemsh --- flag for control of magnetosheath flux calculation:
#                        iusemsh = 0 if (uniform flux) analytic magnetosheath model used.
#                        iusemsh = 1 if user supplied uniform solar wind flux value used.
#                        iusemsh = 2 if magnetosheath database used.
#                        iusemsh = 3 if sum of magnetosheath database value and user
#                                    supplied uniform solar wind flux value used.
#                        iusemsh = 4 if sum of (uniform flux) analytic magnetosheath model
#                                    and user supplied uniform solar wind flux value used.
#            iusemsp --- flag for control of magnetosphere flux calculation:
#                        iusemsp = 0 if only the magnetosphere model flux is used.
#                        iusemsp = 1 if user supplied uniform solar wind flux value
#                                    is added to the magnetosphere flux.
#                        iusemsp = 2 if analytic solar wind model (uniform flux) is
#                                    added to the magnetosphere flux.
            smooth1 --- flag for control of database smoothing filter:
                            smooth1 = 0 if no data smoothing is used.
                            smooth1 = 1 if spike rejection and near neighbor flux.
                            smooth1 = 2 if spike rejection with range weighted
                                        scaling of flux.
                            smooth1 = 3 if spike rejection with average flux.
                            smooth1 = 4 if spatial average of flux in volume
                                        specified by rngtol.
                            smooth1 = 5 if spatial average of flux in volume
                                        specified by rngtol, with the specified
                                        number of high and low flux values inside
                                        the volume dropped first.
                            smooth1 = 6 if spatial averaging of flux in volume
                                        specified by rngtol, with percentile
                                        threshold limits on flux values.
            nflxget --- number of flux values to get for smoothing filter
                                (used if smooth1 = 1,2, or 3)
            ndrophi --- number of high flux values to drop for smoothing
                                filter (used if smooth1 = 1,2,3, or 5).
            ndroplo --- number of low flux values to drop for smoothing
                                filter (used if smooth1 = 1,2,3, or 5).
            logflg  --- flag controlling how flux average is performed
                                (used if smooth1 = 2,3,4,5, or 6).
                            logflg = 1 if log10 of flux values used.
                            logflg = 2 if linear flux values used.
            rngtol  --- range tolerance from near-neigbor used in spatial
                                averaging of database (re)
                                (used if smooth1 = 4,5, or 6).
            fpchi   --- upper percentile limit for spatial averaging of flux
                                (used if smooth1 = 6).
            fpclo   --- lower percentile limit for spatial averaging of flux
                                (used if smooth1 = 6).
            xflux1  --- array of arrays containing the x-coordinate of each data cell's center (re)
            yflux1  --- array of arrays containing the y-coordinate of each data cell's center (re)
            zflux1  --- array of arrays containing the z-coordinate of each data cell's center (re)
            flxbin1 --- array of arrays the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin1 --- array of arrays of the number of non-zero values within each cell
            numdat1 --- number of non-zero values in the database
                        ----for solar wind
            xflux2  --- array of arrays containing the x-coordinate of each data cell's center (re)
            yflux2  --- array of arrays containing the y-coordinate of each data cell's center (re)
            zflux2  --- array of arrays containing the z-coordinate of each data cell's center (re)
            flxbin2 --- array of arrays the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin2 --- array of arrays of the number of non-zero values within each cell
            numdat2 --- number of non-zero values in the database
                        ---- for magnetosheath
            xflux3  --- array of arrays containing the x-coordinate of each data cell's center (re)
            yflux3  --- array of arrays containing the y-coordinate of each data cell's center (re)
            zflux3  --- array of arrays containing the z-coordinate of each data cell's center (re)
            flxbin3 --- array of arrays of the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin3 --- array of arrays of the number of non-zero values within each cell
            numdat3 --- number of non-zero values in the database
            nsphvol3  - number of volume elements stored in search volume.
            ioffset3  - array of offset indices for x-direction.
            joffset3  - array of offset indices for y-direction.
            koffset3  - array of offset indices for z-direction.
            imapindx3 - array of pointers to flux database.
                        ---- for magnetosphere

    output: idloc   --- phenomenogical region location identification flag:
                            idloc = 1 if spacecraft is in solar wind
                            idloc = 2 if spacecraft is in magnetosheath
                            idloc = 3 if spacecraft is in magnetosphere.
            fluxmn  --- mean flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux95  --- 95% flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux50  --- 50% flux (#/[cm^2-sec-sr-mev]) for selected species.
            fluxsd  --- standard deviation of flux for selected species.

    param included numsec, maxkp, maxnum, maxpnt, maxnsphvol
    """

    global flxmn1, flx951, flx501, flxsd1 
    global flxmn2, flx952, flx502, flxsd2
#
#--- initialize the kp save variables
#
#    xkpsav1 = 100.0
    xkpsav2 = 100.0
    xkpsav3 = 100.0
#
#--- initialize the species type save variables
#
#    ispsav0 = 100
#    ispsav1 = 100
    ispsav2 = 100
    ispsav3 = 100
#
#--- determine which phenomenological region the spacecraft is in. the
#--- spacecraft's coordinates are returned after transformation into
#--- the magnetotail aligned coordinate system.
#
    xtail,ytail,ztail,idloc = locreg(xkp,xgsm,ygsm,zgsm)
#
#--- the spacecraft is in region 1: the solar wind
#
    if idloc == 1:
#
#--- use the user's value for the uniform solar wind flux
#
        fluxmn = fswimn
        flux95 = fswi95
        flux50 = fswi50
        fluxsd = fswisd
#
#--- the spacecraft is in region 2, the magnetosheath
#
    elif idloc == 2:
#
#--- use the database driven model to get the magnetosheath flux.
#--- if the user supplied kp or species type has changed, redo the
#--- scaling parameters.
#
        xkpdiff = abs(xkp - xkpsav2)
        ispdiff = ispeci - ispsav2
        if (xkpdiff > xkptol) or (ispdiff != 0):
            nsectr2,sectx2,secty2,scmean2,sc952,sc502,scsig2 = scalkp2(xkp,ispeci)
            xkpsav2 = xkp
            ispsav2 = ispeci
#
#--- calculate the solar wind's flux for this kp value & position.
#
        fluxmn,flux95,flux50,fluxsd = \
            nbrflux(xkp,nsectr2,sectx2,secty2,scmean2,sc952,sc502, \
                    scsig2,xtail,ytail,ztail,numdat2,xflux2,yflux2,zflux2,\
                    flxbin2,numbin2,smooth1,nflxget,ndrophi,ndroplo,logflg,\
                    rngtol,fpchi,fpclo)
#
#--- the spacecraft is in region 3, the magnetosphere
#
    elif idloc == 3:
#
#--- avoid the xkp = 0 value
#
        if xkp <= -1.5:
            xkp3 = 1.5
        else:
            xkp3 = xkp
#
#--- if the user supplied kp or species type has changed, redo the
#--- scaling parameters.
#
        xkpdiff = abs(xkp3 - xkpsav3)
        ispdiff = ispeci - ispsav3
        if (xkpdiff > xkptol) or (ispdiff!= 0):
            nsectr3,sectx3,secty3,scmean3,sc953,sc503,scsig3 = scalkp3(xkp3,ispeci)
            xkpsav3 = xkp3
            ispsav3 = ispeci
#
#---calculate the magnetosphere's flux for this Kp value & position
#
        fluxmn,flux95,flux50,fluxsd = \
                nbrflux_map_z(xkp3,nsectr3,sectx3,secty3,scmean3,sc953,
                              sc503,scsig3,xtail,ytail,ztail,numdat3,xflux3,yflux3,zflux3,
                              flxbin3,numbin3,smooth1,nflxget,ndrophi,ndroplo,logflg,
                              rngtol,fpchi,fpclo,nsphvol3,ioffset3,joffset3,koffset3,
                              imapindx3)
    else:
        print(" error in phenomenological region id!")
        exit(1)


    return idloc, fluxmn, flux95, flux50, fluxsd

#----------------------------------------------------------------------------
#-- mspinit:  opens the crm magnetosphere database file and initializes the datarrays
#----------------------------------------------------------------------------

def  mspinit(ispeci):
    """
    this routine opens the crm magnetosphere database file and
    initializes the datarrays stored in the common block.
    
    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    output: xflux3  --- array of arrays of containing the x-coordinate of each data cell's center (re)
            yflux3  --- array of arrays of containing the y-coordinate of each data cell's center (re)
            zflux3  --- array of arrays of containing the z-coordinate of each data cell's center (re)
            flxbin3 --- array of arrays of the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin3 --- array of arrays of the number of non-zero values within each cell
            numdat3 --- number of non-zero values in the database
            nsphvol3  - number of volume elements stored in search volume.
            ioffset3  - array of offset indices for x-direction.
            joffset3  - array of offset indices for y-direction.
            koffset3  - array of offset indices for z-direction.
            imapindx3 - array of pointers to flux database.

    param included xinc, yinc, zinc
    """
#
#--- open input file containing solar wind data
#
#    if ispeci == 1:
#        ifile = mdat_dir + 'MSPH_Kp_PROT.ASC'
#    elif ispeci == 2:
#        ifile = mdat_dir + 'MSPH_Kp_HEL.ASC'
#    elif ispeci == 3:
#        ifile = mdat_dir + 'MSPH_Kp_CNO.ASC'

    ifile = mdat_dir + 'msph_short.asc'

    if not os.path.isfile(ifile):
        print("No data file found: msph_short.asc")
        exit(1)

    xflux3, yflux3, zflux3, flxbin3, numbin3, numdat3, imapindx3 = read_init_data_file(ifile)
#
#--- get the (i,j,k) index offset values used to search for the
#--- near-neighbor flux
#
#--- set the maximum distance (re) to search for a near-neighbo
#
    distmapmax3 = 20.0
    nsphvol3, ioffset3,joffset3,koffset3 = mapsphere(distmapmax3,xinc,yinc,zinc)

    return  xflux3, yflux3, zflux3, flxbin3, numbin3,numdat3, imapindx3,\
            nsphvol3, ioffset3,joffset3,koffset3

#----------------------------------------------------------------------------
#-- mshinit: opens the crm magnetosheath database file and initializes the datarrays
#----------------------------------------------------------------------------

def mshinit(ispeci):
    """
    this routine opens the crm magnetosheath database file and
    initializes the datarrays stored in the common block.
    
    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    output: xflux2  --- array of arrays of containing the x-coordinate of each data cell's center (re)
            yflux2  --- array of arrays of containing the y-coordinate of each data cell's center (re)
            zflux2  --- array of arrays of containing the z-coordinate of each data cell's center (re)
            flxbin2 --- array of arrays of the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin2 --- array of arrays of the number of non-zero values within each cell
            numdat2 --- number of non-zero values in the database
    """
#
#--- open input file containing solar wind data
#
#    if ispeci == 1:
#        ifile = mdat_dir + 'MSheath_Kp_PROT.ASC'
#    elif ispeci == 2:
#        ifile = mdat_dir + 'MSheath_Kp_HEL.ASC'
#    elif ispeci == 3:
#        ifile = mdat_dir + 'MSheath_Kp_CNO.ASC'

    ifile = mdat_dir + 'msheath_short.asc'

    if not os.path.isfile(ifile):
        print("No data file found: msheath_short.asc")
        exit(1)

    return read_init_data_file(ifile, 0)

#----------------------------------------------------------------------------
#-- swinit: opens the crm solar wind database file and initializes the datarrays
#----------------------------------------------------------------------------

def swinit(ispeci):
    """
    this routine opens the crm solar wind database file and
    initializes the datarrays stored in the common block.
    
    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    output: xflux1  --- array of arrays of containing the x-coordinate of each data cell's center (re)
            yflux1  --- array of arrays of containing the y-coordinate of each data cell's center (re)
            zflux1  --- array of arrays of containing the z-coordinate of each data cell's center (re)
            flxbin1 --- array of arrays of the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin1 --- array of arrays of the number of non-zero values within each cell
            numdat1 --- number of non-zero values in the database
    """
#
#--- open input file containing solar wind data
#
#    if ispeci == 1:
#        ifile = mdat_dir + 'SolWind_Kp_PROT.ASC'
#    elif ispeci == 2:
#        ifile = mdat_dir + 'SolWind_Kp_HEL.ASC'
#    elif ispeci == 3:
#        ifile = mdat_dir + 'SolWind_Kp_CNO.ASC'

    ifile = mdat_dir + 'solwin_short.asc'

    if not os.path.isfile(ifile):
        print("No data file found: solwind_short.asc")
        exit(1)

    return read_init_data_file(ifile, 0)

#----------------------------------------------------------------------------
#-- read_init_data_file(ifile): read input ascii file and initialize the datarrays
#----------------------------------------------------------------------------

def read_init_data_file(ifile, iset=1):
    """
    read input ascii file and initialize the datarrays
    input:  ifile   --- data file name
            iset    --- if > 0, create imapindx
    output: xflux   --- array of arrays of containing the x-coordinate of each data cell's center (re)
            yflux   --- array of arrays of containing the y-coordinate of each data cell's center (re)
            zflux   --- array of arrays of containing the z-coordinate of each data cell's center (re)
            flxbin  --- array of arrays of the average ion flux within each cell  (ions/[cm^2-sec-sr-mev])
            numbin  --- array of arrays of the number of non-zero values within each cell
            Note: sub arrays have different length and you cannot apply noraml numpy operation
            numdat  --- number of non-zero values in the database
            imapindx--- array of pointers to flux database (if iset ==), this is not created)
    """
#
#--- read data file
#
    data = mcf.read_data_file(ifile)
#
#--- initialize
#
    xflux  = []
    yflux  = []
    zflux  = []
    flxbin = []
    numbin = []
    numdat = []
    if iset > 0:
        imapindx = numpy.full((maxkp, maxnum, maxnum, maxnum), -9999, int)
#
#--- the data lists are created for each kp values between 1 and 9 (0 - 8 columns)
#
    for k in range(0, maxkp):
        xflux.append([])
        yflux.append([])
        zflux.append([])
        flxbin.append([])
        numbin.append([])
        numdat.append(0)

    for ent in data:
        atemp = re.split('\s+', ent)
        if len(atemp) != 24:
            continue

        if mcf.is_neumeric(atemp[0]):
#
#--- index in the data file starts from 1. change it to start from 0
#
            xidx = int(float(atemp[0])) -1
            yidx = int(float(atemp[1])) -1
            zidx = int(float(atemp[2])) -1
            xpos = float(atemp[3])
            ypos = float(atemp[4])
            zpos = float(atemp[5])
#
#--- in the table, flxbin data are from column 6 to 14 and numbin1 data are from 15 to 23 
#--- (column start from 0) maxkp columns each
#
            for k in range(0, maxkp):
                fval = float(atemp[6+k])
                nval = int(float(atemp[15+k]))

                if nval > 0:
                    xflux[k].append(xpos)
                    yflux[k].append(ypos)
                    zflux[k].append(zpos)
                    flxbin[k].append(fval)
                    numbin[k].append(nval)

                    if iset > 0:
                        imapindx[k][xidx][yidx][zidx] = int(numdat[k])

                    numdat[k] += 1
#
#--- since the lists in the lists are all different length, we need to handle 
#--- separately to convert into an array
#
    xflux   = numpy.array([numpy.array(xi) for xi in xflux])
    yflux   = numpy.array([numpy.array(xi) for xi in yflux])
    zflux   = numpy.array([numpy.array(xi) for xi in zflux])
    flxbin  = numpy.array([numpy.array(xi) for xi in flxbin])
    numbin  = numpy.array([numpy.array(xi).astype(int) for xi in numbin])
    numdat  = numpy.array(numdat)

    if iset  > 0:
        return xflux, yflux, zflux, flxbin, numbin, numdat, imapindx
    else:
        return xflux, yflux, zflux, flxbin, numbin, numdat
         
#----------------------------------------------------------------------------
#-- locreg: determines which phenomenological region the spacecraft is in  --
#----------------------------------------------------------------------------

def locreg( xkp, xgsm, ygsm, zgsm):
    """
    this routine determines which phenomenological region the
    spacecraft is in.
    
    input:  xkp     --- kp index (real value between 0 & 9).
            xgsm    --- satellite's x-coordinate (re).
            ygsm    --- satellite's y-coordinate (re).
            zgsm    --- satellite's z-coordinate (re).
         
    output: xtail   --- satellite's x-coordinate in geotail system (re).
            ytail   --- satellite's y-coordinate in geotail system (re).
            ztail   --- satellite's z-coordinate in geotail system (re).
            idloc   --- phenomenogical region location identification flag:
                        idloc = 1 if spacecraft is in solar wind
                        idloc = 2 if spacecraft is in magnetosheath
                        idloc = 3 if spacecraft is in magnetosphere
    """
#
#--- set the region identification flag to "no region
#
    idloc = 0
#
#--- get the solar wind parameters used as inputs for the bow shock
#--- and magnetopause boundary models for this value of kp
#
    [bx,by,bz,vx,vy,vz,dennum,swetemp,swptemp,hefrac,swhtemp,bowang,dypres,abang,xhinge]\
                    = solwind(xkp)
#
#--- transform the spacecraft's coordinates to a system aligned with the geotail
#
#--- rotate the bow shock by the aberration angle
#
    angrad        = -abang * 0.01745329252
    [xtail,ytail] = rot8ang(angrad,xgsm,ygsm,xhinge)
    ztail         = zgsm
#
#--- determine if the spacecraft is inside the magnetosphere.  use the
#--- tsyganenko magnetopause model
#
    vel = -1
    xmgp,ymgp,zmgp,dist,xid = locate(dypres,vel,xtail,ytail,ztail)
#
#--- the spacecraft is inside the magnetosphere
#
    if xid == 1:
        idloc = 3
#
#--- determine if the spacecraft is in either the solar wind or
#--- the magnetosheath.  calculate the bow shock radius at this point
#
    else:
        radbs = bowshk2(bx,by,bz,vx,vy,vz,dennum,swetemp,swptemp,hefrac,swhtemp,xtail,bowang)
#
#--- find the distance of the spacecraft from the aberrated x-axi
#
        distsc = math.sqrt(ytail**2 + ztail**2)
#
#--- the spacecraft is in the magnetosheath
#
        if distsc <= radbs:
            idloc = 2
#
#--- the spacecraft is in the solar wind
#
        else:
            idloc = 1

    return xtail, ytail, ztail, idloc

#----------------------------------------------------------------------------
#-- bowshk2: give the bow shock radius, at a given x                      ---
#----------------------------------------------------------------------------

def bowshk2( bx, by, bz, vx, vy, vz, dennum, swetemp, swptemp,  hefrac, swhtemp, xpos, bowang):
    """
    this routine is designed to give the bow shock radius, at a
    given x, of the bow shock for any solar wind conditions.
    
    
    references:
    this routine is adpated from the paper by l. bennet et.al.,
    "a model of the earth's distant bow shock."  this paper was
    to be published in the journal of geophysical research, 1997.
    their source code was obtained from their web site at:
    http://www.igpp.ucla.edu/galileo/newmodel.htm
    
    this routine has been optimized for the simulation.
    
    inputs  bx      --- the imf b_x [nt]
            by      --- the imf b_y [nt]
            bz      --- the imf b_z [nt]
            vx      --- the imf v_x [km/s]
            vy      --- the imf v_y [km/s]
            vz      --- the imf v_z [km/s]
            dennum  --- the solar wind proton number density [#/cm^3]
            swetemp --- the solar wind electron temperature [k]
            swptemp --- the solar wind proton temperature [k]
            hefrac  --- fraction of solar wind ions which are helium ions
            swhtemp --- the temperature of the helium [k]
            xpos    --- down tail distance cross section is calculated [re]
            bowang  --- angle bow shock radius calculated (rad).
    
    output: bowrad  --- updated cylindrical radius (re).

    """
#
#--- convert the temperature from kelvins to ev
#
    etemp  = swetemp / 11600.
    ptemp  = swptemp / 11600.
    hetemp = swhtemp / 11600.
    dpr    = 6.2832  / 360.0
    rade   = 6378.0
    pi     = 4.0 * math.atan(1.0)
    gamma  = 5.0 / 3.0
#
#--- parameters that specify the shape of the base model
#--- of the bow shock.  the model has the form
#--- rho**2 = a*x**2 -b*x + c.
#---
#--- the parameters are for the greenstadt etal. 1990 model
#--- (grl, vol 17, p 753, 1990)
#
    xl = 22.073117134
    x0 =  3.493725046
    xn = 14.422071657
#
#--- here the eccentricity of the base model is adjusted.  see 
#--- the paper for an explanation
#
    eps = 1.0040
#
#--- calculate new paramaters for cylindrical shock model after
#--- adjustment of eccentricity.
#
#--- calculate parameters of interest
#
    btotcgs = math.sqrt(bx * bx + by * by + bz * bz) * 1.e-5    #--- btot in cgs units
    btot    = btotcgs * 1.e+5                                   #--- btot in mks units
    vtot    = math.sqrt(vx * vx + vy * vy + vz * vz) * 1.e+5    #--- vtot in cm/sec
    vtot1   = math.sqrt(vx * vx + vy * vy + vz * vz)            #--- vtot in km/sec
#
#--- the following definitions of v_a and c_s are taken from
#--- slavin & holzer jgr dec 1981
#
    v_a   = btotcgs / math.sqrt(4.0 * pi * dennum * 1.67e-24 * (1.0 + hefrac * 4.0)) 
    pres1 = dennum * ((1.0 + hefrac * 2.0) * etemp + (1 + hefrac * hetemp) * ptemp) * 1.602e-12
    c_s   = math.sqrt(2.0 * pres1 / (dennum * 1.67e-24 * (1.0 + hefrac * 4.0)))
#
#--- calculate mach numbers
#
#--- m_f is the fast magnetosonic speed for theta_bn = 90 degrees
#
    m_a = vtot / v_a
    m_s = vtot / c_s
    m_f = vtot / math.sqrt(v_a * v_a + c_s * c_s)
#
#--- this is the modification for the change in the bow shock due
#--- to changing solar wind dynamic pressure
#
#--- average values of number density and solar wind velocity
#
    xnave =  7.0
    vave = 430.0
#
#--- fracpres is the fraction by which all length scales in the
#--- bow shock model will change due to the change in the sola
#--- wind dynamic pressure
#
    fracpres = ((xnave * vave * vave) / (dennum * vtot1 * vtot1))**(1.0/6.0)

    xn1 = xn * fracpres
    x0  = x0 * fracpres
    xl  = xl * fracpres
#
#--- calculate yet again the parameters for the updated model
#
    a = eps * eps -1
    b = 2.0 * eps * xl + 2.0 *( eps * eps -1) * x0
    c = xl * xl + 2.0 * eps * xl * x0 + (eps * eps -1) * x0 * x0
#
#--- calculate shock with correct pressure
#
    xtemp = a * xpos**2 - b * xpos + c
    if xtemp < 0:
        rho2 = 0
    else:
        rho2 = math.sqrt(xtemp)
#
#--- modify the bow shock for the change in flaring due to the
#--- change in local magnetosonic mach number
#
#--- first calculate the flaring angle for average solar wind conditions
#
    ave_ma   = 9.4
    ave_ms   = 7.2
    vwin_ave = 430.0*1.e+5
    va_ave   = vwin_ave / ave_ma
    vs_ave   = vwin_ave / ave_ms
    bxave    = -3
    byave    =  3
    bzave    =  0

    vms      = math.sqrt(0.5 * ((va_ave**2 + vs_ave**2) \
                + math.sqrt((va_ave**2  + vs_ave**2)**2 \
                - 4.0 * va_ave**2 * vs_ave**2 *(math.cos(45 * dpr)**2))))

    ave_mf   = vwin_ave / vms
    thet2    = math.asin(1.0 / ave_mf)
#
#--- now calculate the cylindrical radius, and the y and z coordinates,
#--- of the shock for the angle bowang around the tail axis for a given
#--- xpos.  note that bowang is 0 along the positive z axis
#--- (bowang/dpr is the angle about the tail axis in degrees,
#--- rhox is the updated cylindrical radius of the prevailing bow
#--- shock at downtail distance xpos in earth radii.
#
    vms      = fast(bx,by,bz,v_a,c_s,vtot,bowang)

    m_f      = vtot / vms
    thet1    = math.asin(1.0 / m_f)
    xtemp1   = xn1 - xpos
    rhox     = rho2 + xtemp1 * (math.tan(thet1) - math.tan(thet2))
    bowrad   = rhox

    return bowrad

#----------------------------------------------------------------------------
#-- fast: local fast magnetosonic speed                                    --
#----------------------------------------------------------------------------

def fast( bx, by, bz, va, vs, v0, alp):
    """
    local fast magnetosonic speed

    it uses the simple bisection method to solve the equations.
    accuracy to 0.01 in v_ms is good enough 
    
        this routine is adpated from the paper by l. bennet et.al.,
        "a model of the earth's distant bow shock."  this paper was
        to be published in the journal of geophysical research, 1997.
        this source code is from their web site at:
        http://www.igpp.ucla.edu/galileo/newmodel.htm
    """
    dpr  = 6.2832/360.0
    btot = math.sqrt(bx * bx + by * by + bz * bz)
    vx   = 1
    va1  = va / 1.0e5
    vs1  = vs / 1.0e5
    v01  = v0 / 1.0e5

    func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)

    step1 = 2.0
    step2 = 0.1
    step3 = 0.01

    if func > 0:
        while func > 0:
            vx += step1
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func <= 0:
                break

        while func < 0:
            vx -= step2
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func >= 0:
                break

        while func > 0:
            vx += step3
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func <= 0:
                break

    elif func < 0:
        while func < 0:
            vx += step1
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func >= 0:
                break

        while func > 0:
            vx -= step2
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func <= 0:
                break

        while func < 0:
            vx += step3
            func = fast_func(bx, by, bz, alp, btot, vx, va1, vs1, v01)
            if func >= 0:
                break

    vy    = math.sin(alp) * math.sqrt(v01 * vx - vx**2)
    vz    = math.cos(alp) * math.sqrt(v01 * vx - vx**2)

    angle = math.acos((bx * vx + by * vy + bz * vz)\
                      /(math.sqrt(bx * bx + by * by + bz * bz) \
                      * math.sqrt(vx * vx + vy * vy + vz * vz)))

    vms   = 1.0e5 * math.sqrt(vx * vx + vy * vy + vz * vz)

    return vms

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def fast_func( bx,  by,  bz,  alp, btot,  vx,  va1,  vs1,  v01):

    out  = va1**2 + vs1**2 - 2.0 * v01 * vx + math.sqrt((va1**2 + vs1**2)**2         \
           - 4.0 *va1**2 * vs1**2 * (vx * bx + by * math.sin(alp) * math.sqrt(v01*vx \
           - vx**2) + bz * math.cos(alp) * math.sqrt(v01*vx                          \
           - vx**2))**2 / (btot**2 *v01 * vx))

    return out

#----------------------------------------------------------------------------
#-- locate: defines the position of a point  at the model magnetopause      -
#----------------------------------------------------------------------------

def locate( xn_pd, vel, xgsm, ygsm, zgsm):
    """
    this subroutine defines the position of a point (xmgnp,ymgnp,zmgnp)
    at the model magnetopause, closest to a given point of space
    (xgsm,ygsm,zgsm),   and the distance between them (dist)
    
     nput:  xn_pd --- either solar wind proton number density (per c.c.) (if vel>0)
                      or the solar wind ram pressure in nanopascals   (if vel<0)
            vel   --- either solar wind velocity (km/sec)
                      or any negative number, which indicates that xn_pd stands
                      for the solar wind pressure, rather than for the density
    
            xgsm,ygsm,zgsm - coordinates of the observation point in earth radii
    
    output: xmgnp,ymgnp,zmgnp - coordinates of a point at the magnetopause,
                                closest to the point  xgsm,ygsm,zgsm
            dist  ---  the distance between the above two points, in re,
            xid   ---  indicator; id=+1 and id=-1 mean that the point
                       (xgsm,ygsm,zgsm)  lies inside or outside
                       the model magnetopause, respectively
    
    the pressure-dependent magnetopause is that used in the t96_01 model
    coded by:  n.a. tsyganenko, aug.1, 1995;  revised  june 22, 1996

    """
#
#--- pd is the solar wind dynamic pressure (in nanopascals)
#
    if vel < 0.0:
        pd = xn_pd
    else:
        pd = 1.94e-6 * xn_pd * vel**2
#
#--- ratio of pd to the average pressure, assumed as 2 npa
#
    rat   = pd / 2.0
#
#--- the power in the scaling factor is the best-fit value
#--- obtained from data in the t96_01 version of the model
#
    rat16 = rat**0.14
#
#--- values of the magnetopause parameters for  pd = 2 npa are:
#---   a0    = 70.00 /   s00   =  1.08 /   x00   =  5.48
#--- values of the magnetopause parameters, scaled to the actual pressure
#
    a     = 70.0 / rat16
    s0    = 1.08
    x0    = 5.48 / rat16
#
#--- this is the x-coordinate of the "seam" between the ellipsoid and the cylinder
#
    xm    = x0 - a
#
#--- (for details on the ellipsoidal coordinates, see the paper:
#--- n.a.tsyganenko, solution of chapman-ferraro problem for an
#--- ellipsoidal magnetopause, planet.space sci., v.37, p.1037, 1989)
#
    if (ygsm != 0.0) or (zgsm != 0.0):
        phi = math.atan2(ygsm,zgsm)
    else:
        phi = 0.0

    rho = math.sqrt(ygsm**2 + zgsm**2)

    if xgsm < xm:
#
#--- calculate (x,y,z) for the closest point at the magnetopause
#
        xmgnp   = xgsm
        rhomgnp = a * math.sqrt(s0**2 - 1)
        ymgnp   = rhomgnp * math.sin(phi)
        zmgnp   = rhomgnp * math.cos(phi)
#
#--- xid=-1 means that the point lies outside the magnetosphere
#--- xid=+1 means that the point lies inside  the magnetosphere
#
        xid     = 0
        if rhomgnp > rho:
            xid =  1
        elif rhomgnp < rho:
            xid = -1

    else:
        xksi  = (xgsm - x0) / a + 1.0
        xdzt  = rho / a
        sq1   = math.sqrt((1.0 + xksi)**2 + xdzt**2)
        sq2   = math.sqrt((1.0 - xksi)**2 + xdzt**2)
        sigma = 0.5 * (sq1 + sq2)
        tau   = 0.5 * (sq1 - sq2)
#
#--- calculate (x,y,z) for the closest point at the magnetopause
#
        xmgnp   = x0 - a * (1.0 - s0 * tau)
        rhomgnp = a * math.sqrt((s0**2 - 1.0)*(1.0 - tau**2))
        ymgnp   = rhomgnp * math.sin(phi)
        zmgnp   = rhomgnp * math.cos(phi)
#
#--- xid=-1 means that the point lies outside the magnetosphere
#--- xid=+1 means that the point lies inside  the magnetosphere
#
        xid = 0
        if sigma > s0:
            xid = -1
        elif sigma < s0:
            xid =  1
#
#--- calculate the shortest distance between the point xgsm,ygsm,zgsm and the magnetopause
#
    dist = compute_rng(xgsm, ygsm, zgsm, xmgnp, ymgnp, zmgnp)

    return xmgnp, ymgnp, zmgnp, dist, xid

#----------------------------------------------------------------------------
#-- mapsphere: finds the (i,j,k) index offset values                      ---
#----------------------------------------------------------------------------

def mapsphere(distmapmax,xinc,yinc,zinc):
    """
    this routine finds the (i,j,k) index offset values which are
    used to define the search volume for the near-neighbor flux
    search.
    
    input:  distmapmax --- maximum distance from flux measurement location
                            allowed for streamline mapping (re).
            xinc       --- extent of database cell in x-direction (re).
            yinc       --- extent of database cell in y-direction (re).
            zinc       --- extent of database cell in z-direction (re).
    
    output: nsphvol    --- number of volume elements stored in the
                            database search volume.
            ioffset    --- array of offset indices for x-direction.
            joffset    --- array of offset indices for y-direction.
            koffset    --- array of offset indices for z-direction.
    
    *** note *** the indices are sorted by range from the center of
    the spherical search volume (ascending order on range).

    """
#
#--- get the number of volume bins that extends 1/2 the length
#--- of each side of the cube which contains the spherical search
#--- volume defined by distmapmax
#
    istep   = int(distmapmax / xinc)
    jstep   = int(distmapmax / yinc)
    kstep   = int(distmapmax / zinc)
#
#--- store the index offset values for each volume element that
#--- lies within the search volume sphere
#
    istart    = -istep
    jstart    = -jstep
    kstart    = -kstep
    istop     =  istep + 1
    jstop     =  jstep + 1
    kstop     =  kstep + 1

    rngoffset = numpy.zeros(maxnsphvol)
    ioffset   = numpy.zeros(maxnsphvol).astype(int)
    joffset   = numpy.zeros(maxnsphvol).astype(int)
    koffset   = numpy.zeros(maxnsphvol).astype(int)
    nsphvol   =0

    for i in range(istart, istop):
        for j in range(jstart, jstop):
            for k in range(kstart, kstop):
#
#--- calculate the distance of this volume element from the
#--- search volume's central volume element
#
                xrng = i * xinc
                yrng = j * yinc
                zrng = k * zinc
                dist = math.sqrt(xrng**2 + yrng**2 + zrng**2)
#
#--- store this volume element's indices as part of the spherical search volume
#
                if dist <= distmapmax:
                    rngoffset[nsphvol] = dist
                    ioffset[nsphvol] = i
                    joffset[nsphvol] = j
                    koffset[nsphvol] = k
                    nsphvol += 1
#
#--- sort the offset index arrays in ascending by geocentric range
#--- from the center of the search volume
#
    rngoffset  = rngoffset[:nsphvol]
    ioffset    = ioffset[:nsphvol]
    joffset    = joffset[:nsphvol]
    koffset    = koffset[:nsphvol]
    [rngoffset, ioffset, joffset, koffset] =\
                    sort_multi_lists([rngoffset, ioffset, joffset, koffset])

    return nsphvol, ioffset, joffset, koffset

#----------------------------------------------------------------------------
#-- msheflx:  provides the magnetosheath ion flux as a function of kp      --
#----------------------------------------------------------------------------

def msheflx(xkp,ispeci):
    """
    this routine provides the magnetosheath ion flux as a function of kp.
    
    input:  xkp     --- kp index (real value between 0 & 9).
            ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    
    output: fluxmn  --- mean flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux95  --- 95% flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux50  --- 50% flux (#/[cm^2-sec-sr-mev]) for selected species.
            fluxsd  --- standard deviation of flux for selected species.
    """
#
#--- provide proton flux value
#
    if ispeci == 1:
        if xkp <= 4.5:
            fluxmn = 7.161418e-3 * xkp**2 + 2.831376e-1 * xkp + 2.57324
        else:
            fluxmn = 2.28935e-1  * xkp    + 2.94481

        flux95 = math.exp(1.227335) * xkp**2.076779e-1
        flux50 = 6.674753e-3 * xkp**3 - 9.069930e-2 * xkp**2 + 6.807628e-1 * xkp + 1.231926
        fluxsd = 1.347388e-1 * xkp + 3.67163

        fluxmn = 10**fluxmn
        flux95 = 10**flux95
        flux50 = 10**flux50
        fluxsd = 10**fluxsd
#
#--- provide helium flux values
#
    elif ispeci == 2:
        fluxmn = -1.e-11
        flux95 = -1.e-11
        flux50 = -1.e-11
        fluxsd = -1.e-11
#
#--- provide cno flux values
#
    elif ispeci == 3:
        fluxmn = -1.e-11
        flux95 = -1.e-11
        flux50 = -1.e-11
        fluxsd = -1.e-11

    return fluxmn, flux95, flux50, fluxsd

#----------------------------------------------------------------------------
#-- nbrflux: provides the region's ion flux as a function of kp            --
#----------------------------------------------------------------------------

def nbrflux(xkp,nsectrs,sectx,secty,scmean,sc95,sc50,scsig,xtail,ytail,ztail,\
            numdat,xflux,yflux,zflux,fluxbin,numbin,smooth1,nflxget,ndrophi,\
            ndroplo,logflg,rngtol,fpchi,fpclo):
    """
    this routine provides the region's ion flux as a function of kp.

    inputs: xkp     --- kp index (real value between 0 & 9).
            nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor.
            xtail   --- satellite's x-coordinate in geotail system (re).
            ytail   --- satellite's y-coordinate in geotail system (re).
            ztail   --- satellite's z-coordinate in geotail system (re).
            numdat  --- number of non-zero values in the database.
            xflux   --- array containing the x-coordinate of each data
                        cell's center  (re).
            yflux   --- array containing the y-coordinate of each data
                        cell's center  (re).
            zflux   --- array containing the z-coordinate of each data
                        cell's center  (re).
            fluxbin --- array containing the average ion flux within
                        each cell  (ions/[cm^2-sec-sr-mev]).
            numbin  --- array containing the number of non-zero values within
                        each cell.
            smooth1 --- flag for control of database smoothing filter:
                        smooth1 = 0 if no data smoothing is used.
                        smooth1 = 1 if spike rejection and near neighbor flux.
                        smooth1 = 2 if spike rejection with range weighted
                                    scaling of flux.
                        smooth1 = 3 if spike rejection with average flux.
                        smooth1 = 4 if spatial average of flux in volume
                                    specified by rngtol.
                        smooth1 = 5 if spatial average of flux in volume
                                    specified by rngtol, with the specified
                                    number of high and low flux values inside
                                    the volume dropped first.
                        smooth1 = 6 if spatial averaging of flux in volume
                                    specified by rngtol, with percentile
                                    threshold limits on flux values.
            MTA uses only smooth1 == 4 case:
            nflxget --- number of flux values to get for smoothing filter
                        (used if smooth1 = 1,2, or 3)
            ndrophi --- number of high flux values to drop for smoothing
                        filter (used if smooth1 = 1,2,3, or 5).
            ndroplo --- number of low flux values to drop for smoothing
                        filter (used if smooth1 = 1,2,3, or 5).
            logflg  --- flag controlling how flux average is performed
                        (used if smooth1 = 2,3,4,5, or 6).
                        logflg = 1 if log10 of flux values used.
                        logflg = 2 if linear flux values used.
            rngtol  --- range tolerance from near-neigbor used in spatial
                        averaging of database (re)
                        (used if smooth1 = 4,5, or 6).
            fpchi   --- upper percentile limit for spatial averaging of flux
                        (used if smooth1 = 6).
            fpclo   --- lower percentile limit for spatial averaging of flux
                        (used if smooth1 = 6).

    output: fluxmn  --- mean flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux95  --- 95% flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux50  --- 50% flux (#/[cm^2-sec-sr-mev]) for selected species.
            fluxsd  --- standard deviation of flux for selected species.
    """
#
#--- set a couple of parameters
#
#    rnggeo  = 6.0
#    numscal = 2
#
#--- do not allow for calculations to take place inside the minimum
#--- sphere, which is needed because of geotail's orbit
#
    rngck = math.sqrt(xtail**2 + ytail**2 + ztail**2)

    if rngck < 6.0:
        fluxmn = 0.
        flux95 = 0.
        flux50 = 0.
        fluxsd = 0.

        return fluxmn, flux95, flux50, fluxsd
#
#--- rank order the kp scaling sectors on the basis of their range
#--- from the satellite in the xy-plan
#
    indsect, rngsect = neighbr(xtail, ytail, sectx, secty)
#
#--- calculate the distance weighted sum of the kp scaling factors
#
    wtmean, wt95, wt50, wtsig = \
            wtscal(2,indsect,rngsect,scmean,sc95,sc50,scsig)
#
#--- find the near-neighbor flux data cell for each kp interval.
#--- these flux values are treated as the average flux at the center
#--- their respective kp intervals.
#
#--- fix the range tolerance for the near-neighbor flux calculation
#
    rngchk  = 1.0
    flux    = numpy.zeros(maxkp)
    avgnum  = numpy.zeros(maxkp)
    rngcell = numpy.zeros(maxkp)
    numcell = numpy.zeros(maxkp)
    tarr    = numpy.zeros(maxcell)
    cdef double [:] flxsto =  copy.deepcopy(tarr)
    cdef double [:] numsto =  copy.deepcopy(tarr)
#
#--- set z range
#   
    zcklo, zckhi = zbinner(xtail, ztail)

    for i in range(0, maxkp):
#
#--- calculate the flux with no data smoothing or with spatial
#--- averaging inside the volume defined by rngtol
#
        flux[i],avgnum[i],rngcell[i],numcell[i] = \
                                flxdat1(xtail, ytail, ztail, numdat[i],\
                                        xflux[i], yflux[i], zflux[i],\
                                        fluxbin[i], numbin[i], rngchk,\
                                        flxsto, numsto, zcklo, zckhi)
#
#--- find the minimum distance to a data cell from any one of the database's kp intervals
#
    rng1 = min(rngcell)
#
#--- get the weighted sum (average) of all of the useable flux values
#--- that lie within the specified range tolerance above the minimum
#--- range. get the flux statistics by multiplying the average flux
#--- value at the spacecraft's location by the distance weighted sum
#--- of the kp scaling factors
#
#
#--- spatial averaging is used
#
    if smooth1 in [4, 5, 6]:
        rngchk = rngtol
#
#--- there is no data smoothing used
#
    else:
        rngchk = 1.0

    rng2 = rng1 + rngchk

    idx    = rngcell <= rng2
    fluxmn = numpy.sum(flux[idx] * avgnum[idx] * wtmean[idx])
    flux95 = numpy.sum(flux[idx] * avgnum[idx] * wt95[idx])
    flux50 = numpy.sum(flux[idx] * avgnum[idx] * wt50[idx])
    fluxsd = numpy.sum(flux[idx] * avgnum[idx] * wtsig[idx])
    totnum = numpy.sum(avgnum[idx])

    if totnum < 1.0:
        totnum = 1.0

    fluxmn = fluxmn / totnum
    flux95 = flux95 / totnum
    flux50 = flux50 / totnum
    fluxsd = fluxsd / totnum

    return fluxmn, flux95, flux50, fluxsd

#----------------------------------------------------------------------------
#-- flxdat1: finds the flux corresponding to the satellite's gsm position coordinate
#----------------------------------------------------------------------------

def flxdat1(double xgsm, double ygsm, double zgsm, long numdat,\
            double [:] xflux, double [:] yflux, double [:] zflux,\
            double [:] fluxbin, long [:] numbin, double rngchk,\
            double [:] flxsto, double [:] numsto, int zcklo, int zckhi):
    """
    this routine finds the flux corresponding to the satellite's
    gsm position coordinates by use of the geotail database.
    
    this routine is used if no data smoothing is selected or if
    spatial averaging within the volume defined by rngchk is selected.
    
    input:  xgsm    --- satellite's x-coordinate (re).
            ygsm    --- satellite's y-coordinate (re).
            zgsm    --- satellite's z-coordinate (re).
            numdat  --- number of non-zero values in the database.
            xflux   --- array containing the x-coordinate of each data
                        cell's center  (re).
            yflux   --- array containing the y-coordinate of each data
                        cell's center  (re).
            zflux   --- array containing the z-coordinate of each data
                        cell's center  (re).
            fluxbin --- array containing the average ion flux within
                        each cell  (ions/[cm^2-sec-sr-mev]).
            numbin  --- array containing the number of non-zero values within
                        each cell.
            rngchk  --- the range tolerance variable (re).
            flxsto  --- array to save flxu value
            numsto  --- array to save data number of the cell
            zcklo   --- lower z value
            zckhi   --- upper z value

    output: flux    --- computed average flux value  (ions/[cm^2-sec-sr-mev]).
            avgnum  --- average number of flux values per cell used to get flux.
            rngcell --- distance to center of flux database cell used  (re).
            numcell --- number of flux database cells used that have the
                        same value of rngcell.
    """
    cdef double flux, avgnum, rngcell, rngdiff, rngabs
    cdef int    i, numcell

    rngcell = 1.0e25
    numcell = 0

    for i in range(0, numdat):
        if (fluxbin[i] > 1) and (zflux[i] > zcklo) and (zflux[i] <= zckhi):

            rng = compute_rng(xflux[i],yflux[i],zflux[i], xgsm, ygsm, zgsm)

            rngdiff = rng - rngcell
            rngabs  = abs(rngdiff)
#
#--- there is a new nearest neighbor data cell
#
            if (rngabs > rngchk) and (rngdiff < 0.0):
                numcell = 1
                rngcell = rng
                flxsto[0] = fluxbin[i]
                numsto[0] = numbin[i]
                
#
#--- there is a new data cell within the range
#--- tolerance to the nearest neighbor.  this cell's flux
#--- should be included in the average for this location
#
            elif rngabs <= rngchk:
                flxsto[numcell] = fluxbin[i]
                numsto[numcell] = numbin[i]
                numcell += 1

                if numcell > maxcell -1:
                    break
#
#--- use the average of the flux from all bins at the same distance
#
    if numcell > 0:
        flux   = numpy.mean(flxsto[:numcell])
        avgnum = numpy.mean(numsto[:numcell])
    else:
        flux   = 0.0
        avgnum = 0.0

    return flux, avgnum, rngcell, numcell

#----------------------------------------------------------------------------
#-- nbrflux_map_z:  provides the region's ion flux as a function of kp    ---
#----------------------------------------------------------------------------

def nbrflux_map_z(xkp,nsectrs,sectx,secty,scmean,sc95,sc50,scsig,xtail,ytail,\
                  ztail,numdat,xflux,yflux,zflux,fluxbin,numbin,smooth1,nflxget,\
                  ndrophi,ndroplo,logflg,rngtol,fpchi,fpclo,nsphvol,ioffset,\
                  joffset,koffset,imapindx):
    """
    this routine provides the region's ion flux as a function of kp.

    input:  xkp     --- kp index (real value between 0 & 9).
            nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor.
            xtail   --- satellite's x-coordinate in geotail system (re).
            ytail   --- satellite's y-coordinate in geotail system (re).
            ztail   --- satellite's z-coordinate in geotail system (re).
            numdat  --- number of non-zero values in the database.
            xflux   --- array containing the x-coordinate of each data
            yflux   --- array containing the y-coordinate of each data
                        cell's center  (re).
            zflux   --- array containing the z-coordinate of each data
                        cell's center  (re).
            fluxbin --- array containing the average ion flux within
                        each cell  (ions/[cm^2-sec-sr-mev]).
            numbin  ---  containing the number of non-zero values within
                        each cell.
            smooth1 --- flag for control of database smoothing filter:
                        smooth1 = 0 if no data smoothing is used.
                        smooth1 = 1 if spike rejection and near neighbor flux.
                        smooth1 = 2 if spike rejection with range weighted
                                    scaling of flux.
                        smooth1 = 3 if spike rejection with average flux.
                        smooth1 = 4 if spatial average of flux in volume
                                    specified by rngtol.
                        smooth1 = 5 if spatial average of flux in volume
                                    specified by rngtol, with the specified
                                    number of high and low flux values inside
                                    the volume dropped first.
                        smooth1 = 6 if spatial averaging of flux in volume
                                    specified by rngtol, with percentile
                                    threshold limits on flux values.
            nflxget  --- number of flux values to get for smoothing filter
                        (used if smooth1 = 1,2, or 3)
            ndrophi  --- number of high flux values to drop for smoothing
                        filter (used if smooth1 = 1,2,3, or 5).
            ndroplo  --- number of low flux values to drop for smoothing
                        filter (used if smooth1 = 1,2,3, or 5).
            logflg   --- flag controlling how flux average is performed
                        (used if smooth1 = 2,3,4,5, or 6).
                        logflg = 1 if log10 of flux values used.
                        logflg = 2 if linear flux values used.
            rngtol   --- range tolerance from near-neigbor used in spatial
                        averaging of database (re)
                        (used if smooth1 = 4,5, or 6).
            fpchi    --- upper percentile limit for spatial averaging of flux
                        (used if smooth1 = 6).
            fpclo    --- lower percentile limit for spatial averaging of flux
                        (used if smooth1 = 6).
            nsphvol  --- number of volume elements stored in the
                        streamline mapping search volume.
            ioffset  --- array of offset indices for x-direction.
            joffset  --- array of offset indices for y-direction.
            koffset  --- array of offset indices for z-direction.
            imapindx --- array of pointers for mapped database.
    
    output: fluxmn  --- mean flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux95  --- 95% flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux50  --- 50% flux (#/[cm^2-sec-sr-mev]) for selected species.
            fluxsd  --- standard deviation of flux for selected species.

    from param file --- maxpnt, maxnum, maxkp, blendx1, blendx2, maxcell, maxnsphvol
    """
#
#--- set a couple of parameters
#
    rnggeo  = 6.0
    numscal = 2
#
#--- do not allow for calculations to take place inside the minimum
#--- sphere, which is needed because of geotail's orbit
#
    rngck = math.sqrt(xtail**2 + ytail**2 + ztail**2)

    if rngck < rnggeo:
        fluxmn = 0.
        flux95 = 0.
        flux50 = 0.
        fluxsd = 0.

        return fluxmn, flux95, flux50, fluxsd
#
#--- rank order the kp scaling sectors on the basis of their range
#--- from the satellite in the xy-plan
#
    indsect, rngsect = neighbr(xtail, ytail, sectx, secty)
#
#--- calculate the distance weighted sum of the kp scaling factors
#
    wtmean, wt95, wt50, wtsig = wtscal(numscal,indsect,rngsect,scmean,sc95,sc50,scsig)
#
#--- find the near-neighbor flux data cell for each kp interval.
#--- these flux values are treated as the average flux at the center
#--- their respective kp intervals.
#
#--- fix the range tolerance for the near-neighbor flux calculation
#
#--- spatial averaging is used
#
    if smooth1 in [4, 5, 6]:
        rngchk = rngtol
#
#--- there is no data smoothing used
#
    else:
        rngchk = 1.0
#
#--- find the index for the current kp value
#
    ikp_good   = numpy.full(maxkp, False)
    flux       = numpy.zeros(maxkp)
    avgnum     = numpy.zeros(maxkp)
    rngcell    = numpy.zeros(maxkp)
    numcell    = numpy.zeros(maxkp)

    ikp_good_z = numpy.full(maxkp, False)
    flux_z     = numpy.zeros(maxkp)
    avgnum_z   = numpy.zeros(maxkp)
    rngcell_z  = numpy.zeros(maxkp)
    numcell_z  = numpy.zeros(maxkp)
#
#--- get the limits on z-values used to search for near-neighbors
#
    zcklo, zckhi = zbinner(xtail, ztail)
#
#--- calculate the index for this s/c position
#
    indx = int((xtail - xmin) / xinc)
    indy = int((ytail - ymin) / yinc)
    indz = int((ztail - zmin) / zinc)

    tarr    = numpy.zeros(maxcell)
    cdef double [:] flxsto = tarr 
    tarr    = numpy.zeros(maxcell).astype(int)
    cdef long [:]   numsto  = tarr

    for ikp in range(2, 7):
#
#--- calculate the flux with no data smoothing or with spatial
#--- averaging inside the volume defined by rngtol
#
#
#--- no z-layers
#
        if xtail >= blendx2:
            flux[ikp],avgnum[ikp],rngcell[ikp], numcell[ikp] = \
                                flxdat1_map(xtail,ytail,ztail,numdat[ikp],xflux[ikp],\
                                            yflux[ikp], zflux[ikp],fluxbin[ikp],\
                                            numbin[ikp],rngchk,nsphvol,ioffset,\
                                            joffset,koffset,imapindx[ikp],\
                                            flxsto, numsto, indx, indy, indz,\
                                            zcklo, zckhi, zchk=0)
#
#--- if numcell == 0, do not include this calculation in the statistics.
#
            if numcell[ikp] == 0:
                ikp_good[ikp] = False
            else:
                ikp_good[ikp] = True
#
#--- use z-layers
#
        if xtail <= blendx1:
            flux_z[ikp],avgnum_z[ikp],rngcell_z[ikp], numcell_z[ikp] = \
                                flxdat1_map(xtail,ytail,ztail,numdat[ikp],xflux[ikp],
                                            yflux[ikp],zflux[ikp],fluxbin[ikp],\
                                            numbin[ikp],rngchk,nsphvol,ioffset,\
                                            joffset,koffset,imapindx[ikp],\
                                            flxsto, numsto, indx, indy, indz,\
                                            zcklo, zckhi, zchk=1)
#
#--- if numcell == 0, do not include this calculation in the statistics.
#
            if numcell_z[ikp] == 0:
                ikp_good_z[ikp] = False
            else:
                ikp_good_z[ikp] = True
#
#--- find the minimum distance to a data cell from any one of the database's kp intervals
#
    rng1     = 1.e+20
    for ikp in range(2, 7):
        if (rng1 >= rngcell[ikp]) and ikp_good[ikp]:
            rng1 = rngcell[ikp]
    deltarng = 0.2
    rng2     = rng1 + deltarng
#
#--- get the weighted sum (average) of all of the useable flux values
#--- that lie within the specified range tolerance above the minimum
#--- range. get the flux statistics by multiplying the average flux
#--- value at the spacecraft's location by the distance weighted sum
#--- of the kp scaling factors.
#
#--- ***** calculate the flux values without z-binning *****
#--- *****        of near-neighbor flux values.        *****
#
    idx     = (rngcell <= rng2) & (ikp_good)
    anndist = numpy.sum(rngcell[idx] * avgnum[idx])
    fluxmn1 = numpy.sum(flux[idx]    * avgnum[idx] * wtmean[idx])
    flux951 = numpy.sum(flux[idx]    * avgnum[idx] * wt95[idx])
    flux501 = numpy.sum(flux[idx]    * avgnum[idx] * wt50[idx])
    fluxsd1 = numpy.sum(flux[idx]    * avgnum[idx] * wtsig[idx])
    totnum1 = numpy.sum(avgnum[idx])

    if totnum1 < 1.0: 
        totnum1 = 1.0
    anndist = anndist / totnum1
    fluxmn1 = fluxmn1 / totnum1
    flux951 = flux951 / totnum1
    flux501 = flux501 / totnum1
    fluxsd1 = fluxsd1 / totnum1
#
#--- ***** calculate the flux values with z-binning    *****
#--- *****        of near-neighbor flux values.        *****
#
#--- find the minimum distance to a data cell from any one of the 
#--- database's kp intervals
#
    try:
        rng1 = numpy.min(rngcell_z[ikp_good_z])
    except:
        rng1     = 1.e+20

    deltarng = 0.2
    rng2     = rng1 + deltarng

    idx     = (rngcell_z <= rng2) & (ikp_good_z)
    anndist = numpy.sum(rngcell_z[idx] * avgnum_z[idx])
    fluxmn2 = numpy.sum(flux_z[idx]    * avgnum_z[idx] * wtmean[idx])
    flux952 = numpy.sum(flux_z[idx]    * avgnum_z[idx] * wt95[idx])
    flux502 = numpy.sum(flux_z[idx]    * avgnum_z[idx] * wt50[idx])
    fluxsd2 = numpy.sum(flux_z[idx]    * avgnum_z[idx] * wtsig[idx])
    totnum2 = numpy.sum(avgnum_z[idx])

    if totnum2 < 1.0: 
        totnum2 = 1.0
    anndist = anndist / totnum2
    fluxmn2 = fluxmn2 / totnum2
    flux952 = flux952 / totnum2
    flux502 = flux502 / totnum2
    fluxsd2 = fluxsd2 / totnum2

#
#--- ***** perform the blending of the flux values from *****
#--- ***** the two near-neighbor algorithms.            *****
#
#--- find the relative weighting of the two flux values.
#
#--- do not use z-layers to find the near-neighbor flux
#
    if xtail >= blendx1:
        blend1 = 1.0
        blend2 = 0.0
#
#--- only use z-layers to find the near-neighbor flux
#
    elif xtail <= blendx2:
        blend1 = 0.0
        blend2 = 1.0
#
#--- the spacecraft is in the transition (blending) region.
#
    else:
#
#--- interpolate to find blend1 value on xtail
#
        blend1 = y_interpolate(blendx1, 1.0, blendx2, 0.0, xtail, 1)
        if blend1 >= 1.0:
            blend1 = 1.0

        if blend1 <= 0.0:
            blend1 = 0.0

        blend2 = 1.0 - blend1
#
#--- get the final flux values
#
    fluxmn = fluxmn1 * blend1 + fluxmn2 * blend2
    flux95 = flux951 * blend1 + flux952 * blend2
    flux50 = flux501 * blend1 + flux502 * blend2
    fluxsd = fluxsd1 * blend1 + fluxsd2 * blend2

    return fluxmn, flux95, flux50, fluxsd

#----------------------------------------------------------------------------
#-- flxdat1_map:  finds the flux corresponding to the satellite's gsm position  
#----------------------------------------------------------------------------

def  flxdat1_map(double xgsm,double ygsm,double zgsm,\
                 long numdat,double [:] xflux,double [:] yflux, double [:] zflux,\
                 double [:] fluxbin,long [:]numbin, long rngchk, long nsphvol,\
                 long [:] ioffset,long [:] joffset,long [:] koffset, \
                 long [:,:,:]imapindx, double [:] flxsto, long [:] numsto, \
                 int indx, int indy, int indz,\
                 float zcklo, float zckhi,int zchk=0):
    """
    this routine finds the flux corresponding to the satellite's
    gsm position coordinates by use of the geotail database.
    
    this routine is used if no data smoothing is selected or if
    spatial averaging within the volume defined by rngchk is selected.
    
    this routine is used if the database has been populated by use
    of streamline mapping.
    
    input:  xgsm     --- satellite's x-coordinate (re).
            ygsm     --- satellite's y-coordinate (re).
            zgsm     --- satellite's z-coordinate (re).
            numdat   --- number of non-zero values in the database.
            xflux    --- array containing the x-coordinate of each data
                         cell's center  (re).
            yflux    --- array containing the y-coordinate of each data
                         cell's center  (re).
            zflux    --- array containing the z-coordinate of each data
                         cell's center  (re).
            fluxbin  --- array containing the average ion flux within
                         each cell  (ions/[cm^2-sec-sr-mev]).
            numbin   --- array containing the number of non-zero values within
                         each cell.
            rngchk   --- the range tolerance variable (re).
            nsphvol  --- number of volume elements stored in the
                         streamline mapping search volume.
            ioffset  --- array of offset indices for x-direction.
            joffset  --- array of offset indices for y-direction.
            koffset  --- array of offset indices for z-direction.
            imapindx --- array of pointers for mapped database.
            flxsto   --- array to save flxu value
            numsto   --- array to save data number of the cell
            indx     --- index of the center x coordinate
            indy     --- index of the center y coordinate
            indz     --- index of the center z coordinate

            zcklo    --- lower z flux value
            zckhi    --- upper z flux value
            zchk     --- indicator of whether to include z flux (> 0) or just x/y (==0)
    
    output: flux    --- computed average flux value  (ions/[cm^2-sec-sr-mev]).
            avgnum  --- average number of flux values per cell used to get flux.
            rngcell --- distance to center of flux database cell used  (re).
            numcell --- number of flux database cells used that have the
                        same value of rngcell.

    from param file --- maxpnt, maxnum, maxkp, maxcell, maxnsphvol
                        xmin, ymin, zmin, xinc, yinc, zinc, maxnum
    """
    cdef int    i, j, k, n, numcell, indexnow
    cdef float  rngchk2
    cdef double rngcell, flux, avgnum, rngdiff, rngabs
    cdef double fve, xve, yve, zve

    rngcell = 1.0e25
    numcell = 0
#
#-- give extra margin on rngchk so that most of the neighbors are included
#
    rngchk2 = 1.20 * rngchk

    for n in range(0, nsphvol):
        i = indx + ioffset[n]
        j = indy + joffset[n]
        k = indz + koffset[n]
        if (i >= 0) and (j >= 0) and (k >= 0)\
           and (i < maxnum) and (j < maxnum) and (k < maxnum):
            indexnow = imapindx[i][j][k]

            if indexnow >= 0:
                zve     = zflux[indexnow]
#
#--- for the map_z, extra check is required
#
                if zchk > 0:
                    if (zve < zcklo) or (zve > zckhi):
                        continue

                fve     = fluxbin[indexnow]
                xve     = xflux[indexnow]
                yve     = yflux[indexnow]

                rng     = compute_rng(xve, yve, zve, xgsm, ygsm, zgsm)
                rngdiff = rng - rngcell
                rngabs  = abs(rngdiff)
#
#--- there is a new nearest neighbor data cell
#
                if numcell == 0:
                    flxsto[numcell] = fve
                    numsto[numcell] = numbin[indexnow]
                    numcell = 1
                    rngcell = rng
#
#--- there is a new data cell within the range tolerance to the nearest neighbor.  
#--- this cell's flux should be included in the average for this location.
#
                else:
                    if rngabs <= rngchk:
                        flxsto[numcell] = fve
                        numsto[numcell] = numbin[indexnow]
                        numcell += 1

                        if numcell > maxcell-1:
                            break
                    else:
                        if rngabs > rngchk2:
                            break
#
#--- use the average of the flux from all bins at the same distance
#
    if numcell == 0:
        flux    = 0.0
        avgnum  = 0.0
        rngcell = 0.0
    
    elif numcell == 1:
        flux    = flxsto[0]
        avgnum  = float(numsto[0])
    
    elif numcell > 1:
        flux    = numpy.mean(flxsto[:numcell])
        avgnum  = numpy.mean(numsto[:numcell])

    return flux, avgnum, rngcell, numcell

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def compute_rng(double xve, double yve, double zve, double xgsm, double ygsm, double zgsm):
    cdef double rng

    rng = math.sqrt((xve - xgsm)**2 + (yve - ygsm)**2 + (zve - zgsm)**2)

    return rng

#----------------------------------------------------------------------------
#-- neighbr:  finds the nearest neighbors to the point in question         --
#----------------------------------------------------------------------------

def neighbr(xtail, ytail, sectx, secty):
    """
    this routine finds the nearest neighbors to the point in
    question. this routine is used to find the spatial sectors used
    to perform the kp scaling for a given point.
    
    input:  xtail   --- satellite's x-coordinate in geotail system (re).
            ytail   --- satellite's y-coordinate in geotail system (re).
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
    
    output: idx     --- index list pointing to the kp scaling sectors,
                        ranked in order of nearest to farthest.
            rngsect --- array containing the sorted range values of the
                        spacecraft to the kp scaling sectors,
    """
#
#--- first, find the range to each sector in their original order
#
    sx      = sectx - xtail
    sy      = secty - ytail
    rngsect = numpy.sqrt(sx * sx + sy * sy)
#
#--- sort the kp scaling sector range list in order of nearest to farthest
#
    idx     = numpy.argsort(rngsect)
    rngsect = rngsect[idx]


    return  idx, rngsect

#----------------------------------------------------------------------------
#-- rot8ang: rotates the 2-d vector about its hinge point in the xy-plane  --
#----------------------------------------------------------------------------

def rot8ang(ang, x, y, xhinge):
    """
    this routine rotates the 2-d vector about its hinge point in the xy-plane.
    input:  ang    --- angle to rotate (rad).
            x      --- initial x value.
            y      --- initial y value.
            xhinge --- x value of aberration hinge point.
    
    output: xrot2  --- final x value.
            yrot2  --- final y value.
    """
    if x <= xhinge:
        xrot2 =  x * math.cos(ang) + y * math.sin(ang)
        yrot2 = -x * math.sin(ang) + y * math.cos(ang)
    else:
        xrot2 = x
        yrot2 = y

    return [xrot2, yrot2]

#----------------------------------------------------------------------------
#-- scalkp1: finds the kp scaling parameters in the solar wind             --
#----------------------------------------------------------------------------

def scalkp1(xkp,ispeci):
    """
    this routine finds the kp scaling parameters in the sloar wind
    input: xkp     --- kp index user desires output for.
           ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    
    output: nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor.

    from parm file      numsec, maxkp
    Note: in MTA case, this is not used
    """
#
#--- magnetosheath section fuction list:
#
    f_list = [sectr11, sectr12, sectr13]

    return get_scalkp(f_list, xkp,ispeci)

#----------------------------------------------------------------------------
#-- scalkp2: finds the kp scaling parameters in the magnetosheath          --
#----------------------------------------------------------------------------

def scalkp2(xkp,ispeci):
    """
    this routine finds the kp scaling parameters in the magnetosheath
    input: xkp     --- kp index user desires output for.
           ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    
    output: nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor.

    from parm file      numsec, maxkp
    """
#
#--- magnetosheath section fuction list:
#
    f_list = [sectr21, sectr22, sectr23, sectr24]

    return get_scalkp(f_list, xkp, ispeci)

#----------------------------------------------------------------------------
#-- scalkp3: finds the kp scaling parameters in the magnetosphere          --
#----------------------------------------------------------------------------

def scalkp3(xkp,ispeci):
    """
    this routine finds the kp scaling parameters in the magnetosphere
    input: xkp     --- kp index user desires output for.
           ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    
    output: nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor.

    from parm file      numsec, maxkp
    """
#
#--- magnetsphere section fuction list:
#
    f_list = [sectr31, sectr32, sectr33,sectr34, sectr35, sectr36,\
              sectr37, sectr38, sectr39, sectr310]

    return get_scalkp(f_list, xkp,ispeci)

#----------------------------------------------------------------------------
#-- get_scalkp: finds the kp scaling parameters of the given sector        --
#----------------------------------------------------------------------------

def get_scalkp(f_list, xkp,ispeci):
    """
    this routine finds the kp scaling parameters of the given sector
    input: f_list  --- a list of sector functions
           xkp     --- kp index user desires output for.
           ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
    
    output: nsectrs --- number of kp scaling sectors in region.
            sectx   --- array of each sector center's x coordinate.
            secty   --- array of each sector center's y coordinate.
            scmean  --- array of each sector's mean flux scale factor.
            sc95    --- array of each sector's 95% flux scale factor.
            sc50    --- array of each sector's 50% flux scale factor.
            scsig   --- array of each sector's std dev flux scale factor
    """
    nsectrs = len(f_list)
 
    scmean = numpy.zeros((nsectrs, maxkp))
    sc95   = numpy.zeros((nsectrs, maxkp))
    sc50   = numpy.zeros((nsectrs, maxkp))
    scsig  = numpy.zeros((nsectrs, maxkp))
    sectx  = numpy.zeros(nsectrs)
    secty  = numpy.zeros(nsectrs)
#
#-- sectr* function returns: [scmean, sc95, sc50, scsig, xcen, ycen]
#
    for k in range(0, nsectrs):
        sect_fnc = f_list[k]
#
#--- get the kp value at the midpoint of the data interval
#
        for m in range(1, 10):
            m1= m  -1
            xkpsc = m - 0.5
         
            out = sect_fnc(ispeci, xkp, xkpsc)
            scmean[k,m1] = out[0]
            sc95[k,m1]   = out[1]
            sc50[k,m1]   = out[2]
            scsig[k,m1]  = out[3]
     
        sectx[k] = out[4]
        secty[k] = out[5]

    return nsectrs, sectx, secty, scmean, sc95, sc50, scsig

#----------------------------------------------------------------------------
#-- sectr11: provides the proton flux vs. kp scaling in sector 1           --
#----------------------------------------------------------------------------

def sectr11(ispeci,xkp,xkpsc):
    """
    ***************** solar wind kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   1:  (+5<x<+20; +13<y<+30; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [ 5.0, 20.0]
    ypar = [13.0, 30.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [0.2477179, 2.532024]
    f95p  = [0.1987326, 3.283149]
    f50p  = [1.31762,   0.127923]
    fsgp  = [0.1528122, 3.316698]
    favp  = [0.2477179, 2.532024]
    mtd   = 6

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr12: provides the proton flux vs. kp scaling in sector 2           --
#----------------------------------------------------------------------------

def sectr12(ispeci,xkp,xkpsc):
    """
    ***************** solar wind kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   2:  (+8<x<+22; -10<y<+10; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [  8.0,  22.0]
    ypar = [-10.0,  10.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.053755, 0.1816665]
    f95p  = [1.23647,  0.1521542]
    f50p  = [0.137769, 1.508285]
    fsgp  = [1.232657, 0.127408]
    favp  = [1.053755, 0.1816665]
    mtd   = 4

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr13: provides the proton flux vs. kp scaling in sector 3           --
#----------------------------------------------------------------------------

def sectr13(ispeci,xkp,xkpsc):
    """
    ***************** solar wind kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   3:  (+5<x<+20; -25<y<-13; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [  5.0,  20.0]
    ypar = [-25.0, -13.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [2.418556,  0.09242323]
    f95p  = [3.129407,  0.07088557]
    f50p  = [0.4192601, 1.12118]
    fsgp  = [0.2818979, 2.802846]
    favp  = [2.418556,  0.09242323]
    mtd   = 5

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr21: provides the proton flux vs. kp scaling in sector 1           --
#----------------------------------------------------------------------------

def sectr21(ispeci,xkp,xkpsc):
    """
    ***************** magnetosheath kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   1:  (-20<x<0; +15<y<+30; all z)..

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-20.0,   0.0]
    ypar = [ 15.0,  30.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.006261,    0.2358533]
    f95p  = [1.242684,    0.167599]
    f50p  = [3.595895e-1, 1.485105]
    fsgp  = [1.154729,    0.1813815]
    favp  = [1.006261,    0.2358533]
    mtd   = 4

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr22: provides the proton flux vs. kp scaling in sector 2           --
#----------------------------------------------------------------------------

def sectr22(ispeci,xkp,xkpsc):
    """
    ***************** magnetosheath kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   2:  (-5<x<+15; +10<y<+23; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [ -5.0,  15.0]
    ypar = [ 10.0,  23.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.075755,    0.228047]
    f95p  = [1.28287,     0.1789508]
    f50p  = [4.152996e-1, 1.144803]
    fsgp  = [1.231504,    0.1678395]
    favp  = [1.075755,    0.228047]
    mtd   = 4

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)


#----------------------------------------------------------------------------
#-- sectr23: provides the proton flux vs. kp scaling in sector 3           --
#----------------------------------------------------------------------------

def sectr23(ispeci,xkp,xkpsc):
    """
    ***************** magnetosheath kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   3:  (-5<x<+15; -10<y<+10; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [ -5.0,  15.0]
    ypar = [-10.0,  10.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.059922,    0.2450142]
    f95p  = [1.262771,    0.2122456]
    f50p  = [2.699979e-1, 1.92621]
    fsgp  = [1.170143    ,0.2329764]
    favp  = [1.059922,    0.2450142]
    mtd   = 4

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr24: provides the proton flux vs. kp scaling in sector 4           --
#----------------------------------------------------------------------------

def sectr24(ispeci,xkp,xkpsc):
    """
    ***************** magnetosheath kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   4:  (-25<x<+5; -30<y<-12; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-25.0,   5.0]
    ypar = [-30.0, -12.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [0.8034997, 0.2943536]
    f95p  = [1.029681,  0.2502851]
    f50p  = [0.6214508, 0.2912395]
    fsgp  = [0.890587,  0.2943353]
    favp  = [0.8034997, 0.2943536]
    mtd   = 2

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr31: provides the proton flux vs. kp scaling in sector 1           --
#----------------------------------------------------------------------------

def sectr31(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   1:  (-10<x<-6; -6<y<+4; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-10.0, -6.0]
    ypar = [ -6.0,  4.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [2.443395e-1, 3.845401]
    f95p  = [4.539177,    3.807753e-2]
    f50p  = [3.058675e-1, 3.264229]
    fsgp  = [2.038728e-1, 4.088105]
    favp  = [2.443395e-1, 3.845401]
    mtd   = 3

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr32: provides the proton flux vs. kp scaling in sector 2           --
#----------------------------------------------------------------------------

def sectr32(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   2:  (-7<x<0; +8<y<+13; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-7.0,  0.0]
    ypar = [ 8.0, 13.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.430943, 1.431528e-1]
    f95p  = [1.510317, 1.432958e-1]
    f50p  = [1.285142, 1.935917e-1]
    fsgp  = [1.544309, 8.922371e-2]
    favp  = [1.430943, 1.431528e-1]
    mtd   = 2

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr33: provides the proton flux vs. kp scaling in sector 5           --
#----------------------------------------------------------------------------

def sectr33(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   4:  (-18<x<-12; -18<y<-11; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-18.0, -12.0]
    ypar = [-18.0, -11.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [4.0986685e-1, 2.083598]
    f95p  = [3.677568e-1,  2.792231]
    f50p  = [4.706894e-1,  1.382612]
    fsgp  = [3.606812e-1,  2.440727]
    favp  = [4.0986685e-1, 2.083598]
    mtd   = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr34: provides the proton flux vs. kp scaling in sector 5           --
#----------------------------------------------------------------------------

def sectr34(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   5:  (-28<x<-21; -18<y<-10; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-28.0, -21.0]
    ypar = [-18.0, -10.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [3.249438e-1, 2.425203]
    f95p  = [2.860754e-1, 3.135966]
    f50p  = [3.848902e-1, 1.684094]
    fsgp  = [2.574007e-1, 2.909206]
    favp  = [3.249438e-1, 2.425203]
    mtd   = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr35: provides the proton flux vs. kp scaling in sector 6           --
#----------------------------------------------------------------------------

def sectr35(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector   6:  (-29<x<-25; -10<y<-3; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-29.0, -25.0]
    ypar = [-10.0,  -3.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [4.343142e-1, 2.180041]
    f95p  = [4.123490e-1, 2.759741]
    f50p  = [4.826937e-1, 1.563440]
    fsgp  = [3.533449e-1, 2.641683]
    favp  = [4.343142e-1, 2.180041]
    mtd   = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr36: provides the proton flux vs. kp scaling in sector 7           --
#----------------------------------------------------------------------------

def sectr36(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector  7:  (-20<x<-15; +1<y<+10; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-20.0, -15.0]
    ypar = [  1.0,  10.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [1.270656, 2.230935e-1]
    f95p  = [1.436059, 1.577674e-1]
    f50p  = [1.051924, 3.327092e-1]
    fsgp  = [1.332255, 1.706059e-1]
    favp  = [1.270656, 2.230935e-1]
    mtd   = 2

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr37: provides the proton flux vs. kp scaling in sector 8           --
#----------------------------------------------------------------------------

def sectr37(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector 8:  (-19<x<-14; +10<y<+19; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-19.0, -14.0]
    ypar = [ 10.0,  19.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp  = [3.213946e-1, 2.964045]
    f95p  = [2.901571e-1, 3.628429]
    f50p  = [3.349902e-1, 2.415445]
    fsgp  = [2.934793e-1, 3.251733]
    favp  = [3.213946e-1, 2.964045]
    mtd   = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr38: provides the proton flux vs. kp scaling in sector 9           --
#----------------------------------------------------------------------------

def sectr38(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector 9:  (-30<x<-24; +10<y<+17; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits
#
    xpar = [-30.0, -24.0]
    ypar = [ 10.0,  17.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp = [1.114799,    2.013791e-1]
    f95p = [1.283152,    1.715240e-1]
    f50p = [8.948732e-1, 2.100576e-1]
    fsgp = [1.232212,    1.728799e-1]
    favp = [1.114799,    2.013791e-1]
    mtd  = 2

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sectr39: provides the proton flux vs. kp scaling in sector 10          --
#----------------------------------------------------------------------------

def sectr39(ispeci,xkp,xkpsc):
    """
    ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector 10:  (0<x<+8; +8<y<+13; all z).

    input:  ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#--- setting parameter of this sector's limits.
#
    xpar =  [0.0,  8.0]
    ypar =  [8.0, 13.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp = [2.373299e-1, 3.988981]
    f95p = [1.769049e-1, 4.660334]
    f50p = [2.427994e-1, 3.717080]
    fsgp = [2.079478e-1, 4.169556]
    favp = [2.373299e-1, 3.988981]
    mtd  = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)


#----------------------------------------------------------------------------
#-- sectr310:  provides the proton flux vs. kp scaling in sector 310       --
#----------------------------------------------------------------------------

def sectr310(ispeci, xkp, xkpsc):
    """
     ***************** magnetosphere kp scaling *********************
    this routine provides the proton flux vs. kp scaling in
    sector 10:  (0<x<+8; -11<y<-6; all z).

    inputs: ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).
    """
#
#---setting parameter of this sector's limits.
#
    xpar = [-8.0,   -6.0]
    ypar = [-16.0, -14.0]
#
#--- setting parameters of the proton flux scaling parameters
#
    fmnp = [2.373299e-1, 3.988981]
    f95p = [1.769049e-1, 4.660334]
    f50p = [2.427994e-1, 3.717080]
    fsgp = [2.079478e-1, 4.169556]
    favp = [2.373299e-1, 3.988981]
    mtd  = 1

    return sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd)

#----------------------------------------------------------------------------
#-- sect_comp: compute the proton flux vs kp scaling for the section       --
#----------------------------------------------------------------------------

def sect_comp(ispeci, xkp, xkpsc, xpar, ypar, fmnp, f95p, f50p, fsgp, favp, mtd):
    """
    compute the proton flux vs kp scaling for the section

    inputs: ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            xkp     --- user selected kp index (real value between 0 & 9).
            xkpsc   --- the kp value at the midpoint of the data interval.
            xpar    --- parameter set of sector limit in x
            ypar    --- parameter set of sector limit in y
            fmnp    --- parameter set of fmean computation
            f95p    --- parameter set of f95 computation
            f50p    --- parameter set of f50 computation
            fsgp    --- parameter set of fsig computation
            favp    --- parameter set of favg computation
            mtd     --- indicator of two different way of computing the flux
    
    output: scmean  --- mean flux scale factor.
            sc95    --- 95% flux scale factor.
            sc50    --- 50% flux scale factor.
            scsig   --- standard deviation scale factor of flux.
            xcen    --- sector center's x-coordinate (re).
            ycen    --- sector center's x-coordinate (re).

    """
#
#--- set up this sector's limits.
#
    xcen = (xpar[0] + xpar[1]) / 2.0
    ycen = (ypar[0] + ypar[1]) / 2.0
#
#--- calculate the proton flux scaling parameters
#
    if ispeci == 1:
        if mtd == 1:
            fmean = fmnp[0] * xkp   + fmnp[1]
            f95   = f95p[0] * xkp   + f95p[1]
            f50   = f50p[0] * xkp   + f50p[1]
            fsig  = fsgp[0] * xkp   + fsgp[1]
            favg  = favp[0] * xkpsc + favp[1]

        elif mtd == 2:
            fmean = math.exp(fmnp[0]) * (xkp**fmnp[1])
            f95   = math.exp(f95p[0]) * (xkp**f95p[1])
            f50   = math.exp(f50p[0]) * (xkp**f50p[1])
            fsig  = math.exp(fsgp[0]) * (xkp**fsgp[1])
            favg  = math.exp(favp[0]) * (xkpsc**favp[1])

        elif mtd == 3:
            fmean = fmnp[0] * xkp   + fmnp[1]
            f95   = f95p[0] * math.exp(f95p[1] * xkp)
            f50   = f50p[0] * xkp   + f50p[1]
            fsig  = fsgp[0] * xkp   + fsgp[1]
            favg  = favp[0] * xkpsc + favp[1]

        elif mtd == 4:
            fmean = math.exp(fmnp[0]) * (xkp**fmnp[1])
            f95   = math.exp(f95p[0]) * (xkp**f95p[1])
            f50   = f50p[0] * xkp   + f50p[1]
            fsig  = math.exp(fsgp[0]) * (xkp**fsgp[1])
            favg  = math.exp(favp[0]) * (xkpsc**favp[1])

        elif mtd == 5:
            fmean = fmnp[0] * math.exp(fmnp[1] * xkp)
            f95   = f95p[0] * math.exp(f95p[1] * xkp)
            f50   = f50p[0] * xkp   + f50p[1]
            fsig  = fsgp[0] * xkp   + fsgp[1]
            favg  = favp[0] * math.exp(favp[1] * xkpsc)

        elif mtd == 6:
            fmean = fmnp[0] * xkp   + fmnp[1]
            f95   = f95p[0] * xkp   + f95p[1]
            f50   = f50p[0] * math.exp(f50p[1] * xkp)
            fsig  = fsgp[0] * xkp   + fsgp[1]
            favg  = favp[0] * xkpsc + favp[1]


        fmean  = 10**fmean
        f95    = 10**f95
        f50    = 10**f50
        fsig   = 10**fsig
        favg   = 10**favg

        scmean = fmean / favg
        sc95   = f95   / favg
        sc50   = f50   / favg
        scsig  = fsig  / favg
#
#--- calculate the helium flux scaling parameters
#
    elif ispeci == 2:
        cmean  = -1.0e-11
        sc95   = -1.0e-11
        sc50   = -1.0e-11
        scsig  = -1.0e-11
#
#---  calculate the cno flux scaling parameters
#
    else:
        scmean = -1.0e-11
        sc95   = -1.0e-11
        sc50   = -1.0e-11
        scsig  = -1.0e-11

    return [scmean, sc95, sc50, scsig, xcen, ycen]

#----------------------------------------------------------------------------
#-- solwflx: provides the solar wind ion flux as a function of kp          --
#----------------------------------------------------------------------------

def solwflx(int xkp, int ispeci):
    """
    this routine provides the solar wind ion flux as a function of kp.

    input: xkp      --- kp index (real value between 0 & 9).
            ispeci  --- ion species selection flag
                        ispeci = 1 for protons
                        ispeci = 2 for helium
                        ispeci = 3 for cno
            
    output: fluxmn  --- mean flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux95  --- 95% flux (#/[cm^2-sec-sr-mev]) for selected species.
            flux50  --- 50% flux (#/[cm^2-sec-sr-mev]) for selected species.
            fluxsd  --- standard deviation of flux for selected species.
    """
#
#--- provide proton flux values
#
    if ispeci == 1:
        if xkp <= 5.5:
            fluxmn = -8.009051e-3 * xkp**2 + 3.011148e-1 * xkp + 2.427724
            flux95 =  1.172813e-2 * xkp**2 + 1.805303e-1 * xkp + 3.216384
        else:
            fluxmn = -1.989790e-1 * xkp**2 + 3.018409    * xkp - 6.741037
            flux95 = -2.644953e-1 * xkp**2 + 3.832377    * xkp - 8.525337

        flux50 = 3.732036e-2 * xkp**2 + 1.509852e-2 * xkp + 1.586031
        fluxsd = 2.128721e-1 * xkp    + 3.166099

        fluxmn = 10**fluxmn
        flux95 = 10**flux95
        flux50 = 10**flux50
        fluxsd = 10**fluxsd
#
#--- provide helium flux values.
#
    elif ispeci == 2:
        fluxmn = -1.0e-11
        flux95 = -1.0e-11
        flux50 = -1.0e-11
        fluxsd = -1.0e-11
#
#--- provide cno flux values
#
    elif ispeci == 3:
        fluxmn = -1.0e-11
        flux95 = -1.0e-11
        flux50 = -1.0e-11
        fluxsd = -1.0e-11


    return fluxmn, flux95, flux50, fluxsd

#----------------------------------------------------------------------------
#-- solwind: get the solar wind parameters used as inputs for the bow shock -
#----------------------------------------------------------------------------

def solwind(xkp):
    """
    get the solar wind parameters used as inputs for the bow shock
    and magnetopause boundary models.
    
    input:  xkp     --- kp index (real value between 0 & 9).
    output: bx      --- the imf b_x [nt]
            by      --- the imf b_y [nt]
            bz      --- the imf b_z [nt]
            vx      --- x component of solar wind bulk flow velocity (km/s).
            vy      --- y component of solar wind bulk flow velocity (km/s).
            vz      --- z component of solar wind bulk flow velocity (km/s).
            dennum  --- the solar wind proton number density [#/cm^3]
            swetemp --- the solar wind electron temperature [k]
            swptemp --- the solar wind proton temperature [k]
            hefrac  --- fraction of solar wind ions which are helium ions
            swhtemp --- the temperature of the helium [k]
            bowang  --- angle bow shock radius calculated (rad).
            dypres  --- solar wind dynamic pressure (np).
            abang   --- aberration angle of magnetotail (deg).
            xhinge  --- hinge point of magnetotail (re).

    from parm file      pi
    """

    bx      =   -5.0
    by      =    6.0
    bz      =    6.0
    vx      = -500.0
    vy      =    0.0
    vz      =    0.0

    dennum  = 8.0
    swetemp = 1.4e+5
    swptemp = 1.2e+5
    hefrac  = 0.047
    swhtemp = 5.8e+5
    bowang  = pi

    if xkp <= 4.0:
        dypres  =    1.0
        abang   =    4.0
        xhinge  =   14.0
        vx      = -400.0

    elif (xkp > 4.0) and (xkp <= 6.0): 
        dypres1 =    1.0
        abang1  =    4.0
        vx1     = -400.0
        dypres2 =    4.0
        abang2  =    0.0
        vx2     = -500.0

        dypres  = y_interpolate(4.0, dypres1, 6.0, dypres2, xkp, 1)
        abang   = y_interpolate(4.0, abang1,  6.0, abang2,  xkp, 1)
        xhinge  = 14.0
        vx      = y_interpolate(4.0, vx1,     6.0, vx2,     xkp, 1)

    else:
        dypres1 =    4.0
        dypres2 =   10.0
        dypres  = y_interpolate(6.0, dypres1, 9.0, dypres2, xkp, 1)
        abang   =    0.0
        xhinge  =   14.0
        vx      = -500.0

    return [bx, by, bz, vx, vy, vz, dennum, swetemp, swptemp, hefrac,\
            swhtemp, bowang, dypres, abang, xhinge]

#----------------------------------------------------------------------------
#-- sort_multi_lists: sort all lists in list_save with in the sorted order of the list at postion given
#----------------------------------------------------------------------------

def sort_multi_lists(array_save, pos=0):
    """
    sort all lists in list_save with in the sorted order of the list at postion given
    input:  array_save  --- a list of lists
            pos         --- the position of the list to be ordered
    output: save        --- a list of lists ordered 
    """

    idx    = numpy.argsort(array_save[pos])
    save   = []
    for tarray in array_save:

        save.append(tarray[idx])

    return save

#----------------------------------------------------------------------------
#-- statflx: calculates the statistics based on flux or fluence contained in one energy bin
#----------------------------------------------------------------------------

def statflx(ain, fpchi, fpclo):
    """
    this routine calculates the statistics based on list ain, the
    flux or fluence contained in one energy bin.
    
    input:  ain    --- flux/fluence contained in one energy bin.
            fpchi  --- upper percentile limit for spatial averaging of flux.
            fpclo  --- lower percentile limit for spatial averaging of flux.
    
    output: apchi  --- fpchi percentile level of ain.
            apclo  --- fpclo percentile level of ain.
            amean  --- mean of ain.
            asig   --- standard deviation of ain.
            amax   --- maximum of ain.
            amin   --- minimum of ain.
    """
#
#--- compute mean, std, max, min
#
    if len(ain) > 0:
        amean = numpy.mean(ain)
        amax  = max(ain)
        amin  = min(ain)
    else:
        amean = 0.0
        amax  = 0.0
        amin  = 0.0
    try:
        asig = numpy.std(ain)
    except:
        asig = 0.0
#
#--- compute values of given percentiles.
#
    if len(ain) > 1:
        apchi = numpy.percentile(ain, fpchi)
        apclo = numpy.percentile(ain, fpclo)

    elif len(ain) == 1:
        apchi = ain[0]
        apclo = ain[0]

    else:
        apchi = 0
        apclo = 0

    return apchi, apclo, amean, asig, amax, amin

#----------------------------------------------------------------------------
#-- wtscal:  calculates the distance weighted sum of the Kp scaling factors -
#----------------------------------------------------------------------------

def wtscal(numscal, indsect, rngsect, scmean, sc95, sc50, scsig):
    """
    This routine calculates the distance weighted sum of the Kp
    scaling factors.  The objective of this approach is to arrive
    at a set of Kp scaling factors that have been "blended" together
    according to their relative distances from the point at which
    output is desired.
    
    Algorithm:
    
    (1) Multiply the closest sector's Kp scaling factors by the
        distance to the farthest sector.
    (2) Multiply the  2nd closest sector's Kp scaling factors by the
        distance to the 2nd farthest sector.
    (3) Repeat this process until you multiply the farthest sector's
        Kp scaling factors by the distance to the closest sector.
    (4) Get the final set of Kp scaling factors by summing the distance
        scaled quantities and dividing the sum by the total distance
        to all of the sectors.
    
    input:  numscal --- the number of Kp scaling sectors to use per
                        calculation. (NUMSCAL must not exceed NUMSEC!)
            indsect --- index list pointing to the Kp scaling sectors,
                        ranked in order of nearest to farthest.
            rngsect --- list containing the sorted range values of the
                        spacecraft to the Kp scaling sectors,
            scmean  --- list of each sector's mean flux scale factor.
            sc95    --- list of each sector's 95% flux scale factor.
            sc50    --- list of each sector's 50% flux scale factor.
            scsig   --- list of each sector's std dev flux scale factor.
    
    output: wtmean  --- distance weighted sum of the mean flux scale factors.
            wt95    --- distance weighted sum of the 95% flux scale factors.
            wt50    --- distance weighted sum of the 50% flux scale factors.
            wtsig   --- distance weighted sum of the std dev flux scale factors.

    from param file     maxkp
    """
    wtmean = numpy.zeros(maxkp)
    wt95   = numpy.zeros(maxkp)
    wt50   = numpy.zeros(maxkp)
    wtsig  = numpy.zeros(maxkp)
    
    dtot   = 0
    for i in range(0, numscal):
        dtot  += rngsect[i]
        m  = indsect[i]
        n  = numscal - i - 1
        weight = rngsect[n]
     
        wtmean = create_weighted_sum(wtmean, scmean[m], weight)
        wt95   = create_weighted_sum(wt95,   sc95[m],   weight)
        wt50   = create_weighted_sum(wt50,   sc50[m],   weight)
        wtsig  = create_weighted_sum(wtsig,  scsig[m],  weight)
    
    wtmean /= float(dtot)
    wt95   /= float(dtot)
    wt50   /= float(dtot)
    wtsig  /= float(dtot)

    return wtmean, wt95, wt50, wtsig

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def create_weighted_sum(a, b, w):

    a += b * w

    return a

#----------------------------------------------------------------------------
#-- y_interpolate: return y coordinate corresponding to xin                --
#----------------------------------------------------------------------------

def y_interpolate(x1, y1, x2, y2, xin, mode=1):
    """
    return y coordinate corresponding to xin along the line define by (x1, y1)/(x2, y2)
    input:  (x1, y1)/(x2, y2)   --- coordinates of two points
            xin                 --- x value to be estimated
            mode                --- 1: linear
                                    2: semilog log/linear
                                    3: semilog linear/log
                                    4: log/log
    output: yest                --- resulted y value
    """
    if mode in [2, 4]:
        x1  = math.log(x1)
        x2  = math.log(x2)
        xin = math.log(xin)

    if mode in [3, 4]:
        y1  = math.log(y1)
        y2  = math.log(y2)
#
#--- linear interpolation
#
    yest = y1 - (y1 - y2) *(x1 -xin) / (x1 - x2)

    if mode in [3, 4]:
        yest = math.exp(yest)

    return yest

#----------------------------------------------------------------------------
#-- zbinner: determins the z-layer of the magnetosphere used to find       --
#----------------------------------------------------------------------------

def zbinner(xgsm, zgsm):
    """
    this routine determins the z-layer of the magnetosphere used to find
    the speacecraft's near-nighbor flux
    input:  xgsm    --- satellite's x-coordinate in re
            zgsm    --- satellite's z-coordinate in re
    output: zcklo   --- lower z-value used to check for near-neighbor flux in re
            zckhi   --- upper z-value used to check for near-neighbor flux in re
    """
#
#--- do not use z-layer on the dayside of the magnetospere
#
    if xgsm >= 0:
        zcklo = -7.0
        zckhi = 100.0
#
#--- use the nearest neighbor flux only inside a range of z-values
#
    else:
#
#--- use the nearest neighbor in the -7 < z < -6 range
#
        if zgsm < -6.0:
            zcklo = -7.0
            zckhi = -6.0
#
#--- use the nearest neighbor in the -6 < Z < -5. range
#
        elif (zgsm > -6.0) and (zgsm <= -5.0):
            zcklo = -6.0
            zckhi = -5.0
#
#--- use the nearest neighbor in the -5 < Z < +4. range
#
        elif (zgsm > -5.0) and (zgsm <=  4.0):
            zcklo = -5.0
            zckhi =  4.0
#
#--- use the nearest neighbor in the +4 < Z < +5. range
#
        elif (zgsm >  4.0) and (zgsm <=  5.0):
            zcklo =  4.0
            zckhi =  5.0
#
#--- use the nearest neighbor in the +5 < Z < +6. range
#
        elif (zgsm >  5.0) and (zgsm <=  6.0):
            zcklo =  5.0
            zckhi =  6.0
#
#--- use the nearest neighbor in the +6 < Z < +7. range
#
        elif (zgsm >  6.0) and (zgsm <=  7.0):
            zcklo =  6.0
            zckhi =  7.0
#
#--- use the nearest neighbor in the +7 < Z < +8. range
#
        elif (zgsm >  7.0) and (zgsm <=  8.0):
            zcklo =  7.0
            zckhi =  8.0
#
#--- use the nearest neighbor in the +8 < Z < +9. range
#
        elif (zgsm >  8.0) and (zgsm <=  9.0):
            zcklo =  8.0
            zckhi =  9.0
#
#--- use the nearest neighbor in the +9 < Z < +10. range
#
        elif (zgsm >  9.0) and (zgsm <=  10.0):
            zcklo =  9.0
            zckhi = 10.0
#
#--- use the nearest neighbor in the +10 < Z < +11. range
#
        elif zgsm > 10.0:
            zcklo = 10.0
            zckhi = 11.0

    return zcklo, zckhi

#----------------------------------------------------------------------------
#---TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST  ----------------------
#----------------------------------------------------------------------------

class run_test(unittest.TestCase):
    """
    test functions
    """

#---------------------------------------

    def test_scalkp(self):
        xkp    = 2.3
        ispeci = 1
        out = scalkp1(xkp,ispeci)
        print('sec 1:' + str(out[1]))

        out = scalkp2(xkp,ispeci)
        print('sec 2:' + str(out[1]))

        out = scalkp3(xkp,ispeci)
        print('sec 3:' + str(out[1]))

#---------------------------------------

    def test_sectr310(self):
        ispeci = 1
        xkp    = 3
        xkpsc  = 3.1

        scmean, sc95, sc50, scsig, xcen, ycen = sectr310(ispeci, xkp, xkpsc)
        print(" sectr310: %3.2f" % scmean)

#---------------------------------------

    def test_solwflx(self):
        xkp    = 3.1
        ispeci = 1
        fluxmn, flux95, flux50, fluxsd = solwflx(xkp,ispeci)
        print(" solwflx: %3.2f" % fluxmn)

#---------------------------------------

    def test_solwind(self):
        xkp= 2.3
        out = solwind(xkp)
        print("solwind: %2.3f" % round(out[-3], 3))

        xkp= 4.3
        out = solwind(xkp)
        print("solwind: %2.3f" % round(out[-3], 3))

#---------------------------------------

    def test_statflx(self):
        ain  = [1.1,1.2, 1.3, 1.3, 1.1, 1.5, 1.8, 1.4]
        fpchi = 50
        fpclo = 30
        n    = 1
        rin  = ain
        nin  = ain
        apchi, apclo, amean, asig, amax, amin =  statflx(ain, fpchi, fpclo)

        self.assertEqual(apchi, 1.3)
        self.assertEqual(apclo, 1.21)

#---------------------------------------

    def test_interpolate(self):
        x1  = 1.0
        y1  = 1.0
        x2  = 3.0
        y2  = 3.0
        xin = 2.0
        yin = y_interpolate(x1, y1, x2, y2, xin)
    
        self.assertEqual(yin, 2.0)

#---------------------------------------
