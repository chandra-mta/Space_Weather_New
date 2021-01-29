CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
C
C  REQUIREMENT REFERENCE NUMBERS:  3.5.3.7
C
C  PURPOSE:  Given Chandra's ephemeris and fluence threshold level per orbit,
C            this routine calculates the protection and turn-on event times and
C            locations.
C
C  INPUT DATA:    SUN AND SPACECRAFT EPHEMERIS, FLUENCE LEVELS
C
C  OUTPUT DATA:   SCIENCE INSTRUMENT TURN-ON AND TURN-OFF EVENT TIMES
C
C  INVOCATION METHOD:  FORTRAN SUBROUTINE CALL
C
      SUBROUTINE CXORAD(EPHSTP,NUMEPH,SUNECI,EPHECI,EPHDATE,ISPECI,
     $      FLUTHR,FLUTOL,FLULVL,REARTH,RNGMIN,LUNIT,IUSESW,FSWIMN,
     $      FSWI95,FSWI50,FSWISD,IUSEMSH,NUMKPS,XKPIN,FRACKP,SMOOTH1,
     $      NFLXGET,NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2,
     $      OFFEVNT,TONEVNT,ACISIN,ACISOUT,ECITON,ECISAFE,GSETON,
     $      GSESAFE,GSMTON,GSMSAFE,FLUWARN,CXOFLUE,CXOTIME)
C
C ARGUMENT LIST:
C
C    ARGUMENT NAME   TYPE   USE    DESCRIPTION
C  ----------------  ----   ---   -----------------------------------
C
C       EPHSTP        R*4    I    Time step between ephemeris points.
C                                 (sec) 
C
C       NUMEPH        I*4    I    Number of points in ephemeris.
C
C       SUNECI        R*8    I    Array containing Sun ephemeris points in ECI
C                                 coordinate system (km).
C                                 SUNECI(I,1) = x coordinate of Ith ephemeris point.
C                                 SUNECI(I,2) = y coordinate of Ith ephemeris point.
C                                 SUNECI(I,3) = z coordinate of Ith ephemeris point.
C
C       EPHECI        R*8    I    Array containing Chandra ephemeris points in ECI
C                                 coordinate system (km).
C                                 EPHECI(I,1) = x coordinate of Ith ephemeris point.
C                                 EPHECI(I,2) = y coordinate of Ith ephemeris point.
C                                 EPHECI(I,3) = z coordinate of Ith ephemeris point.
C
C       EPHDATE       I*4    I    Integer array containing dates of Sun and Chandra 
C                                 ephemeris points.
C                                 EPHDATE(I,1) = Year (YYYY) of Ith ephemeris point.
C                                 EPHDATE(I,2) = Day (DDD) of Year of Ith ephemeris point.
C                                 EPHDATE(I,3) = Hour (HH) of Day of Ith ephemeris point.
C                                 EPHDATE(I,4) = Minute (MM) of Hour of Ith ephemeris point.
C                                 EPHDATE(I,5) = Second (SS) of Minute of Ith ephemeris point.
C
C       ISPECI        I*4    I    Ion species calculation control flag.
C                                 ISPECI = 1  -> calculate proton environment.
C                                 ISPECI = 2  -> calculate helium environment.
C                                 ISPECI = 3  -> calculate CNO environment.
C
C       FLUTHR        R*4    I    Fluence per orbit threshold (ions/cm^2-sr-MeV).
C
C       FLUTOL        R*4    I    Fluence calculation tolerance (% of fluence threshold).
C
C       FLULVL        I*4    I    Percentile level (e.g., 50%, 95%) of particle flux
C                                 environment used in fluence calculation.
C                                 FLULVL = 1  -> mean flux used
C                                 FLULVL = 2  -> 95% flux used
C                                 FLULVL = 3  -> 50% flux used
C
C       REARTH        R*8    I    Radius of the Earth (km)
C
C       RNGMIN        R*4    I    Minimum geocentric range that ion flux
C                                 calculations are performed (Re)
C
C       LUNIT         I*4    I    Array of unit numbers used in opening CRM's database files.
C                                 LUNIT(1) = solar wind database unit number
C                                 LUNIT(2) = magnetosheath database unit number
C                                 LUNIT(3) = magnetosphere database unit number
C
C       IUSESW        I*4    I    flag for control of solar wind flux calculation:
C                                 IUSESW = 0 if (uniform flux) analytic solar wind model used.
C                                 IUSESW = 1 if user supplied uniform solar wind flux value used.
C                                 IUSESW = 2 if solar wind database used.
C                                 IUSESW = 3 if sum of solar wind database value and user
C                                            supplied uniform solar wind flux value used.
C                                 IUSESW = 4 if sum of (uniform flux) analytic solar wind model
C                                            and user supplied uniform solar wind flux value used.
C
C       FSWIMN        R*4    I    user supplied mean uniform solar wind flux for the
C                                 selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWI95        R*4    I    user supplied 95% level uniform solar wind flux for
C                                 the selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWI50        R*4    I    user supplied 50% level uniform solar wind flux for
C                                 the selected species (#/[cm^2-sec-sr-MeV]).
C
C       FSWISD        R*4    I    user supplied std. dev. of uniform solar wind flux
C                                 for the selected species (#/[cm^2-sec-sr-MeV]).
C
C       IUSEMSH       I*4    I    flag for control of magnetosheath flux calculation:
C                                 IUSEMSH = 0 if (uniform flux) analytic magnetosheath model used.
C                                 IUSEMSH = 1 if user supplied uniform solar wind flux value used.
C                                 IUSEMSH = 2 if magnetosheath database used.
C                                 IUSEMSH = 3 if sum of magnetosheath database value and user
C                                             supplied uniform solar wind flux value used.
C                                 IUSEMSH = 4 if sum of (uniform flux) analytic magnetosheath model
C                                             and user supplied uniform solar wind flux value used.
C
C       NUMKPS        I*4    I    number of Kp index intervals used as input distribution.
C
C       XKPIN         R*4    I    array of Kp interval midpoint values.
C
C       FRACKP        R*4    I    array containing the fraction (value between 0. & 1.) of
C                                 the corresponding Kp interval.
C
C       SMOOTH1       I*4    I    flag for control of database smoothing filter:
C                                 SMOOTH1 = 0 if no data smoothing is used.
C                                 SMOOTH1 = 1 if spike rejection and near neighbor flux.
C                                 SMOOTH1 = 2 if spike rejection with range weighted scaling of flux.
C                                 SMOOTH1 = 3 if spike rejection with average flux.
C                                 SMOOTH1 = 4 if spatial average of flux in volume specified by RNGTOL.
C                                 SMOOTH1 = 5 if spatial average of flux in volume specified by
C                                             RNGTOL, with the specified number of high and low
C                                             flux values inside the volume dropped first.
C                                 SMOOTH1 = 6 if spatial averaging of flux in volume specified by
C                                             RNGTOL, with percentile threshold limits on flux values.
C
C       NFLXGET       I*4    I    number of flux values to get for smoothing filter.
C                                 (used if SMOOTH1 = 1,2, or 3)
C
C       NDROPHI       I*4    I    number of high flux values to drop for smoothing filter.
C                                 (used if SMOOTH1 = 1,2,3, or 5)
C
C       NDROPLO       I*4    I    number of low flux values to drop for smoothing filter.
C                                 (used if SMOOTH1 = 1,2,3, or 5)
C
C       LOGFLG        I*4    I    flag controlling how flux average is performed.
C                                 LOGFLG = 1 if log10 of flux values used.
C                                 LOGFLG = 2 if linear flux values used.
C                                 (used if SMOOTH1 = 2,3,4,5, or 6)
C
C       RNGTOL        R*4    I    range tolerance from near-neigbor used in spatial averaging of
C                                 database (Re).
C                                 (used if SMOOTH1 = 4,5 or 6)
C
C       FPCHI         I*4    I    upper percentile limit for spatial averaging of flux.
C                                 (used if SMOOTH1 = 6)
C
C       FPCLO         I*4    I    lower percentile limit for spatial averaging of flux.
C                                 (used if SMOOTH1 = 6)
C
C       SMOOTH2       I*4    I    flag for control of flux smoothing along orbit.
C                                 SMOOTH2 = 0 if no data smoothing is used along orbit.
C                                 SMOOTH2 = 1 if data smoothing is used along orbit.
C
C       OFFEVNT       L*4    O    ACIS protection event flag.
C                                 OFFEVNT = .TRUE. if a protection event is found before the
C                                 last position prior to the minimum range.
C
C       TONEVNT       L*4    O    ACIS turn-on event flag.
C                                 TONEVNT = .TRUE. if a turn-on event is found after the
C                                 first position beyond the minimum range.
C
C       ACISIN        I*4    O    ACIS placed in focal plane (turn-on event).
C                                 ACISIN(1) = Year (YYYY) of event.
C                                 ACISIN(2) = Day (DDD) of Year of event.
C                                 ACISIN(3) = Hour (HH) of Day of event.
C                                 ACISIN(4) = Minute (MM) of Hour of event.
C                                 ACISIN(5) = Second (SS) of Minute of event.
C       
C       ACISOUT       I*4    O    ACIS taken out of focal plane (protection event).
C                                 ACISOUT(1) = Year (YYYY) of event.
C                                 ACISOUT(2) = Day (DDD) of Year of event.
C                                 ACISOUT(3) = Hour (HH) of Day of event.
C                                 ACISOUT(4) = Minute (MM) of Hour of event.
C                                 ACISOUT(5) = Second (SS) of Minute of event.
C
C       ECITON        R*8    O    Array containing ECI coordinates of turn-on 
C                                 event (km).
C                                 ECITON(1) = x coordinate of turn-on event.
C                                 ECITON(2) = y coordinate of turn-on event.
C                                 ECITON(3) = z coordinate of turn-on event.
C
C       ECISAFE       R*8    O    Array containing ECI coordinates of protection 
C                                 (turn-off) event (km).
C                                 ECISAFE(1) = x coordinate of protection event.
C                                 ECISAFE(2) = y coordinate of protection event.
C                                 ECISAFE(3) = z coordinate of protection event.
C
C       GSETON        R*8    O    Array containing GSE coordinates of turn-on 
C                                 event (Re).
C                                 GSETON(1) = x coordinate of turn-on event.
C                                 GSETON(2) = y coordinate of turn-on event.
C                                 GSETON(3) = z coordinate of turn-on event.
C
C       GSESAFE       R*8    O    Array containing GSE coordinates of protection 
C                                 (turn-off) event (Re).
C                                 GSESAFE(1) = x coordinate of protection event.
C                                 GSESAFE(2) = y coordinate of protection event.
C                                 GSESAFE(3) = z coordinate of protection event.
C
C       GSMTON        R*8    O    Array containing GSM coordinates of turn-on 
C                                 event (Re).
C                                 GSMTON(1) = x coordinate of turn-on event.
C                                 GSMTON(2) = y coordinate of turn-on event.
C                                 GSMTON(3) = z coordinate of turn-on event.
C
C       GSMSAFE       R*8    O    Array containing GSM coordinates of protection 
C                                 (turn-off) event (Re).
C                                 GSMSAFE(1) = x coordinate of protection event.
C                                 GSMSAFE(2) = y coordinate of protection event.
C                                 GSMSAFE(3) = z coordinate of protection event.
C
C       FLUWARN       I*4    O    Integer array containing warning flags.
C                                 FLUWARN(1) = 0 if ephemeris time step is OK.
C                                 FLUWARN(1) = 1 if ephemeris time step too large.
C                                 FLUWARN(2) = 0 if fluence tolerance OK.
C                                 FLUWARN(2) = 1 if fluence tolerance too large.
C                                 FLUWARN(3) = 0 if Kp distribution fractions add to 1.
C                                 FLUWARN(3) = 1 if Kp distribution fractions do not add to 1.
C
C       CXOFLUE       R*4    O    Fluence calculated for this ephemeris (ions/[cm^2-sr-MeV]).
C
C       CXOTIME       R*4    O    Time duration of fluence calculation (sec).
C
C
C  EXTERNAL VARIABLES:  NONE
C
C  EXTERNAL REFERENCES:  list subroutines called here, if any
C
C  DEVELOPMENT HISTORY:
C                                              DESCRIPTION
C      AUTHOR      RELEASE    DATE             OF CHANGE
C   ------------   -------  ---------   ---------------------------------------
C   B. BLACKWELL    TBD       7/00      ORIGINAL VERSION
C
C
C  NOTES:  EPHECI is the ephemeris for 1 orbit or less.  Nominally, it will
C          cover an interval from perigee to perigee.  Exceptions will be partial
C          orbits at the start or end of an ephemeris file or run time spans
C          that are less than one orbit.
C
C          If the ephemeris' time step is too large, or if the tolerance
C          on the fluence calculation tolerance is too small,the
C          appropriate flag in FLUWARN is set and a warning message
C          is written.
C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
C
      INCLUDE 'MAXEPH1.PAR'
      INCLUDE 'MAXKPS.PAR'
C
      REAL*8 SUNECI(MAXEPH1,3),EPHECI(MAXEPH1,3),ECITON(3),ECISAFE(3)
      REAL*8 REARTH
      REAL*4 EPHGSE(MAXEPH1,3),EPHGSM(MAXEPH1,3)
      REAL*4 FLUX(MAXEPH1),FLUE(MAXEPH1),TSPAN(MAXEPH1)
      REAL*4 XKPIN(MAXKPS),FRACKP(MAXKPS)
      REAL*4 GSETON(3),GSESAFE(3),GSMTON(3),GSMSAFE(3)
      INTEGER *4 IDFLUX(MAXEPH1),ISTART(MAXEPH1),ISTOP(MAXEPH1)
      INTEGER*4 EPHDATE(MAXEPH1,5),ISPECI,ACISIN(5),ACISOUT(5),
     $  FLUWARN(3),FLULVL,SMOOTH1,SMOOTH2,FPCHI,FPCLO,LUNIT(3)
      LOGICAL*4 OFFEVNT, TONEVNT
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED CXORAD!'
D     WRITE(*,*)' EPHSTP,NUMEPH   = ',EPHSTP,NUMEPH
D     WRITE(*,*)
D     WRITE(*,*)' EPHDATE(1,1-5)  = ',(EPHDATE(1,J),J=1,5)
D     WRITE(*,*)' EPHDATE(92,1-5) = ',(EPHDATE(92,J),J=1,5)
D     WRITE(*,*)' SUNECI(1,1-3)   = ',(SUNECI(1,J),J=1,3)
D     WRITE(*,*)' SUNECI(92,1-3)  = ',(SUNECI(92,J),J=1,3)
D     WRITE(*,*)' SUNECI(6000,1-3)  = ',(SUNECI(6000,J),J=1,3)
D     WRITE(*,*)' EPHECI(1,1-3)   = ',(EPHECI(1,J),J=1,3)
D     WRITE(*,*)' EPHECI(92,1-3)  = ',(EPHECI(92,J),J=1,3)
D     WRITE(*,*)' EPHECI(6000,1-3)  = ',(EPHECI(6000,J),J=1,3)
D     WRITE(*,*)
D     WRITE(*,*)' ISPECI,FLUTHR,FLUTOL,FLULVL = ',
D    $            ISPECI,FLUTHR,FLUTOL,FLULVL
D     WRITE(*,*)' REARTH,RNGMIN,LUNIT,IUSESW,IUSEMSH = ',
D    $            REARTH,RNGMIN,LUNIT,IUSESW,IUSEMSH
D     WRITE(*,*)' FSWIMN,FSWI95,FSWI50,FSWISD = ',
D    $            FSWIMN,FSWI95,FSWI50,FSWISD
D     WRITE(*,*)' FMSHIMN,FMSHI95,FMSHI50,FMSHISD = ',
D    $            FMSHIMN,FMSHI95,FMSHI50,FMSHISD
D     WRITE(*,*)' NUMKPS = ',NUMKPS
D     WRITE(*,*)' XKPIN(1-NUMKPS) = ',(XKPIN(J),J=1,NUMKPS)
D     WRITE(*,*)' FRACKP(1-NUMKPS) = ',(FRACKP(J),J=1,NUMKPS)
D     WRITE(*,*)
D     PAUSE
C
C     Check for warnings on inputs.
C
      CALL GETWARN(EPHSTP,FLUTOL,NUMKPS,FRACKP,FLUWARN)
C
C     Calculate the flux at each point along the ephemeris (if it is
C     inside the valid data range).
C
      NFLUX = 0
C
      DO 1000 I = 1,NUMEPH
C
C       Convert the spacecraft's ECI coordinates to GSE.
C
        CALL ECI2GSE(I,REARTH,SUNECI,EPHECI,EPHDATE,
     $    XGSE,YGSE,ZGSE)
C
C       Convert from GSE to GSM coordinate system.
C
C       Initialize GEOPACK's rotation matrices for this time.
        IYR   = EPHDATE(I,1)
        IDAY  = EPHDATE(I,2)
        IHR   = EPHDATE(I,3)
        MINIT = EPHDATE(I,4)
        ISEC  = EPHDATE(I,5)
        CALL RECALC(IYR,IDAY,IHR,MINIT,ISEC)
C
C       Get the satellite's coordinates in the GSM system.
        CALL GSMGSE(XGSM,YGSM,ZGSM,XGSE,YGSE,ZGSE,-1)
        RGSM = SQRT(XGSM**2+YGSM**2+ZGSM**2)
C
C       Store the GSE & GSM coordinates of the ephemeris.
        EPHGSE(I,1) = XGSE
        EPHGSE(I,2) = YGSE
        EPHGSE(I,3) = ZGSE
        EPHGSM(I,1) = XGSM
        EPHGSM(I,2) = YGSM
        EPHGSM(I,3) = ZGSM
C
C       RNGMIN  - minimum geocentric distance used in calculation (Re).
D       WRITE(*,*)' I,RGSM,XGSM,YGSM,ZGSM = ',I,RGSM,XGSM,YGSM,ZGSM
        IF(RGSM.GE.RNGMIN) THEN
C         Increment the number of flux values counted.
          NFLUX = NFLUX + 1
C         Store this point's index.
          IDFLUX(NFLUX) = I
C         Find the flux (ions/[cm^2-sec-sr-MeV]) at this location.
          FLUX(NFLUX) = 0.0
          DO KK = 1,NUMKPS
            CALL CRMFLX(LUNIT,XKPIN(KK),XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $        FSWIMN,FSWI95,FSWI50,FSWISD,IUSEMSH,SMOOTH1,NFLXGET,
     $        NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $        FLUX95,FLUX50,FLUXSD)
            IF(FLULVL.EQ.1) THEN
              FLUX1 = FLUXMN
            ELSE IF(FLULVL.EQ.2) THEN
              FLUX1 = FLUX95
            ELSE IF(FLULVL.EQ.3) THEN
              FLUX1 = FLUX50
            ELSE
              WRITE(*,*)
              WRITE(*,*)' Flux output type incorrect!  FLULVL = ',FLULVL
              PAUSE
              STOP 21
            END IF
            FLUX(NFLUX) = FLUX(NFLUX) + FRACKP(KK)*FLUX1
D           WRITE(*,*)' I,KK,NFLUX,FLUX1,FRACKP(KK),FLUX(NFLUX) = ',
D    $                  I,KK,NFLUX,FLUX1,FRACKP(KK),FLUX(NFLUX)
          END DO
        END IF
1000  CONTINUE
C
C     Calculate the fluence with each ephemeris point as the starting
C     point (start with the first point that lies outside of CRMFLX's
C     "data hole".  Integrate the fluence until it passes the fluence
C     threshold value.  Store the fluence and start and stop indices
C     of the points.  The stop point is of course the place immediately
C     prior to the crossing of the fluence threshold.
C
C
      DO I = 1,NFLUX-1
C       Get the index for the start point for this fluence calculation.
        ISTART(I) = IDFLUX(I)
        I1 = ISTART(I)
C       Calculate this fluence, stop index, and the fluence integration
C       duration.
        CALL GETFLUE(NUMEPH,FLUTHR,FLUTOL,EPHSTP,I1,NFLUX,FLUX,
     $    I2,TSPAN(I),FLUE(I))
        ISTOP(I) = IDFLUX(I2)
      END DO
C
C     Sort on TSPAN (ascending order) and make the corresponding
C     adjustments to ISTART & ISTOP.
C
      CALL TIMSORT(NFLUX-1,TSPAN,FLUE,ISTART,ISTOP)
C
C     Since the sort was made in ascending order, use the last values
C     in the sorted table for the case where the time span is largest.
C
      NN = NFLUX-1
      I1 = ISTART(NN)
      I2 = ISTOP(NN)
      CXOFLUE = FLUE(NN)
      CXOTIME = TSPAN(NN)
C
C     Load the turn-on and protection event times.
      DO I = 1,5
        ACISIN(I) = EPHDATE(I1,I)
        ACISOUT(I) = EPHDATE(I2,I)
      END DO
C
C     Load the turn-on and protection event position vectors.
      DO I = 1,3
        ECITON(I)  = EPHECI(I1,I)
        ECISAFE(I) = EPHECI(I2,I)
        GSETON(I)  = EPHGSE(I1,I)
        GSESAFE(I) = EPHGSE(I2,I)
        GSMTON(I)  = EPHGSM(I1,I)
        GSMSAFE(I) = EPHGSM(I2,I)
      END DO
C
      IF(I1.GT.IDFLUX(1)) THEN
C       The turn-on event occurs after the first position beyond the
C       minimum range.
        TONEVNT = .TRUE.
      ELSE
C       The turn-on event occurs at first position beyond the minimum
C       range.
        TONEVNT = .FALSE.
      END IF
C
      IF(I2.LT.IDFLUX(NFLUX-1)) THEN
C       The protection event occurs before the last position prior to the
C       minimum range.
        OFFEVNT = .TRUE.
      ELSE
C       The protection event occurs at the last position prior to the
C       minimum range.
        OFFEVNT = .FALSE.
      END IF
C
10    FORMAT(1X,2I5,4F7.2,1X,E13.3,I5,F7.2)
11    FORMAT(1X,I5,2I9,2X,F10.1,2X,E13.3)
12    FORMAT(1X,I5,2X,F9.2,2X,E13.3,2I8)
C
      RETURN
      END
C
C
      SUBROUTINE GETFLUE(NUMEPH,FLUTHR,FLUTOL,EPHSTP,I1,NFLUX,FLUX,
     $  I2,TSPAN,FLUE)
C
C     This routine calculates the fluence, stop index, and the
C     duration of the fluence integration.
C
C     *** NOTE ***  I need CSC's orbit interpolation routine so that
C     I can get the fluence within the tolerance level! Until then, the
C     protection and operation events will depend on the ephemeris'
C     time step.  For now, I will simply check on if the calculated
C     fluence exceeds FLUMAX, the upper limit.  After I get the
C     interpolation routine, I will do a binary type of search for
C     the fluence value that lies within FLUTHR +/- FLUTOL.
C
C     Inputs:
C       NUMEPH  - number of points in ephemeris.
C       FLUTHR  - fluence per orbit threshold (ions/cm^2-sr-MeV).
C       FLUTOL  - fluence calculation tolerance (% of fluence threshold).
C       EPHSTP  - time step between ephemeris points (sec).
C       I1      - index of fluence calculation's start point
C                 (referenced to the first element of the array of
C                  flux values).
C       NFLUX   - number of flux calculation points.
C       FLUX    - array of NFLUX flux values (ions/cm^2-sec-sr-MeV).
C
C     Outputs:
C       I2      - index of fluence calculation's stop point
C                 (referenced to the first element of the array of
C                  flux values).
C       TSPAN   - time spanned by fluence integration (sec).
C       FLUE    - fluence (ions/cm^2-sr-MeV).
C
      REAL*4 FLUX(NUMEPH)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED GETFLUE!'
D     WRITE(*,*)' NUMEPH,FLUTHR,FLUTOL = ',NUMEPH,FLUTHR,FLUTOL
D     WRITE(*,*)' EPHSTP,I1,NFLUX = ',EPHSTP,I1,NFLUX
D     DO I = 1,NUMEPH
D       WRITE(*,*)' I,FLUX(I) = ',I,FLUX(I)
D     END DO
D     PAUSE
C
C     Get the maximum fluence allowed for this calculation.
      FLUMAX = (FLUTOL/100. + 1.)*FLUTHR
C
      FLUE = 0.
      TSPAN = 0.
C
      DO I = I1,NFLUX-1
C       Use the average of the two flux values that bound this time
C       step to calculate the fluence.
        FLUESAV = FLUE
        FLUE = FLUE + 0.5*(FLUX(I)+FLUX(I+1))*EPHSTP
        TSPAN = TSPAN + EPHSTP
        IF(FLUE.GE.FLUMAX) THEN
C         The fluence threshold has been exceeded.
          FLUE = FLUESAV
          I2 = I-1
          TSPAN = TSPAN - EPHSTP
          GO TO 1001
        END IF
      END DO
      I2 = NFLUX
1001  CONTINUE
C
      IF(I2.LE.I1) THEN
        I2 = I1
        TSPAN = 0.0
        FLUE = 0.0
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE GETWARN(EPHSTP,FLUTOL,NUMKPS,FRACKP,FLUWARN)
C
C     This routine checks the inputs to CXORAD and issues warnings
C     if their values are outside of the desired range.
C
C     Inputs:
C       EPHSTP  - time step between ephemeris points (sec).
C       FLUTOL  - fluence calculation tolerance (% of fluence threshold).
C       NUMKPS  - number of Kp index intervals used as input distribution.
C       FRACKP  - array containing the fraction (value between 0. & 1.) of
C                 the corresponding Kp interval.
C
C     Outputs:
C       FLUWARN - Integer array containing warning flags.
C                 FLUWARN(1) = 0 if ephemeris time step is OK.
C                 FLUWARN(1) = 1 if ephemeris time step too large.
C                 FLUWARN(2) = 0 if fluence tolerance OK.
C                 FLUWARN(2) = 1 if fluence tolerance too large.
C                 FLUWARN(3) = 0 if Kp distribution fractions add to 1.
C                 FLUWARN(3) = 1 if Kp distribution fractions do not add to 1.
C
      REAL*4 FRACKP(NUMKPS)
      INTEGER*4 FLUWARN(3)
C
C     Set the maximum epehemeris time step to 20 minutes + 20 seconds.
      PARAMETER (STPMAX = 1220.)
C
C     Set the upper limit on the fluence tolerance to 50%.
      PARAMETER (TOLMAX = 50.)
C
C     Set the amount that the sum of the Kp distribution's fractions
C     may differ from 1.0.
      PARAMETER (FRACMAX = 0.05)
C
      IF(EPHSTP.GT.STPMAX) THEN
        WRITE(*,*)
        WRITE(*,*)' Warning! The time step in CXORAD is too large.'
        WRITE(*,*)' EPHSTP, STPMAX = ',EPHSTP,STPMAX
        WRITE(*,*)
        FLUWARN(1) = 1
      ELSE
        FLUWARN(1) = 0
      END IF
C
      IF(FLUTOL.GT.TOLMAX) THEN
        WRITE(*,*)
        WRITE(*,*)' Warning! The fluence calcualtion tolerance (%)',
     $            ' in CXORAD is too large.'
        WRITE(*,*)' FLUTOL, TOLMAX = ',FLUTOL,TOLMAX
        WRITE(*,*)
        FLUWARN(2) = 1
      ELSE
        FLUWARN(2) = 0
      END IF
C
      SUMFRAC = 0.
      DO I = 1,NUMKPS
        SUMFRAC = SUMFRAC + FRACKP(I)
      END DO
      ABSDIFF = ABS(1.-SUMFRAC)
C
      IF(ABSDIFF.GT.FRACMAX) THEN
        WRITE(*,*)
        WRITE(*,*)' Warning! The sum of the Kp distribution ',
     $            'fractions in CXORAD exceeds 1.0 by more than the',
     $            ' tolerance.'
        WRITE(*,*)' SUMFRAC, FRACMAX = ',SUMFRAC,FRACMAX
        WRITE(*,*)
        FLUWARN(3) = 1
      ELSE
        FLUWARN(3) = 0
      END IF
C
      RETURN
      END
C
C
      SUBROUTINE ECI2GSE(K,REARTH,SUNECI,EPHECI,EPHDATE,
     $  XGSE,YGSE,ZGSE)
C
C     This routine takes a location vector, EPHECI, in the standard equatorial system
C     (also referred to as ECI), and converts it to a location in the geocentric
C     solar ecliptic (GSE) coordinate system, given the date.
C
C     This routine is adapted from Bill Cooke's eq2gse routine.
C
C     Inputs:
C       K       - index number of current ephemeris location.
C       REARTH  - radius of the Earth (km) (double precision).
C       SUNECI  - Sun's ECI coordinates (km) (double precision 3 vector).
C                 SUNECI(K,1) = x coordinate of Kth ephemeris point.
C                 SUNECI(K,2) = y coordinate of Kth ephemeris point.
C                 SUNECI(K,3) = z coordinate of Kth ephemeris point.
C       EPHECI  - spacecraft's ECI coordinates (km)
C                 (double precision 3 vector).
C                 EPHECI(K,1) = x coordinate of Kth ephemeris point.
C                 EPHECI(K,2) = y coordinate of Kth ephemeris point.
C                 EPHECI(K,3) = z coordinate of Kth ephemeris point.
C       EPHDATE -Integer array containing dates of Sun and spacecraft 
C                ephemeris points.
C                EPHDATE(K,1) = Year (YYYY) of Kth ephemeris point.
C                EPHDATE(K,2) = Day (DDD) of Year of Kth ephemeris point.
C                EPHDATE(K,3) = Hour (HH) of Day of Kth ephemeris point.
C                EPHDATE(K,4) = Minute (MM) of Hour of Kth ephemeris point.
C                EPHDATE(K,5) = Second (SS) of Minute of Kth ephemeris point.
C
C     OUTPUTS:
C       XGSE  - spacecraft x-coordinate (GSE system, Re units)
C               (single precision).
C       YGSE  - spacecraft y-coordinate (GSE system, Re units)
C               (single precision).
C       ZGSE  - spacecraft z-coordinate (GSE system, Re units)
C               (single precision).
C
C     Declare variables
C
      INCLUDE 'MAXEPH1.PAR'
C
      REAL*8 REARTH
      REAL*8 SUNECI(MAXEPH1,3),EPHECI(MAXEPH1,3)
      INTEGER*4 EPHDATE(MAXEPH1,5)
      REAL*8 xgse1(3),dom,tjd,sunlon,obl
      REAL*8 jcen,dg2rad,pi
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED ECI2GSE!'
D     WRITE(*,*)' K,REARTH = ',K,REARTH
D     WRITE(*,*)' EPHDATE(1,1-5)  = ',(EPHDATE(1,J),J=1,5)
D     WRITE(*,*)' EPHDATE(92,1-5) = ',(EPHDATE(92,J),J=1,5)
D     WRITE(*,*)' SUNECI(1,1-3)   = ',(SUNECI(1,J),J=1,3)
D     WRITE(*,*)' SUNECI(92,1-3)  = ',(SUNECI(92,J),J=1,3)
D     WRITE(*,*)' EPHECI(1,1-3)   = ',(EPHECI(1,J),J=1,3)
D     WRITE(*,*)' EPHECI(92,1-3)  = ',(EPHECI(92,J),J=1,3)
D     WRITE(*,*)
D     WRITE(*,*)' EPHDATE(K,1-5)  = ',(EPHDATE(K,J),J=1,5)
D     WRITE(*,*)' SUNECI(K,1-3)   = ',(SUNECI(K,J),J=1,3)
D     WRITE(*,*)' EPHECI(K,1-3)   = ',(EPHECI(K,J),J=1,3)
D     PAUSE
C
C     Define pi, degrees to radians conversion.
C
      pi=3.141592654d0
      dg2rad=pi/1.8d2
C
C     Initialize gse coordinate array.
C
      do 10 i=1,3
10    xgse1(i)=0.0d0
C
C     Compute Julian date (Note: This assumes the time given is TDT
C     (terrestrial dynamical time, or atomic clock time); if UT is used
C     bear in mind that there can be over a minute difference between
C     the two...).
C
      IYR     = EPHDATE(K,1)
      IDAYY   = EPHDATE(K,2)
      IHR     = EPHDATE(K,3)
      IMINUTE = EPHDATE(K,4)
      ISECON  = EPHDATE(K,5)
C
C     Get the floating number representation of the day of the year.
      DOY = FLOAT(IDAYY)+FLOAT(IHR)/24.+FLOAT(IMINUTE)/1440.
     $     +FLOAT(ISECON)/86400.
C
C     Get the floating number representation of the day of the month.
D     WRITE(*,*)
D     WRITE(*,*)' B4 DATE2 IN ECI2GSE! IYR,DOY = ',IYR,DOY
      CALL DATE2(IYR,DOY,IMON,IDAYM)
      dom = FLOAT(IDAYM)+FLOAT(IHR)/24.+FLOAT(IMINUTE)/1440.
     $     +FLOAT(ISECON)/86400.
D     WRITE(*,*)' AFTER DATE2 IN ECI2GSE! IMON,IDAYM,dom = ',
D    $                                    IMON,IDAYM,dom
C
      call jdate(IYR,IMON,dom,tjd)
C
C     Now compute the obliquity of the ecliptic.
C
      jcen=(tjd-2451545.0d0)/3.6525d4
      obl=23.439291111112 - (46.8150*jcen-5.9d-4*jcen*jcen+
     &    1.813d-3*jcen**3)/3.6d3
      obl=obl*dg2rad
C
C     Get the solar longitude (rad).
C
      sunlon = ATAN2(SUNECI(K,2),SUNECI(K,1))
D     WRITE(*,*)' obl,sunlon = ',obl,sunlon
C
C     Perform transformation to GSE system.
C
      xgse1(1)=EPHECI(K,1)*cos(sunlon)+EPHECI(K,2)
     $        *sin(sunlon)*cos(obl)+EPHECI(K,3)*sin(sunlon)*sin(obl)
      xgse1(2)=-EPHECI(K,1)*sin(sunlon)+EPHECI(K,2)
     $        *cos(sunlon)*cos(obl)+EPHECI(K,3)*cos(sunlon)*sin(obl)
      xgse1(3)=-EPHECI(K,2)*sin(obl)+EPHECI(K,3)*cos(obl)
C
C     Convert from km to Re units (single precision).
      XGSE = xgse1(1)/REARTH
      YGSE = xgse1(2)/REARTH
      ZGSE = xgse1(3)/REARTH
D     WRITE(*,*)' XGSE,YGSE,ZGSE = ',XGSE,YGSE,ZGSE
C
C
      RETURN
      END
C
C
      SUBROUTINE DATE2(IYR,DOY,IMON,IDAY)
C
C     This routine converts the time, a single real number, to the
C     month of the year (IMON) and the day of the month (IDAY).
C
C     INPUTS:
C       IYR  - year in (YYYY) format.
C       DOY  - day of year in floating point format (e.g., 313.472).
C
C     OUTPUTS:
C       IMON - month of year (MM).
C       IDAY - day of month (DD).
C
      INTEGER IDY(13),IDY2(13)
C
C     The array IDY contains the day number for the start of each month
C     (non-leap years) plus the day number for the start of the next year.
      DATA IDY /1,32,60,91,121,152,182,213,244,274,
     $          305,335,366 /
C
C     Account for leap years.
      ITEST = MOD(IYR,4)
      IF(ITEST.EQ.0) THEN
        ILP = 1
      ELSE
        ILP = 0
      END IF
C
      DO I = 1,13
        IF(I.LE.2) THEN
          IDY2(I) = IDY(I)
        ELSE
          IDY2(I) = IDY(I) + ILP
        END IF
      END DO
C
      IDOY = INT(DOY)
      DO I = 1,12
        IF((IDOY.GE.IDY2(I)).AND.(IDOY.LT.IDY2(I+1))) THEN
          IMON = I
          IDAY = IDOY - IDY2(I) + 1
          RETURN
        END IF
      END DO
C
      WRITE(*,*)
      WRITE(*,*)' Error in DATE2! IYR, DOY = ',IYR,DOY
      PAUSE
      STOP21
C
      END
C
C
      subroutine jdate(yr,mn,d,jd)
C
C     The subroutine calculates the Julian day, given the calendar
C     date for any day in the Gregorian calendar
C
C     Declare variables
C
      INTEGER yr,mn,yy,mm,a,b
      REAL*8 d,jd
C
C     Compute jd.
C
      if (mn.le.2) then
        yy=yr-1
        mm=mn+12
      else
        yy=yr
        mm=mn
      end if
      a=int(yy/100.0)
      b=2-a+int(a/4.0)
      jd=int(365.25*(yy+4716))+int(30.6001*(mm+1))+d+b-1.5245d3
C
C     Finished.
C
      return
      end
C
C
      subroutine calday(jd,iyr,mon,dd,hh,mm,s)
C
C     This subroutine computes the calendar date from
C     the julian date
C
C     Declare variables
C
      INTEGER iyr,mon,dd,hh,mm,z,a,alpha,b,c,d,e
      REAL s
      REAL*8 jd,jd0,f
C
      jd0=jd+0.5
      z=dint(jd0)
      f=jd0-z
      if (z.lt.2299161) then
        a=z
      else
        alpha=int((z-1867216.25)/36524.25)
        a=z+1+alpha-int(alpha/4)
      end if
      b=a+1524
      c=int((b-122.1)/365.25)
      d=int(365.25*c)
      e=int((b-d)/30.6001)
      dd=int(b-d-int(30.6001*e)+f)
      hh=int((b-d-int(30.6001*e)+f-dd)*24)
      mm=int(((b-d-int(30.6001*e)+f-dd)*24-hh)*60)
      s=(((b-d-int(30.6001*e)+f-dd)*24-hh)*60-mm)*60.0
      if (e.lt.14) then
        mon=e-1
      else
        mon=e-13
      end if
      if (mon.gt.2) then
        iyr=c-4716
      else
        iyr=c-4715
      end if
C
C     Finished.
C
      return
      end
C
C
      SUBROUTINE TIMSORT(N,RA,RB,INDA,INDB)
C
C     *** 	Based on SORT2 taken from "Numerical Recipes" ***
C     Sorts an array RA of length N into ascending numerical order
C     using the Heapsort algorithm, while making the corresponding
C     rearrangement of the arrays RB, INDA & INDB.
C
      REAL RA(N),RB(N)
      INTEGER INDA(N),INDB(N)
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED TIMSORT!!'
D     WRITE(*,*)' 1,RA(1),RB(1),INDA(1),INDB(1) = ',
D    $            1,RA(1),RB(1),INDA(1),INDB(1)
D     WRITE(*,*)
D     DO I = 1,N
D       WRITE(*,*)' I,RA(I),RB(I),INDA(I),INDB(I) = ',
D    $              I,RA(I),RB(I),INDA(I),INDB(I)
D     END DO
D     WRITE(*,*)
D     PAUSE 'PAUSED!!'
      L=N/2+1
      IR=N
10    CONTINUE
        IF(L.GT.1) THEN
          L=L-1
D         WRITE(*,*)' #1: L = ',L
D         WRITE(*,*)' #1: L,RA(L),RB(L),INDA(L),INDB(L) = ',
D    $                    L,RA(L),RB(L),INDA(L),INDB(L)
          RRA=RA(L)
          RRB=RB(L)
          IINDA=INDA(L)
          IINDB=INDB(L)
        ELSE
D         WRITE(*,*)' #2: IR = ',IR
D         WRITE(*,*)' #2: IR,RA(IR),RB(IR),INDA(IR),INDB(IR) = ',
D    $                    IR,RA(IR),RB(IR),INDA(IR),INDB(IR)
          RRA=RA(IR)
          RRB=RB(IR)
          IINDA=INDA(IR)
          IINDB=INDB(IR)
          RA(IR)=RA(1)
          RB(IR)=RB(1)
          INDA(IR)=INDA(1)
          INDB(IR)=INDB(1)
          IR=IR-1
          IF(IR.EQ.1)THEN
            RA(1)=RRA
            RB(1)=RRB
            INDA(1)=IINDA
            INDB(1)=IINDB
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
D           WRITE(*,*)' #4: J,RA(J),RB(J),INDA(J),INDB(J) = ',
D    $                      J,RA(J),RB(J),INDA(J),INDB(J)
            RA(I)=RA(J)
            RB(I)=RB(J)
            INDA(I)=INDA(J)
            INDB(I)=INDB(J)
            I=J
            J=J+J
          ELSE
            J=IR+1
          ENDIF
          GOTO 20
        ENDIF
D       WRITE(*,*)' #5: I = ',I
D       WRITE(*,*)' #5: I,RA(I),RB(I),INDA(I),INDB(I) = ',
D    $                  I,RA(I),RB(I),INDA(I),INDB(I)
        RA(I)=RRA
        RB(I)=RRB
        INDA(I)=IINDA
        INDB(I)=IINDB
      GOTO 10
C
      END
C
C
