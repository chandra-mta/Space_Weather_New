C
C   this collection of subroutines/functions are taken from CRMFLX_V33.f
C   to supple sburoutines/functions needed in cococha.f and GEOPAKC.f
C
C
      SUBROUTINE BOWSHK2(BX,BY,BZ,VX,VY,VZ,DENNUM,SWETEMP,SWPTEMP,
     $  HEFRAC,SWHTEMP,XPOS,BOWANG,BOWRAD)
C
C
C     This routine is designed to give the bow shock radius, at a
C     given x, of the bow shock for any solar wind conditions.
c
C
C     REFERENCES:
C     This routine is adpated from the paper by L. Bennet et.al.,
C     "A Model of the Earth's Distant Bow Shock."  This paper was
C     to be published in the Journal of Geophysical Research, 1997.
C     Their source code was obtained from their web site at:
C     http://www.igpp.ucla.edu/galileo/newmodel.htm
C
C     This routine has been optimized for the simulation.
C
C     INPUTS:
C       BX      - the IMF B_x [nT]
C       BY      - the IMF B_y [nT]
C       BZ      - the IMF B_z [nT]
C       VX      - the IMF V_x [km/s]
C       VY      - the IMF V_y [km/s]
C       VZ      - the IMF V_z [km/s]
C       DENNUM  - the solar wind proton number density [#/cm^3]
C       SWETEMP - the solar wind electron temperature [K]
C       SWPTEMP - the solar wind proton temperature [K]
C       HEFRAC  - fraction of solar wind ions which are Helium ions
C       SWHTEMP - the temperature of the Helium [K]
C       XPOS    - down tail distance cross section is calculated [Re]
C       BOWANG  - angle bow shock radius calculated (rad).
C
C     OUTPUTS:
C       BOWRAD - updated cylindrical radius (Re).
C
C
      IMPLICIT NONE
C
      REAL SWETEMP,PTEMP,SWPTEMP,HETEMP,SWHTEMP,DPR,RADE,PI,GAMMA,XL,X0
      REAL XN,EPS,BTOTCGS,BX,BY,BZ,BTOT,VTOT,VX,VY,VZ,VTOT1,V_A,DENNUM
      REAL HEFRAC,PRES1,C_S,XNAVE,VAVE,FRACPRES,XN1,A,B,C,XTEMP,XPOS
      REAL RHO2,AVE_MA,AVE_MS,VWIN_AVE,VA_AVE,VS_AVE,BXAVE,BYAVE,BZAVE
      REAL VMS,AVE_MF,THET2,BOWANG,THET1,XTEMP1,RHOX,BOWRAD,ETEMP
C
      REAL M_A,M_S,M_F
C
C     Convert the temperature from Kelvins to eV.
      ETEMP = SWETEMP/11600.
      PTEMP = SWPTEMP/11600.
      HETEMP = SWHTEMP/11600.
      DPR = 6.2832/360.0
      RADE = 6378.0
      PI = 4.0*ATAN(1.0)
      GAMMA = 5.0/3.0
C
c     WRITE(*,*)
c     WRITE(*,*)' ENTER BOWSHK2!'
c     WRITE(*,*)' BX,BY,BZ,VX,VY,VZ = ',BX,BY,BZ,VX,VY,VZ
c     WRITE(*,*)' DENNUM,SWETEMP,SWPTEMP = ',DENNUM,SWETEMP,SWPTEMP
c     WRITE(*,*)' HEFRAC,SWHTEMP,XPOS = ',HEFRAC,SWHTEMP,XPOS
c     WRITE(*,*)' ETEMP,PTEMP,HETEMP = ',ETEMP,PTEMP,HETEMP
c     PAUSE  'PAUSED!!'
c     WRITE(*,*)
C
C     Parameters that specify the shape of the base model
C     of the bow shock.  The model has the form 
C     rho**2 = a*x**2 -b*x + c.
C
C     The parameters are for the Greenstadt etal. 1990 model
C     (GRL, Vol 17, p 753, 1990)
C
C     a = 0.04
C     b = 45.3
C     c = 645.0
C
C     Calculate nominal eccentricity (eps) and latus rectum (xl)
C     nose position (xn) and focus position (x0) for base model.
c
c     EPS = SQRT(A+1)
c     XL = SQRT(0.25*(B*B- 4.0*C*(EPS*EPS -1)))
c     X0 = (B - 2*EPS*XL)/(2.0*(EPS*EPS -1))
c     XN = (XL/(1.0 + EPS)) + X0
c
C     The above variables are constants.
      XL = 22.073117134
      X0 = 3.493725046
      XN = 14.422071657
C
C     Here the eccentricity of the base model is adjusted.  See
C     the paper for an explanation
C
      EPS = 1.0040
C
C     Calculate new paramaters for cylindrical shock model after
C     adjustment of eccentricity.
C
C     Calculate parameters of interest.
C
      BTOTCGS = SQRT(BX*BX + BY*BY + BZ*BZ)*1.E-5   ! btot in cgs units
      BTOT = BTOTCGS*1.E+5                          ! btot in mks units
      VTOT = SQRT(VX*VX + VY*VY + VZ*VZ)*1.E+5      ! vtot in cm/sec
      VTOT1 = SQRT(VX*VX + VY*VY + VZ*VZ)           ! vtot in km/sec
C
C     The following definitions of V_A and C_S are taken from
C     Slavin & Holzer JGR Dec 1981.
C
      V_A = BTOTCGS/SQRT(4.0*PI*DENNUM*1.67E-24*(1.0 + HEFRAC*4.0))
      PRES1 = DENNUM*((1.0 + HEFRAC*2.0)*ETEMP + 
     1        (1 + HEFRAC*HETEMP)*PTEMP)*1.602E-12
      C_S = SQRT(2.0*PRES1/(DENNUM*1.67E-24*(1.0 + HEFRAC*4.0)))
C
C     Calculate Mach numbers.
C
C     M_F is the fast magnetosonic speed for Theta_Bn = 90 degrees.
C
      M_A = VTOT/V_A
      M_S = VTOT/C_S
      M_F = VTOT/SQRT(V_A*V_A + C_S*C_S)
C
C     This is the modification for the change in the bow shock due
C     to changing solar wind dynamic pressure.
C
C     Average values of number density and solar wind velocity
      XNAVE = 7.
      VAVE = 430.
C
C     FRACPRES is the fraction by which all length scales in the
C     bow shock model will change due to the change in the solar
C     wind dynamic pressure
C
      FRACPRES = ((XNAVE*VAVE*VAVE)/(DENNUM*VTOT1*VTOT1))**(1.0/6.0)
C
      XN1 = XN*FRACPRES
      X0  = X0*FRACPRES
      XL  = XL*FRACPRES
C
C     Calculate yet again the parameters for the updated model.
C
      A = EPS*EPS -1
      B = 2.0*EPS*XL + 2.0*(EPS*EPS -1)*X0
      C = XL*XL + 2.0*EPS*XL*X0 + (EPS*EPS -1)*X0*X0
C
C     Calculate shock with correct pressure.
C
      XTEMP = A*XPOS**2 - B*XPOS +C
      IF (XTEMP.LT.0) then
        RHO2 = 0
      ELSE
        RHO2 = SQRT(XTEMP)
      END IF
C
C     Modify the bow shock for the change in flaring due to the
C     change in local magnetosonic Mach number.
C
C     First calculate the flaring angle for average solar wind
C     conditions
C
      AVE_MA = 9.4
      AVE_MS = 7.2
      VWIN_AVE = 430.*1.E+5
      VA_AVE = VWIN_AVE/AVE_MA
      VS_AVE = VWIN_AVE/AVE_MS
      BXAVE = -3
      BYAVE = 3
      BZAVE = 0
C
      VMS = SQRT(0.5*((VA_AVE**2 + VS_AVE**2) + SQRT((VA_AVE**2 + 
     1    VS_AVE**2)**2 - 4.0*VA_AVE**2*VS_AVE**2*(COS(45*DPR)**2))))
C
      AVE_MF = VWIN_AVE/VMS
      THET2 = ASIN(1.0/AVE_MF)
C
C     Now calculate the cylindrical radius, and the y and z coordinates,
C     of the shock for the angle BOWANG around the tail axis for a given
C     XPOS.  Note that BOWANG is 0 along the positive z axis
C     (BOWANG/DPR is the angle about the tail axis in degrees,
C     RHOX is the updated cylindrical radius of the prevailing bow
C     shock at downtail distance XPOS in Earth radii.
C    
      CALL FAST(BX,BY,BZ,V_A,C_S,VTOT,BOWANG,VMS)
C
      M_F = VTOT/VMS
      THET1 = ASIN(1.0/M_F)
      XTEMP1 = XN1 - XPOS
      RHOX = RHO2 + XTEMP1*(TAN(THET1) - TAN(THET2))
      BOWRAD = RHOX
c     WRITE(*,*)' XPOS,BOWANG,BOWRAD = ',XPOS,BOWANG,BOWRAD
C
 2000 CONTINUE 
C
      RETURN 
      END
C

C-----------------------------------------------------------------------------


      SUBROUTINE LOCATE(XN_PD,VEL,XGSM,YGSM,ZGSM,XMGNP,YMGNP,ZMGNP,DIST,
     *  ID)
C
C     THIS SUBROUTINE DEFINES THE POSITION OF A POINT (XMGNP,YMGNP,ZMGNP)
C            AT THE MODEL MAGNETOPAUSE, CLOSEST TO A GIVEN POINT OF SPACE
C               (XGSM,YGSM,ZGSM),   AND THE DISTANCE BETWEEN THEM (DIST)
C
C INPUT:  XN_PD - EITHER SOLAR WIND PROTON NUMBER DENSITY (PER C.C.) (IF VEL>0)
C                    OR THE SOLAR WIND RAM PRESSURE IN NANOPASCALS   (IF VEL<0)
C         VEL - EITHER SOLAR WIND VELOCITY (KM/SEC)
C                  OR ANY NEGATIVE NUMBER, WHICH INDICATES THAT XN_PD STANDS
C                     FOR THE SOLAR WIND PRESSURE, RATHER THAN FOR THE DENSITY
C
C         XGSM,YGSM,ZGSM - COORDINATES OF THE OBSERVATION POINT IN EARTH RADII
C
C  OUTPUT: XMGNP,YMGNP,ZMGNP - COORDINATES OF A POINT AT THE MAGNETOPAUSE,
C                                    CLOSEST TO THE POINT  XGSM,YGSM,ZGSM
C          DIST -  THE DISTANCE BETWEEN THE ABOVE TWO POINTS, IN RE,
C          ID -    INDICATOR; ID=+1 AND ID=-1 MEAN THAT THE POINT
C                       (XGSM,YGSM,ZGSM)  LIES INSIDE OR OUTSIDE
C                        THE MODEL MAGNETOPAUSE, RESPECTIVELY
C
C   THE PRESSURE-DEPENDENT MAGNETOPAUSE IS THAT USED IN THE T96_01 MODEL
C
c            CODED BY:  N.A. TSYGANENKO, AUG.1, 1995;  REVISED  JUNE 22, 1996
C
      IMPLICIT NONE
      REAL DIST, PD, RAT, RAT16, VEL, XN_PD, A, A0, S00, X00, S0, X0
      REAL XM, PHI, ZMGNP, YMGNP, XMGNP, ZGSM, YGSM, XGSM, RHO
      REAL RHOMGNP, XKSI, XDZT, SQ1, SQ2, SIGMA, TAU
      INTEGER ID
C
      IF (VEL.LT.0.) THEN
       PD=XN_PD
                  ELSE
       PD=1.94E-6*XN_PD*VEL**2  ! PD IS THE SOLAR WIND DYNAMIC PRESSURE
C                                      (IN NANOPASCALS)
      ENDIF
C
      RAT=PD/2.0  ! RATIO OF PD TO THE AVERAGE PRESSURE, ASSUMED AS 2 nPa
C
      RAT16=RAT**0.14 ! THE POWER IN THE SCALING FACTOR IS THE BEST-FIT VALUE
C                         OBTAINED FROM DATA IN THE T96_01 VERSION OF THE MODEL
C
      A0=70.
      S00=1.08
      X00=5.48    !  VALUES OF THE MAGNETOPAUSE PARAMETERS FOR  PD = 2 nPa
C
      A=A0/RAT16
      S0=S00
      X0=X00/RAT16   !  VALUES OF THE MAGNETOPAUSE PARAMETERS, SCALED TO THE
C                         ACTUAL PRESSURE
C
       XM=X0-A    !  THIS IS THE X-COORDINATE OF THE "SEAM" BETWEEN THE
C                             ELLIPSOID AND THE CYLINDER
C
C        (FOR DETAILS ON THE ELLIPSOIDAL COORDINATES, SEE THE PAPER:
C            N.A.TSYGANENKO, SOLUTION OF CHAPMAN-FERRARO PROBLEM FOR AN
C             ELLIPSOIDAL MAGNETOPAUSE, PLANET.SPACE SCI., V.37, P.1037, 1989).
C
          IF (YGSM.NE.0..OR.ZGSM.NE.0.) THEN
             PHI=ATAN2(YGSM,ZGSM)
              ELSE
             PHI=0.
          ENDIF
C
          RHO=SQRT(YGSM**2+ZGSM**2)
C
         IF (XGSM.LT.XM) THEN
           XMGNP=XGSM
           RHOMGNP=A*SQRT(S0**2-1)
           YMGNP=RHOMGNP*SIN(PHI)
           ZMGNP=RHOMGNP*COS(PHI)
           DIST=SQRT((XGSM-XMGNP)**2+(YGSM-YMGNP)**2+(ZGSM-ZMGNP)**2)
           IF (RHOMGNP.GT.RHO) ID=+1
           IF (RHOMGNP.LT.RHO) ID=-1
           RETURN
         ENDIF
C
          XKSI=(XGSM-X0)/A+1.
          XDZT=RHO/A
          SQ1=SQRT((1.+XKSI)**2+XDZT**2)
          SQ2=SQRT((1.-XKSI)**2+XDZT**2)
          SIGMA=0.5*(SQ1+SQ2)
          TAU=0.5*(SQ1-SQ2)
C
C  NOW CALCULATE (X,Y,Z) FOR THE CLOSEST POINT AT THE MAGNETOPAUSE
C
          XMGNP=X0-A*(1.-S0*TAU)
          RHOMGNP=A*SQRT((S0**2-1.)*(1.-TAU**2))
          YMGNP=RHOMGNP*SIN(PHI)
          ZMGNP=RHOMGNP*COS(PHI)
C
C  NOW CALCULATE THE SHORTEST DISTANCE BETWEEN THE POINT XGSM,YGSM,ZGSM AND THE
C            MAGNETOPAUSE
C
      DIST=SQRT((XGSM-XMGNP)**2+(YGSM-YMGNP)**2+(ZGSM-ZMGNP)**2)
C
      IF (SIGMA.GT.S0) ID=-1   !  ID=-1 MEANS THAT THE POINT LIES OUTSIDE
      IF (SIGMA.LT.S0) ID=+1   !  ID=+1 MEANS THAT THE POINT LIES INSIDE
C                                           THE MAGNETOSPHERE
      RETURN
      END

C--------------------------------------------------------------------------------

C
      SUBROUTINE LOCREG(XKP,XGSM,YGSM,ZGSM,XTAIL,YTAIL,ZTAIL,IDLOC)
C
C     This routine determines which phenomenological region the
C     spacecraft is in.
C
C     Input:
C       XKP     - Kp index (real value between 0 & 9).
C       XGSM    - satellite's X-coordinate (Re).
C       YGSM    - satellite's Y-coordinate (Re).
C       ZGSM    - satellite's Z-coordinate (Re).
C
C     Outputs:
C       XTAIL   - satellite's X-coordinate in geotail system (Re).
C       YTAIL   - satellite's Y-coordinate in geotail system (Re).
C       ZTAIL   - satellite's Z-coordinate in geotail system (Re).
C       IDLOC   - phenomenogical region location identification flag:
C                 IDLOC = 1 if spacecraft is in solar wind
C                 IDLOC = 2 if spacecraft is in magnetosheath
C                 IDLOC = 3 if spacecraft is in magnetosphere
C
      IMPLICIT NONE
      REAL XKP, XGSM, YGSM, ZGSM, XTAIL, YTAIL, ZTAIL, XHINGE
      REAL VEL, DIST, DYPRES, XMGP, YMGP, ZMGP, ABANG, ANGRAD
      REAL DISTSC, VZ, VX, VY, BZ, BY, BX, SWETEMP, SWPTEMP, HEFRAC
      REAL SWHTEMP, BOWANG, RADBS, DENNUM
      INTEGER ID, IDLOC
C
c     WRITE(*,*)
c     WRITE(*,*)' Entered LOCREG!'
c     WRITE(*,*)' XKP,XGSM,YGSM,ZGSM = ',
c    $            XKP,XGSM,YGSM,ZGSM
c     PAUSE
C
C     Set the region identification flag to "no region".
      IDLOC = 0
C
C     Get the solar wind parameters used as inputs for the bow shock
C     and magnetopause boundary models for this value of Kp.
C
      CALL SOLWIND(XKP,BX,BY,BZ,VX,VY,VZ,DENNUM,SWETEMP,SWPTEMP,
     $  HEFRAC,SWHTEMP,BOWANG,DYPRES,ABANG,XHINGE)
C
C     Transform the spacecrafts coordinates to a system aligned
C     with the geotail.
C     Rotate the bow shock by the aberration angle.
      ANGRAD = -ABANG * 0.01745329252
      CALL ROT8ANG(ANGRAD,XGSM,YGSM,XHINGE,XTAIL,YTAIL)
      ZTAIL = ZGSM
C
C     Determine if the spacecraft is inside the magnetosphere.  Use the
C     Tsyganenko magnetopause model.
C
      VEL = -1.
      CALL LOCATE(DYPRES,VEL,XTAIL,YTAIL,ZTAIL,XMGP,YMGP,ZMGP,DIST,ID)
C
      IF(ID.EQ.+1) THEN
C       The spacecraft is inside the magnetosphere.
        IDLOC = 3
      ELSE
C       Determine if the spacecraft is in either the solar wind or
C       the magnetosheath.  Calculate the bow shock radius at this point.
C
        CALL BOWSHK2(BX,BY,BZ,VX,VY,VZ,DENNUM,SWETEMP,SWPTEMP,HEFRAC,
     $    SWHTEMP,XTAIL,BOWANG,RADBS)
C
C       Find the distance of the spacecraft from the aberrated x-axis.
        DISTSC = SQRT(YTAIL**2 + ZTAIL**2)
C
        IF(DISTSC.LE.RADBS) THEN
C         The spacecraft is in the magnetosheath.
          IDLOC = 2
        ELSE
C         The spacecraft is in the solar wind.
          IDLOC = 1
        END IF
      END IF
C
      RETURN
      END
C

C-------------------------------------------------------------------------


      SUBROUTINE ROT8ANG(ANG,X,Y,XHINGE,XROT2,YROT2)
C
C     This routine rotates the 2-D vector about its hinge point in the
C     xy-plane.
C
C     INPUTS:
C       ANG    - angle to rotate (rad).
C       X      - initial x value.
C       Y      - initial y value.
C       XHINGE - x value of aberration hinge point.
C
C     OUTPUTS:
C       XROT2  - final x value.
C       YROT2  - final y value.
C
      IMPLICIT NONE
C
      REAL X, Y, ANG, XHINGE, YROT2, XROT2
C
c     WRITE(*,*)
c     WRITE(*,*)' ENTERED ROT8ANG!'
c     WRITE(*,*)' ANG,X,Y,XHINGE = ',ANG,X,Y,XHINGE
c     PAUSE
C
C
      IF(X.LE.XHINGE) THEN
        XROT2 = X*COS(ANG) + Y*SIN(ANG)
        YROT2 = -X*SIN(ANG) + Y*COS(ANG)
      ELSE
        XROT2 = X
        YROT2 = Y
      END IF
c     WRITE(*,*)' ANG,XROT2,YROT2 = ',ANG,XROT2,YROT2
c     PAUSE
      RETURN
      END
C
C





      SUBROUTINE SOLWIND(XKP,BX,BY,BZ,VX,VY,VZ,DENNUM,SWETEMP,SWPTEMP,
     $  HEFRAC,SWHTEMP,BOWANG,DYPRES,ABANG,XHINGE)
C
C     Get the solar wind parameters used as inputs for the bow shock
C     and magnetopause boundary models.
C
C     Input:
C       XKP     - Kp index (real value between 0 & 9).
C
C     Outputs:
C       BX      - the IMF B_x [nT]
C       BY      - the IMF B_y [nT]
C       BZ      - the IMF B_z [nT]
C       VX      - x component of solar wind bulk flow velocity (km/s).
C       VY      - y component of solar wind bulk flow velocity (km/s).
C       VZ      - z component of solar wind bulk flow velocity (km/s).
C       DENNUM  - the solar wind proton number density [#/cm^3]
C       SWETEMP - the solar wind electron temperature [K]
C       SWPTEMP - the solar wind proton temperature [K]
C       HEFRAC  - fraction of solar wind ions which are Helium ions
C       SWHTEMP - the temperature of the Helium [K]
C       BOWANG  - angle bow shock radius calculated (rad).
C       DYPRES  - solar wind dynamic pressure (nP).
C       ABANG   - aberration angle of magnetotail (deg).
C       XHINGE  - hinge point of magnetotail (Re).
C
      IMPLICIT NONE
C
      INCLUDE 'PI.PAR'
C
      REAL BX, BY, BZ, VX, VY, VZ, DENNUM, SWETEMP, SWPTEMP
      REAL HEFRAC, SWHTEMP, DYPRES, XKP, ABANG, XHINGE
      REAL DYPRES1, DYPRES2, ABANG1, ABANG2, VX1, VX2, YINT
      REAL BOWANG
C
      BX = -5.
      BY = +6.
      BZ = +6.
      VX = -500.
      VY = 0.
      VZ = 0.
      DENNUM = 8.
      SWETEMP = 1.4E+5
      SWPTEMP = 1.2E+5
      HEFRAC = 0.047
      SWHTEMP = 5.8E+5
      BOWANG = PI
C
      IF(XKP.LE.4.) THEN
        DYPRES = 1.0
        ABANG = 4.0
        XHINGE = +14.
        VX = -400.
      ELSE IF((XKP.GT.4).AND.(XKP.LE.6.)) THEN
        DYPRES1 = 1.0
        ABANG1 = 4.0
        VX1 = -400.
        DYPRES2 = 4.0
        ABANG2 = 0.0
        VX2 = -500.
C
        DYPRES = YINT(4.,DYPRES1,6.,DYPRES2,XKP,1)
        ABANG  = YINT(4.,ABANG1,6.,ABANG2,XKP,1)
        XHINGE = +14.
        VX     = YINT(4.,VX1,6.,VX2,XKP,1)
      ELSE
        DYPRES1 = 4.0
        DYPRES2 = 10.0
C
        DYPRES = YINT(6.,DYPRES1,9.,DYPRES2,XKP,1)
        ABANG = 0.0
        XHINGE = +14.
        VX = -500.
      END IF
C
      RETURN
      END



      REAL FUNCTION YINT(X1,Y1,X2,Y2,XIN,MODE)
C         
C *** FUNCTION INTERPOLATE -- RETURNS Y-COORDINATE CORRESPONDING TO XIN         
C *** ALONG THE "LINE" DEFINED BY (X1, Y1), (X2, Y2).  MODE REFERS TO 
C *** INTERPOLATION MODE WHERE  1 IS LINEAR       
C ***                           2 IS SEMILOG - LOG/LINEAR   
C ***                           3 IS SEMILOG - LINEAR/LOG   
C ***                           4 IS LOG/LOG      
C         
C
      IMPLICIT NONE
      INTEGER MODE
      REAL X1, Y1, X2, Y2, XIN
      REAL XX1, XX2, XXIN, YY1, YY2
C
C *** IF MODE = 2 OR 4 THEN TAKE LOG OF X1, X2, AND XIN     
        IF ((MODE .EQ. 2) .OR. (MODE .EQ. 4)) THEN
         XX1  = ALOG(X1)
         XX2  = ALOG(X2)
         XXIN = ALOG(XIN)
      ELSE
         XX1  = X1
         XX2  = X2
         XXIN = XIN
      ENDIF
C         
C *** IF MODE = 3 OR 4 THEN TAKE LOG OF Y1 AND Y2 
        IF ((MODE .EQ. 3) .OR. (MODE .EQ. 4)) THEN
         YY1 = ALOG(Y1)
         YY2 = ALOG(Y2)
      ELSE
         YY1 = Y1
         YY2 = Y2
      ENDIF
C         
C *** LINEAR INTERPOLATION FORMULA      
C         
      YINT = YY1 - (YY1 - YY2) * (XX1 - XXIN) / (XX1 - XX2)
      IF ((MODE .EQ. 3) .OR. (MODE .EQ. 4)) YINT = EXP(YINT)
C         
      RETURN
      END

C
C
      SUBROUTINE FAST(bx,by,bz,va,vs,v0,alp,vms)

C       subroutine to solve the equations 21-24 in Bennets paper for the
C       local fast magnetosonic speed
C
C       It uses the simple bisection method to solve the equations.
C       accuracy to 0.01 in V_ms is good enough 
C
C     This routine is adpated from the paper by L. Bennet et.al.,
C     "A Model of the Earth's Distant Bow Shock."  This paper was
C     to be published in the Journal of Geophysical Research, 1997.
C     This source code is from their web site at:
C     http://www.igpp.ucla.edu/galileo/newmodel.htm
C
      IMPLICIT NONE
C
      REAL btot,bx,by,va1,va,vs1,vs,v01,v0,func,alp,step1,step2
      REAL step3,vy,vz,angle,vms,bz,vx,dpr
C

      dpr = 6.2832/360.0

      btot = sqrt(bx*bx + by*by + bz*bz)
      vx = 1
      va1 = va/1.0e5
      vs1 = vs/1.0e5
      v01 = v0/1.0e5

      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))

      step1 = 2.0
      step2 = 0.1
      step3 = 0.01

      if (func.gt.0) then
 100     vx = vx + step1
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.gt.0) goto 100

 200     vx = vx - step2
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.lt.0) goto 200

 300     vx = vx + step3
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.gt.0) goto 300

         goto 1000

      end if

      if (func.lt.0) then
 400     vx = vx + step1
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.lt.0) goto 400
 
 500     vx = vx - step2 
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.gt.0) goto 500 
 
 600     vx = vx + step3
      func = va1**2 + vs1**2 - 2.0*v01*vx + sqrt((va1**2 + vs1**2)**2 
     1     - 4.0*va1**2*vs1**2*(vx*bx + by*sin(alp)*sqrt(v01*vx 
     2     - vx**2) + bz*cos(alp)*sqrt(v01*vx 
     3     - vx**2))**2/(btot**2*v01*vx))
         if (func.lt.0) goto 600

         goto 1000
 
      end if

 1000 continue

      vy = sin(alp)*sqrt(v01*vx - vx**2)
      vz = cos(alp)*sqrt(v01*vx - vx**2)

      angle = acos((bx*vx + by*vy + bz*vz)/(sqrt(bx*bx + by*by 
     1      +bz*bz)*sqrt(vx*vx + vy*vy + vz*vz)))

      vms = 1.0e5*sqrt(vx*vx + vy*vy + vz*vz)

      return
      end
C
C
