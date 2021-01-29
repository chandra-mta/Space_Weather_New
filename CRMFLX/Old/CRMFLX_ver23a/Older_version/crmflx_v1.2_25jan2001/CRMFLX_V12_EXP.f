      SUBROUTINE CRMFLX(LUNIT,XKP,XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $        FSWIMN,FSWI95,FSWI50,FSWISD,IUSEMSH,SMOOTH1,NFLXGET,
     $        NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $        FLUX95,FLUX50,FLUXSD)
C
C     CRMFLX Vers. 1.2 (Experimental) - 18 January 2001
C
C     ******************************************************************
C     Code Change History:
C
C        9 Sept. 2000 -> fixed error in 50% & 95% flux for solar wind
C                        and magnetosheath.
C
C       13 Sept. 2000 -> changed CRMFLX`s interface so that the data
C                        initialization routine is called by the main
C                        routine, CRMFLX. This relieves the user from
C                        the responsibility of reinitializing the data
C                        arrays if the species type changes.
C
C       13 Sept. 2000 -> changed CRMFLX`s interface so that the user
C                        has the option of providing the solar wind
C                        and/or the magnetosheath uniform flux,
C                        instead of using the modeled data.
C
C       11 Oct. 2000  -> corrected error that appeared as data drop-outs
C                        in flux scenes (e.g., Zgsm=0, Kp = 6, XY slice).
C                        NUMSCAL was incorrectly set to 1 instead of 2,
C                        as intended.  This led to singularities at the
C                        Kp scaling sector sites.
C
C       11 Jan. 2001  -> (1) added smoothing algorithm control variables
C                            to CRMFLX`s interface.
C                        (2) removed all inputs to CRMFLX that allow
C                            the user to control magnetosheath flux
C                            calculations.
C                        (3) IUSESW has been changed so that the user
C                            has the option of supplying a uniform
C                            value of solar wind (ACE data), use the
C                            CRMFLX database, or sum the ACE data with
C                            the database values.
C                        (4) CRMFLX now opens 3 separate databse files,
C                            magnetosphere, magnetosheath, solar wind.
C                            LUNIT has been changed from a scalar to
C                            LUNIT(3) to accommodate this change.
C
C       23 Feb. 2001  -> (1) added IUSEMSH back to the interface.
C                        (2) changed near-neighbor selection algorithm
C                            so there are no Zgsm layers if Xgsm > 0.
C     ******************************************************************
C
C     This routine calculates the ion flux as a function of the
C     magnetic activity Kp index.
C
C     *** NOTE ***  Subroutine MSPINIT, MSHINIT, SWINIT must be called
C     once prior to the first call to CRMFLX so that the data arrays are
C     loaded!
C
C     Inputs:
C       LUNIT   - Array of unit numbers used in opening CRM`s database
C                 files.
C                 LUNIT(1) = solar wind database unit number
C                 LUNIT(2) = magnetosheath database unit number
C                 LUNIT(3) = magnetosphere database unit number.
C
C       XKP     - Kp index user desires output for.
C
C       XGSM    - satellite`s X-coordinate (Re).
C
C       YGSM    - satellite`s Y-coordinate (Re).
C
C       ZGSM    - satellite`s Z-coordinate (Re).
C
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO.
C
C       IUSESW  - flag for control of solar wind flux calculation:
C          IUSESW = 0 if (uniform flux) analytic solar wind model used.
C          IUSESW = 1 if user supplied uniform solar wind flux value used.
C          IUSESW = 2 if solar wind database used.
C          IUSESW = 3 if sum of solar wind database value and user
C                     supplied uniform solar wind flux value used.
C          IUSESW = 4 if sum of (uniform flux) analytic solar wind model
C                     and user supplied uniform solar wind flux value used.
C
C       FSWIMN  - user supplied mean uniform solar wind flux for the
C                 selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWI95  - user supplied 95% level uniform solar wind flux for
C                 the selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWI50  - user supplied 50% level uniform solar wind flux for
C                 the selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWISD  - user supplied std. dev. of uniform solar wind flux
C                 for the selected species (#/[cm^2-sec-sr-MeV]).
C
C       IUSEMSH - flag for control of magnetosheath flux calculation:
C          IUSEMSH = 0 if (uniform flux) analytic magnetosheath model used.
C          IUSEMSH = 1 if user supplied uniform solar wind flux value used.
C          IUSEMSH = 2 if magnetosheath database used.
C          IUSEMSH = 3 if sum of magnetosheath database value and user
C                      supplied uniform solar wind flux value used.
C          IUSEMSH = 4 if sum of (uniform flux) analytic magnetosheath model
C                      and user supplied uniform solar wind flux value used.
C
C       SMOOTH1 - flag for control of database smoothing filter:
C              SMOOTH1 = 0 if no data smoothing is used.
C              SMOOTH1 = 1 if spike rejection and near neighbor flux.
C              SMOOTH1 = 2 if spike rejection with range weighted
C                           scaling of flux.
C              SMOOTH1 = 3 if spike rejection with average flux.
C              SMOOTH1 = 4 if spatial average of flux in volume
C                           specified by RNGTOL.
C              SMOOTH1 = 5 if spatial average of flux in volume
C                           specified by RNGTOL, with the specified
C                           number of high and low flux values inside
C                           the volume dropped first.
C              SMOOTH1 = 6 if spatial averaging of flux in volume
C                           specified by RNGTOL, with percentile
C                           threshold limits on flux values.
C
C       NFLXGET - number of flux values to get for smoothing filter
C                  (used if SMOOTH1 = 1,2, or 3)
C
C       NDROPHI - number of high flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2,3, or 5).
C
C       NDROPLO - number of low flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2,3, or 5).
C
C       LOGFLG  - flag controlling how flux average is performed
C                  (used if SMOOTH1 = 2,3,4,5, or 6).
C              LOGFLG = 1 if log10 of flux values used.
C              LOGFLG = 2 if linear flux values used.
C
C       RNGTOL  - range tolerance from near-neigbor used in spatial
C                  averaging of database (Re)
C                  (used if SMOOTH1 = 4,5, or 6).
C
C       FPCHI   - upper percentile limit for spatial averaging of flux
C                  (used if SMOOTH1 = 6).
C
C       FPCLO   - lower percentile limit for spatial averaging of flux
C                  (used if SMOOTH1 = 6).
C
C     Outputs:
C       IDLOC   - phenomenogical region location identification flag:
C              IDLOC = 1 if spacecraft is in solar wind
C              IDLOC = 2 if spacecraft is in magnetosheath
C              IDLOC = 3 if spacecraft is in magnetosphere.
C
C       FLUXMN  - mean flux (#/[cm^2-sec-sr-MeV]) for selected species.
C
C       FLUX95  - 95% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C
C       FLUX50  - 50% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C
C       FLUXSD  - standard deviation of flux for selected species.
C
C
C     Set the Kp tolerance variable.  If the Kp value for which output
C     is desired changes by more than this value, the Kp scaling
C     parameters are recalculated.
      PARAMETER (XKPTOL = 0.3)
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'MAXPNT.PAR'
C
C     CRMDAT1.CMN contains the solar wind flux database arrays.
      INCLUDE 'CRMDAT1.CMN'
C
C     CRMDAT2.CMN contains the magnetosheath flux database arrays.
      INCLUDE 'CRMDAT2.CMN'
C
C     CRMDAT3.CMN contains the magnetosphere flux database arrays.
      INCLUDE 'CRMDAT3.CMN'
C
      REAL SECTX1(NUMSEC),SECTY1(NUMSEC)
      REAL SCMEAN1(NUMSEC,MAXKP),SC951(NUMSEC,MAXKP)
      REAL SC501(NUMSEC,MAXKP),SCSIG1(NUMSEC,MAXKP)
C
      REAL SECTX2(NUMSEC),SECTY2(NUMSEC)
      REAL SCMEAN2(NUMSEC,MAXKP),SC952(NUMSEC,MAXKP)
      REAL SC502(NUMSEC,MAXKP),SCSIG2(NUMSEC,MAXKP)
C
      REAL SECTX3(NUMSEC),SECTY3(NUMSEC)
      REAL SCMEAN3(NUMSEC,MAXKP),SC953(NUMSEC,MAXKP)
      REAL SC503(NUMSEC,MAXKP),SCSIG3(NUMSEC,MAXKP)
C
      INTEGER LUNIT(3),SMOOTH1,FPCHI,FPCLO
C
C     Initialize the Kp save variables.
      DATA XKPSAV1/100./
      DATA XKPSAV2/100./
      DATA XKPSAV3/100./
C
C     Initialize the species type save variables.
      DATA ISPSAV0/100/
      DATA ISPSAV1/100/
      DATA ISPSAV2/100/
      DATA ISPSAV3/100/
C
      SAVE XKPSAV1,XKPSAV2,XKPSAV3,FLXMN1,FLX951,FLX501,FLXSD1,
     $ FLXMN2,FLX952,FLX502,FLXSD2,ISPSAV0,ISPSAV1,ISPSAV2,ISPSAV3,
     $ SECTX1,SECTY1,SCMEAN1,SC951,SC501,SCSIG1,SECTX2,SECTY2,
     $ SCMEAN2,SC952,SC502,SCSIG2,SECTX3,SECTY3,SCMEAN3,SC953,
     $ SC503,SCSIG3,NSECTR1,NSECTR2,NSECTR3
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED CRMFLX!'
D     WRITE(*,*)' LUNIT,XKP,XGSM,YGSM,ZGSM = ',LUNIT,XKP,XGSM,YGSM,ZGSM
D     WRITE(*,*)' ISPECI,IUSESW,IUSEMSH = ',ISPECI,IUSESW,IUSEMSH
D     WRITE(*,*)' FSWIMN,FSWI95,FSWI50,FSWISD = ',
D    $            FSWIMN,FSWI95,FSWI50,FSWISD
D     WRITE(*,*)' SMOOTH1,NFLXGET,NDROPHI,NDROPLO = ',
D    $            SMOOTH1,NFLXGET,NDROPHI,NDROPLO
D     WRITE(*,*)' LOGFLG,RNGTOL,FPCHI,FPCLO = ',
D    $            LOGFLG,RNGTOL,FPCHI,FPCLO
D     PAUSE
      ISPDIFF = ISPECI - ISPSAV0
      IF(ISPDIFF.NE.0) THEN
C       Read solar wind database.
        CALL SWINIT(LUNIT(1),ISPECI)
C       Read magnetosheath database.
        CALL MSHINIT(LUNIT(2),ISPECI)
        ISPSAV0 = ISPECI
C       Read magnetosphere database.
        CALL MSPINIT(LUNIT(3),ISPECI)
      END IF
C
C     Determine which phenomenological region the spacecraft is in. The
C     spacecraft`s coordinates are returned after transformation into
C     the magnetotail aligned coordinate system.
      CALL LOCREG(XKP,XGSM,YGSM,ZGSM,XTAIL,YTAIL,ZTAIL,IDLOC)
C
D     WRITE(*,*)' After LOCREG!  IDLOC,XTAIL,YTAIL,ZTAIL = ',
D    $                           IDLOC,XTAIL,YTAIL,ZTAIL
D     PAUSE
C
      IF(IDLOC.EQ.1) THEN
C       The spacecraft is in region 1, the solar wind.
        IF(IUSESW.EQ.0) THEN
C         Use the simple (uniform flux) analytic solar wind model.
C         If the user supplied Kp or species type has changed, redo the
C         uniform flux value.
          XKPDIFF = ABS(XKP - XKPSAV1)
          ISPDIFF = ISPECI - ISPSAV1
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL SOLWFLX(XKP,ISPECI,FLXMN1,FLX951,FLX501,FLXSD1)
            XKPSAV1 = XKP
            ISPSAV1 = ISPECI
          END IF
          FLUXMN = FLXMN1
          FLUX95 = FLX951
          FLUX50 = FLX501
          FLUXSD = FLXSD1
        ELSE IF(IUSESW.EQ.1) THEN
C         Use the user`s value for the uniform solar wind flux.
          FLUXMN = FSWIMN
          FLUX95 = FSWI95
          FLUX50 = FSWI50
          FLUXSD = FSWISD
        ELSE IF((IUSESW.EQ.2).OR.(IUSESW.EQ.3)) THEN
C         Use the database driven model to get the solar wind flux.
C         If the user supplied Kp or species type has changed, redo the
C         scaling parameters.
          XKPDIFF = ABS(XKP - XKPSAV1)
          ISPDIFF = ISPECI - ISPSAV1
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL SCALKP1(XKP,ISPECI,NSECTR1,SECTX1,SECTY1,SCMEAN1,SC951,
     $                   SC501,SCSIG1)
            XKPSAV1 = XKP
            ISPSAV1 = ISPECI
          END IF
C         Calculate the solar wind`s flux for this Kp value & position.
          CALL NBRFLUX(XKP,NSECTR1,SECTX1,SECTY1,SCMEAN1,SC951,SC501,
     $      SCSIG1,XTAIL,YTAIL,ZTAIL,NUMDAT1,XFLUX1,YFLUX1,ZFLUX1,
     $      FLXBIN1,NUMBIN1,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,LOGFLG,
     $      RNGTOL,FPCHI,FPCLO,FLUXMN,FLUX95,FLUX50,FLUXSD)
          IF(IUSESW.EQ.3) THEN
C           Add the user`s solar wind flux to this database model`s
C           flux predictions.
            FLUXMN = FLUXMN + FSWIMN
            FLUX95 = FLUX95 + FSWI95
            FLUX50 = FLUX50 + FSWI50
            FLUXSD = FLUXSD + FSWISD
          END IF
        ELSE IF(IUSESW.EQ.4) THEN
C         Add the user`s solar wind flux to the simple (uniform flux)
C         analytic solar wind model.
          XKPDIFF = ABS(XKP - XKPSAV1)
          ISPDIFF = ISPECI - ISPSAV1
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL SOLWFLX(XKP,ISPECI,FLXMN1,FLX951,FLX501,FLXSD1)
            XKPSAV1 = XKP
            ISPSAV1 = ISPECI
          END IF
          FLUXMN = FLXMN1 + FSWIMN
          FLUX95 = FLX951 + FSWI95
          FLUX50 = FLX501 + FSWI50
          FLUXSD = FLXSD1 + FSWISD
        END IF
      ELSE IF(IDLOC.EQ.2) THEN
C       The spacecraft is in region 2, the magnetosheath.
        IF(IUSEMSH.EQ.0) THEN
C         Use the simple (uniform flux) analytic magnetosheath model.
C         If the user supplied Kp or species type has changed, redo the
C         uniform flux value.
          XKPDIFF = ABS(XKP - XKPSAV2)
          ISPDIFF = ISPECI - ISPSAV2
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL MSHEFLX(XKP,ISPECI,FLXMN2,FLX952,FLX502,FLXSD2)
            XKPSAV2 = XKP
            ISPSAV2 = ISPECI
          END IF
          FLUXMN = FLXMN2
          FLUX95 = FLX952
          FLUX50 = FLX502
          FLUXSD = FLXSD2
        ELSE IF(IUSEMSH.EQ.1) THEN
C         Scale the user`s value for the uniform solar wind flux for
C         the uniform magnetosheath flux.  A temporary scale factor
C         to use is just simply multiply the user`s solar wind flux
C         by 2.  A more detailed model will be implemented in the next
C         release.
          FLUXMN = FSWIMN * 2.
          FLUX95 = FSWI95 * 2.
          FLUX50 = FSWI50 * 2.
          FLUXSD = FSWISD * 2.
        ELSE IF((IUSEMSH.EQ.2).OR.(IUSEMSH.EQ.3)) THEN
C         Use the database driven model to get the magnetosheath flux.
C         If the user supplied Kp or species type has changed, redo the
C         scaling parameters.
          XKPDIFF = ABS(XKP - XKPSAV2)
          ISPDIFF = ISPECI - ISPSAV2
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL SCALKP2(XKP,ISPECI,NSECTR2,SECTX2,SECTY2,SCMEAN2,SC952,
     $                   SC502,SCSIG2)
            XKPSAV2 = XKP
            ISPSAV2 = ISPECI
          END IF
C         Calculate the solar wind`s flux for this Kp value & position.

          CALL NBRFLUX(XKP,NSECTR2,SECTX2,SECTY2,SCMEAN2,SC952,SC502,
     $      SCSIG2,XTAIL,YTAIL,ZTAIL,NUMDAT2,XFLUX2,YFLUX2,ZFLUX2,
     $      FLXBIN2,NUMBIN2,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,LOGFLG,
     $      RNGTOL,FPCHI,FPCLO,FLUXMN,FLUX95,FLUX50,FLUXSD)
c         write(*,*) "I AM HERE: ", fluxmn,flux95,flux50,fluxsd
          IF(IUSEMSH.EQ.3) THEN
C           Add the user`s scaled solar wind flux to the database
C           model`s flux predictions.
            FLUXMN = FLUXMN + FSWIMN * 2.
            FLUX95 = FLUX95 + FSWI95 * 2.
            FLUX50 = FLUX50 + FSWI50 * 2.
            FLUXSD = FLUXSD + FSWISD * 2.
          END IF
        ELSE IF(IUSEMSH.EQ.4) THEN
C         Add the user`s solar wind flux to the simple (uniform flux)
C         analytic magnetosheath model.
          XKPDIFF = ABS(XKP - XKPSAV2)
          ISPDIFF = ISPECI - ISPSAV2
          IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
            CALL MSHEFLX(XKP,ISPECI,FLXMN2,FLX952,FLX502,FLXSD2)
            XKPSAV2 = XKP
            ISPSAV2 = ISPECI
          END IF
          FLUXMN = FLXMN2 + FSWIMN * 2.
          FLUX95 = FLX952 + FSWI95 * 2.
          FLUX50 = FLX502 + FSWI50 * 2.
          FLUXSD = FLXSD2 + FSWISD * 2.
        END IF
      ELSE IF(IDLOC.EQ.3) THEN
C       The spacecraft is in region 3, the magnetosphere.
C
C       If the user supplied Kp or species type has changed, redo the
C       scaling parameters.
        XKPDIFF = ABS(XKP - XKPSAV3)
        ISPDIFF = ISPECI - ISPSAV3
        IF((XKPDIFF.GT.XKPTOL).OR.(ISPDIFF.NE.0)) THEN
          CALL SCALKP3(XKP,ISPECI,NSECTR3,SECTX3,SECTY3,SCMEAN3,SC953,
     $                 SC503,SCSIG3)
          XKPSAV3 = XKP
          ISPSAV3 = ISPECI
        END IF
C       Calculate the magnetosphere`s flux for this Kp value & position.
        CALL NBRFLUX(XKP,NSECTR3,SECTX3,SECTY3,SCMEAN3,SC953,SC503,
     $    SCSIG3,XTAIL,YTAIL,ZTAIL,NUMDAT3,XFLUX3,YFLUX3,ZFLUX3,FLXBIN3,
     $    NUMBIN3,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,
     $    FPCLO,FLUXMN,FLUX95,FLUX50,FLUXSD)
      ELSE
        WRITE(*,*)
        WRITE(*,*)' Error in phenomenological region ID!'
      END IF
C
D     WRITE(*,*)' END OF CRMFLX!'
D     WRITE(*,*)' FLUXMN,FLUX95,FLUX50,FLUXSD = ',
D    $            FLUXMN,FLUX95,FLUX50,FLUXSD
C
      RETURN
      END
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
C     "A Model of the Earth`s Distant Bow Shock."  This paper was
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
D     WRITE(*,*)
D     WRITE(*,*)' ENTER BOWSHK2!'
D     WRITE(*,*)' BX,BY,BZ,VX,VY,VZ = ',BX,BY,BZ,VX,VY,VZ
D     WRITE(*,*)' DENNUM,SWETEMP,SWPTEMP = ',DENNUM,SWETEMP,SWPTEMP
D     WRITE(*,*)' HEFRAC,SWHTEMP,XPOS = ',HEFRAC,SWHTEMP,XPOS
D     WRITE(*,*)' ETEMP,PTEMP,HETEMP = ',ETEMP,PTEMP,HETEMP
D     PAUSE  'PAUSED!!'
D     WRITE(*,*)
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
D     WRITE(*,*)' XPOS,BOWANG,BOWRAD = ',XPOS,BOWANG,BOWRAD
C
 2000 CONTINUE 
C
      RETURN 
      END
C
C
      SUBROUTINE MSPINIT(LUNIT,ISPECI)
C
C     This routine opens the CRM magnetosphere database file and
C     initializes the data arrays stored in the COMMON block.
C
C     Input:
C       LUNIT   - unit number used in opening CRM`s database.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
C
      CHARACTER*1 SKIP
      REAL FLXKP(MAXKP)
      INTEGER NUMKP(MAXKP)
C
      INCLUDE 'CRMDAT3.CMN'
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED MSPINIT!!'
D     WRITE(*,*)' ISPECI = ',ISPECI
D     PAUSE 'PAUSED!'
C
C     Open input file containing magnetosphere data.
      IF(ISPECI.EQ.1) THEN
        OPEN(LUNIT,FILE='/data/mta4/proj/rac/ops/CRM/v1.21/crmflx_v1.2_2&
     &5jan2001/MSPH_Kp_PROT.BIN',
c    &5jan2001/MSPH_Kp_PROTDASC',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.2) THEN
        OPEN(LUNIT,FILE='MSPH_Kp_HEL.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.3) THEN
        OPEN(LUNIT,FILE='MSPH_Kp_CNO.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE
        WRITE(*,*)
        WRITE(*,*)' Error in species ID!'
      END IF
C
C     Skip the header record in the data file.
      READ(LUNIT) SKIP
C
C     Initialize counters to zero.
      ICNT = 0
      DO KK = 1,MAXKP
        NUMDAT3(KK) = 0
      END DO
C
      WRITE(*,*)
      WRITE(*,*)' Read CRMFLX magnetosphere data file.'
      WRITE(*,*)
C
C     Read in the data.
      DO 1000 II = 1,5000000
        ICNT = ICNT + 1
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
D         WRITE(*,*)' II = ',II
        END IF
C
        READ(LUNIT,ERR=1001,END=1002) I,J,K,XD,YD,ZD,
     $    (FLXKP(JJ),JJ=1,MAXKP),(NUMKP(KK),KK=1,MAXKP)
C
D       WRITE(*,*)' II,I,J,K,XD,YD,ZD = ',II,I,J,K,XD,YD,ZD
D       WRITE(*,*)' II, FLXKP = ',(FLXKP(JJ),JJ=1,MAXKP)
D       WRITE(*,*)' II, NUMKP = ',(NUMKP(JJ),JJ=1,MAXKP)
D       PAUSE
C
        DO KK = 1,MAXKP
          IF(NUMKP(KK).GT.0) THEN
            NUMDAT3(KK) = NUMDAT3(KK) + 1
            XFLUX3(KK,NUMDAT3(KK)) = XD
            YFLUX3(KK,NUMDAT3(KK)) = YD
            ZFLUX3(KK,NUMDAT3(KK)) = ZD
            FLXBIN3(KK,NUMDAT3(KK)) = FLXKP(KK)
            NUMBIN3(KK,NUMDAT3(KK)) = NUMKP(KK)
C
D           IF((XFLUX3(KK,NUMDAT3(KK)).GE.-15.).AND.
D    $         (XFLUX3(KK,NUMDAT3(KK)).LE.-5.).AND.
D    $         (YFLUX3(KK,NUMDAT3(KK)).GE.5.).AND.
D    $         (YFLUX3(KK,NUMDAT3(KK)).LE.15.)) THEN
D             WRITE(*,*)' KK,NUMDAT3(KK) = ',KK,NUMDAT3(KK)
D             WRITE(*,*)' XFLUX3(KK,NUMDAT3(KK)),',
D    $          'YFLUX3(KK,NUMDAT3(KK)),ZFLUX3(KK,NUMDAT3(KK)) = ',
D    $          XFLUX3(KK,NUMDAT3(KK)),YFLUX3(KK,NUMDAT3(KK)),
D    $          ZFLUX3(KK,NUMDAT3(KK))
D             WRITE(*,*)' NUMBIN3(KK,NUMDAT3(KK)),FLXBIN3(KK,NUMDAT3',
D    $          '(KK)) = ',
D    $          NUMBIN3(KK,NUMDAT3(KK)),FLXBIN3(KK,NUMDAT3(KK))
D             WRITE(*,*)
D             PAUSE 'PAUSED!'
D           END IF
C
          END IF
        END DO
C
1000  CONTINUE
1001  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Error reading data!  II = ',II
      PAUSE
      STOP 1
1002  CONTINUE
      CLOSE(LUNIT)
C
      RETURN
      END
C
C
      SUBROUTINE MSHINIT(LUNIT,ISPECI)
C
C     This routine opens the CRM magnetosheath database file and
C     initializes the data arrays stored in the COMMON block.
C
C     Input:
C       LUNIT   - unit number used in opening CRM`s database.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
C
      CHARACTER*1 SKIP
      REAL FLXKP(MAXKP)
      INTEGER NUMKP(MAXKP)
C
      INCLUDE 'CRMDAT2.CMN'
C
C     Open input file containing magnetosheath data.
      IF(ISPECI.EQ.1) THEN
        OPEN(LUNIT,FILE='/data/mta4/proj/rac/ops/CRM/v1.21/crmflx_v1.2_2&
     &5jan2001/MSheath_Kp_PROT.BIN',
c    &5jan2001/MSheath_Kp_PROT.ASC',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.2) THEN
        OPEN(LUNIT,FILE='MSheath_Kp_HEL.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.3) THEN
        OPEN(LUNIT,FILE='MSheath_Kp_CNO.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE
        WRITE(*,*)
        WRITE(*,*)' Error in species ID!'
      END IF
C
C     Skip the header record in the data file.
      READ(LUNIT) SKIP
C
C     Initialize counters to zero.
      ICNT = 0
      DO KK = 1,MAXKP
        NUMDAT2(KK) = 0
      END DO
C
      WRITE(*,*)
      WRITE(*,*)' Read CRMFLX magnetosheath data file.'
      WRITE(*,*)
C
C     Read in the data.
      DO 1000 II = 1,5000000
        ICNT = ICNT + 1
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
D         WRITE(*,*)' II = ',II
        END IF
C
        READ(LUNIT,ERR=1001,END=1002) I,J,K,XD,YD,ZD,
     $    (FLXKP(JJ),JJ=1,MAXKP),(NUMKP(KK),KK=1,MAXKP)
C
D       WRITE(*,*)' II,I,J,K,XD,YD,ZD = ',II,I,J,K,XD,YD,ZD
D       WRITE(*,*)' II, FLXKP = ',(FLXKP(JJ),JJ=1,MAXKP)
D       WRITE(*,*)' II, NUMKP = ',(NUMKP(JJ),JJ=1,MAXKP)
D       PAUSE
C
        DO KK = 1,MAXKP
          IF(NUMKP(KK).GT.0) THEN
            NUMDAT2(KK) = NUMDAT2(KK) + 1
            XFLUX2(KK,NUMDAT2(KK)) = XD
            YFLUX2(KK,NUMDAT2(KK)) = YD
            ZFLUX2(KK,NUMDAT2(KK)) = ZD
            FLXBIN2(KK,NUMDAT2(KK)) = FLXKP(KK)
            NUMBIN2(KK,NUMDAT2(KK)) = NUMKP(KK)
          END IF
        END DO
C
1000  CONTINUE
1001  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Error reading data!  II = ',II
      PAUSE
      STOP 1
1002  CONTINUE
      CLOSE(LUNIT)
C
      RETURN
      END
C
C
      SUBROUTINE SWINIT(LUNIT,ISPECI)
C
C     This routine opens the CRM solar wind database file and
C     initializes the data arrays stored in the COMMON block.
C
C     Input:
C       LUNIT   - unit number used in opening CRM`s database.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
C
      CHARACTER*1 SKIP
      REAL FLXKP(MAXKP)
      INTEGER NUMKP(MAXKP)
C
      INCLUDE 'CRMDAT1.CMN'
C
C     Open input file containing solar wind data.
      IF(ISPECI.EQ.1) THEN
        OPEN(LUNIT,FILE='/data/mta4/proj/rac/ops/CRM/v1.21/crmflx_v1.2_2&
     &5jan2001/SolWind_Kp_PROT.BIN',
c    &5jan2001/SolWind_Kp_PROT.ASC',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.2) THEN
        OPEN(LUNIT,FILE='SolWind_Kp_HEL.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE IF(ISPECI.EQ.3) THEN
        OPEN(LUNIT,FILE='SolWind_Kp_CNO.BIN',
     $    ACCESS='SEQUENTIAL',FORM='UNFORMATTED',STATUS='OLD')
      ELSE
        WRITE(*,*)
        WRITE(*,*)' Error in species ID!'
      END IF
C
C     Skip the header record in the data file.
      READ(LUNIT) SKIP
C
C     Initialize counters to zero.
      ICNT = 0
      DO KK = 1,MAXKP
        NUMDAT1(KK) = 0
      END DO
C
C     WRITE(*,*)
C     WRITE(*,*)' Read CRMFLX solar wind data file.'
C     WRITE(*,*)
C
C     Read in the data.
      DO 1000 II = 1,5000000
        ICNT = ICNT + 1
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
D         WRITE(*,*)' II = ',II
        END IF
C
DD      write(*,*) "I AM HERE ICNT ", icnt, lunit,maxkp
        READ(LUNIT, ERR=1001,END=1002) I,J,K,XD,YD,ZD,
     $    (FLXKP(JJ),JJ=1,MAXKP),(NUMKP(KK),KK=1,MAXKP)
C
D       WRITE(*,*)' II,I,J,K,XD,YD,ZD = ',II,I,J,K,XD,YD,ZD
D       WRITE(*,*)' II, FLXKP = ',(FLXKP(JJ),JJ=1,MAXKP)
D       WRITE(*,*)' II, NUMKP = ',(NUMKP(JJ),JJ=1,MAXKP)
D       PAUSE
C
        DO KK = 1,MAXKP
          IF(NUMKP(KK).GT.0) THEN
            NUMDAT1(KK) = NUMDAT1(KK) + 1
            XFLUX1(KK,NUMDAT1(KK)) = XD
            YFLUX1(KK,NUMDAT1(KK)) = YD
            ZFLUX1(KK,NUMDAT1(KK)) = ZD
            FLXBIN1(KK,NUMDAT1(KK)) = FLXKP(KK)
            NUMBIN1(KK,NUMDAT1(KK)) = NUMKP(KK)
          END IF
        END DO
C
1000  CONTINUE
1001  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Error reading data!  II = ',II
      PAUSE
      STOP 1
1002  CONTINUE
      CLOSE(LUNIT)
C
      RETURN
      END
C
C
      subroutine fast(bx,by,bz,va,vs,v0,alp,vms)

c subroutine to solve the equations 21-24 in Bennet`s paper for the
c local fast magnetosonic speed
c
c It uses the simple bisection method to solve the equations.
c accuracy to 0.01 in V_ms is good enough 
C
C     This routine is adpated from the paper by L. Bennet et.al.,
C     "A Model of the Earth`s Distant Bow Shock."  This paper was
C     to be published in the Journal of Geophysical Research, 1997.
C     This source code is from their web site at:
C     http://www.igpp.ucla.edu/galileo/newmodel.htm
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
      SUBROUTINE FLXDAT1(IKP,XGSM,YGSM,ZGSM,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $  FLUXBIN,NUMBIN,RNGCHK,FLUX,AVGNUM,RNGCELL,NUMCELL)
C
C     This routine finds the flux corresponding to the satellite`s
C     GSM position coordinates by use of the GEOTAIL database.
C
C     This routine is used if no data smoothing is selected or if
C     spatial averaging within the volume defined by RNGCHK is selected.
C
C     INPUTS:
C       IKP     - Kp interval index (1 -> MAXKP).
C       XGSM    - satellite`s X-coordinate (Re).
C       YGSM    - satellite`s Y-coordinate (Re).
C       ZGSM    - satellite`s Z-coordinate (Re).
C       NUMDAT  - number of non-zero values in the database.
C       XFLUX   - array containing the X-coordinate of each data
C                 cell`s center  (Re).
C       YFLUX   - array containing the Y-coordinate of each data
C                 cell`s center  (Re).
C       ZFLUX   - array containing the Z-coordinate of each data
C                 cell`s center  (Re).
C       FLUXBIN - array containing the average ion flux within
C                 each cell  (ions/[cm^2-sec-sr-MeV]).
C       NUMBIN  - array containing the number of non-zero values within
C                 each cell.
C       RNGCHK  - the range tolerance variable (Re).
C
C     OUTPUTS:
C       FLUX    - computed average flux value  (ions/[cm^2-sec-sr-MeV]).
C       AVGNUM  - average number of flux values per cell used to get FLUX.
C       RNGCELL - distance to center of flux database cell used  (Re).
C       NUMCELL - number of flux database cells used that have the
C                 same value of RNGCELL.
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'MAXCELL.PAR'
C
      INTEGER NUMDAT(MAXKP),NUMBIN(MAXKP,MAXPNT)
      REAL FLUXBIN(MAXKP,MAXPNT),XFLUX(MAXKP,MAXPNT)
      REAL YFLUX(MAXKP,MAXPNT),ZFLUX(MAXKP,MAXPNT)
C
      REAL FLXSTO(MAXCELL)
      INTEGER NUMSTO(MAXCELL)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED FLXDAT1!!'
D     WRITE(*,*)' IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1) = ',
D    $            IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1)
D     WRITE(*,*)' ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1) = ',
D    $            ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1)
D     WRITE(*,*)' XGSM,YGSM,ZGSM = ',XGSM,YGSM,ZGSM
D     PAUSE
C
C     Find the nearest non-zero data cell.  Use its flux value.
C
      IF(XGSM.GE.0.) THEN
C       Do not use Z-layers on the dayside of the magnetosphere.
        ZCKLO = -7.
        ZCKHI = +100.
      ELSE
C       Use the nearest neighbor flux only inside a range of Z-values.
        IF(ZGSM.LE.-6.) THEN
C         Use the nearest neighbor in the -7 < Z < -6. range.
          ZCKLO = -7.
          ZCKHI = -6.
        ELSE IF((ZGSM.GT.-6.).AND.(ZGSM.LE.-5.)) THEN
C         Use the nearest neighbor in the -6 < Z < -5. range.
          ZCKLO = -6.
          ZCKHI = -5.
        ELSE IF((ZGSM.GT.-5.).AND.(ZGSM.LE.+4.)) THEN
C         Use the nearest neighbor in the -5 < Z < +4. range.
          ZCKLO = -5.
          ZCKHI = +4.
        ELSE IF((ZGSM.GT.+4.).AND.(ZGSM.LE.+5.)) THEN
C         Use the nearest neighbor in the +4 < Z < +5. range.
          ZCKLO = +4.
          ZCKHI = +5.
        ELSE IF((ZGSM.GT.+5.).AND.(ZGSM.LE.+6.)) THEN
C         Use the nearest neighbor in the +5 < Z < +6. range.
          ZCKLO = +5.
          ZCKHI = +6.
        ELSE IF((ZGSM.GT.+6.).AND.(ZGSM.LE.+7.)) THEN
C         Use the nearest neighbor in the +6 < Z < +7. range.
          ZCKLO = +6.
          ZCKHI = +7.
        ELSE IF((ZGSM.GT.+7.).AND.(ZGSM.LE.+8.)) THEN
C         Use the nearest neighbor in the +7 < Z < +8. range.
          ZCKLO = +7.
          ZCKHI = +8.
        ELSE IF((ZGSM.GT.+8.).AND.(ZGSM.LE.+9.)) THEN
C         Use the nearest neighbor in the +8 < Z < +9. range.
          ZCKLO = +8.
          ZCKHI = +9.
        ELSE IF((ZGSM.GT.+9.).AND.(ZGSM.LE.+10.)) THEN
C         Use the nearest neighbor in the +9 < Z < +10. range.
          ZCKLO = +9.
          ZCKHI = +10.
        ELSE IF(ZGSM.GT.+10.) THEN
C         Use the nearest neighbor in the +10 < Z < +11. range.
          ZCKLO = +10.
          ZCKHI = +11.
        END IF
      END IF
C
D     WRITE(*,*)' ZCKLO,ZCKHI = ',ZCKLO,ZCKHI
C
      RNGCELL = 1.E+25
      NUMCELL = 0
      DO I = 1,NUMDAT(IKP)
        IF((FLUXBIN(IKP,I) .GT.1.).AND.(ZFLUX(IKP,I).GT.ZCKLO)
     $     .AND.(ZFLUX(IKP,I).LE.ZCKHI)) THEN

          RNG = SQRT((XFLUX(IKP,I)-XGSM)**2 + (YFLUX(IKP,I)-YGSM)**2
     $      + (ZFLUX(IKP,I)-ZGSM)**2)
D         WRITE(*,*)' I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),',
D    $              'ZFLUX(IKP,I) = ',
D    $                I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),
D    $               ZFLUX(IKP,I)
D         WRITE(*,*)' I,RNG,RNGCELL = ',I,RNG,RNGCELL
          RNGDIFF = RNG - RNGCELL
          RNGABS = ABS(RNGDIFF)
          IF((RNGABS.GT.RNGCHK).AND.(RNGDIFF.LT.0.0)) THEN
C           There is a new nearest neighbor data cell.
            NUMCELL = 1
            RNGCELL = RNG
            FLXSTO(1) = FLUXBIN(IKP,I)
            NUMSTO(1) = NUMBIN(IKP,I)
          ELSE IF(RNGABS.LE.RNGCHK) THEN
C           There is a new data cell within the range
C           tolerance to the nearest neighbor.  This cell`s flux
C           should be included in the average for this location.
            NUMCELL = NUMCELL + 1
            FLXSTO(NUMCELL) = FLUXBIN(IKP,I)
            NUMSTO(NUMCELL) = NUMBIN(IKP,I)
            IF(NUMCELL.EQ.MAXCELL) GO TO 1000
          END IF
        END IF
      END DO
C
1000  CONTINUE
C
C     Use the average of the flux from all bins at the same distance.
C
      FLUX = 0.
      AVGNUM = 0.
      IF(NUMCELL.EQ.1) THEN
        FLUX = FLXSTO(1)
        AVGNUM = FLOAT(NUMSTO(1))
      ELSE IF(NUMCELL.GT.1) THEN
        NUMAVG = 0
        DO I = 1,NUMCELL
          FLUX = FLUX + FLXSTO(I)
          NUMAVG = NUMAVG + NUMSTO(I)
        END DO
        FLUX = FLUX/FLOAT(NUMCELL)
        AVGNUM = FLOAT(NUMAVG)/FLOAT(NUMCELL)
      END IF
C
C
D     WRITE(*,*)
D     WRITE(*,*)' END FLXDAT1!!'
D     WRITE(*,*)' RNGCELL,FLUX = ',RNGCELL,FLUX
D     WRITE(*,*)
C
      RETURN
      END
C
C
      SUBROUTINE FLXDAT2(IKP,XGSM,YGSM,ZGSM,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $  FLUXBIN,NUMBIN,RNGCHK,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,LOGFLG,
     $  FLUX,DISNUM,RNGCELL,NUMCELL)
C
C     This routine finds the flux corresponding to the satellite`s
C     GSM position coordinates by use of the GEOTAIL database.
C
C     This routine uses spike rejection to filter (smooth) the data.
C
C     INPUTS:
C       IKP     - Kp interval index (1 -> MAXKP).
C       XGSM    - satellite`s X-coordinate (Re).
C       YGSM    - satellite`s Y-coordinate (Re).
C       ZGSM    - satellite`s Z-coordinate (Re).
C       NUMDAT  - number of non-zero values in the database.
C       XFLUX   - array containing the X-coordinate of each data
C                 cell`s center  (Re).
C       YFLUX   - array containing the Y-coordinate of each data
C                 cell`s center  (Re).
C       ZFLUX   - array containing the Z-coordinate of each data
C                 cell`s center  (Re).
C       FLUXBIN - array containing the average ion flux within
C                 each cell  (ions/[cm^2-sec-sr-MeV]).
C       NUMBIN  - array containing the number of non-zero values within
C       RNGCHK  - the range tolerance variable (Re).
C       SMOOTH1 - flag for control of database smoothing filter:
C              SMOOTH1 = 1 if spike rejection and near neighbor flux.
C              SMOOTH1 = 2 if spike rejection with range weighted
C                           scaling of flux.
C              SMOOTH1 = 3 if spike rejection with average flux.
C       NFLXGET - number of flux values to get for smoothing filter
C                  (used if SMOOTH1 = 1,2, or 3)
C
C       NDROPHI - number of high flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2, or 3).
C
C       NDROPLO - number of low flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2, or 3).
C
C       LOGFLG  - flag controlling how flux average is performed
C                  (used if SMOOTH1 = 3).
C              LOGFLG = 1 if log10 of flux values used.
C              LOGFLG = 2 if linear flux values used.
C
C     OUTPUTS:
C       FLUX    - computed distance weighted flux value (ions/[cm^2-sec-sr-MeV]).
C       DISNUM  - distance weighted number of flux values per cell used
C                 to get FLUX.
C       RNGCELL - distance to center of nearest flux database cell
C                 used  (Re).
C       NUMCELL - number of flux database cells used.
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'NSAVE.PAR'
C
      INTEGER NUMDAT(MAXKP),NUMBIN(MAXKP,MAXPNT)
      REAL FLUXBIN(MAXKP,MAXPNT),XFLUX(MAXKP,MAXPNT)
      REAL YFLUX(MAXKP,MAXPNT),ZFLUX(MAXKP,MAXPNT)
C
      REAL FLXSTO(NSAVE),RNGSTO(NSAVE)
      INTEGER NUMSTO(NSAVE)
C
      REAL FLXUSE(NSAVE),RNGUSE(NSAVE)
      INTEGER NUMUSE(NSAVE)
C
      INTEGER SMOOTH1
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED FLXDAT2!!'
D     WRITE(*,*)' IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1) = ',
D    $            IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1)
D     WRITE(*,*)' ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1) = ',
D    $            ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1)
D     WRITE(*,*)' XGSM,YGSM,ZGSM = ',XGSM,YGSM,ZGSM
D     WRITE(*,*)' RNGCHK,SMOOTH1 = ',RNGCHK,SMOOTH1
D     PAUSE
C
C     Find the nearest non-zero data cell.  Use its flux value.
C
      IF(XGSM.GE.0.) THEN
C       Do not use Z-layers on the dayside of the magnetosphere.
        ZCKLO = -7.
        ZCKHI = +100.
      ELSE
C       Use the nearest neighbor flux only inside a range of Z-values.
        IF(ZGSM.LE.-6.) THEN
C         Use the nearest neighbor in the -7 < Z < -6. range.
          ZCKLO = -7.
          ZCKHI = -6.
        ELSE IF((ZGSM.GT.-6.).AND.(ZGSM.LE.-5.)) THEN
C         Use the nearest neighbor in the -6 < Z < -5. range.
          ZCKLO = -6.
          ZCKHI = -5.
        ELSE IF((ZGSM.GT.-5.).AND.(ZGSM.LE.+4.)) THEN
C         Use the nearest neighbor in the -5 < Z < +4. range.
          ZCKLO = -5.
          ZCKHI = +4.
        ELSE IF((ZGSM.GT.+4.).AND.(ZGSM.LE.+5.)) THEN
C         Use the nearest neighbor in the +4 < Z < +5. range.
          ZCKLO = +4.
          ZCKHI = +5.
        ELSE IF((ZGSM.GT.+5.).AND.(ZGSM.LE.+6.)) THEN
C         Use the nearest neighbor in the +5 < Z < +6. range.
          ZCKLO = +5.
          ZCKHI = +6.
        ELSE IF((ZGSM.GT.+6.).AND.(ZGSM.LE.+7.)) THEN
C         Use the nearest neighbor in the +6 < Z < +7. range.
          ZCKLO = +6.
          ZCKHI = +7.
        ELSE IF((ZGSM.GT.+7.).AND.(ZGSM.LE.+8.)) THEN
C         Use the nearest neighbor in the +7 < Z < +8. range.
          ZCKLO = +7.
          ZCKHI = +8.
        ELSE IF((ZGSM.GT.+8.).AND.(ZGSM.LE.+9.)) THEN
C         Use the nearest neighbor in the +8 < Z < +9. range.
          ZCKLO = +8.
          ZCKHI = +9.
        ELSE IF((ZGSM.GT.+9.).AND.(ZGSM.LE.+10.)) THEN
C         Use the nearest neighbor in the +9 < Z < +10. range.
          ZCKLO = +9.
          ZCKHI = +10.
        ELSE IF(ZGSM.GT.+10.) THEN
C         Use the nearest neighbor in the +10 < Z < +11. range.
          ZCKLO = +10.
          ZCKHI = +11.
        END IF
      END IF
C
C     *********** (IUSE out of NFLXGET) Algorithm Description ************
C
C (1) Find the NFLXGET nearest neighbor data cells (with respect to the
C     observation point) which lie within the z-slice of the observation
C     point (not the range from the nearest neighbor data cell as used
C     previously).
C
C (2) Sort the NFLXGET data cells by their range from the observation
C     point.
C
C (3) Throw away the highest flux value and lowest flux value data
C     cells.  So, IUSE = NFLXGET - 2.
C
C     *** NOTE *** For the remaining IUSE data cells, this routine
C     calculates the distance weighted sum of the flux values.  The
C     objective of this approach is to smooth the database by taking
C     out the +/- "spikes" and performing a spatial blending of the
C     remaining data. This approach is very similar to that used for the
C     Kp scaling factors.
C
C (4) Multiply the closest data cell by the distance to the farthest
C     data cell.
C
C (5) Multiply the 2nd closest data cell by the distance to the 2nd
C     farthest data cell.
C
C (6) Repeat this process until you multiply the farthest data cell`s by
C     the distance to the closest data cell.
C
C (7) Get the final ion flux by summing the distance scaled quantities
C     and dividing the sum by the total distance to all of the data
C     cells.
C
C (8) Get the distance weighted sum of the number of flux values per
C     cell used to get FLUX.  Repeat steps 4 -> 7 above, but for the
C     number of flux measurements per data cell (not for the average
C     flux value in that cell).
C
C     ***************** End of Algorithm Description *******************
C
C
D     WRITE(*,*)' ZCKLO,ZCKHI = ',ZCKLO,ZCKHI
D     WRITE(*,*)' NFLXGET,NDROPHI,NDROPLO,LOGFLG = ',
D    $            NFLXGET,NDROPHI,NDROPLO,LOGFLG
D     PAUSE
C
C
C     Gather the NFLXGET flux values.
C
      NGOT = 1
      DO I = 1,NUMDAT(IKP)
        IF((FLUXBIN(IKP,I) .GT.1.).AND.(ZFLUX(IKP,I).GT.ZCKLO)
     $     .AND.(ZFLUX(IKP,I).LE.ZCKHI)) THEN
          RNG = SQRT((XFLUX(IKP,I)-XGSM)**2 + (YFLUX(IKP,I)-YGSM)**2
     $      + (ZFLUX(IKP,I)-ZGSM)**2)
D         WRITE(*,*)' I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),',
D    $              'ZFLUX(IKP,I) = ',
D    $                I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),
D    $               ZFLUX(IKP,I)
D         WRITE(*,*)' I,RNG,RNGCELL = ',I,RNG,RNGCELL
C
          IF(NGOT.LT.NFLXGET) THEN
C           Increment the counter and save the data cell information.
            RNGSTO(NGOT) = RNG
            FLXSTO(NGOT) = FLUXBIN(IKP,I)
            NUMSTO(NGOT)  = NUMBIN(IKP,I)
            NGOT = NGOT + 1
          ELSE IF(NGOT.EQ.NFLXGET) THEN
C           Save the data cell information and sort the NFLXGET data cells
C           (in ascending order) on the basis of their ranges from the
C           observation point.
            RNGSTO(NFLXGET) = RNG
            FLXSTO(NFLXGET) = FLUXBIN(IKP,I)
            NUMSTO(NFLXGET)  = NUMBIN(IKP,I)
            CALL SORTRG5(NFLXGET,RNGSTO,FLXSTO,NUMSTO)
          ELSE
C           There are already NFLXGET data cells loaded in the near
C           neighbor storage arrays.  Check if the current data cell
C           location is closer to the observation point than is the
C           farthest data cell in the current list.
            IF(RNG.LT.RNGSTO(NFLXGET)) THEN
              RNGSTO(NFLXGET) = RNG
              FLXSTO(NFLXGET) = FLUXBIN(IKP,I)
              NUMSTO(NFLXGET)  = NUMBIN(IKP,I)
C             Re-sort the NFLXGET data cells (in ascending order) on the
C             basis of their ranges from the observation point.
              CALL SORTRG5(NFLXGET,RNGSTO,FLXSTO,NUMSTO)
            END IF
          END IF
        END IF
      END DO
C
1000  CONTINUE
C
D     WRITE(*,*)' BEFORE HIGH INDEX!'
D     DO I = 1,NFLXGET
D       WRITE(*,*)' RNGSTO(I),FLXSTO(I),NUMSTO(I) = ',
D    $              RNGSTO(I),FLXSTO(I),NUMSTO(I)
D     END DO
D     PAUSE
C
      NDO = NFLXGET
      DO J =1,NDROPHI
C
C       Find the index of the high flux value data cell.
C
        FLXMAX = 0.0
        DO I = 1,NDO
          IF(FLXSTO(I).GE.FLXMAX) THEN
            FLXMAX = FLXSTO(I)
            INDMAX = I
          END IF
        END DO
D       WRITE(*,*)' J,NDO,INDMAX,FLXMAX = ',J,NDO,INDMAX,FLXMAX
C
C       Save the IUSE data cells' information to the work arrays.
C
        IUSE = 0
        DO I = 1,NDO
          IF(I.NE.INDMAX) THEN
            IUSE = IUSE + 1
            RNGUSE(IUSE) = RNGSTO(I)
            FLXUSE(IUSE) = FLXSTO(I)
            NUMUSE(IUSE) = NUMSTO(I)
            FLXSTO(IUSE) = FLXUSE(IUSE)
D           WRITE(*,*)' J,I,IUSE,RNGUSE(IUSE),FLXUSE(IUSE),',
D    $                 'NUMUSE(IUSE) = ',
D    $                  J,I,IUSE,RNGUSE(IUSE),FLXUSE(IUSE),NUMUSE(IUSE)
          END IF
        END DO
      END DO
C
D     WRITE(*,*)' AFTER HIGH INDEX!  IUSE = ',IUSE
D     DO I = 1,IUSE
D       WRITE(*,*)' RNGUSE(I),FLXUSE(I),NUMUSE(I) = ',
D    $              RNGUSE(I),FLXUSE(I),NUMUSE(I)
D     END DO
D     PAUSE
C
      NDO = IUSE
      DO J =1,NDROPLO
C
C       Find the index of the low flux value data cell.
C
        FLXMIN = 1.E+25
        DO I = 1,NDO
          IF(FLXSTO(I).LE.FLXMIN) THEN
            FLXMIN = FLXSTO(I)
            INDMIN = I
          END IF
        END DO
C
C       Save the IUSE data cells' information to the work arrays.
C
        IUSE = 0
        DO I = 1,NDO
          IF(I.NE.INDMIN) THEN
            IUSE = IUSE + 1
            RNGUSE(IUSE) = RNGSTO(I)
            FLXUSE(IUSE) = FLXSTO(I)
            NUMUSE(IUSE) = NUMSTO(I)
            FLXSTO(IUSE) = FLXUSE(IUSE)
          END IF
        END DO
      END DO
C
D     WRITE(*,*)' AFTER LOW INDEX!  IUSE = ',IUSE
D     DO I = 1,IUSE
D       WRITE(*,*)' RNGUSE(I),FLXUSE(I),NUMUSE(I) = ',
D    $              RNGUSE(I),FLXUSE(I),NUMUSE(I)
D     END DO
D     PAUSE
C
      IF(IUSE.LE.1) THEN
C       There is only one data cell.
        DISNUM = FLOAT(NUMUSE(1))
        RNGCELL = RNGUSE(1)
        NUMCELL = 1
        FLUX = FLXUSE(1)
        RETURN
      END IF
C
C     The spike rejection process is complete.  Calculate the final
C     flux value.
C
      IF(SMOOTH1.EQ.1) THEN
C       Find the near-neighbor flux.
        DISNUM = FLOAT(NUMUSE(1))
        RNGCELL = RNGUSE(1)
        NUMCELL = 1
        FLUX = FLXUSE(1)
D       WRITE(*,*)' SMOOTH1! DISNUM,RNGCELL,NUMCELL,FLUX = ',
D    $                       DISNUM,RNGCELL,NUMCELL,FLUX
        RETURN
      ELSE IF(SMOOTH1.EQ.2) THEN
C       Calculate the distance weighted sum of the flux and NUMBIN
C       values.
C
        FLUX = 0.0
        DISNUM = 0.0
        DTOT = 0.0
        DO I = 1,IUSE
          DTOT = DTOT + RNGUSE(I)
          J = IUSE - I + 1
          WEIGHT = RNGUSE(J)
          IF(LOGFLG.EQ.1) THEN
            FLUX   = FLUX   + LOG10(FLXUSE(I))*WEIGHT
          ELSE
            FLUX   = FLUX   + FLXUSE(I)*WEIGHT
          END IF
          DISNUM = DISNUM + FLOAT(NUMUSE(I))*WEIGHT
        END DO
C
        FLUX = FLUX/DTOT
        DISNUM = DISNUM/DTOT
D       WRITE(*,*)' SMOOTH1! DISNUM,RNGCELL,NUMCELL,FLUX = ',
D    $                       DISNUM,RNGCELL,NUMCELL,FLUX
      ELSE
C       Get average flux.
        FLUX = 0.0
        DISNUM = 0.0
        DO I = 1,IUSE
          IF(LOGFLG.EQ.1) THEN
            FLUX   = FLUX   + LOG10(FLXUSE(I))
          ELSE
            FLUX   = FLUX   + FLXUSE(I)
          END IF
          DISNUM = DISNUM + FLOAT(NUMUSE(I))
        END DO
        FLUX = FLUX/FLOAT(IUSE)
        DISNUM = DISNUM/FLOAT(IUSE)
D       WRITE(*,*)' SMOOTH1! DISNUM,RNGCELL,NUMCELL,FLUX = ',
D    $                       DISNUM,RNGCELL,NUMCELL,FLUX
      END IF
C
      IF(LOGFLG.EQ.1) FLUX = 10.**FLUX
      NUMCELL = IUSE
      RNGCELL = RNGUSE(1)
C
C
D     WRITE(*,*)
D     WRITE(*,*)' END FLXDAT2!!'
D     WRITE(*,*)' DISNUM,RNGCELL,NUMCELL,FLUX = ',
D    $            DISNUM,RNGCELL,NUMCELL,FLUX
D     WRITE(*,*)
C
      RETURN 
      END
C
C
      SUBROUTINE FLXDAT3(IKP,XGSM,YGSM,ZGSM,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $  FLUXBIN,NUMBIN,RNGCHK,NDROPHI,NDROPLO,LOGFLG,FLUX,AVGNUM,
     $  RNGCELL,NUMCELL)
C
C     This routine finds the flux corresponding to the satellite`s
C     GSM position coordinates by use of the GEOTAIL database.
C
C     This routine is used to calculate the spatial average of flux in a
C     volume given by RNGCHK, with the specified number of high and low
C     flux values inside the volume dropped first.
C
C     INPUTS:
C       IKP     - Kp interval index (1 -> MAXKP).
C       XGSM    - satellite`s X-coordinate (Re).
C       YGSM    - satellite`s Y-coordinate (Re).
C       ZGSM    - satellite`s Z-coordinate (Re).
C       NUMDAT  - number of non-zero values in the database.
C       XFLUX   - array containing the X-coordinate of each data
C                 cell`s center  (Re).
C       YFLUX   - array containing the Y-coordinate of each data
C                 cell`s center  (Re).
C       ZFLUX   - array containing the Z-coordinate of each data
C                 cell`s center  (Re).
C       FLUXBIN - array containing the average ion flux within
C                 each cell  (ions/[cm^2-sec-sr-MeV]).
C       NUMBIN  - array containing the number of non-zero values within
C                 each cell.
C       RNGCHK  - the range tolerance variable (Re).
C       NDROPHI - number of high flux values to drop for smoothing
C                  filter.
C
C       NDROPLO - number of low flux values to drop for smoothing
C                  filter.
C
C       LOGFLG  - flag controlling how flux average is performed
C              LOGFLG = 1 if log10 of flux values used.
C              LOGFLG = 2 if linear flux values used.
C
C     OUTPUTS:
C       FLUX    - computed average flux value  (ions/[cm^2-sec-sr-MeV]).
C       AVGNUM  - average number of flux values per cell used to get FLUX.
C       RNGCELL - distance to center of flux database cell used  (Re).
C       NUMCELL - number of flux database cells used that have the
C                 same value of RNGCELL.
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'MAXCELL.PAR'
C
      INTEGER NUMDAT(MAXKP),NUMBIN(MAXKP,MAXPNT)
      REAL FLUXBIN(MAXKP,MAXPNT),XFLUX(MAXKP,MAXPNT)
      REAL YFLUX(MAXKP,MAXPNT),ZFLUX(MAXKP,MAXPNT)
C
      REAL FLXSTO(MAXCELL),RNGSTO(MAXCELL)
      INTEGER NUMSTO(MAXCELL)
C
      REAL FLXUSE(MAXCELL),RNGUSE(MAXCELL)
      INTEGER NUMUSE(MAXCELL)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED FLXDAT3!!'
D     WRITE(*,*)' IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1) = ',
D    $            IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1)
D     WRITE(*,*)' ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1) = ',
D    $            ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1)
D     WRITE(*,*)' XGSM,YGSM,ZGSM = ',XGSM,YGSM,ZGSM
D     WRITE(*,*)' LOGFLG,RNGCHK,NDROPHI,NDROPLO = ',
D    $            LOGFLG,RNGCHK,NDROPHI,NDROPLO
D     PAUSE
C
C     Find the nearest non-zero data cell.  Use its flux value.
C
      IF(XGSM.GE.0.) THEN
C       Do not use Z-layers on the dayside of the magnetosphere.
        ZCKLO = -7.
        ZCKHI = +100.
      ELSE
C       Use the nearest neighbor flux only inside a range of Z-values.
        IF(ZGSM.LE.-6.) THEN
C         Use the nearest neighbor in the -7 < Z < -6. range.
          ZCKLO = -7.
          ZCKHI = -6.
        ELSE IF((ZGSM.GT.-6.).AND.(ZGSM.LE.-5.)) THEN
C         Use the nearest neighbor in the -6 < Z < -5. range.
          ZCKLO = -6.
          ZCKHI = -5.
        ELSE IF((ZGSM.GT.-5.).AND.(ZGSM.LE.+4.)) THEN
C         Use the nearest neighbor in the -5 < Z < +4. range.
          ZCKLO = -5.
          ZCKHI = +4.
        ELSE IF((ZGSM.GT.+4.).AND.(ZGSM.LE.+5.)) THEN
C         Use the nearest neighbor in the +4 < Z < +5. range.
          ZCKLO = +4.
          ZCKHI = +5.
        ELSE IF((ZGSM.GT.+5.).AND.(ZGSM.LE.+6.)) THEN
C         Use the nearest neighbor in the +5 < Z < +6. range.
          ZCKLO = +5.
          ZCKHI = +6.
        ELSE IF((ZGSM.GT.+6.).AND.(ZGSM.LE.+7.)) THEN
C         Use the nearest neighbor in the +6 < Z < +7. range.
          ZCKLO = +6.
          ZCKHI = +7.
        ELSE IF((ZGSM.GT.+7.).AND.(ZGSM.LE.+8.)) THEN
C         Use the nearest neighbor in the +7 < Z < +8. range.
          ZCKLO = +7.
          ZCKHI = +8.
        ELSE IF((ZGSM.GT.+8.).AND.(ZGSM.LE.+9.)) THEN
C         Use the nearest neighbor in the +8 < Z < +9. range.
          ZCKLO = +8.
          ZCKHI = +9.
        ELSE IF((ZGSM.GT.+9.).AND.(ZGSM.LE.+10.)) THEN
C         Use the nearest neighbor in the +9 < Z < +10. range.
          ZCKLO = +9.
          ZCKHI = +10.
        ELSE IF(ZGSM.GT.+10.) THEN
C         Use the nearest neighbor in the +10 < Z < +11. range.
          ZCKLO = +10.
          ZCKHI = +11.
        END IF
      END IF
C
D     WRITE(*,*)' ZCKLO,ZCKHI = ',ZCKLO,ZCKHI
C
      RNGCELL = 1.E+25
      NUMCELL = 0
      DO I = 1,NUMDAT(IKP)
        IF((FLUXBIN(IKP,I) .GT.1.).AND.(ZFLUX(IKP,I).GT.ZCKLO)
     $     .AND.(ZFLUX(IKP,I).LE.ZCKHI)) THEN
          RNG = SQRT((XFLUX(IKP,I)-XGSM)**2 + (YFLUX(IKP,I)-YGSM)**2
     $      + (ZFLUX(IKP,I)-ZGSM)**2)
D         WRITE(*,*)' I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),',
D    $              'ZFLUX(IKP,I) = ',
D    $                I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),
D    $               ZFLUX(IKP,I)
D         WRITE(*,*)' I,RNG,RNGCELL = ',I,RNG,RNGCELL
          RNGDIFF = RNG - RNGCELL
          RNGABS = ABS(RNGDIFF)
          IF((RNGABS.GT.RNGCHK).AND.(RNGDIFF.LT.0.0)) THEN
C           There is a new nearest neighbor data cell.
            NUMCELL = 1
            RNGCELL = RNG
            RNGSTO(1) = RNG
            FLXSTO(1) = FLUXBIN(IKP,I)
            NUMSTO(1) = NUMBIN(IKP,I)
          ELSE IF(RNGABS.LE.RNGCHK) THEN
C           There is a new data cell within the range
C           tolerance to the nearest neighbor.  This cell`s flux
C           should be included in the average for this location.
            NUMCELL = NUMCELL + 1
            RNGSTO(NUMCELL) = RNG
            FLXSTO(NUMCELL) = FLUXBIN(IKP,I)
            NUMSTO(NUMCELL) = NUMBIN(IKP,I)
            IF(NUMCELL.EQ.MAXCELL) GO TO 1000
          END IF
        END IF
      END DO
C
1000  CONTINUE
C
      NDO = NUMCELL
      DO J =1,NDROPHI
C
C       Find the index of the high flux value data cell.
C
        FLXMAX = 0.0
        DO I = 1,NDO
          IF(FLXSTO(I).GE.FLXMAX) THEN
            FLXMAX = FLXSTO(I)
            INDMAX = I
          END IF
        END DO
D       WRITE(*,*)' J,NDO,INDMAX,FLXMAX = ',J,NDO,INDMAX,FLXMAX
C
C       Save the IUSE data cells` information to the work arrays.
C
        IUSE = 0
        DO I = 1,NDO
          IF(I.NE.INDMAX) THEN
            IUSE = IUSE + 1
            RNGUSE(IUSE) = RNGSTO(I)
            FLXUSE(IUSE) = FLXSTO(I)
            NUMUSE(IUSE) = NUMSTO(I)
            FLXSTO(IUSE) = FLXUSE(IUSE)
D           WRITE(*,*)' J,I,IUSE,RNGUSE(IUSE),FLXUSE(IUSE),',
D    $                 'NUMUSE(IUSE) = ',
D    $                  J,I,IUSE,RNGUSE(IUSE),FLXUSE(IUSE),NUMUSE(IUSE)
          END IF
        END DO
      END DO
C
D     WRITE(*,*)' AFTER HIGH INDEX!  IUSE = ',IUSE
D     DO I = 1,IUSE
D       WRITE(*,*)' RNGUSE(I),FLXUSE(I),NUMUSE(I) = ',
D    $              RNGUSE(I),FLXUSE(I),NUMUSE(I)
D     END DO
D     PAUSE
C
      NDO = IUSE
      DO J =1,NDROPLO
C
C       Find the index of the low flux value data cell.
C
        FLXMIN = 1.E+25
        DO I = 1,NDO
          IF(FLXSTO(I).LE.FLXMIN) THEN
            FLXMIN = FLXSTO(I)
            INDMIN = I
          END IF
        END DO
C
C       Save the IUSE data cells' information to the work arrays.
C
        IUSE = 0
        DO I = 1,NDO
          IF(I.NE.INDMIN) THEN
            IUSE = IUSE + 1
            RNGUSE(IUSE) = RNGSTO(I)
            FLXUSE(IUSE) = FLXSTO(I)
            NUMUSE(IUSE) = NUMSTO(I)
            FLXSTO(IUSE) = FLXUSE(IUSE)
          END IF
        END DO
      END DO
C
D     WRITE(*,*)' AFTER LOW INDEX!  IUSE = ',IUSE
D     DO I = 1,IUSE
D       WRITE(*,*)' RNGUSE(I),FLXUSE(I),NUMUSE(I) = ',
D    $              RNGUSE(I),FLXUSE(I),NUMUSE(I)
D     END DO
D     PAUSE
C
      IF(IUSE.LE.1) THEN
C       There is only one data cell.
        AVGNUM = FLOAT(NUMUSE(1))
        RNGCELL = RNGUSE(1)
        NUMCELL = 1
        FLUX = FLXUSE(1)
        RETURN
      END IF
C
C     Get average flux.
      FLUX = 0.0
      AVGNUM = 0.0
      RNGCELL = 0.0
      DO I = 1,IUSE
        IF(LOGFLG.EQ.1) THEN
          FLUX   = FLUX   + LOG10(FLXUSE(I))
        ELSE
          FLUX   = FLUX   + FLXUSE(I)
        END IF
        AVGNUM = AVGNUM + FLOAT(NUMUSE(I))
        RNGCELL = RNGCELL + RNGUSE(I)
      END DO
      FLUX = FLUX/FLOAT(IUSE)
      AVGNUM = AVGNUM/FLOAT(IUSE)
      RNGCELL = RNGCELL/FLOAT(IUSE)
C
      IF(LOGFLG.EQ.1) FLUX = 10.**FLUX
      NUMCELL = IUSE
C
C
D     WRITE(*,*)
D     WRITE(*,*)' END FLXDAT3!!'
D     WRITE(*,*)' RNGCELL,FLUX = ',RNGCELL,FLUX
D     WRITE(*,*)
D     PAUSE 'PAUSED!'
C
      RETURN
      END
C
C
      SUBROUTINE FLXDAT4(IKP,XGSM,YGSM,ZGSM,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $  FLUXBIN,NUMBIN,RNGCHK,LOGFLG,FPCHI,FPCLO,FLUX,AVGNUM,
     $  RNGCELL,NUMCELL)
C
C     This routine finds the flux corresponding to the satellite`s
C     GSM position coordinates by use of the GEOTAIL database.
C
C     This routine is used to calculate the spatial average of flux in a
C     volume given by RNGCHK, with percentile threshold limits on flux
C     values.
C
C     INPUTS:
C       IKP     - Kp interval index (1 -> MAXKP).
C       XGSM    - satellite`s X-coordinate (Re).
C       YGSM    - satellite`s Y-coordinate (Re).
C       ZGSM    - satellite`s Z-coordinate (Re).
C       NUMDAT  - number of non-zero values in the database.
C       XFLUX   - array containing the X-coordinate of each data
C                 cell`s center  (Re).
C       YFLUX   - array containing the Y-coordinate of each data
C                 cell`s center  (Re).
C       ZFLUX   - array containing the Z-coordinate of each data
C                 cell`s center  (Re).
C       FLUXBIN - array containing the average ion flux within
C                 each cell  (ions/[cm^2-sec-sr-MeV]).
C       NUMBIN  - array containing the number of non-zero values within
C                 each cell.
C       RNGCHK  - the range tolerance variable (Re).
C       LOGFLG  - flag controlling how flux average is performed
C              LOGFLG = 1 if log10 of flux values used.
C              LOGFLG = 2 if linear flux values used.
C       FPCHI   - upper percentile limit for spatial averaging of flux
C       FPCLO   - lower percentile limit for spatial averaging of flux
C
C     OUTPUTS:
C       FLUX    - computed average flux value  (ions/[cm^2-sec-sr-MeV]).
C       AVGNUM  - average number of flux values per cell used to get FLUX.
C       RNGCELL - distance to center of flux database cell used  (Re).
C       NUMCELL - number of flux database cells used that have the
C                 same value of RNGCELL.
C
      INCLUDE 'MAXPNT.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'MAXCELL.PAR'
C
      INTEGER NUMDAT(MAXKP),NUMBIN(MAXKP,MAXPNT)
      REAL FLUXBIN(MAXKP,MAXPNT),XFLUX(MAXKP,MAXPNT)
      REAL YFLUX(MAXKP,MAXPNT),ZFLUX(MAXKP,MAXPNT)
C
      REAL FLXSTO(MAXCELL),RNGSTO(MAXCELL)
      INTEGER NUMSTO(MAXCELL)
C
      REAL FLXUSE(MAXCELL),RNGUSE(MAXCELL)
      INTEGER NUMUSE(MAXCELL)
C
      INTEGER FPCHI,FPCLO
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED FLXDAT4!!'
D     WRITE(*,*)' IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1) = ',
D    $            IKP,NUMDAT(1),XFLUX(1,1),YFLUX(1,1)
D     WRITE(*,*)' ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1) = ',
D    $            ZFLUX(1,1),FLUXBIN(1,1),NUMBIN(1,1)
D     WRITE(*,*)' XGSM,YGSM,ZGSM = ',XGSM,YGSM,ZGSM
D     WRITE(*,*)' LOGFLG,RNGCHK,FPCHI,FPCLO = ',
D    $            LOGFLG,RNGCHK,FPCHI,FPCLO
D     PAUSE
C
C     Find the nearest non-zero data cell.  Use its flux value.
C
      IF(XGSM.GE.0.) THEN
C       Do not use Z-layers on the dayside of the magnetosphere.
        ZCKLO = -7.
        ZCKHI = +100.
      ELSE
C       Use the nearest neighbor flux only inside a range of Z-values.
        IF(ZGSM.LE.-6.) THEN
C         Use the nearest neighbor in the -7 < Z < -6. range.
          ZCKLO = -7.
          ZCKHI = -6.
        ELSE IF((ZGSM.GT.-6.).AND.(ZGSM.LE.-5.)) THEN
C         Use the nearest neighbor in the -6 < Z < -5. range.
          ZCKLO = -6.
          ZCKHI = -5.
        ELSE IF((ZGSM.GT.-5.).AND.(ZGSM.LE.+4.)) THEN
C         Use the nearest neighbor in the -5 < Z < +4. range.
          ZCKLO = -5.
          ZCKHI = +4.
        ELSE IF((ZGSM.GT.+4.).AND.(ZGSM.LE.+5.)) THEN
C         Use the nearest neighbor in the +4 < Z < +5. range.
          ZCKLO = +4.
          ZCKHI = +5.
        ELSE IF((ZGSM.GT.+5.).AND.(ZGSM.LE.+6.)) THEN
C         Use the nearest neighbor in the +5 < Z < +6. range.
          ZCKLO = +5.
          ZCKHI = +6.
        ELSE IF((ZGSM.GT.+6.).AND.(ZGSM.LE.+7.)) THEN
C         Use the nearest neighbor in the +6 < Z < +7. range.
          ZCKLO = +6.
          ZCKHI = +7.
        ELSE IF((ZGSM.GT.+7.).AND.(ZGSM.LE.+8.)) THEN
C         Use the nearest neighbor in the +7 < Z < +8. range.
          ZCKLO = +7.
          ZCKHI = +8.
        ELSE IF((ZGSM.GT.+8.).AND.(ZGSM.LE.+9.)) THEN
C         Use the nearest neighbor in the +8 < Z < +9. range.
          ZCKLO = +8.
          ZCKHI = +9.
        ELSE IF((ZGSM.GT.+9.).AND.(ZGSM.LE.+10.)) THEN
C         Use the nearest neighbor in the +9 < Z < +10. range.
          ZCKLO = +9.
          ZCKHI = +10.
        ELSE IF(ZGSM.GT.+10.) THEN
C         Use the nearest neighbor in the +10 < Z < +11. range.
          ZCKLO = +10.
          ZCKHI = +11.
        END IF
      END IF
C
D     WRITE(*,*)' ZCKLO,ZCKHI = ',ZCKLO,ZCKHI
C
      RNGCELL = 1.E+25
      NUMCELL = 0
      DO I = 1,NUMDAT(IKP)
        IF((FLUXBIN(IKP,I) .GT.1.).AND.(ZFLUX(IKP,I).GT.ZCKLO)
     $     .AND.(ZFLUX(IKP,I).LE.ZCKHI)) THEN
          RNG = SQRT((XFLUX(IKP,I)-XGSM)**2 + (YFLUX(IKP,I)-YGSM)**2
     $      + (ZFLUX(IKP,I)-ZGSM)**2)
D         WRITE(*,*)' I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),',
D    $              'ZFLUX(IKP,I) = ',
D    $                I,FLUXBIN(IKP,I),XFLUX(IKP,I),YFLUX(IKP,I),
D    $               ZFLUX(IKP,I)
D         WRITE(*,*)' I,RNG,RNGCELL = ',I,RNG,RNGCELL
          RNGDIFF = RNG - RNGCELL
          RNGABS = ABS(RNGDIFF)
          IF((RNGABS.GT.RNGCHK).AND.(RNGDIFF.LT.0.0)) THEN
C           There is a new nearest neighbor data cell.
            NUMCELL = 1
            RNGCELL = RNG
            RNGSTO(1) = RNG
            FLXSTO(1) = FLUXBIN(IKP,I)
            NUMSTO(1) = NUMBIN(IKP,I)
          ELSE IF(RNGABS.LE.RNGCHK) THEN
C           There is a new data cell within the range
C           tolerance to the nearest neighbor.  This cell`s flux
C           should be included in the average for this location.
            NUMCELL = NUMCELL + 1
            RNGSTO(NUMCELL) = RNG
            FLXSTO(NUMCELL) = FLUXBIN(IKP,I)
            NUMSTO(NUMCELL) = NUMBIN(IKP,I)
            IF(NUMCELL.EQ.MAXCELL) GO TO 1000
          END IF
        END IF
      END DO
C
1000  CONTINUE
C
C     Calculate the flux statistics for the values inside this volume.
      CALL STATFLX(NUMCELL,RNGSTO,NUMSTO,FLXSTO,FPCHI,FPCLO,FMEAN,FLXHI,
     $  FLXLO,FSIG,FMAX,FMIN)
C
D     WRITE(*,*)' FPCHI,FPCLO,FLXHI,FLXLO = ',FPCHI,FPCLO,FLXHI,FLXLO
D     DO I = 1,NUMCELL
D       WRITE(*,*)' I,RNGSTO(I),NUMSTO(I),FLXSTO(I) = ',
D    $              I,RNGSTO(I),NUMSTO(I),FLXSTO(I)
D     END DO
C
C     Throw out flux values in the table that are above FLXHI or
C     below FLXLO.
C
      IUSE = 0
      DO I = 1,NUMCELL
        IF((FLXSTO(I).LT.FLXHI).AND.(FLXSTO(I).GT.FLXLO)) THEN
C         Use this flux value to perform spatial averaging.
          IUSE = IUSE + 1
          RNGUSE(IUSE) = RNGSTO(I)
          FLXUSE(IUSE) = FLXSTO(I)
          NUMUSE(IUSE) = NUMSTO(I)
D         WRITE(*,*)' IUSE,RNGUSE(IUSE),FLXUSE(IUSE),NUMUSE(IUSE) = ',
D    $                IUSE,RNGUSE(IUSE),FLXUSE(IUSE),NUMUSE(IUSE)
        END IF
      END DO
C
C
      IF(IUSE.LE.1) THEN
C       There is only one data cell.
        AVGNUM = FLOAT(NUMUSE(1))
        RNGCELL = RNGUSE(1)
        NUMCELL = 1
        FLUX = FLXUSE(1)
        RETURN
      END IF
C
C     Get average flux.
      FLUX = 0.0
      AVGNUM = 0.0
      RNGCELL = 0.0
      DO I = 1,IUSE
        IF(LOGFLG.EQ.1) THEN
          FLUX   = FLUX   + LOG10(FLXUSE(I))
        ELSE
          FLUX   = FLUX   + FLXUSE(I)
        END IF
        AVGNUM = AVGNUM + FLOAT(NUMUSE(1))
        RNGCELL = RNGCELL + RNGUSE(I)
      END DO
      FLUX = FLUX/FLOAT(IUSE)
      AVGNUM = AVGNUM/FLOAT(IUSE)
      RNGCELL = RNGCELL/FLOAT(IUSE)
C
      IF(LOGFLG.EQ.1) FLUX = 10.**FLUX
      NUMCELL = IUSE
C
C
D     WRITE(*,*)
D     WRITE(*,*)' END FLXDAT4!!'
D     WRITE(*,*)' NUMCELL,AVGNUM,RNGCELL,FLUX = ',
D    $            NUMCELL,AVGNUM,RNGCELL,FLUX
D     WRITE(*,*)
D     PAUSE 'PAUSED!'
C
      RETURN
      END
C
C
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
C
C
      SUBROUTINE LOCREG(XKP,XGSM,YGSM,ZGSM,XTAIL,YTAIL,ZTAIL,IDLOC)
C
C     This routine determines which phenomenological region the
C     spacecraft is in.
C
C     Input:
C       XKP     - Kp index (real value between 0 & 9).
C       XGSM    - satellite`s X-coordinate (Re).
C       YGSM    - satellite`s Y-coordinate (Re).
C       ZGSM    - satellite`s Z-coordinate (Re).
C
C     Outputs:
C       XTAIL   - satellite`s X-coordinate in geotail system (Re).
C       YTAIL   - satellite`s Y-coordinate in geotail system (Re).
C       ZTAIL   - satellite`s Z-coordinate in geotail system (Re).
C       IDLOC   - phenomenogical region location identification flag:
C                 IDLOC = 1 if spacecraft is in solar wind
C                 IDLOC = 2 if spacecraft is in magnetosheath
C                 IDLOC = 3 if spacecraft is in magnetosphere
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered LOCREG!'
D     WRITE(*,*)' XKP,XGSM,YGSM,ZGSM = ',
D    $            XKP,XGSM,YGSM,ZGSM
D     PAUSE
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
C     Transform the spacecraft`s coordinates to a system aligned
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
C
      SUBROUTINE MSHEFLX(XKP,ISPECI,FLUXMN,FLUX95,FLUX50,FLUXSD)
C
C     This routine provides the magnetosheath ion flux as a function
C     of Kp.
C
C     Input:
C       XKP     - Kp index (real value between 0 & 9).
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
C     Output:
C       FLUXMN  - mean flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX95  - 95% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX50  - 50% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUXSD  - standard deviation of flux for selected species.
C
      IF(ISPECI.EQ.1) THEN
C       Provide proton flux values.
        IF(XKP.LE.4.5) THEN
          FLUXMN = 7.161418E-3*XKP**2 + 2.831376E-1*XKP + 2.57324
        ELSE
          FLUXMN = 2.28935E-1*XKP + 2.94481
        END IF
        A = EXP(1.227335)
        FLUX95 = A*XKP**2.076779E-1
        FLUX50 = 6.674753E-3*XKP**3 - 9.069930E-2*XKP**2
     $         + 6.807628E-1*XKP + 1.231926
        FLUXSD = 1.347388E-1*XKP + 3.671634
C
        FLUXMN = 10**FLUXMN
        FLUX95 = 10**FLUX95
        FLUX50 = 10**FLUX50
        FLUXSD = 10**FLUXSD
      ELSE IF(ISPECI.EQ.2) THEN
C       Provide helium flux values.
        FLUXMN = -1.E-11
        FLUX95 = -1.E-11
        FLUX50 = -1.E-11
        FLUXSD = -1.E-11
      ELSE IF(ISPECI.EQ.3) THEN
C       Provide CNO flux values.
        FLUXMN = -1.E-11
        FLUX95 = -1.E-11
        FLUX50 = -1.E-11
        FLUXSD = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE NBRFLUX(XKP,NSECTRS,SECTX,SECTY,SCMEAN,SC95,SC50,
     $  SCSIG,XTAIL,YTAIL,ZTAIL,NUMDAT,XFLUX,YFLUX,ZFLUX,FLUXBIN,
     $  NUMBIN,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,
     $  FPCLO,FLUXMN,FLUX95,FLUX50,FLUXSD)
C
C     This routine provides the region`s ion flux as a function
C     of Kp.
C
C     Inputs:
C       XKP     - Kp index (real value between 0 & 9).
C
C       NSECTRS - number of Kp scaling sectors in region.
C
C       SECTX   - array of each sector center`s x coordinate.
C
C       SECTY   - array of each sector center`s y coordinate.
C
C       SCMEAN  - array of each sector`s mean flux scale factor.
C
C       SC95    - array of each sector`s 95% flux scale factor.
C
C       SC50    - array of each sector`s 50% flux scale factor.
C
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C       XTAIL   - satellite`s X-coordinate in geotail system (Re).
C
C       YTAIL   - satellite`s Y-coordinate in geotail system (Re).
C
C       ZTAIL   - satellite`s Z-coordinate in geotail system (Re).
C
C       NUMDAT  - number of non-zero values in the database.
C
C       XFLUX   - array containing the X-coordinate of each data
C                 cell`s center  (Re).
C
C       YFLUX   - array containing the Y-coordinate of each data
C                 cell`s center  (Re).
C
C       ZFLUX   - array containing the Z-coordinate of each data
C                 cell`s center  (Re).
C
C       FLUXBIN - array containing the average ion flux within
C                 each cell  (ions/[cm^2-sec-sr-MeV]).
C
C       NUMBIN  - array containing the number of non-zero values within
C                 each cell.
C
C       SMOOTH1 - flag for control of database smoothing filter:
C              SMOOTH1 = 0 if no data smoothing is used.
C              SMOOTH1 = 1 if spike rejection and near neighbor flux.
C              SMOOTH1 = 2 if spike rejection with range weighted
C                           scaling of flux.
C              SMOOTH1 = 3 if spike rejection with average flux.
C              SMOOTH1 = 4 if spatial average of flux in volume
C                           specified by RNGTOL.
C              SMOOTH1 = 5 if spatial average of flux in volume
C                           specified by RNGTOL, with the specified
C                           number of high and low flux values inside
C                           the volume dropped first.
C              SMOOTH1 = 6 if spatial averaging of flux in volume
C                           specified by RNGTOL, with percentile
C                           threshold limits on flux values.
C
C       NFLXGET - number of flux values to get for smoothing filter
C                  (used if SMOOTH1 = 1,2, or 3)
C
C       NDROPHI - number of high flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2,3, or 5).
C
C       NDROPLO - number of low flux values to drop for smoothing
C                  filter (used if SMOOTH1 = 1,2,3, or 5).
C
C       LOGFLG  - flag controlling how flux average is performed
C                  (used if SMOOTH1 = 2,3,4,5, or 6).
C              LOGFLG = 1 if log10 of flux values used.
C              LOGFLG = 2 if linear flux values used.
C
C       RNGTOL  - range tolerance from near-neigbor used in spatial
C                  averaging of database (Re)
C                  (used if SMOOTH1 = 4,5, or 6).
C
C       FPCHI   - upper percentile limit for spatial averaging of flux
C                  (used if SMOOTH1 = 6).
C
C       FPCLO   - lower percentile limit for spatial averaging of flux
C                  (used if SMOOTH1 = 6).
C
C     Output:
C       FLUXMN  - mean flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX95  - 95% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX50  - 50% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUXSD  - standard deviation of flux for selected species.
C
C     Set the minimum range for magnetosphere calculations.
      PARAMETER (RNGGEO = 6.0)
C
C     Set the number of Kp scaling sectors to use per calculation.
C     (NUMSCAL must not exceed NUMSEC!)
      PARAMETER (NUMSCAL = 2)
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
      INCLUDE 'MAXPNT.PAR'
C
      REAL SECTX(NUMSEC),SECTY(NUMSEC)
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
      REAL WTMEAN(MAXKP),WT95(MAXKP),WT50(MAXKP),WTSIG(MAXKP)
      REAL RNGSECT(NUMSEC),FLUX(MAXKP),AVGNUM(MAXKP),RNGCELL(MAXKP)
      INTEGER INDSECT(NUMSEC),NUMCELL(MAXKP)
C
      INTEGER NUMDAT(MAXKP),NUMBIN(MAXKP,MAXPNT)
      REAL FLUXBIN(MAXKP,MAXPNT),XFLUX(MAXKP,MAXPNT)
      REAL YFLUX(MAXKP,MAXPNT),ZFLUX(MAXKP,MAXPNT)
C
      INTEGER SMOOTH1,FPCHI,FPCLO
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered NBRFLUX!'
D     WRITE(*,*)' XKP = ',XKP
D     DO I = 1,NSECTRS
D       WRITE(*,*)
D       WRITE(*,*)' I,SECTX(I),SECTY(I) = ',I,SECTX(I),SECTY(I)
D       DO J = 1,MAXKP
D         WRITE(*,*)' I,J,SCMEAN(I,J),SC95(I,J) = ',
D    $                I,J,SCMEAN(I,J),SC95(I,J)
D         WRITE(*,*)' I,J,SC50(I,J),SCSIG(I,J) = ',
D    $                I,J,SC50(I,J),SCSIG(I,J)
D       END DO
D     END DO
D     WRITE(*,*)
D     WRITE(*,*)' XTAIL,YTAIL,ZTAIL = ',XTAIL,YTAIL,ZTAIL
D     WRITE(*,*)
D     DO I = 1,MAXKP
D       WRITE(*,*)' I,NUMDAT(I) = ',I,NUMDAT(I)
D       DO J = 1,MAXPNT
D         IF((XFLUX(I,J).GE.-15.).AND.(XFLUX(I,J).LE.-5.).AND.
D    $       (YFLUX(I,J).GE.-30.).AND.(YFLUX(I,J).LE.-20.)) THEN
D           WRITE(*,*)' I,J,XFLUX(I,J),YFLUX(I,J),ZFLUX(I,J) = ',
D    $                  I,J,XFLUX(I,J),YFLUX(I,J),ZFLUX(I,J)
D           WRITE(*,*)' I,J,NUMBIN(I,J),FLUXBIN(I,J) = ',
D    $                  I,J,NUMBIN(I,J),FLUXBIN(I,J)
D           WRITE(*,*)
D           PAUSE 'PAUSED!'
D         END IF
D       END DO
D     END DO
D     WRITE(*,*)
D     PAUSE 'PAUSED!'
C
C     Do not allow for calculations to take place inside the minimum
C     sphere, which is needed because of GEOTAIL`s orbit.
C
      RNGCK = SQRT(XTAIL**2 + YTAIL**2 + ZTAIL**2)
      IF(RNGCK.LT.RNGGEO) THEN
D       WRITE(*,*)
D       WRITE(*,*)' Entered magnetosphere data gap region!'
        FLUXMN = 0.
        FLUX95 = 0.
        FLUX50 = 0.
        FLUXSD = 0.
        RETURN
      END IF
C
C     Rank order the Kp scaling sectors on the basis of their range
C     from the satellite in the XY-plane.
C
      CALL NEIGHBR(XTAIL,YTAIL,NSECTRS,SECTX,SECTY,INDSECT,RNGSECT)
D     WRITE(*,*)' After NEIGHBR!'
D     DO I = 1,NSECTRS
D       WRITE(*,*)' I,INDSECT(I),RNGSECT(I) = ',I,INDSECT(I),RNGSECT(I)
D     END DO
D     WRITE(*,*)
C
C     Calculate the distance weighted sum of the Kp scaling factors.
C
C     NUMWT = NUMSCAL
      CALL WTSCAL(XTAIL,YTAIL,NUMSCAL,INDSECT,RNGSECT,SCMEAN,SC95,
     $  SC50,SCSIG,WTMEAN,WT95,WT50,WTSIG)
CC    CALL WTSCAL2(NUMSCAL,INDSECT,RNGSECT,SCMEAN,SC95,
CC   $  SC50,SCSIG,WTMEAN,WT95,WT50,WTSIG)
D     WRITE(*,*)' After WTSCAL!'
C
C     Find the near-neighbor flux data cell for each Kp interval.
C     These flux values are treated as the average flux at the center
C     their respective Kp intervals.
C
C     Fix the range tolerance for the near-neighbor flux calculation.
      RNGCHK = 1.0
C
      DO I = 1,MAXKP
        IF((SMOOTH1.EQ.0).OR.(SMOOTH1.EQ.4)) THEN
C         Calculate the flux with no data smoothing or with spatial
C         averaging inside the volume defined by RNGTOL.
          CALL FLXDAT1(I,XTAIL,YTAIL,ZTAIL,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $      FLUXBIN,NUMBIN,RNGCHK,FLUX(I),AVGNUM(I),RNGCELL(I),
     $      NUMCELL(I))
        ELSE IF((SMOOTH1.EQ.1).OR.(SMOOTH1.EQ.2).OR.(SMOOTH1.EQ.3)) THEN
C         Spike rejection option.
          CALL FLXDAT2(I,XTAIL,YTAIL,ZTAIL,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $      FLUXBIN,NUMBIN,RNGCHK,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,
     $      LOGFLG,FLUX(I),AVGNUM(I),RNGCELL(I),NUMCELL(I))
        ELSE IF(SMOOTH1.EQ.5) THEN
C         Perform the spatial average inside the volume defined by
C         RNGTOL after the specified number of high & low flux values
C         inside the volume have been dropped.
          CALL FLXDAT3(I,XTAIL,YTAIL,ZTAIL,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $      FLUXBIN,NUMBIN,RNGCHK,NDROPHI,NDROPLO,LOGFLG,FLUX(I),
     $      AVGNUM(I),RNGCELL(I),NUMCELL(I))
        ELSE
C         (SMOOTH1 = 6 case) Perform spatial averaging of flux in the
C         volume specified by RNGTOL, with percentile threshold limits
C         on flux values used in averaging.
          CALL FLXDAT4(I,XTAIL,YTAIL,ZTAIL,NUMDAT,XFLUX,YFLUX,ZFLUX,
     $      FLUXBIN,NUMBIN,RNGCHK,LOGFLG,FPCHI,FPCLO,FLUX(I),AVGNUM(I),
     $      RNGCELL(I),NUMCELL(I))
        END IF
D       WRITE(*,*)' After FLUXDAT!'
D       WRITE(*,*)' I,FLUX(I),AVGNUM(I),RNGCELL(I),NUMCELL(I) = ',
D    $              I,FLUX(I),AVGNUM(I),RNGCELL(I),NUMCELL(I)
      END DO
C
C     Find the minimum distance to a data cell from any one of the
C     database`s Kp intervals.
C
      RNG1 = RNGMIN1(MAXKP,RNGCELL)
D     WRITE(*,*)' After RNGMIN!'
C
C     Get the weighted sum (average) of all of the useable flux values
C     that lie within the specified range tolerance above the minimum
C     range. Get the flux statistics by multiplying the average flux
C     value at the spacecraft`s location by the distance weighted sum
C     of the Kp scaling factors.
C
      IF((SMOOTH1.EQ.4).OR.(SMOOTH1.EQ.5).OR.(SMOOTH1.EQ.6)) THEN
C       Spatial averaging is used.
        RNGCHK = RNGTOL
      ELSE
C       There is no data smoothing used.
        RNGCHK = 1.0
      END IF
C
      TOTNUM = 0.
      FLUXMN = 0.
      FLUX95 = 0.
      FLUX50 = 0.
      FLUXSD = 0.
      RNG2 = RNG1 + RNGCHK
C
      ANNDIST = 0.
      DO I = 1,MAXKP
        IF(RNGCELL(I).LE.RNG2) THEN
          ANNDIST = ANNDIST + RNGCELL(I)*AVGNUM(I)
          FLUXMN = FLUXMN + FLUX(I)*AVGNUM(I)*WTMEAN(I)
D         WRITE(*,*)' I,RNGCELL(I),RNG2,FLUXMN,AVGNUM(I),WTMEAN(I) = ',
D    $                I,RNGCELL(I),RNG2,FLUXMN,AVGNUM(I),WTMEAN(I)
          FLUX95 = FLUX95 + FLUX(I)*AVGNUM(I)*WT95(I)
          FLUX50 = FLUX50 + FLUX(I)*AVGNUM(I)*WT50(I)
          FLUXSD = FLUXSD + FLUX(I)*AVGNUM(I)*WTSIG(I)
          TOTNUM = TOTNUM + AVGNUM(I)
D         WRITE(*,*)' I,TOTNUM = ',I,TOTNUM
        END IF
      END DO
C
      ANNDIST = ANNDIST/TOTNUM
C
      FLUXMN = FLUXMN/TOTNUM
      FLUX95 = FLUX95/TOTNUM
      FLUX50 = FLUX50/TOTNUM
      FLUXSD = FLUXSD/TOTNUM
C
      RETURN
      END
C
C
      SUBROUTINE NEIGHBR(XTAIL,YTAIL,NSECTRS,SECTX,SECTY,
     $  INDSECT,RNGSECT)
C
C     This routine finds the nearest neighbors to the point in
C     question. This routine is used to find the spatial sectors used
C     to perform the Kp scaling for a given point.
C
C     Inputs:
C       XTAIL   - satellite`s X-coordinate in geotail system (Re).
C       YTAIL   - satellite`s Y-coordinate in geotail system (Re).
C       NSECTRS - number of Kp scaling sectors in region.
C       SECTX   - array of each sector center`s x coordinate.
C       SECTY   - array of each sector center`s y coordinate.
C
C     Outputs:
C       INDSECT - index array pointing to the Kp scaling sectors,
C                 ranked in order of nearest to farthest.
C       RNGSECT - array containing the sorted range values of the
C                 spacecraft to the Kp scaling sectors,
C
      INCLUDE 'NUMSEC.PAR'
C
      REAL SECTX(NUMSEC),SECTY(NUMSEC),RNGSECT(NUMSEC)
      INTEGER INDSECT(NUMSEC)
C
C     First, find the range to each sector in their original order.
      DO I = 1,NSECTRS
        INDSECT(I) = I
        RNGSECT(I) = SQRT((XTAIL-SECTX(I))**2 + (YTAIL-SECTY(I))**2)
      END DO
C
C     Sort the Kp scaling sector range and index arrays in order of
C     nearest to farthest.
      CALL SORTRNG(NSECTRS,RNGSECT,INDSECT)
C
      RETURN
      END
C
C
      REAL FUNCTION RNGMIN1(N,RNG)
C
C     This routine returns the minimum range from the list.
C
      REAL RNG(N)
C
      RNGMIN1 = 1.E+30
      DO I = 1,N
        IF(RNG(I).LT.RNGMIN1) RNGMIN1 = RNG(I)
      END DO
C
      RETURN
      END
C
C
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
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED ROT8ANG!'
D     WRITE(*,*)' ANG,X,Y,XHINGE = ',ANG,X,Y,XHINGE
D     PAUSE
C
C
      IF(X.LE.XHINGE) THEN
        XROT2 = X*COS(ANG) + Y*SIN(ANG)
        YROT2 = -X*SIN(ANG) + Y*COS(ANG)
      ELSE
        XROT2 = X
        YROT2 = Y
      END IF
D     WRITE(*,*)' ANG,XROT2,YROT2 = ',ANG,XROT2,YROT2
D     PAUSE
      RETURN
      END
C
C
      SUBROUTINE SCALKP1(XKP,ISPECI,NSECTRS,SECTX,SECTY,SCMEAN,SC95,
     $  SC50,SCSIG)
C
C     This routine finds the Kp scaling parameters in the solar wind.
C
C     Inputs:
C       XKP     - Kp index user desires output for.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
C     Outputs:
C       NSECTRS - number of Kp scaling sectors in region.
C       SECTX   - array of each sector center`s x coordinate.
C       SECTY   - array of each sector center`s y coordinate.
C       SCMEAN  - array of each sector`s mean flux scale factor.
C       SC95    - array of each sector`s 95% flux scale factor.
C       SC50    - array of each sector`s 50% flux scale factor.
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
C
      REAL SECTX(NUMSEC),SECTY(NUMSEC)
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SCALKP1!'
D     WRITE(*,*)' XKP,ISPECI = ',XKP,ISPECI
C
C     Number of sectors used in the solar wind.
      NSECTRS = 3
C
C     Get the flux scaling for each spatial sector (protons).
C
      DO I = 1,9
C
C       Get the Kp value at the midpoint of the data interval.
        XKPSC = FLOAT(I) - 0.5
D       WRITE(*,*)' I,XKPSC = ',I,XKPSC
C
        CALL SECTR11(ISPECI,XKP,XKPSC,SCMEAN(1,I),SC95(1,I),SC50(1,I),
     $    SCSIG(1,I),SECTX(1),SECTY(1))
C
        CALL SECTR12(ISPECI,XKP,XKPSC,SCMEAN(2,I),SC95(2,I),SC50(2,I),
     $    SCSIG(2,I),SECTX(2),SECTY(2))
C
        CALL SECTR13(ISPECI,XKP,XKPSC,SCMEAN(3,I),SC95(3,I),SC50(3,I),
     $    SCSIG(3,I),SECTX(3),SECTY(3))
      END DO
C
      RETURN
      END
C
C
      SUBROUTINE SCALKP2(XKP,ISPECI,NSECTRS,SECTX,SECTY,SCMEAN,SC95,
     $  SC50,SCSIG)
C
C     This routine finds the Kp scaling parameters in the magnetosheath.
C
C     Inputs:
C       XKP     - Kp index user desires output for.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
C     Outputs:
C       NSECTRS - number of Kp scaling sectors in region.
C       SECTX   - array of each sector center`s x coordinate.
C       SECTY   - array of each sector center`s y coordinate.
C       SCMEAN  - array of each sector`s mean flux scale factor.
C       SC95    - array of each sector`s 95% flux scale factor.
C       SC50    - array of each sector`s 50% flux scale factor.
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
C
      REAL SECTX(NUMSEC),SECTY(NUMSEC)
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SCALKP2!'
D     WRITE(*,*)' XKP,ISPECI = ',XKP,ISPECI
C
C     Number of sectors used in the magnetosheath.
      NSECTRS = 4
C
C     Get the flux scaling for each spatial sector (protons).
C
      DO I = 1,9
C
C       Get the Kp value at the midpoint of the data interval.
        XKPSC = FLOAT(I) - 0.5
D       WRITE(*,*)' I,XKPSC = ',I,XKPSC
C
        CALL SECTR21(ISPECI,XKP,XKPSC,SCMEAN(1,I),SC95(1,I),SC50(1,I),
     $    SCSIG(1,I),SECTX(1),SECTY(1))
C
        CALL SECTR22(ISPECI,XKP,XKPSC,SCMEAN(2,I),SC95(2,I),SC50(2,I),
     $    SCSIG(2,I),SECTX(2),SECTY(2))
C
        CALL SECTR23(ISPECI,XKP,XKPSC,SCMEAN(3,I),SC95(3,I),SC50(3,I),
     $    SCSIG(3,I),SECTX(3),SECTY(3))
C
        CALL SECTR24(ISPECI,XKP,XKPSC,SCMEAN(4,I),SC95(4,I),SC50(4,I),
     $    SCSIG(4,I),SECTX(4),SECTY(4))
      END DO
C
      RETURN
      END
C
C
      SUBROUTINE SCALKP3(XKP,ISPECI,NSECTRS,SECTX,SECTY,SCMEAN,SC95,
     $  SC50,SCSIG)
C
C     This routine finds the Kp scaling parameters in the magnetosphere.
C
C     Inputs:
C       XKP     - Kp index user desires output for.
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
C     Outputs:
C       NSECTRS - number of Kp scaling sectors in region.
C       SECTX   - array of each sector center`s x coordinate.
C       SECTY   - array of each sector center`s y coordinate.
C       SCMEAN  - array of each sector`s mean flux scale factor.
C       SC95    - array of each sector`s 95% flux scale factor.
C       SC50    - array of each sector`s 50% flux scale factor.
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
C
      REAL SECTX(NUMSEC),SECTY(NUMSEC)
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SCALKP3!'
D     WRITE(*,*)' XKP,ISPECI = ',XKP,ISPECI
C
C     Number of sectors used in the magnetosphere.
      NSECTRS = 10
C
C     Get the flux scaling for each spatial sector (protons).
C
      DO I = 1,9
C
C       Get the Kp value at the midpoint of the data interval.
        XKPSC = FLOAT(I) - 0.5
D       WRITE(*,*)' I,XKPSC = ',I,XKPSC
C
        CALL SECTR31(ISPECI,XKP,XKPSC,SCMEAN(1,I),SC95(1,I),SC50(1,I),
     $    SCSIG(1,I),SECTX(1),SECTY(1))
C
        CALL SECTR32(ISPECI,XKP,XKPSC,SCMEAN(2,I),SC95(2,I),SC50(2,I),
     $    SCSIG(2,I),SECTX(2),SECTY(2))
C
        CALL SECTR33(ISPECI,XKP,XKPSC,SCMEAN(3,I),SC95(3,I),SC50(3,I),
     $    SCSIG(3,I),SECTX(3),SECTY(3))
C
        CALL SECTR34(ISPECI,XKP,XKPSC,SCMEAN(4,I),SC95(4,I),SC50(4,I),
     $    SCSIG(4,I),SECTX(4),SECTY(4))
C
        CALL SECTR35(ISPECI,XKP,XKPSC,SCMEAN(5,I),SC95(5,I),SC50(5,I),
     $    SCSIG(5,I),SECTX(5),SECTY(5))
C
        CALL SECTR36(ISPECI,XKP,XKPSC,SCMEAN(6,I),SC95(6,I),SC50(6,I),
     $    SCSIG(6,I),SECTX(6),SECTY(6))
C
        CALL SECTR37(ISPECI,XKP,XKPSC,SCMEAN(7,I),SC95(7,I),SC50(7,I),
     $    SCSIG(7,I),SECTX(7),SECTY(7))
C
        CALL SECTR38(ISPECI,XKP,XKPSC,SCMEAN(8,I),SC95(8,I),SC50(8,I),
     $    SCSIG(8,I),SECTX(8),SECTY(8))
C
        CALL SECTR39(ISPECI,XKP,XKPSC,SCMEAN(9,I),SC95(9,I),SC50(9,I),
     $    SCSIG(9,I),SECTX(9),SECTY(9))
C
        CALL SECTR310(ISPECI,XKP,XKPSC,SCMEAN(10,I),SC95(10,I),
     $    SC50(10,I),SCSIG(10,I),SECTX(10),SECTY(10))
      END DO
C
      RETURN
      END
C
C
      SUBROUTINE SECTR11(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Solar Wind Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 1:  (+5<X<+20; +13<Y<+30; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR11!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = +5.
      X2 = +20.
      Y1 = +13.
      Y2 = +30.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 0.2477179*XKP + 2.532024
        F95 = 0.1987326*XKP + 3.283149
        F50 = 1.31762*EXP(0.127923*XKP)
        FSIG = 0.1528122*XKP + 3.316698
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 0.2477179*XKPSC + 2.532024
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR12(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Solar Wind Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 2:  (+8<X<+22; -10<Y<+10; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR12!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = +8.
      X2 = +22.
      Y1 = -10.
      Y2 = +10.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = EXP(1.053755)*(XKP**0.1816665)
        F95 = EXP(1.23647)*(XKP**0.1521542)
        F50 = 0.137769*XKP + 1.508285
        FSIG = EXP(1.232657)*(XKP**0.127408)
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = EXP(1.053755)*(XKPSC**0.1816665)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR13(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Solar Wind Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 3:  (+5<X<+20; -25<Y<-13; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR13!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = +5.
      X2 = +20.
      Y1 = -25.
      Y2 = -13.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 2.418556*EXP(0.09242323*XKP)
        F95 = 3.129407*EXP(0.07088557*XKP)
        F50 = 0.4192601*XKP + 1.12118
        FSIG = 0.2818979*XKP + 2.802846
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 2.418556*EXP(0.09242323*XKPSC)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR21(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosheath Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 1:  (-20<X<0; +15<Y<+30; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR21!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = -20.
      X2 = 0.
      Y1 = +15.
      Y2 = +30.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = EXP(1.006261)*(XKP**0.2358533)
        F95 = EXP(1.242684)*(XKP**0.167599)
        F50 = 3.595895E-1*XKP + 1.485105
        FSIG = EXP(1.154729)*(XKP**0.1813815)
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = EXP(1.006261)*(XKPSC**0.2358533)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR22(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosheath Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 2:  (-5<X<+15; +10<Y<+23; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR22!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = -5.
      X2 = +15.
      Y1 = +10.
      Y2 = +23.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = EXP(1.075755)*(XKP**0.228047)
        F95 = EXP(1.28287)*(XKP**0.1789508)
        F50 = 4.152996E-1*XKP + 1.144803
        FSIG = EXP(1.231504)*(XKP**0.1678395)
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = EXP(1.075755)*(XKPSC**0.228047)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR23(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosheath Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 3:  (-5<X<+15; -10<Y<+10; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR23!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = -5.
      X2 = +15.
      Y1 = -10.
      Y2 = +10.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = EXP(1.059922)*(XKP**0.2450142)
        F95 = EXP(1.262771)*(XKP**0.2122456)
        F50 = 2.699979E-1*XKP + 1.92621
        FSIG = EXP(1.170143)*(XKP**0.2329764)
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = EXP(1.059922)*(XKPSC**0.2450142)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR24(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosheath Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 4:  (-25<X<+5; -30<Y<-12; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR24!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = -25.
      X2 = +5.
      Y1 = -30.
      Y2 = -12.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = EXP(0.8034997)*(XKP**0.2943536)
        F95 = EXP(1.029681)*(XKP**0.2502851)
        F50 = EXP(0.6214508)*(XKP**0.2912395)
        FSIG = EXP(0.890587)*(XKP**0.2943353)
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = EXP(0.8034997)*(XKPSC**0.2943536)
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR31(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 1:  (-10<X<-6; -6<Y<+4; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered SECTR31!'
D     WRITE(*,*)' ISPECI,XKP,XKPSC = ',ISPECI,XKP,XKPSC
C
C     Set up this sector`s limits.
      X1 = -10.
      X2 = -6.
      Y1 = -6.
      Y2 = +4.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
D     WRITE(*,*)' XCEN,YCEN = ',XCEN,YCEN
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 2.443395E-1*XKP + 3.845401
        F95 = 4.539177 * EXP(3.807753E-2*XKP)
        F50 = 3.058675E-1*XKP + 3.264229
        FSIG = 2.038728E-1*XKP + 4.088105
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
D       WRITE(*,*)' FMEAN,F95,F50,FSIG = ',FMEAN,F95,F50,FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 2.443395E-1*XKPSC + 3.845401
D       WRITE(*,*)'FAVG = ',FAVG
        FAVG = 10**FAVG
D       WRITE(*,*)'FAVG = ',FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
D       WRITE(*,*)' SCMEAN,SC95,SC50,SCSIG = ',SCMEAN,SC95,SC50,SCSIG
D       PAUSE
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR32(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 2:  (-7<X<0; +8<Y<+13; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -7.
      X2 = 0.
      Y1 = +8.
      Y2 = +13.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        A = EXP(1.430943)
        FMEAN = A * (XKP**1.431528E-1)
        A = EXP(1.510317)
        F95 = A * (XKP**1.432958E-1)
        A = EXP(1.285142)
        F50 = A * (XKP**1.935917E-1)
        A = EXP(1.544309)
        FSIG = A * (XKP**8.922371E-2)
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        A = EXP(1.430943)
        FAVG = A * (XKPSC**1.431528E-1)
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR33(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 4:  (-18<X<-12; -18<Y<-11; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -18.
      X2 = -12.
      Y1 = -18.
      Y2 = -11.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 4.0986685E-1*XKP + 2.083598
        F95 = 3.677568E-1*XKP + 2.792231
        F50 = 4.706894E-1*XKP + 1.382612
        FSIG = 3.606812E-1*XKP + 2.440727
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 4.0986685E-1*XKPSC + 2.083598
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR34(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 5:  (-28<X<-21; -18<Y<-10; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -28.
      X2 = -21.
      Y1 = -18.
      Y2 = -10.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 3.249438E-1*XKP + 2.425203
        F95 = 2.860754E-1*XKP + 3.135966
        F50 = 3.848902E-1*XKP + 1.684094
        FSIG = 2.574007E-1*XKP + 2.909206
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 3.249438E-1*XKPSC + 2.425203
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR35(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 6:  (-29<X<-25; -10<Y<-3; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -29.
      X2 = -25.
      Y1 = -10.
      Y2 = -3.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 4.343142E-1*XKP + 2.180041
        F95 = 4.123490E-1*XKP + 2.759741
        F50 = 4.826937E-1*XKP + 1.563440
        FSIG = 3.533449E-1*XKP + 2.641683
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 4.343142E-1*XKPSC + 2.180041
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR36(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 7:  (-20<X<-15; +1<Y<+10; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -20.
      X2 = -15.
      Y1 = +1.
      Y2 = +10.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        A = EXP(1.270656)
        FMEAN = A * (XKP**2.230935E-1)
        A = EXP(1.436059)
        F95 = A * (XKP**1.577674E-1)
        A = EXP(1.051924)
        F50 = A * (XKP**3.327092E-1)
        A = EXP(1.332255)
        FSIG = A * (XKP**1.706059E-1)
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        A = EXP(1.270656)
        FAVG = A * (XKPSC**2.230935E-1)
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR37(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 8:  (-19<X<-14; +10<Y<+19; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -19.
      X2 = -14.
      Y1 = +10.
      Y2 = +19.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 3.213946E-1*XKP + 2.964045
        F95 = 2.901571E-1*XKP + 3.628429
        F50 = 3.349902E-1*XKP + 2.415445
        FSIG = 2.934793E-1*XKP + 3.251733
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 3.213946E-1*XKPSC + 2.964045
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR38(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 9:  (-30<X<-24; +10<Y<+17; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -30.
      X2 = -24.
      Y1 = 10.
      Y2 = +17.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        A = EXP(1.114799)
        FMEAN = A * (XKP**2.013791E-1)
        A = EXP(1.283152)
        F95 = A * (XKP**1.715240E-1)
        A = EXP(8.948732E-1)
        F50 = A * (XKP**2.100576E-1)
        A = EXP(1.232212)
        FSIG = A * (XKP**1.728799E-1)
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        A = EXP(1.114799)
        FAVG = A * (XKPSC**2.013791E-1)
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEA = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR39(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 10:  (0<X<+8; +8<Y<+13; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = 0.
      X2 = +8.
      Y1 = +8.
      Y2 = +13.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 2.373299E-1*XKP + 3.988981
        F95 = 1.769049E-1*XKP + 4.660334
        F50 = 2.427994E-1*XKP + 3.717080
        FSIG = 2.079478E-1*XKP + 4.169556
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 2.373299E-1*XKPSC + 3.988981
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SECTR310(ISPECI,XKP,XKPSC,SCMEAN,SC95,SC50,SCSIG,
     $  XCEN,YCEN)
C
C     ***************** Magnetosphere Kp Scaling *********************
C
C     This routine provides the proton flux vs. Kp scaling in
C     sector 10:  (0<X<+8; -11<Y<-6; All Z).
C
C     Inputs:
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C       XKP     - user selected Kp index (real value between 0 & 9).
C       XKPSC   - the Kp value at the midpoint of the data interval.
C
C     Outputs:
C       SCMEAN  - mean flux scale factor.
C       SC95    - 95% flux scale factor.
C       SC50    - 50% flux scale factor.
C       SCSIG   - standard deviation scale factor of flux.
C       XCEN    - sector center`s x-coordinate (Re).
C       YCEN    - sector center`s x-coordinate (Re).
C
C     Set up this sector`s limits.
      X1 = -8.
      X2 = -6.
      Y1 = -16.
      Y2 = -14.
C
      XCEN = (X1 + X2)/2.
      YCEN = (Y1 + Y2)/2.
C
      IF(ISPECI.EQ.1) THEN
C       *** Calculate the proton flux scaling parameters ***
C
        FMEAN = 2.373299E-1*XKP + 3.988981
        F95 = 1.769049E-1*XKP + 4.660334
        F50 = 2.427994E-1*XKP + 3.717080
        FSIG = 2.079478E-1*XKP + 4.169556
C
        FMEAN = 10**FMEAN
        F95 = 10**F95
        F50 = 10**F50
        FSIG = 10**FSIG
C
C       Scale from the average Kp value for the database in this data
C       interval.
C
        FAVG = 2.373299E-1*XKPSC + 3.988981
        FAVG = 10**FAVG
C
        SCMEAN = FMEAN/FAVG
        SC95 = F95/FAVG
        SC50 = F50/FAVG
        SCSIG = FSIG/FAVG
C
      ELSE IF(ISPECI.EQ.2) THEN
C       *** Calculate the helium flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
C
      ELSE
C       *** Calculate the CNO flux scaling parameters ***
C
        SCMEAN = -1.E-11
        SC95 = -1.E-11
        SC50 = -1.E-11
        SCSIG = -1.E-11
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SOLWFLX(XKP,ISPECI,FLUXMN,FLUX95,FLUX50,FLUXSD)
C
C     This routine provides the solar wind ion flux as a function
C     of Kp.
C
C     Input:
C       XKP     - Kp index (real value between 0 & 9).
C       ISPECI  - ion species selection flag
C                 ISPECI = 1 for protons
C                 ISPECI = 2 for Helium
C                 ISPECI = 3 for CNO
C
C     Output:
C       FLUXMN  - mean flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX95  - 95% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUX50  - 50% flux (#/[cm^2-sec-sr-MeV]) for selected species.
C       FLUXSD  - standard deviation of flux for selected species.
C
      IF(ISPECI.EQ.1) THEN
C       Provide proton flux values.
        IF(XKP.LE.5.5) THEN
          FLUXMN = -8.009051E-3*XKP**2 + 3.011148E-1*XKP + 2.427724
          FLUX95 = 1.172813E-2*XKP**2 + 1.805303E-1*XKP + 3.216384
        ELSE
          FLUXMN = -1.989790E-1*XKP**2 + 3.018409*XKP - 6.741037
          FLUX95 = -2.644953E-1*XKP**2 + 3.832377*XKP - 8.525337
        END IF
        FLUX50 = 3.732036E-2*XKP**2 + 1.509852E-2*XKP + 1.586031
        FLUXSD = 2.128721E-1*XKP + 3.166099
C
        FLUXMN = 10** FLUXMN
        FLUX95 = 10** FLUX95
        FLUX50 = 10** FLUX50
        FLUXSD = 10** FLUXSD
      ELSE IF(ISPECI.EQ.2) THEN
C       Provide helium flux values.
        FLUXMN = -1.E-11
        FLUX95 = -1.E-11
        FLUX50 = -1.E-11
        FLUXSD = -1.E-11
      ELSE IF(ISPECI.EQ.3) THEN
C       Provide CNO flux values.
        FLUXMN = -1.E-11
        FLUX95 = -1.E-11
        FLUX50 = -1.E-11
        FLUXSD = -1.E-11
      END IF
C
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
      INCLUDE 'PI.PAR'
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
        DYPRES = 4.0
        ABANG = 0.0
        XHINGE = +14.
        VX = -500.
      ELSE
        DYPRES = 10.0
        ABANG = 0.0
        XHINGE = +14.
        VX = -500.
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE SORTRNG(N,RA,INDA)
C
C     *** 	Based on SORT2 taken from "Numerical Recipes" ***
C     Sorts an array RA of length N into ascending numerical order
C     using the Heapsort algorithm, while making the corresponding
C     rearrangement of the index array INDA.
C
      INCLUDE 'NUMSEC.PAR'
C
      REAL RA(NUMSEC)
      INTEGER INDA(NUMSEC)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED SORTRNG!!'
D     WRITE(*,*)' 1,RA(1),INDA(1) = ',
D    $            1,RA(1),INDA(1)
D     WRITE(*,*)
D     DO I = 1,N
D       WRITE(*,*)' I,RA(I),INDA(I) = ',
D    $              I,RA(I),INDA(I)
D     END DO
D     WRITE(*,*)
D     PAUSE 'PAUSED!!'
      L=N/2+1
      IR=N
10    CONTINUE
        IF(L.GT.1) THEN
          L=L-1
D         WRITE(*,*)' #1: L = ',L
D         WRITE(*,*)' #1: L,RA(L),INDA(L) = ',L,RA(L),INDA(L)
          RRA=RA(L)
          IINDA=INDA(L)
        ELSE
D         WRITE(*,*)' #2: IR = ',IR
D         WRITE(*,*)' #2: IR,RA(IR),INDA(IR) = ',IR,RA(IR),INDA(IR)
          RRA=RA(IR)
          IINDA=INDA(IR)
          RA(IR)=RA(1)
          INDA(IR)=INDA(1)
          IR=IR-1
          IF(IR.EQ.1)THEN
            RA(1)=RRA
            INDA(1)=IINDA
            RETURN
          ENDIF
        ENDIF
        I=L
        J=L+L
20      IF(J.LE.IR)THEN
          IF(J.LT.IR)THEN
D           WRITE(*,*)' #3: J = ',J
D           WRITE(*,*)' #3: J,RA(J),RA(J+1) = ',J,RA(J),RA(J+1)
            IF(RA(J).LT.RA(J+1))J=J+1
          ENDIF
          IF(RRA.LT.RA(J))THEN
D           WRITE(*,*)' #4: J = ',J
D           WRITE(*,*)' #4: J,RA(J),INDA(J) = ',J,RA(J),INDA(J)
            RA(I)=RA(J)
            INDA(I)=INDA(J)
            I=J
            J=J+J
          ELSE
            J=IR+1
          ENDIF
          GOTO 20
        ENDIF
D       WRITE(*,*)' #5: I = ',I
D       WRITE(*,*)' #5: I,RA(I),INDA(I) = ',I,RA(I),INDA(I)
        RA(I)=RRA
        INDA(I)=IINDA
      GOTO 10
C
      END
C
C
      SUBROUTINE SORTRG5(NSAVE,RA,RB,INDA)
C
C     *** 	Based on SORT2 taken from "Numerical Recipes" ***
C     Sorts an array RA of length NSAVE into ascending numerical order
C     using the Heapsort algorithm, while making the corresponding
C     rearrangement of the arrays RB and INDA.
C
      REAL RA(NSAVE),RB(NSAVE)
      INTEGER INDA(NSAVE)
C
      N = NSAVE
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED SORTRG2!!'
D     WRITE(*,*)' 1,RA(1),RB(1),INDA(1) = ',
D    $            1,RA(1),RB(1),INDA(1)
D     WRITE(*,*)
D     DO I = 1,N
D       WRITE(*,*)' I,RA(I),RB(I),INDA(I) = ',
D    $              I,RA(I),RB(I),INDA(I) 
D     END DO
D     WRITE(*,*)
D     PAUSE 'PAUSED!!'
      L=N/2+1
      IR=N
10    CONTINUE
        IF(L.GT.1) THEN
          L=L-1
D         WRITE(*,*)' #1: L = ',L
D         WRITE(*,*)' #1: L,RA(L),RB(L),INDA(L) = ',
D    $                    L,RA(L),RB(L),INDA(L)
          RRA=RA(L)
          RRB=RB(L)
          IINDA=INDA(L)
        ELSE
D         WRITE(*,*)' #2: IR = ',IR
D         WRITE(*,*)' #2: IR,RA(IR),RB(IR),INDA(IR) = ',
D                         IR,RA(IR),RB(IR),INDA(IR)
          RRA=RA(IR)
          RRB=RB(IR)
          IINDA=INDA(IR)
          RA(IR)=RA(1)
          RB(IR)=RB(1)
          INDA(IR)=INDA(1)
          IR=IR-1
          IF(IR.EQ.1)THEN
            RA(1)=RRA
            RB(1)=RRB
            INDA(1)=IINDA
            RETURN
          ENDIF
        ENDIF
        I=L
        J=L+L
20      IF(J.LE.IR)THEN
          IF(J.LT.IR)THEN
D           WRITE(*,*)' #3: J = ',J
D           WRITE(*,*)' #3: J,RA(J),RA(J+1) = ',J,RA(J),RA(J+1)
D           WRITE(*,*)' #3: J,RB(J),RB(J+1) = ',J,RB(J),RB(J+1)
            IF(RA(J).LT.RA(J+1))J=J+1
          ENDIF
          IF(RRA.LT.RA(J))THEN
D           WRITE(*,*)' #4: J = ',J
D           WRITE(*,*)' #4: J,RA(J),RB(J),INDA(J) = ',
D    $                      J,RA(J),RB(J),INDA(J)
            RA(I)=RA(J)
            RB(I)=RB(J)
            INDA(I)=INDA(J)
            I=J
            J=J+J
          ELSE
            J=IR+1
          ENDIF
          GOTO 20
        ENDIF
D       WRITE(*,*)' #5: I = ',I
D       WRITE(*,*)' #5: I,RA(I),RB(I),INDA(I) = ',
D    $                  I,RA(I),RB(I),INDA(I)
        RA(I)=RRA
        RB(I)=RRB
        INDA(I)=IINDA
      GOTO 10
C
      END
C
C
      SUBROUTINE SORTFL2(N,RA,RB,NB)
C
C     *** 	Based on SORT2 taken from "Numerical Recipes" ***
C     Sorts an array RA of length N into ascending numerical order
C     using the Heapsort algorithm, while making the corresponding
C     rearrangement of the arrays RB and NB.
C
      INCLUDE 'MAXCELL.PAR'
C
      REAL RA(MAXCELL),RB(MAXCELL)
      INTEGER NB(MAXCELL)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED SORTFL2!!'
D     WRITE(*,*)' N,RA(1) = ',
D    $            N,RA(1)
D     PAUSE 'PAUSED!!'
      L=N/2+1
      IR=N
10    CONTINUE
        IF(L.GT.1) THEN
          L=L-1
          RRA=RA(L)
          RRB=RB(L)
          NNB=NB(L)
        ELSE
          RRA=RA(IR)
          RRB=RB(IR)
          NNB=NB(IR)
          RA(IR)=RA(1)
          RB(IR)=RB(1)
          NB(IR)=NB(1)
          IR=IR-1
          IF(IR.EQ.1)THEN
            RA(1)=RRA
            RB(1)=RRB
            NB(1)=NNB
            RETURN
          ENDIF
        ENDIF
        I=L
        J=L+L
20      IF(J.LE.IR)THEN
          IF(J.LT.IR)THEN
            IF(RA(J).LT.RA(J+1))J=J+1
          ENDIF
          IF(RRA.LT.RA(J))THEN
            RA(I)=RA(J)
            RB(I)=RB(J)
            NB(I)=NB(J)
            I=J
            J=J+J
          ELSE
            J=IR+1
          ENDIF
          GOTO 20
        ENDIF
        RA(I)=RRA
        RB(I)=RRB
        NB(I)=NNB
      GOTO 10
C
      END
C
C
      SUBROUTINE STATFLX(N,RIN,NIN,AIN,FPCHI,FPCLO,AMEAN,APCHI,APCLO,
     $  ASIG,AMAX,AMIN)
C
C     This routine calculates the statistics based on array AIN, the
C     flux or fluence contained in one energy bin.
C
C     INPUTS:
C       N      - total number of samples.
C       RIN    - range array.
C       NIN    - number stored array.
C       AIN    - flux/fluence contained in one energy bin.
C       FPCHI  - upper percentile limit for spatial averaging of flux.
C       FPCLO  - lower percentile limit for spatial averaging of flux.
C
C     OUTPUTS:
C       AMEAN  - mean of AIN.
C       APCHI  - FPCHI percentile level of AIN.
C       APCLO  - FPCLO percentile level of AIN.
C       ASIG   - standard deviation of AIN.
C       AMAX   - maximum of AIN.
C       AMIN   - minimum of AIN.
C     
C
      INCLUDE 'MAXCELL.PAR'
C
      REAL AIN(MAXCELL),RIN(MAXCELL)
      INTEGER NIN(MAXCELL),FPCHI,FPCLO
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED STATFLX!!'
D     WRITE(*,*)' N,AIN(1),FPCHI,FPCLO = ',
D    $            N,AIN(1),FPCHI,FPCLO
D     PAUSE 'PAUSED!!'
C
      RFPCHI = FLOAT(FPCHI)
      RFPCLO = FLOAT(FPCLO)
C
      ASUM=0.0
      AMAX=1.E-30
      AMIN=1.E+30
      DO 100 L=1,N
        ASUM=ASUM+AIN(L)
        IF(AIN(L).GE.AMAX) THEN
          AMAX=AIN(L)
        END IF
        IF(AIN(L).LE.AMIN) THEN
          AMIN=AIN(L)
        END IF
100   CONTINUE
      AMEAN=ASUM/FLOAT(N)
C
      ASUMSQ=0.0
      DO 200 L=1,N
        ASUMSQ=ASUMSQ+(AIN(L)-AMEAN)**2
200   CONTINUE
      IF(N.GT.1) THEN
        ASIG=SQRT(ASUMSQ/FLOAT(N-1))
      ELSE
        ASIG=0.0
      ENDIF
C
C     Find the FPCHI and FPCLO percentile values of AIN.
      IF(N.GT.1) THEN
        CALL SORTFL2(N,AIN,RIN,NIN)
        PERSTP=100./FLOAT(N)
        ILO=INT(RFPCHI/PERSTP)
        IF(ILO.LT.1) ILO=1
        IHI=ILO+1
        IF(IHI.GT.N) IHI=N
        IF(ILO.EQ.IHI) THEN
          APCHI=AIN(ILO)
        ELSE
          PERLO=PERSTP*FLOAT(ILO)
          PERHI=PERSTP*FLOAT(IHI)
          APCHI=YINT(PERLO,AIN(ILO),PERHI,AIN(IHI),RFPCHI,1)
        ENDIF
        ILO=INT(RFPCLO/PERSTP)
        IF(ILO.LT.1) ILO=1
        IHI=ILO+1
        IF(IHI.GT.N) IHI=N
        IF(ILO.EQ.IHI) THEN
          APCLO=AIN(ILO)
        ELSE
          PERLO=PERSTP*FLOAT(ILO)
          PERHI=PERSTP*FLOAT(IHI)
          APCLO=YINT(PERLO,AIN(ILO),PERHI,AIN(IHI),RFPCLO,1)
        ENDIF
      ELSE
        APCHI=AIN(1)
        APCLO=AIN(1)
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE WTSCAL(XTAIL,YTAIL,NUMSCAL,INDSECT,RNGSECT,SCMEAN,
     $  SC95,SC50,SCSIG,WTMEAN,WT95,WT50,WTSIG)
C
C     This routine calculates the distance weighted sum of the Kp
C     scaling factors.  The objective of this approach is to arrive
C     at a set of Kp scaling factors that have been "blended" together
C     according to their relative distances from the point at which
C     output is desired.
C
C     Algorithm:
C
C     (1) Multiply the closest sector`s Kp scaling factors by the
C         distance to the farthest sector.
C     (2) Multiply the  2nd closest sector`s Kp scaling factors by the
C         distance to the 2nd farthest sector.
C     (3) Repeat this process until you multiply the farthest sector`s
C         Kp scaling factors by the distance to the closest sector.
C     (4) Get the final set of Kp scaling factors by summing the distance
C         scaled quantities and dividing the sum by the total distance
C         to all of the sectors.
C
C     Inputs:
C       XTAIL   - satellite`s X-coordinate in geotail system (Re).
C       YTAIL   - satellite`s Y-coordinate in geotail system (Re).
C       NUMSCAL - the number of Kp scaling sectors to use per
C                 calculation. (NUMSCAL must not exceed NUMSEC!)
C       INDSECT - index array pointing to the Kp scaling sectors,
C                 ranked in order of nearest to farthest.
C       RNGSECT - array containing the sorted range values of the
C                 spacecraft to the Kp scaling sectors,
C       SCMEAN  - array of each sector`s mean flux scale factor.
C       SC95    - array of each sector`s 95% flux scale factor.
C       SC50    - array of each sector`s 50% flux scale factor.
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C     Outputs:
C       WTMEAN  - distance weighted sum of the mean flux scale factors.
C       WT95    - distance weighted sum of the 95% flux scale factors.
C       WT50    - distance weighted sum of the 50% flux scale factors.
C       WTSIG   - distance weighted sum of the std dev flux scale factors.
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
C
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
      REAL WTMEAN(MAXKP),WT95(MAXKP),WT50(MAXKP),WTSIG(MAXKP)
      REAL RNGSECT(NUMSEC)
      INTEGER INDSECT(NUMSEC)
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered WTSCAL!'
D     WRITE(*,*)' NUMSCAL = ',NUMSCAL
D     DO I = 1,NUMSCAL
D       WRITE(*,*)' I,INDSECT(I),RNGSECT(I) = ',I,INDSECT(I),RNGSECT(I)
D     END DO
D     DO I = 1,NUMSEC
D       DO J = 1,MAXKP
D         IF(J.EQ.1) THEN
D           WRITE(*,*)' I,J,SCMEAN(I,J),SC95(I,J) = ',
D    $                  I,J,SCMEAN(I,J),SC95(I,J)
D           WRITE(*,*)' I,J,SC50(I,J),SCSIG(I,J) = ',
D    $                  I,J,SC50(I,J),SCSIG(I,J)
D         END IF
D       END DO
D     END DO
C
CC    IF(XTAIL.GE.0.) THEN
C       Choose sector 10 only for dayside magnetosphere.
CC      DO J = 1,MAXKP
CC        WTMEAN(J) = SCMEAN(10,J)
CC        WT95(J) = SC95(10,J)
CC        WT50(J) = SC50(10,J)
CC        WTSIG(J) = SCSIG(10,J)
CC      END DO
CC      RETURN
CC    END IF
C
      DTOT = 0.
      DO J = 1,MAXKP
        WTMEAN(J) = 0.
        WT95(J) = 0.
        WT50(J) = 0.
        WTSIG(J) = 0.
      END DO
C
      DO I = 1,NUMSCAL
        DTOT = DTOT + RNGSECT(I)
        II = INDSECT(I)
        JJ = NUMSCAL - I + 1
        WEIGHT = RNGSECT(JJ)
D       WRITE(*,*)' I,II,JJ,DTOT,WEIGHT = ',I,II,JJ,DTOT,WEIGHT
        DO J = 1,MAXKP
          WTMEAN(J) = WTMEAN(J) + SCMEAN(II,J)*WEIGHT
          WT95(J) = WT95(J) + SC95(II,J)*WEIGHT
          WT50(J) = WT50(J) + SC50(II,J)*WEIGHT
          WTSIG(J) = WTSIG(J) + SCSIG(II,J)*WEIGHT
        END DO
      END DO
C
      DO J = 1,MAXKP
        WTMEAN(J) = WTMEAN(J)/DTOT
        WT95(J) = WT95(J)/DTOT
        WT50(J) = WT50(J)/DTOT
        WTSIG(J) = WTSIG(J)/DTOT
D       IF(J.EQ.1) THEN
D         WRITE(*,*)' J,WTMEAN(J),WT95(J),WT50(J),WTSIG(J) = ',
D    $                J,WTMEAN(J),WT95(J),WT50(J),WTSIG(J)
D       END IF
      END DO
D     WRITE(*,*)' Exit WTSCAL!'
C
      RETURN
      END
C
C
      SUBROUTINE WTSCAL2(NUMSCAL,INDSECT,RNGSECT,SCMEAN,SC95,SC50,SCSIG,
     $  WTMEAN,WT95,WT50,WTSIG)
C
C     This routine calculates the Kp scaling factors.
C
C     Inputs:
C       NUMSCAL - the number of Kp scaling sectors to use per
C                 calculation. (NUMSCAL must not exceed NUMSEC!)
C       INDSECT - index array pointing to the Kp scaling sectors,
C                 ranked in order of nearest to farthest.
C       RNGSECT - array containing the sorted range values of the
C                 spacecraft to the Kp scaling sectors,
C       SCMEAN  - array of each sector`s mean flux scale factor.
C       SC95    - array of each sector`s 95% flux scale factor.
C       SC50    - array of each sector`s 50% flux scale factor.
C       SCSIG   - array of each sector`s std dev flux scale factor.
C
C     Outputs:
C       WTMEAN  - mean flux scale factors.
C       WT95    - 95% flux scale factors.
C       WT50    - 50% flux scale factors.
C       WTSIG   - std dev flux scale factors.
C
      INCLUDE 'NUMSEC.PAR'
      INCLUDE 'MAXKP.PAR'
C
      REAL SCMEAN(NUMSEC,MAXKP),SC95(NUMSEC,MAXKP)
      REAL SC50(NUMSEC,MAXKP),SCSIG(NUMSEC,MAXKP)
      REAL WTMEAN(MAXKP),WT95(MAXKP),WT50(MAXKP),WTSIG(MAXKP)
      REAL RNGSECT(NUMSEC)
      INTEGER INDSECT(NUMSEC)
C
D     WRITE(*,*)
D     WRITE(*,*)' Entered WTSCAL2!'
D     WRITE(*,*)' NUMSCAL = ',NUMSCAL
D     DO I = 1,NUMSCAL
D       WRITE(*,*)' I,INDSECT(I),RNGSECT(I) = ',I,INDSECT(I),RNGSECT(I)
D     END DO
D     DO I = 1,NUMSCAL
D       DO J = 1,MAXKP
D         WRITE(*,*)' I,J,SCMEAN(I,J),SC95(I,J) = ',
D    $                I,J,SCMEAN(I,J),SC95(I,J)
D         WRITE(*,*)' I,J,SC50(I,J),SCSIG(I,J) = ',
D    $                I,J,SC50(I,J),SCSIG(I,J)
D       END DO
D     END DO
C
      DTOT = 0.
      DO J = 1,MAXKP
        WTMEAN(J) = 0.
        WT95(J) = 0.
        WT50(J) = 0.
        WTSIG(J) = 0.
      END DO
C
      DO I = 1,NUMSCAL
        II = INDSECT(I)
        DO J = 1,MAXKP
          WTMEAN(J) = WTMEAN(J) + SCMEAN(II,J)
          WT95(J) = WT95(J) + SC95(II,J)
          WT50(J) = WT50(J) + SC50(II,J)
          WTSIG(J) = WTSIG(J) + SCSIG(II,J)
        END DO
      END DO
C
      DO J = 1,MAXKP
        WTMEAN(J) = WTMEAN(J)/FLOAT(NUMSCAL)
        WT95(J) = WT95(J)/FLOAT(NUMSCAL)
        WT50(J) = WT50(J)/FLOAT(NUMSCAL)
        WTSIG(J) = WTSIG(J)/FLOAT(NUMSCAL)
      END DO
D     WRITE(*,*)' Exit WTSCAL2!'
C
      RETURN
      END
C
C
      FUNCTION YINT(X1,Y1,X2,Y2,XIN,MODE)         
C         
C *** FUNCTION INTERPOLATE -- RETURNS Y-COORDINATE CORRESPONDING TO XIN         
C *** ALONG THE "LINE" DEFINED BY (X1, Y1), (X2, Y2).  MODE REFERS TO 
C *** INTERPOLATION MODE WHERE  1 IS LINEAR       
C ***                           2 IS SEMILOG - LOG/LINEAR   
C ***                           3 IS SEMILOG - LINEAR/LOG   
C ***                           4 IS LOG/LOG      
C         
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
