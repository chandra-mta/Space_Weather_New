#!/proj/sot/ska3/flight/bin/python

#####################################################################################
#                                                                                   #
#       cocochan.py: convert Chandra ECI linear coords to GSE, GSE coord            #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last updae: Mar 16, 2021                                                #
#                                                                                   #
#####################################################################################

import os
import sys
import re
import string
import math
import numpy
import time
import Chandra.Time
import calendar
from datetime import datetime
sys.path.append('/data/mta4/Script/Python3.8/lib/python3.8/site-packages')  
from geopack  import geopack
#import astropy.io.fits  as pyfits

path = '/data/mta4/Space_Weather/EPHEM/house_keeping/dir_list_py'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append  pathes to private folders to a python directory
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)
#
#--- import several functions
#
import mta_common_functions as mcf  #---- contains other functions commonly used in MTA scripts
#
#--- some constants
#
pi     = math.pi
earth  = 6371.0         #--- Earth radius
dpr    = 6.2832/360.0   #--- degree per rad
gamma  = 5.0 / 3.0

#---------------------------------------------------------------------------------------
#-- cocochan: convert Chandra ECI linear coords to GSE, GSM coords                    --
#---------------------------------------------------------------------------------------

def cocochan(ifile):
    """
    convert Chandra ECI linear coords to GSE, GSM coords
    input: ifile    --- a data file name with:
                        t, x, y, z, vx, vy, vz, fy, mon, day, hh, mm, ss, kp
    output: line    --- data line with:
                        t, x, y, z, xsm, ysm, zsm, lid
                            lid = 1 if spacecraft is in solar wind
                            lid = 2 if spacecraft is in magnetosheath
                            lid = 3 if spacecraft is in magnetosphere

    Note: this python script is converted from Robert Cameron (2001) f77 program
          cocochan.f and crmflx_**.f which came with geopack.f

    python version of geopack: https://pypi.org/project/geopack/
    """
#
#--- read data
#
    out = mcf.read_data_file(ifile)
#
#--- separate data and convert into column data
#
    try:
        [t, x, y, z, vx, vy, vz, fy, mon, day, hh, mm, ss, kp] = mcf.separate_data_to_arrays(out)
    except:
        [t, x, y, z, vx, vy, vz, fy, mon, day, hh, mm, ss] = mcf.separate_data_to_arrays(out)
        kp = [1] * len(t)
#
#--- compute ut in seconds from 1970.1.1
#
    uts = ut_in_secs(fy[0], mon[0], day[0], hh[0], mm[0], ss[0])
#
#--- usually this need to be run only once but it seems better to run every time; 
#--- value is kept to be used by other geopack functions
#
    psi = geopack.recalc(uts)

    line1 = ''
    line2 = ''
    line3 = ''
    for k in range(0, len(t)):
#
#--- convert position to km
#
        xs  = x[k] /1.0e3
        ys  = y[k] /1.0e3
        zs  = z[k] /1.0e3
        r   = math.sqrt(xs * xs + ys * ys + zs * zs)

        uts = ut_in_secs(fy[k], mon[k], day[k], hh[k], mm[k], ss[k])
        psi = geopack.recalc(uts)
#
#--- convert the coordinates into gsm and gse
#
        [xgsm, ygsm, zgsm, xgm, ygm, zgm, xge, yge, zge, lid] = compute_gsm(xs, ys, zs,  kp[k])
#
#--- convert to special coordinates
#
        [mr, mt, mp] = convert_to_special_coords(xgsm, ygsm, zgsm)
        [er, et, ep] = convert_to_special_coords(xge, yge, zge)



        line1 = line1 + '%11.1f'   %  t[k]
        line1 = line1 + '\t%10.2f' %  r
        line1 = line1 + '\t%10.2f' %  xs 
        line1 = line1 + '\t%10.2f' %  ys 
        line1 = line1 + '\t%10.2f' %  zs 
        line1 = line1 + '\t%10.2f' %  xgsm
        line1 = line1 + '\t%10.2f' %  ygsm
        line1 = line1 + '\t%10.2f' %  zgsm
        line1 = line1 + '\t%12.6f' %  fy[k]
        line1 = line1 + '%3d'      %  mon[k]
        line1 = line1 + '%3d'      %  day[k]
        line1 = line1 + '%3d'      %  hh[k]
        line1 = line1 + '%3d'      %  mm[k]
        #line1 = line1 + ' %3d'    %  ss[k]
        line1 = line1 + '\t%1.1f'  %  kp[k]
        line1 = line1 + '\t\t%1d'  %  lid
        line1 = line1 + '\n'

        line2 = line2 + '%11.1f'   %  t[k]
        line2 = line2 + '\t%2.5f'  %  xgm
        line2 = line2 + '\t%2.5f'  %  ygm
        line2 = line2 + '\t%2.5f'  %  zgm
        line2 = line2 + '\t%2.5f'  %  xge 
        line2 = line2 + '\t%2.5f'  %  yge 
        line2 = line2 + '\t%2.5f'  %  zge 
        line2 = line2 + '\t%12.6f' %  fy[k]
        line2 = line2 + '%3d'      %  mon[k]
        line2 = line2 + '%3d'      %  day[k]
        line2 = line2 + '%3d'      %  hh[k]
        line2 = line2 + '%3d'      %  mm[k]
        #line2 = line2 + '%3d'     %  ss[k]
        line2 = line2 + '\t%1.1f'  %  kp[k]
        line2 = line2 + '\t\t%1d'  %  lid
        line2 = line2 + '\n'

        line3 = line3 + '%11.1f'   %  t[k]
        line3 = line3 + '\t%2.5f'  %  (mr / 1.0e3)
        line3 = line3 + '\t%2.5f'  %  mt 
        line3 = line3 + '\t%2.5f'  %  mp 
        line3 = line3 + '\t%2.5f'  %  et 
        line3 = line3 + '\t%2.5f'  %  ep  
        line3 = line3 + '\t%12.6f' %  fy[k]
        line3 = line3 + '%3d'      %  mon[k]
        line3 = line3 + '%3d'      %  day[k]
        line3 = line3 + '%3d'      %  hh[k]
        line3 = line3 + '%3d'      %  mm[k]
        #line3 = line3 + '%3d'     %  ss[k]
        line3 = line3 + '\t%1.1f'  %  kp[k]
        line3 = line3 + '\t\t%1d'  %  lid
        line3 = line3 + '\n'

    return [line1, line2,  line3]

#---------------------------------------------------------------------------------------
#-- compute_gsm: compute magnetic coordinates from equatorial coordinates             --
#---------------------------------------------------------------------------------------

def compute_gsm(x, y, z, kp):
    """
    compute magnetic coordinates from equatorial coordinates
    input:  x   --- x coordinate in km
            y   --- y coordinate in km
            z   --- z coordinate in km
            kp  --- kp value
    output: xgm --- x magnetic coordinates
            ygm --- y magnetic coordinates
            zgm --- z magnetic coordinates
            xge --- x geocentric soloar ecliptic
            yge --- y geocentric soloar ecliptic
            zge --- z geocentric soloar ecliptic
            lid --- location id
                    lid = 1 if spacecraft is in solar wind
                    lid = 2 if spacecraft is in magnetosheath
                    lid = 3 if spacecraft is in magnetosphere
    """
#
#--- Converts equatorial inertial (gei) to geographical (geo) coords
#
    xgeo, ygeo, zgeo = geopack.geigeo(x, y, z, 1)
#
#--- Converts geographic (geo) to geocentric solar magnetospheric (gsm) coordinates
#
    xgsm, ygsm, zgsm = geopack.geogsm(xgeo, ygeo, zgeo, 1)   
#    if xgsm < 0 or ygsm < 0:
#        xgsm *= -1.0
#        ygsm *= -1.0
#
#--- Convert gsm to gsw (geocentric solar wind coordinates)
#
#    xgsw, ygsw, zgsw = geopack.gswgsm(xgsm, ygsm, zgsm, -1)   
#    xgsw *= -1.0
#    ygsw *= -1.0
#
#--- Convert magnetosperic (gsm) to gse
#
    xgse, ygse, zgse = geopack.gsmgse(xgsm, ygsm, zgsm, 1)
#
#--- find location id; convert coordinate into earth radii before run locreg
#
    xgm   = xgsm / earth
    ygm   = ygsm / earth
    zgm   = zgsm / earth

#    xgm   = xgsw / earth
#    ygm   = ygsw / earth
#    zgm   = zgsw / earth

    exgse = xgse / earth
    eygse = ygse / earth
    ezgse = zgse / earth

    xtail, ytail, ztail, lid = locreg(kp, xgm, ygm, zgm)

    return [xgsm, ygsm, zgsm, xgm, ygm, zgm, exgse, eygse, ezgse, lid]

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------

def convert_to_special_coords(x, y, z):
    r, t, p = geopack.sphcar(x, y, z, -1)
    t       = t * 180 / pi 
    p       = p * 180 / pi 
    if p >= 180.0: 
        p -= 360.0

    return [r, t, p]

#---------------------------------------------------------------------------------------
#-- ut_in_secs: onvert calendar date into univarsal time in sec                       --
#---------------------------------------------------------------------------------------

def ut_in_secs(year, mon, day, hh, mm, ss):
    """
    convert calendar date into univarsal time in sec (seconds from 1970.1.1)
    input:  year    --- year
            mon     --- month
            day     --- day
            hh      --- hour
            mm      --- minutes
            ss      --- seconds
    output:uts      --- UT in seconds from 1970.1.1
    """
    year = int(float(year))
    mon  = int(float(mon))
    day  = int(float(day))
    hh   = int(float(hh))
    mm   = int(float(mm))
    ss   = int(float(ss))

    uts  = (datetime(year, mon, day, hh, mm, ss)\
                    - datetime(1970,1,1)).total_seconds()
    uts += 86400.0

    return uts

#---------------------------------------------------------------------------------------
#-- locreg: determines which phenomenological region the spacecraft is in            ---
#---------------------------------------------------------------------------------------

def locreg(kp, xsm, ysm, zsm):
    """
    determines which phenomenological region the spacecraft is in
    input   kp  --- kp index
            xsm --- solar magnetic coordinate x (in earth radius)
            ysm --- solar magnetic coordinate y (in earth radius)
            zsm --- solar magnetic coordinate z (in earth radius)
    output: xtail   --- satellite's X-coordinate in geotail system (Re)
            ytail   --- satellite's Y-coordinate in geotail system (Re)
            ztail   --- satellite's Z-coordinate in geotail system (Re)
            idloc   --- phenomenogical region location identification flag:
                            idloc = 1 if spacecraft is in solar wind
                            idloc = 2 if spacecraft is in magnetosheath
                            idloc = 3 if spacecraft is in magnetosphere
    """
#
#--- set the region identificaiton flag to 'no region'
#
    idloc = 0
#
#--- get the solar wind parameters used as inputs for the bow shock 
#--- and magnetopause boundary models
#
    [bx, by, bz, vx, vy, vz, dennum, swetemp, swptemp, \
     hefrac, swhtemp, bowang, dypres, abang, xhinge] = solwind(kp)
#
#--- transform the spacecrafts coordinates to a system aligned with the geotail
#--- rotate the bow shock by the aberration angle
#
    angrad         = -1.0 * abang * 0.01745329252
    [xtail, ytail] = rot8ang(angrad, xsm, ysm, xhinge)
    ztail          = zsm
#
#--- determin if the spacecraft is inside the magnetosphere
#
    vel = -1
    [xmgnp, ymgnp, zmgnp, dist, xid] = locate(dypres, vel, xtail, ytail, ztail)
#
#--- the spacecraft is inside the magnetosphere
#
    if xid == 1:
        idloc = 3
    else:
#
#--- determin if the spacecraft is in either the solar wind or
#--- the magnetosheath. calculate the bow shock radius and this point
#
        radbs = bowshk2(bx, by, bz, vx, vy, vz, dennum, swetemp,\
                        swptemp, hefrac, swhtemp, xtail, bowang)
#
#--- find the distance of the spacecraft from the aberrated x-axis
#
        distsc = math.sqrt(ytail**2 + ztail**2)
#
#--- the spacecraft is in the magnetoshearth
#
        if distsc <= radbs:
            idloc = 2
#
#--- the spacecraft is in the solar wind
#
        else:
            idloc = 1

    return [xtail, ytail, ztail, idloc]

#---------------------------------------------------------------------------------------
#-- solwind: get the solar wind parameters used as inputs for the bow shock           --
#---------------------------------------------------------------------------------------

def solwind(kp):
    """
    get the solar wind parameters used as inputs for the bow shock 
    and magnetopause boundary models
    input:  kp      --- kp index
    output: bx      --- the IMF B_x [nT]
            by      --- the IMF B_y [nT]
            bz      --- the IMF B_z [nT]
            vx      --- x component of solar wind bulk flow velocity (km/s).
            vy      --- y component of solar wind bulk flow velocity (km/s).
            vz      --- z component of solar wind bulk flow velocity (km/s).
            dennum  --- the solar wind proton number density [#/cm^3]
            swetemp --- the solar wind electron temperature [K]
            swptemp --- the solar wind proton temperature [K]
            hefrac  --- fraction of solar wind ions which are Helium ions
            swhtemp --- the temperature of the Helium [K]
            bowang  --- angle bow shock radius calculated (rad).
            dypres  --- solar wind dynamic pressure (nP).
            abang   --- aberration angle of magnetotail (deg).
            xhinge  --- hinge point of magnetotail (Re).
    """
    bx      = -5.
    by      =  6.
    bz      =  6.
    vx      = -500.
    vy      =  0.
    vz      =  0.
    dennum  =  8.
    swetemp =  1.4E+5
    swptemp =  1.2E+5
    hefrac  =  0.047
    swhtemp =  5.8E+5
    bowang  = pi

    if kp <= 4.0:
        dypres =    1.0
        abang  =    4.0
        xhinge =   14.0
        vx     = -400.0

    elif (kp > 4.0) and (kp <= 6.0):
        dypres1 =    1.0
        abang1  =    4.0
        vx1     = -400.0
        dypres2 =    4.0
        abang2  =    0.0
        vx2     = -500.0

        dypres  = y_interpolate(4.0, dypres1, 6.0, dypres2, kp, 1)
        abang   = y_interpolate(4.0, abang1,  6.0, abang2,  kp, 1)
        xhinge  =   14.0
        vx      = y_interpolate(4.0, vx1,     6.0, vx2,     kp, 1)

    else:
        dypres1 =    4.0
        dypres2 =   10.0
        dypres  = y_interpolate(6.0, dypres1, 9.0, dypres2, kp, 1)
        abang   =    0.0
        xhinge  =   14.0
        vx      = -500.0

    return [bx, by, bz, vx, vy, vz, dennum, swetemp, swptemp, \
             hefrac, swhtemp, bowang, dypres, abang, xhinge]

#---------------------------------------------------------------------------------------
#-- y_interpolate: interpolate and returns y coordinate correspoinding to xin         --
#---------------------------------------------------------------------------------------

def y_interpolate(x1, y1, x2, y2, xin, mode):
    """
    interpolate and returns y coordinate correspoinding to xin along 
    the 'line' defined by (x1, y1), (x2, y2)
    input:  x1, y1  --- starting coordindatse
            x2, y2  --- ending coordindates
            xin     --- position to be extimated
            mode    --- fitting mode;   1: linear
                                        2: semilog  log/linear
                                        3: semilog  linear/log
                                        4: log-log
    output: yint    --- estimated value
    """
#
#--- if log is rrequested, change them into log
#
    if (mode in [2, 4]) and (x1 > 0 and x2 > 0 and xin > 0):
        xx1  = math.log(x1)
        xx2  = math.log(x2)
        xxin = math.log(xin)
    else:
        xx1  = x1
        xx2  = x2
        xxin = xin

    if (mode in [3, 4]) and (y1 > 0 and y2 > 0):
        yy1  = math.log(y1)
        yy2  = math.log(y2)
    else:
        yy1  = y1
        yy2  = y2
#
#--- linear interpolation 
#
    yint = yy1 - (yy1 - yy2) * (xx1 - xxin) / (xx1 - xx2)
#
#--- if it is in log, convert back 
#
    if mode in [3, 4]:
        yint = math.exp(yint)

    return yint

#---------------------------------------------------------------------------------------
#-- rot8ang: rotates the 2-D vector about its hinge point in the xy-plane            ---
#---------------------------------------------------------------------------------------

def rot8ang(ang, x, y, xhinge):
    """
    rotates the 2-D vector about its hinge point in the xy-plane
    input:  ang     --- angle to rotate (rad)
            x       --- initial x value
            y       --- initial y value
            xhinge  --- x value of aberration hinge point
    output: xrot2   --- final x value
            yrot2   --- final y value
    """

    if x <= xhinge:
        xrot2 =  x * math.cos(ang) + y * math.sin(ang)
        yrot2 = -x * math.sin(ang) + y * math.cos(ang)
    else:
        xrot2 = x
        yrot2 = y

    return [xrot2, yrot2]

#---------------------------------------------------------------------------------------
#-- locate: defines the position of a point at the model magnetopause                ---
#---------------------------------------------------------------------------------------

def locate(xn_pd, vel, xgsm, ygsm, zgsm):
    """
    defines the position of a point at the model magnetopause, closest 
    to a given point of space and the distance between them 
    input:  xn_pd       --- either solar wind proton number density (vel > 0)
                            or the soloar wind ram pressure in nanopascals (vel < 0)
            vel         --- either solar wind velocity (km/sec) or any negative 
                            number, which indicates that xn_pd stands for the 
                            soloar wind pressure, rather than for the densityy
            xgsm, ygsm, zgsm --- coordinates of the observation point in earth radii
    output: XMGNP,YMGNP,ZMGNP   --- coordinates of a point at the magnetopause, closest
                                    to the point xgsm, ygsm, zgsm
            dist            --- the distance between the above two points in re
            xid             ---  1  xgsm, ygsm, zgsm lies inside of magnetopause
                                -1  xgsm, ygsm, zgsm lies outside of magnetopause

    ref. THE PRESSURE-DEPENDENT MAGNETOPAUSE IS THAT USED IN THE T96_01 MODEL
            CODED BY:  N.A. TSYGANENKO, AUG.1, 1995;  REVISED  JUNE 22, 1996
    """
#
#--- pd is the solar wind dynamic pressure (nano-pascals)
#
    if vel < 0.0:
        pd = xn_pd
    else:
        pd = 1.94e-6 * xn_pd * vel**2
#
#--- ratio of pd to the average pressure, assumed as 2 nPa
#
    rat = pd / 2.0
#
#--- the power in the scaling factor is the best-fit value obtained 
#--- from data in the t96_01 version of the model
#
    rat16 = rat**0.14
#
#--- values of the magnetopuase parameters for pd = 2 nPa
#
    a0  = 70.0
    s00 = 1.08
    x00 = 5.48  
#
#--- values f the magnetopause parameters, scaled to the actual pressure
#
    a   = a0  / rat16
    s0  = s00
    x0  = x00 / rat16
#
#--- the x-coordinate of the 'seam' between the ellipsoid and the cylinder
#---- (ref: N.A.TSYGANENKO, SOLUTION OF CHAPMAN-FERRARO PROBLEM FOR AN 
#----       ELLIPSOIDAL MAGNETOPAUSE, PLANET.SPACE SCI., V.37, P.1037, 1989)
#
    xm = x0 - a

    if (ygsm != 0.0) or (zgsm != 0.0):
        phi = math.atan2(ygsm, zgsm)
    else:
        phi = 0.0

    rho = math.sqrt(ygsm**2 + zgsm**2)

    if xgsm < xm: 
        xmgnp = xgsm
        rhomgnp = a * math.sqrt(s0**2 - 1)
        ymgnp   = rhomgnp * math.sin(phi)
        zmgnp   = rhomgnp * math.cos(phi)
        dist    = math.sqrt((xgsm - xmgnp)**2 + (ygsm - ymgnp)**2 + (zgsm - zmgnp)**2)

        if rhomgnp >= rho:
            xid =  1
        if rhomgnp < rho:
            xid = -1
    else:
        xksi  = (xgsm - x0) / a + 1
        xdzt  = rho / a
        sq1   = math.sqrt((1.0 + xksi)**2 + xdzt**2)
        sq2   = math.sqrt((1.0 - xksi)**2 + xdzt**2)
        sigma = 0.5 * (sq1 + sq2)
        tau   = 0.5 * (sq1 - sq2)
#
#--- calcurate(x, y, z) for the closest point at the magnetpause
#
        xmgnp   = x0 - a * (1.0 - s0 * tau)
        rhomgnp = a * math.sqrt((s0**2 - 1) * (1.0 - tau**2))
        ymgnp   = rhomgnp * math.sin(phi)
        zmgnp   = rhomgnp * math.cos(phi)
#
#--- calculate the shortest distance between the point, xgsm, xgsm, zgsm
#--- and the magnetpause
#
        dist    = math.sqrt((xgsm - xmgnp)**2 + (ygsm - ymgnp)**2 +  (zgsm - zmgnp)**2)
        if sigma > s0:
            xid = -1
        if sigma <= s0:
            xid =  1

    return [xmgnp, ymgnp, zmgnp, dist, xid]

#---------------------------------------------------------------------------------------
#-- bowshk2: give the bow shock radius at a given x of the bow shock                  --
#---------------------------------------------------------------------------------------

def bowshk2(bx, by, bz, vx, vy, vz, dennum, swetemp, swptemp, hefrac, swhtemp, xpos, bowang):
    """
    give the bow shock radius at a given x of the bow shock for any soloar wind donditions
    input:  bx      --- imf b_x [nT]
            by      --- imf b_y [nT]
            bz      --- imf b_z [nT]
            dennum  --- the solar wind proton number density [#/cm^3]
            swetemp --- the solar wind electron temperature [K]
            swptemp --- the solar wind proton temperature [K]
            hefrac  --- fraction of solar wind ions which are Helium ions
            swhtemp --- the temperature of the Helium [K]
            xpos    --- down tail distance cross section is calculated [Re]
            bpwagm  --- angle bow shock radius calculated (rad)
    output: bowrad  --- updated cylindrical radius (Re)

    Ref:
        L. Bennet et.al., "A Model of the Earth's Distant Bow Shock." 
        the Journal of Geophysical Research, 1997
        http://www.igpp.ucla.edu/galileo/newmodel.htm
    """
#
#--- convert the temperature from kelvins to eV
#
    etemp  = swetemp / 11600.0
    ptemp  = swptemp / 11600.0
    hetemp = swhtemp / 11600.0
#
#--- rameters that specify the shape of the base model of the bow shock.  
#--- The model has the form: rho**2 = a*x**2 - b*x + c
#--- The parameters are for the Greenstadt etal. 1990 model
#---         (GRL, Vol 17, p 753, 1990)
#---        a = 0.04
#---        b = 45.3
#---        c = 645.0

#
#--- set nominal eccentricity (eps) and latus rectum (xl)
#--- nose position (xn) and focus position (x0) for base model.
#
    eps =  1.0040
    xl  = 22.073117134
    x0  =  3.493725046
    xn  = 14.422071657
#
#--- calculate new parameters for cylindrical shok model after adjustment of eccentricity
#
    btot    = math.sqrt(bx * bx + by * by + bz * bz)            #--- btot in mks units
    btotcgs = btot * 1.0e-5                                     #--- btot in cgs units
    vtot1   = math.sqrt(vx * vx + vy * vy + vz * vz)            #--- vtot in km/sec
    vtot    = vtot1 * 1.0e+5                                    #--- vtot in cm/sec
#
#--- the following definitions of V_A and C_S are taken from
#--- Slavin & Holzer JGR Dec 1981.
#
    v_a   = btotcgs / math.sqrt(4.0 * pi * dennum * 1.67e-24 *(1.0 + hefrac * 4.0))
    pres1 = dennum * ((1.0 * hefrac * 2.0) * etemp \
                        + (1.0 + hefrac * hetemp) * ptemp) * 1.602e-12
    c_s   = math.sqrt(2.0 * pres1 / (dennum * 1.67e-24 * (1.0 + hefrac * 4.0)))
#
#--- calculate Mach number
#--- m_f s the fast magnetosonic speed for Theta_Bn = 90 degrees.
#
    m_a = vtot / v_a
    m_s = vtot / c_s
    m_f = vtot / math.sqrt(v_a * v_a + c_s * c_s)
#
#--- this is the modification for the change in the bow shock due
#--- to changing solar wind dynamic pressure.
#
#--- average values of number density and solar wind velocity
#
    xnave = 7.0
    vave  = 430.0
#
#--- FRACPRES is the fraction by which all length scales in the
#--- bow shock model will change due to the change in the solar
#--- wind dynamic pressure
#
    fracpres = ((xnave * vave * vave) / (dennum * vtot1 * vtot1))**(1.0/6.0)

    xn1 = xn * fracpres
    x0  = x0 * fracpres
    xl  = xl * fracpres
#
#--- calculate yet again the parameters for the updated model.
#
    a   = eps * eps -1
    b   = 2.0 * eps * xl + 2.0 * (eps * eps -1) * x0
    c   = xl * xl + 2.0 * eps * xl * x0 + (eps * eps -1) * x0 * x0
#
#--- calculate shock with correct pressure
#
    xtemp = a * xpos**2 - b * xpos + c
    if xtemp < 0.0:
        rho2 = 0.0
    else:
        rho2 = math.sqrt(xtemp)
#
#--- modify the bow shock for the change in flaring due to the
#--- change in local magnetosonic Mach number.
#
#--- first calculate the flaring angle for average solar wind conditions
#
    ave_ma    = 9.4
    ave_ms    = 7.2
    vwin_ave  = 4.300e7
    va_ave    = vwin_ave / ave_ma
    vs_ave    = vwin_ave / ave_ms
    bxave     = -3
    byave     =  3
    bzave     =  0
    a45       = 45.0 * dpr

    vms       = math.sqrt(0.5 * ((va_ave**2 + vs_ave**2) \
                + math.sqrt((va_ave**2 + vs_ave**2)**2 - 4.0 * va_ave**2 * vs_ave**2 \
                * (math.cos(a45)**2))))
    ave_mf    = vwin_ave / vms
    theta2    = math.asin(1.0 / ave_mf)
#
#--- calculate the cylindrical radius, and the y and z coordinates,
#--- of the shock for the angle BOWANG around the tail axis for a given
#--- XPOS.  Note that BOWANG is 0 along the positive z axis
#--- (BOWANG/DPR is the angle about the tail axis in degrees,
#--- RHOX is the updated cylindrical radius of the prevailing bow
#--- shock at downtail distance XPOS in Earth radii.
#
    [vms, vangle] = fast(bx, by, bz, v_a, c_s, vtot, bowang)

    m_f    = vtot / vms
    theta1 = math.asin(1.0 / m_f)
    xtemp1 = xn1 - xpos
    bowrad = rho2 + xtemp1 * (math.tan(theta1) - math.tan(theta2))

    return bowrad

#---------------------------------------------------------------------------------------
#-- fast: solve for the local fast magnetosonic speed                                 --
#---------------------------------------------------------------------------------------

def fast(bx, by, bz, va, vs, v0, alp):
    """
    solve the equations 21-24 in Bennets paper for the local fast magnetosonic speed
    It uses the simple bisection method to solve the equations accuracy to 0.01 in 
    Vms is good enough
    input:  bx      --- imf b_x [nT]
            by      --- imf b_y [nT]
            bz      --- imf b_z [nT]
            va
            vs
            v0
            alp     --- angle bow shock radius calculated (rad)

    output: vms     --- updated cylindrical radius (Re) of bow shock
            angle   ---

    Ref.L. Bennet et.al., "A Model of the Earth's Distant Bow Shock."
            Journal of Geophysical Research, 1997
            http://www.igpp.ucla.edu/galileo/newmodel.htm
    """
#
#--- three step sizes to narrow down the estimate
#
    step1  = 2.0
    step2  = 0.1
    step3  = 0.01
#
#--- first guess
#
    btot  = math.sqrt(bx*bx + by*by + bz*bz)
    vx    = 1.0
    va1   = va/1.0e5
    vs1   = vs/1.0e5
    v01   = v0/1.0e5

    v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
#
#--- start narrowing down the estimate
#
    if v_est > 0.0:
        while v_est > 0.0:
            vx   += step1
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est <= 0.0:
                break

        while v_est < 0.0:
            vx   -= step2
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est >= 0.0:
                break

        while v_est > 0.0:
            vx   += step3
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est <= 0.0:
                break

    elif v_est < 0.0:
        while v_est < 0.0:
            vx   += step1
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est >= 0.0:
                break

        while v_est > 0.0:
            vx   -= step2
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est <= 0.0:
                break

        while v_est < 0.0:
            vx   += step3
            v_est = bennets(va1, vs1, v01, vx, bx, by, bz, btot, alp)
            if v_est >= 0.0:
                break
#
#--- got a decent vx value estimate; compute magnetosonic speed
#
    vb    = math.sqrt(v01 * vx - vx**2)
    vy    = math.sin(alp) * vb
    vz    = math.cos(alp) * vb

    bot   = math.sqrt(bx * bx + by * by +  bz * bz) * math.sqrt(vx * vx + vy * vy + vz * vz)
    angle = math.acos((bx * vx + by * by + bz * vz) / bot)

    vms   = 1.0e5 * math.sqrt(vx * vx + vy * vy + vz * vz)

    return [vms, angle]

#---------------------------------------------------------------------------------------
#-- bennets: the equations in Bennets paper for the local fast magnetosonic speed     --
#---------------------------------------------------------------------------------------

def bennets(va1, vs1, v01, vx, bx, by, bz,  btot, alp):
    """
    the equations 21-24 in Bennets paper for the local fast magnetosonic speed
    """
    v_est = va1**2 + vs1**2 - 2.0 * v01 * vx \
            + math.sqrt((va1**2 + vs1**2)**2 \
            - 4.0 * va1**2 * vs1**2 * (vx * bx + by* math.sin(alp)\
            * math.sqrt(v01 * vx - vx**2) \
            + bz * math.cos(alp) \
            * math.sqrt(v01 * vx - vx**2))**2/(btot**2 * v01 * vx))

    return v_est
    
#---------------------------------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) > 1:
        ifile = sys.argv[1]
        out = cocochan(ifile)
        
        with open('test_out', 'w') as fo:
            fo.write(out[2])

