      PROGRAM CXODRV
C
C     Stand-alone driver for CXORAD.
C
C     This routine accepts the user's selection for the start and end
C     dates and time of day and provides CXORAD output for each orbit
C     covered by this period.
C
      INCLUDE 'MAXEPH.PAR'
      INCLUDE 'MAXEPH1.PAR'
      INCLUDE 'MAXKPS.PAR'
C
      CHARACTER*32 EPHFIL,FILOUT
      INTEGER DATEPTS(MAXEPH,5)
      REAL*8 SUNPTS(MAXEPH,3),EPHPTS(MAXEPH,3)
      REAL*8 REARTH,RECI,RLAST1,RLAST2,RLAST3
      REAL*4 XKPIN(MAXKPS),FRACKP(MAXKPS)
      REAL*8 SUNECI(MAXEPH1,3),EPHECI(MAXEPH1,3),ECITON(3),ECISAFE(3)
      REAL*4 GSETON(3),GSESAFE(3),GSMTON(3),GSMSAFE(3)
C
      INTEGER*4 EPHDATE(MAXEPH1,5),ISPECI,ACISIN(5),ACISOUT(5),
     $  FLUWARN(3),FLULVL,LUNIT(3)
      INTEGER*4 SMOOTH1,FPCHI,FPCLO,SMOOTH2
      LOGICAL*4 OFFEVNT, TONEVNT
C
C     Get the user selected inputs.
C
D     WRITE(*,*)' B4 GETINP!'
D     PAUSE
      CALL GETINP(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,IYR2,IMON2,
     $  IDAYM2,IHR2,IMINIT2,ISEC2,EPHFIL,FILOUT,ISPECI,FLUTHR,FLUTOL,
     $  FLULVL,REARTH,RNGMIN,LUNIT,IUSESW,FSWIMN,FSWI95,FSWI50,FSWISD,
     $  IUSEMSH,NUMKPS,XKPIN,FRACKP,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,
     $  LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2)
D     WRITE(*,*)' AFTER GETINP! FLULVL = ',FLULVL
D     WRITE(*,*)' IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1 = ',
D    $            IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1
D     WRITE(*,*)' IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2 = ',
D    $            IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2
D     WRITE(*,*)' EPHFIL,FILOUT = ',EPHFIL,FILOUT
D     WRITE(*,*)' ISPECI,FLUTHR,FLUTOL = ',ISPECI,FLUTHR,FLUTOL
D     WRITE(*,*)' FLULVL,REARTH,RNGMIN,LUNIT = ',
D    $            FLULVL,REARTH,RNGMIN,LUNIT
D     WRITE(*,*)' IUSESW,IUSEMSH,FSWIMN,FSWI95 = ',
D    $            IUSESW,IUSEMSH,FSWIMN,FSWI95
D     WRITE(*,*)' FSWI50,FSWISD = ',
D    $            FSWI50,FSWISD
D     WRITE(*,*)' NUMKPS = ',NUMKPS
D     WRITE(*,*)' XKPIN = ',(XKPIN(I),I=1,NUMKPS)
D     WRITE(*,*)' FRACKP = ',(FRACKP(I),I=1,NUMKPS)
D     WRITE(*,*)' SMOOTH1,NFLXGET,NDROPHI,NDROPLO = ',
D    $            SMOOTH1,NFLXGET,NDROPHI,NDROPLO
D     WRITE(*,*)' LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2 = ',
D    $            LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2
D     PAUSE
C
C     Load the spacecraft ephemeris (ECI) into arrays from the data
C     file.  (The Sun's ECI position is calculated for each point.)
C
      CALL GETEPH(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,IYR2,IMON2,
     $  IDAYM2,IHR2,IMINIT2,ISEC2,EPHFIL,NUMPTS,DATEPTS,SUNPTS,
     $  EPHPTS,EPHSTP)
D     WRITE(*,*)' AFTER GETEPH!'
D     WRITE(*,*)' NUMPTS,EPHSTP = ',NUMPTS,EPHSTP
D     WRITE(*,*)'SUNPTS(92,1-3) = ',(SUNPTS(92,JJ),JJ=1,3)
D     WRITE(*,*)'EPHPTS(92,1-3) = ',(EPHPTS(92,JJ),JJ=1,3)
D     WRITE(*,*)'SUNPTS(1000000,1-3) = ',(SUNPTS(1000000,JJ),JJ=1,3)
D     WRITE(*,*)'EPHPTS(1000000,1-3) = ',(EPHPTS(1000000,JJ),JJ=1,3)
D     PAUSE
C
C     Open the output file.
C
      CLOSE(50)
D     WRITE(*,*)' B4 OPEN: FILOUT = ',FILOUT
D     PAUSE
      OPEN(50,FILE=FILOUT,FORM='FORMATTED',ACCESS='SEQUENTIAL',
     $  STATUS='UNKNOWN')
D     WRITE(*,*)' AFTER OPEN: FILOUT = ',FILOUT
D     PAUSE
C
C     Write the header to the output file.
C
      WRITE(50,100)
C
C     Set the orbit counters.
      J1 = 0
      IORB = 0
C
C     Set the range check values.
      RLAST1 = +1.E+20
      RLAST2 = 0.0
      RLAST3 = 0.0
C
C     Find the index for the perigee of each orbit contained in the
C     ephemeris' data file that is spanned by the user's selection.
C
D     WRITE(*,*)' B4 1000 LOOP: NUMPTS = ',NUMPTS
D     PAUSE
      ICNT = 0
      DO 1000 I = 1,NUMPTS
        ICNT = ICNT + 1
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
D         WRITE(*,*)' I = ',I
        END IF
C       Get the geocentric range to this point.
        RECI = SQRT(EPHPTS(I,1)**2 + EPHPTS(I,2)**2 + EPHPTS(I,3)**2)
D       WRITE(*,*)' I,J1,RECI,RLAST1,RLAST2,RLAST3 = ',
D    $              I,J1,RECI,RLAST1,RLAST2,RLAST3
D       PAUSE
        IF((RECI.GT.RLAST1).AND.(RLAST1.LT.RLAST2)
     $    .AND.(RLAST2.LT.RLAST3).AND.(J1.GT.3)) THEN
D         WRITE(*,*)' I,J1,RECI,RLAST1,RLAST2,RLAST3 = ',
D    $                I,J1,RECI,RLAST1,RLAST2,RLAST3
D         PAUSE
C         The last value was the perigee location.
          NUMEPH = J1
C
C         Determine the protection and turn-on event times (and
C         locations) for each orbit.
C
D         WRITE(*,*)' B4 CXORAD! FLULVL = ',FLULVL
D         PAUSE
C
          CALL CXORAD(EPHSTP,NUMEPH,SUNECI,EPHECI,EPHDATE,ISPECI,FLUTHR,
     $      FLUTOL,FLULVL,REARTH,RNGMIN,LUNIT,IUSESW,FSWIMN,FSWI95,
     $      FSWI50,FSWISD,IUSEMSH,NUMKPS,XKPIN,FRACKP,SMOOTH1,NFLXGET,
     $      NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2,OFFEVNT,
     $      TONEVNT,ACISIN,ACISOUT,ECITON,ECISAFE,GSETON,GSESAFE,GSMTON,
     $      GSMSAFE,FLUWARN,CXOFLUE,CXOTIME)
C
C         Calculate the geocentric range (Re) to the turn-on event.
          GEORNG1 = SQRT(GSMTON(1)**2 + GSMTON(2)**2 + GSMTON(3)**2)
C
C         Calculate the geocentric range (Re) to the protection event.
          GEORNG2 = SQRT(GSMSAFE(1)**2 + GSMSAFE(2)**2 +GSMSAFE(3)**2)
C
          WRITE(50,200) IORB,OFFEVNT,TONEVNT,(ACISIN(JJ),JJ=1,5),
     $      (ACISOUT(JJ),JJ=1,5),(ECITON(JJ),JJ=1,3),
     $      (ECISAFE(JJ),JJ=1,3),(GSETON(JJ),JJ=1,3),
     $      (GSESAFE(JJ),JJ=1,3),(GSMTON(JJ),JJ=1,3),
     $      (GSMSAFE(JJ),JJ=1,3),GEORNG1,GEORNG2,CXOFLUE,CXOTIME,
     $      CXOTIME/3600.
C
C         Initialize the ephemeris counters for the next orbit.
          IORB = IORB + 1
          J1 = 1
        ELSE
C         Increment ephemeris counter for this orbit.
          J1 = J1 + 1
        END IF
C
        RLAST3 = RLAST2
        RLAST2 = RLAST1
        RLAST1 = RECI
C
C       Load this orbit's ephemeris prior to the next call to CXORAD.
C
        DO JJ = 1,3
          SUNECI(J1,JJ) = SUNPTS(I,JJ)
          EPHECI(J1,JJ) = EPHPTS(I,JJ)
        END DO
        DO JJ = 1,5
          EPHDATE(J1,JJ) = DATEPTS(I,JJ)
        END DO
1000  CONTINUE
C
100   FORMAT(1X,'ORBIT OFFEVNT TONEVNT ACISIN(1) ACISIN(2) ACISIN(3) ',
     $  'ACISIN(4) ACISIN(5) ACISOUT(1) ACISOUT(2) ACISOUT(3) ',
     $  'ACISOUT(4) ACISOUT(5) ECITON(1) ECITON(2) ECITON(3) ',
     $  'ECISAFE(1) ECISAFE(2) ECISAFE(3) ',
     $  'GSETON(1) GSETON(2) GSETON(3) GSESAFE(1) GSESAFE(2) ',
     $  'GSESAFE(3) GSMTON(1) GSMTON(2) GSMTON(3) GSMSAFE(1) ',
     $  'GSMSAFE(2) GSMSAFE(3) GEORNG1 GEORNG2 CXOFLUE CXOTIME(sec) ',
     $  'CXOTIME(hr)')
C
200   FORMAT(1X,I7,1X,L3,1X,L3,10I6,6(1X,E12.3),12(1X,E12.3),
     $       2F7.2,3(1X,E12.3))
C
      STOP
      END
C
C
      SUBROUTINE GETINP(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,IYR2,IMON2,
     $  IDAYM2,IHR2,IMINIT2,ISEC2,EPHFIL,FILOUT,ISPECI,FLUTHR,FLUTOL,
     $  FLULVL,REARTH,RNGMIN,LUNIT,IUSESW,FSWIMN,FSWI95,FSWI50,FSWISD,
     $  IUSEMSH,NUMKPS,XKPIN,FRACKP,SMOOTH1,NFLXGET,NDROPHI,NDROPLO,
     $  LOGFLG,RNGTOL,FPCHI,FPCLO,SMOOTH2)
C
C     Read user's inputs from file.
C
      INCLUDE 'MAXKPS.PAR'
C
      CHARACTER*32 EPHFIL,FILOUT
      CHARACTER*1 SKIP
      REAL*8 REARTH
      REAL*4 XKPIN(MAXKPS),FRACKP(MAXKPS)
      INTEGER*4 FLULVL,LUNIT(3),SMOOTH1,FPCHI,FPCLO,SMOOTH2
C
C     Open the user input deck.
C
      OPEN(30,FILE='CXODRV.INP',FORM='FORMATTED',ACCESS='SEQUENTIAL',
     $  STATUS='OLD')
C
C     Skip header records.
      DO I = 1,7
        READ(30,*) SKIP
      END DO
C
C     Read BLOCK #1: Run start/stop times.
C
C     Read IYR1 - year (YYYY) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) IYR1
D     WRITE(*,*)' IYR1 = ',IYR1
D     PAUSE
C
C     Read IMON1 - month (MM) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IMON1
D     WRITE(*,*)' IMON1 = ',IMON1
D     PAUSE
C
C     Read IDAYM1 - day of month (DD) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IDAYM1
D     WRITE(*,*)' IDAYM1 = ',IDAYM1
D     PAUSE
C
C     Read IHR1 - hour of day (HH) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IHR1
D     WRITE(*,*)' IHR1 = ',IHR1
D     PAUSE
C
C     Read IMINIT1 - minute of hour (MM) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IMINIT1
D     WRITE(*,*)' IMINIT1 = ',IMINIT1
D     PAUSE
C
C     Read ISEC1 - second of minute (SS) of start time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) ISEC1
D     WRITE(*,*)' ISEC1 = ',ISEC1
D     PAUSE
C
C     Read IYR2 - year (YYYY) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IYR2
D     WRITE(*,*)' IYR2 = ',IYR2
D     PAUSE
C
C     Read IMON2 - month (MM) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IMON2
D     WRITE(*,*)' IMON2 = ',IMON2
D     PAUSE
C
C     Read IDAYM2 - day of month (DD) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IDAYM2
D     WRITE(*,*)' IDAYM2 = ',IDAYM2
D     PAUSE
C
C     Read IHR2 - hour of day (HH) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IHR2
D     WRITE(*,*)' IHR2 = ',IHR2
D     PAUSE
C
C     Read IMINIT2 - minute of hour (MM) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) IMINIT2
D     WRITE(*,*)' IMINIT2 = ',IMINIT2
D     PAUSE
C
C     Read ISEC2 - second of minute (SS) of stop time (INTEGER).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) ISEC2
D     WRITE(*,*)' ISEC2 = ',ISEC2
D     PAUSE
C
C     Read BLOCK #2: Run start/stop times.
C
C     Skip header records.
      DO I = 1,10
        READ(30,*) SKIP
      END DO
C     Read ISPECI - ion species selection flag (INTEGER).
      READ(30,*) ISPECI
D     WRITE(*,*)' ISPECI = ',ISPECI
D     PAUSE
C
C     Read FLUTHR - fluence per orbit threshold
C                   (ions/cm^2-sr-MeV) (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FLUTHR
D     WRITE(*,*)' FLUTHR = ',FLUTHR
D     PAUSE
C
C     Read FLUTOL - fluence calculation tolerance 
C                   (% of fluence threshold) (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FLUTOL
D     WRITE(*,*)' FLUTOL = ',FLUTOL
D     PAUSE
C
C     Read FLULVL - Percentile level (e.g., 50%, 95%) of particle flux
C                   environment used in fluence calculation.
C                   FLULVL = 1  -> mean flux used
C                   FLULVL = 2  -> 95% flux used
C                   FLULVL = 3  -> 50% flux used (REAL).
      DO I = 1,7
        READ(30,*) SKIP
      END DO
      READ(30,*) FLULVL
D     WRITE(*,*)' FLULVL = ',FLULVL
D     PAUSE
C
C     Read REARTH - radius of the Earth (km). (REAL*8).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) REARTH
D     WRITE(*,*)' REARTH = ',REARTH
D     PAUSE
C
C     Read RNGMIN - minimum geocentric range that ion flux
C                   calculations are performed (Re). (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) RNGMIN
D     WRITE(*,*)' RNGMIN = ',RNGMIN
D     PAUSE
C
C     Read LUNIT - unit number used in opening CRMFLX's database (INTEGER).
C                LUNIT(1) = solar wind database unit number
C                LUNIT(2) = magnetosheath database unit number
C                LUNIT(3) = magnetosphere database unit number
      DO I = 1,6
        READ(30,*) SKIP
      END DO
      READ(30,*) (LUNIT(KK),KK=1,3)
D     WRITE(*,*)' LUNIT = ',LUNIT
D     PAUSE
C
C     Read IUSESW - flag for control of solar wind flux calculation:
C               IUSESW = 0 if (uniform flux) analytic solar wind model used.
C               IUSESW = 1 if user supplied uniform flux value used.
C               IUSESW = 2 if solar wind database used.
C               IUSESW = 3 if sum of solar wind database value and user
C                          supplied uniform flux value used.
C               IUSESW = 4 if sum of (uniform flux) analytic solar wind model
C                          and user supplied uniform flux value used.
C          (INTEGER).
      DO I = 1,10
        READ(30,*) SKIP
      END DO
      READ(30,*) IUSESW
D     WRITE(*,*)' IUSESW = ',IUSESW
D     PAUSE
C
C     Read FSWIMN - user supplied mean uniform solar wind flux for the
C                   selected species (#/[cm^2-sec-sr-MeV]). (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FSWIMN
D     WRITE(*,*)' FSWIMN = ',FSWIMN
D     PAUSE
C
C     Read FSWI95 - user supplied 95% uniform solar wind flux for the
C                   selected species (#/[cm^2-sec-sr-MeV]). (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FSWI95
D     WRITE(*,*)' FSWI95 = ',FSWI95
D     PAUSE
C
C     Read FSWI50 - user supplied 50% uniform solar wind flux for the
C                   selected species (#/[cm^2-sec-sr-MeV]). (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FSWI50
D     WRITE(*,*)' FSWI50 = ',FSWI50
D     PAUSE
C
C     Read FSWISD - user supplied std dev of uniform solar wind flux
C                   for the selected species (#/[cm^2-sec-sr-MeV]).
C                   (REAL).
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) FSWISD
D     WRITE(*,*)' FSWISD = ',FSWISD
D     PAUSE
C
C       IUSEMSH - flag for control of magnetosheath flux calculation:
C                 IUSEMSH = 0 if (uniform flux) analytic magnetosheath model used.
C                 IUSEMSH = 1 if user supplied uniform solar wind flux value used.
C                 IUSEMSH = 2 if magnetosheath database used.
C                 IUSEMSH = 3 if sum of magnetosheath database value and user
C                             supplied uniform solar wind flux value used.
C                 IUSEMSH = 4 if sum of (uniform flux) analytic magnetosheath model
C                             and user supplied uniform solar wind flux value used.
C          (INTEGER).
      DO I = 1,10
        READ(30,*) SKIP
      END DO
      READ(30,*) IUSEMSH
D     WRITE(*,*)' IUSEMSH = ',IUSEMSH
D     PAUSE
C
C     Read BLOCK #3: Magnetic activity (Kp) distribution.
C
C     Skip header records.
      DO I = 1,8
        READ(30,*) SKIP
      END DO
C     Read NUMKPS - number of Kp index intervals used as input 
C                 distribution. (INTEGER)
      READ(30,*) NUMKPS
D     WRITE(*,*)' NUMKPS = ',NUMKPS
D     PAUSE
C
      DO I = 1,6
        READ(30,*) SKIP
      END DO
C     Read XKPIN - array of Kp interval midpoint values. Data for XKPIN
C                  must be entered on one line with spaces or commas
C                  between values.  For example, if NUMKPS = 4, XKPIN
C                  can be entered on one line as: 1.0 2.3 5.2 7.1).
      READ(30,*) (XKPIN(I),I=1,NUMKPS)
D     WRITE(*,*)' XKPIN = ',(XKPIN(I),I=1,NUMKPS)
D     PAUSE
C
      DO I = 1,8
        READ(30,*) SKIP
      END DO
C     Read FRACKP -  array containing the fraction (value between 0. & 1.)
C                    of the corresponding Kp interval. Data for FRACKP
C                    must be entered on one line with spaces or commas
C                    between values.  For example, if NUMKPS = 4, FRACKP
C                    can be entered on one line as: 0.1 0.4 0.3 0.2).
C          CAUTION!  The sum of FRACKP's elements must total to 1.
      READ(30,*) (FRACKP(I),I=1,NUMKPS)
D     WRITE(*,*)' FRACKP = ',(FRACKP(I),I=1,NUMKPS)
D     PAUSE
C
C     Read BLOCK #4: Smoothing Algorithm Control.
C
C     Skip header records.
      DO I = 1,17
        READ(30,*) SKIP
      END DO
C     Read SMOOTH1 - flag for control of database smoothing filter:
C                   (INTEGER)
C                   SMOOTH1 = 0 if no data smoothing is used.
C                   SMOOTH1 = 1 if spike rejection and near neighbor flux.
C                   SMOOTH1 = 2 if spike rejection with range weighted scaling of flux.
C                   SMOOTH1 = 3 if spike rejection with average flux.
C                   SMOOTH1 = 4 if spatial average of flux in volume specified by RNGTOL.
C                   SMOOTH1 = 5 if spatial average of flux in volume specified by
C                               RNGTOL, with the specified number of high and low
C                               flux values inside the volume dropped first.
C                   SMOOTH1 = 6 if spatial averaging of flux in volume specified by
C                               RNGTOL, with percentile threshold limits on flux values.
      READ(30,*) SMOOTH1
D     WRITE(*,*)' SMOOTH1 = ',SMOOTH1
D     PAUSE
C
C     Read NFLXGET - number of flux values to get for smoothing filter.
C                    (used if SMOOTH1 = 1,2, or 3)
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) NFLXGET
D     WRITE(*,*)' NFLXGET = ',NFLXGET
D     PAUSE
C
C     Read NDROPHI - number of high flux values to drop for smoothing
C                    filter. (used if SMOOTH1 = 1,2,3, or 5)
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) NDROPHI
D     WRITE(*,*)' NDROPHI = ',NDROPHI
D     PAUSE
C
C     Read NDROPLO - number of low flux values to drop for smoothing
C                    filter. (used if SMOOTH1 = 1,2,3, or 5)
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) SKIP
      READ(30,*) NDROPLO
D     WRITE(*,*)' NDROPLO = ',NDROPLO
D     PAUSE
C
C     Read LOGFLG - flag controlling how flux average is performed.
C                     LOGFLG = 1 if log10 of flux values used.
C                     LOGFLG = 2 if linear flux values used.
C                    (used if SMOOTH1 = 2,3,4,5, or 6)
      DO I = 1,6
        READ(30,*) SKIP
      END DO
      READ(30,*) LOGFLG
D     WRITE(*,*)' LOGFLG = ',LOGFLG
D     PAUSE
C
C     Read RNGTOL - range tolerance from near-neigbor used in spatial
C                   averaging of database (Re).
C                   (used if SMOOTH1 = 4,5 or 6)
      DO I = 1,5
        READ(30,*) SKIP
      END DO
      READ(30,*) RNGTOL
D     WRITE(*,*)' RNGTOL = ',RNGTOL
D     PAUSE
C
C     Read FPCHI - upper percentile limit for spatial averaging of flux.
C                   (used if SMOOTH1 = 6)
      DO I = 1,4
        READ(30,*) SKIP
      END DO
      READ(30,*) FPCHI
D     WRITE(*,*)' FPCHI = ',FPCHI
D     PAUSE
C
C     Read FPCLO - lower percentile limit for spatial averaging of flux.
C                   (used if SMOOTH1 = 6)
      DO I = 1,4
        READ(30,*) SKIP
      END DO
      READ(30,*) FPCLO
D     WRITE(*,*)' FPCLO = ',FPCLO
D     PAUSE
C
C     Read SMOOTH2 - lower percentile limit for spatial averaging of flux.
C                   (used if SMOOTH1 = 6)
      DO I = 1,5
        READ(30,*) SKIP
      END DO
      READ(30,*) SMOOTH2
D     WRITE(*,*)' SMOOTH2 = ',SMOOTH2
D     PAUSE
C
C     Read BLOCK #5: File names.
C
C     Skip header records.
      DO I = 1,6
        READ(30,*) SKIP
      END DO
C     Read EPHFIL - ephemeris data file name (up to 32 characters).
      READ(30,1)  EPHFIL
D     WRITE(*,*)' EPHFIL = ',EPHFIL
D     PAUSE
C
      READ(30,*) SKIP
      READ(30,*) SKIP
C     Read FILOUT - output data file name (up to 32 characters).
      READ(30,1)  FILOUT
D     WRITE(*,*)' FILOUT = ',FILOUT
D     PAUSE
C
      CLOSE(30)
C
1     FORMAT(A)
C
      RETURN
      END
C
C
      SUBROUTINE GETEPH(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,IYR2,
     $  IMON2,IDAYM2,IHR2,IMINIT2,ISEC2,EPHFIL,NUMPTS,DATEPTS,SUNPTS,
     $  EPHPTS,EPHSTP)
C
C     This routine reads CSC's XXX.erp files containing the S/C
C     ephemeris (ECI).
C
C     This routine takes the user's selection of the start and stop
C     dates and times and reads those positions from the ephemeris
C     file which lie between these times.  There is no available data
C     file of the corresponding Solar ECI positions, so they are
C     calculated.
C
C     INPUTS:
C       IYR1    - year (YYYY) of start time.
C       IMON1   - month (MM) of start time.
C       IDAYM1  - day of month (DD) of start time.
C       IHR1    - hour of day (HH) of start time.
C       IMINIT1 - minute of hour (MM) of start time.
C       ISEC1   - second of minute (SS) of start time.
C       IYR2    - year (YYYY) of stop time.
C       IMON2   - month (MM) of stop time.
C       IDAYM2  - day of month (DD) of stop time.
C       IHR2    - hour of day (HH) of stop time.
C       IMINIT2 - minute of hour (MM) of stop time.
C       ISEC2   - second of minute (SS) of stop time.
C       EPHFIL  - ephemeris data file name (up to 32 characters).
C
C     OUTPUTS:
C       NUMPTS  - number of ephemeris points that lie between the
C                 start and stop times.
C       DATEPTS - integer array containing ephemeris location dates
C                 that are between the stop and start times.
C                 DATEPTS(K,1) = Year (YYYY) of Kth ephemeris point.
C                 DATEPTS(K,2) = Day (DDD) of Year of Kth ephemeris point.
C                 DATEPTS(K,3) = Hour (HH) of Day of Kth ephemeris point.
C                 DATEPTS(K,4) = Minute (MM) of Hour of Kth ephemeris point.
C                 DATEPTS(K,5) = Second (SS) of Minute of Kth ephemeris point.
C       SUNPTS  - array containing Sun ephemeris points in ECI coordinate
C                 system (km) corresponding to times between start and
C                 stop (double precision).
C                 SUNPTS(K,1) = x coordinate of Kth ephemeris point.
C                 SUNPTS(K,2) = y coordinate of Kth ephemeris point.
C                 SUNPTS(K,3) = z coordinate of Kth ephemeris point.
C       EPHPTS  - array containing spacecraft ephemeris points in ECI
C                 coordinate system (km) corresponding to times between
C                 start & stop (double precision).
C                 EPHPTS(K,1) = x coordinate of Kth ephemeris point.
C                 EPHPTS(K,2) = y coordinate of Kth ephemeris point.
C                 EPHPTS(K,3) = z coordinate of Kth ephemeris point.
C       EPHSTP  - time step between ephemeris points (sec).
C
C
      INCLUDE 'MAXEPH.PAR'
C
      CHARACTER*32 EPHFIL
      CHARACTER*80 SKIP
      INTEGER DATEPTS(MAXEPH,5)
      REAL*8 SUNPTS(MAXEPH,3),EPHPTS(MAXEPH,3)
      REAL*8 XREAD(3),FDOM,TJDATE,SUNLON,DSUN,PI,DG2RAD
C
      DATA NLOOP/500000/
C
C     Statement function to calculate the floating point day of year.
C       IDFUN  - integer day of year (DDD).
C       IHFUN  - integer hour of day (HH).
C       IMFUN  - integer minute of hour (MM).
C       ISFUN  - integer second of minute (SS).
      DOYFUN(IDFUN,IHFUN,IMFUN,ISFUN) = FLOAT(IDFUN)+FLOAT(IHFUN)/24.
     $  + FLOAT(IMFUN)/1440. + FLOAT(ISFUN)/86400.
C
      PI = 3.141592654D0
      DG2RAD = PI/1.8D2
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED GETEPH!'
D     WRITE(*,*)' IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1 = ',
D    $            IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1
D     WRITE(*,*)' IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2 = ',
D    $            IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2
D     WRITE(*,*)' EPHFIL = ',EPHFIL
D     PAUSE
D     WRITE(*,*)
C
      NUMPTS = 0
C
C     Convert inputs to floating point day of year (DOY) format.
C
      CALL DOYEAR2(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,DOYIN1)
      CALL DOYEAR2(IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2,DOYIN2)
D     WRITE(*,*)' DOYIN1,DOYIN2 = ',DOYIN1,DOYIN2
C
D     WRITE(*,*)' B4 OPEN: EPHFIL = ',EPHFIL
D     PAUSE
      OPEN(40,FILE=EPHFIL,FORM='FORMATTED',ACCESS='SEQUENTIAL',
     $  STATUS='OLD')
D     WRITE(*,*)' AFTER OPEN: EPHFIL = ',EPHFIL
D     PAUSE
C
C     Skip first 7 header records.
      DO I = 1,7
D       READ(40,1) SKIP
D       WRITE(*,*)' SKIP = ',SKIP
        READ(40,*)
      END DO
D     WRITE(*,*)' AFTER SKIP 7'
D     PAUSE
C
C     Read the start & stop times of the data file.
      READ(40,100) IYSTRT,IDSTRT,IHSTRT,IMSTRT,SECSTRT
      READ(40,100) IYSTOP,IDSTOP,IHSTOP,IMSTOP,SECSTOP
D     WRITE(*,*)' IYSTRT,IDSTRT,IHSTRT,IMSTRT,SECSTRT = ',
D    $            IYSTRT,IDSTRT,IHSTRT,IMSTRT,SECSTRT
D     WRITE(*,*)' IYSTOP,IDSTOP,IHSTOP,IMSTOP,SECSTOP = ',
D    $            IYSTOP,IDSTOP,IHSTOP,IMSTOP,SECSTOP
D     PAUSE
C     Convert data file's start & stop times to floating point DOY format.
      ISECSTRT = INT(SECSTRT)
      DOYSTRT = DOYFUN(IDSTRT,IHSTRT,IMSTRT,ISECSTRT)
      ISECSTOP = INT(SECSTOP)
      DOYSTOP = DOYFUN(IDSTOP,IHSTOP,IMSTOP,ISECSTOP)
D     WRITE(*,*)' DOYSTRT,DOYSTOP = ',DOYSTRT,DOYSTOP
D     PAUSE
C
C     Check if the user's start & stop times overlap the ephemeris
C     data file times.
      IF((IYSTRT.GT.IYR2).OR.(IYSTOP.LT.IYR1)) RETURN
      IF((IYR1.EQ.IYSTOP).AND.(DOYIN1.GT.DOYSTOP)) RETURN
      IF((IYR2.EQ.IYSTRT).AND.(DOYIN2.LT.DOYSTRT)) RETURN
C
C     Read the time step size (sec).
      READ(40,1) SKIP
      READ(40,200) EPHSTP
D     WRITE(*,*)' EPHSTP = ',EPHSTP
D     PAUSE
C
C     Skip next 6 header records.
      DO I = 1,6
        READ(40,1) SKIP
      END DO
C
C     Read the ephemeris locations.
C
      WRITE(*,*)
      WRITE(*,*)' Reading Ephemeris locations:'
      WRITE(*,*)
      ICNT = 0
      DO I = 1,NLOOP
        ICNT = ICNT + 1
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
          WRITE(*,*)' I = ',I
        END IF
        READ(40,300,ERR=1001,END=1002) IYYYY,IDDD,IHH,IMM,SECS,
     $                                 (XREAD(J),J=1,3)
        ISECS = INT(SECS)
        DOYNOW = DOYFUN(IDDD,IHH,IMM,ISECS)
        IF(((IYYYY.EQ.IYR1).AND.(DOYNOW.GE.DOYIN1)).OR.
     $    ((IYYYY.EQ.IYR2).AND.(DOYNOW.LE.DOYIN2)).OR.
     $    ((IYYYY.GT.IYR1).AND.(IYYYY.LT.IYR2))) THEN
C         This point's time lies between the user's start & stop dates.
C         Include this point in the work arrays.
          NUMPTS = NUMPTS + 1
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)' I,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS = ',
D    $                  I,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS
D           WRITE(*,*)' (XREAD(J),J=1,3) = ',(XREAD(J),J=1,3)
D         END IF
C
C         Load this date and time in the work array.
          DATEPTS(NUMPTS,1) = IYYYY
          DATEPTS(NUMPTS,2) = IDDD
          DATEPTS(NUMPTS,3) = IHH
          DATEPTS(NUMPTS,4) = IMM
          DATEPTS(NUMPTS,5) = ISECS
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'DATEPTS(92,1-5) = ',(DATEPTS(92,JJ),JJ=1,5)
D         END IF
C
C         Load this spacecraft position in the work array.
          DO K = 1,3
            EPHPTS(NUMPTS,K) = XREAD(K)
D           IF(NUMPTS.GT.88) THEN
D             WRITE(*,*)' I,NUMPTS,K,EPHPTS(NUMPTS,K) = ',
D    $                    I,NUMPTS,K,EPHPTS(NUMPTS,K)
D           END IF
          END DO
D         IF(NUMPTS.GT.88) THEN
D           RECICK = SQRT(EPHPTS(NUMPTS,1)**2+EPHPTS(NUMPTS,2)**2
D    $                   +EPHPTS(NUMPTS,3)**2)
D           RECICK = RECICK/6347.
D           WRITE(*,*)'I,NUMPTS,RECICK,EPHPTS(NUMPTS,1-3) = ',
D    $                 I,NUMPTS,RECICK,(EPHPTS(NUMPTS,JJ),JJ=1,3)
D           PAUSE
D         END IF
C
C         Calculate the Sun's ECI coordinates for test purposes, since
C         the official Solar epehemeris is not available.
C
C         Compute the Julian date.
C
          CALL DATE2(IYYYY,DOYNOW,IMM2,IDOM)
          FDOM = DOYFUN(IDOM,IHH,IMM,ISECS)
          CALL jdate(IYYYY,IMM2,FDOM,TJDATE)
C
C         Calculate the solar longitude.
C
          CALL sollon(TJDATE,SUNLON,DSUN)
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'TJDATE,SUNLON,DSUN = ',TJDATE,SUNLON,DSUN
D         END IF
C
          SLONR = SUNLON * DG2RAD
C
          SUNPTS(NUMPTS,1) = 100.*COS(SLONR)
          SUNPTS(NUMPTS,2) = 100.*SIN(SLONR)
          SUNPTS(NUMPTS,3) = 0.0
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'SUNPTS(NUMPTS,1-3) = ',(SUNPTS(NUMPTS,JJ),JJ=1,3)
D           PAUSE
D         END IF
C
        END IF
      END DO
1001  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Error reading data!  I = ',I
      PAUSE
      STOP 1
1002  CONTINUE
C
      CLOSE(40)
C
1     FORMAT(A)
100   FORMAT(29X,I4,1X,I3,1X,I2,1X,I2,1X,F6.3)
200   FORMAT(30X,F10.3)
300   FORMAT(I4,1X,I3,1X,I2,1X,I2,1X,F6.3,1X,F13.4,3X,F13.4,3X,F13.4)
C
      RETURN
      END
C
C
      SUBROUTINE GETEPH2(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,IYR2,
     $  IMON2,IDAYM2,IHR2,IMINIT2,ISEC2,EPHFIL,NUMPTS,DATEPTS,SUNPTS,
     $  EPHPTS,EPHSTP)
C
C     This routine reads STK output files containing the S/C
C     ephemeris (ECI).
C
C     This routine takes the user's selection of the start and stop
C     dates and times and reads those positions from the ephemeris
C     file which lie between these times.  There is no available data
C     file of the corresponding Solar ECI positions, so they are
C     calculated.
C
C     INPUTS:
C       IYR1    - year (YYYY) of start time.
C       IMON1   - month (MM) of start time.
C       IDAYM1  - day of month (DD) of start time.
C       IHR1    - hour of day (HH) of start time.
C       IMINIT1 - minute of hour (MM) of start time.
C       ISEC1   - second of minute (SS) of start time.
C       IYR2    - year (YYYY) of stop time.
C       IMON2   - month (MM) of stop time.
C       IDAYM2  - day of month (DD) of stop time.
C       IHR2    - hour of day (HH) of stop time.
C       IMINIT2 - minute of hour (MM) of stop time.
C       ISEC2   - second of minute (SS) of stop time.
C       EPHFIL  - ephemeris data file name (up to 32 characters).
C
C     OUTPUTS:
C       NUMPTS  - number of ephemeris points that lie between the
C                 start and stop times.
C       DATEPTS - integer array containing ephemeris location dates
C                 that are between the stop and start times.
C                 DATEPTS(K,1) = Year (YYYY) of Kth ephemeris point.
C                 DATEPTS(K,2) = Day (DDD) of Year of Kth ephemeris point.
C                 DATEPTS(K,3) = Hour (HH) of Day of Kth ephemeris point.
C                 DATEPTS(K,4) = Minute (MM) of Hour of Kth ephemeris point.
C                 DATEPTS(K,5) = Second (SS) of Minute of Kth ephemeris point.
C       SUNPTS  - array containing Sun ephemeris points in ECI coordinate
C                 system (km) corresponding to times between start and
C                 stop (double precision).
C                 SUNPTS(K,1) = x coordinate of Kth ephemeris point.
C                 SUNPTS(K,2) = y coordinate of Kth ephemeris point.
C                 SUNPTS(K,3) = z coordinate of Kth ephemeris point.
C       EPHPTS  - array containing spacecraft ephemeris points in ECI
C                 coordinate system (km) corresponding to times between
C                 start & stop (double precision).
C                 EPHPTS(K,1) = x coordinate of Kth ephemeris point.
C                 EPHPTS(K,2) = y coordinate of Kth ephemeris point.
C                 EPHPTS(K,3) = z coordinate of Kth ephemeris point.
C       EPHSTP  - time step between ephemeris points (sec).
C
C
      INCLUDE 'MAXEPH.PAR'
C
      CHARACTER*32 EPHFIL
      CHARACTER *1 SKIP
      CHARACTER*3 CMON,CMONS
      INTEGER DATEPTS(MAXEPH,5)
      REAL*8 SUNPTS(MAXEPH,3),EPHPTS(MAXEPH,3)
      REAL*8 XREAD(3),FDOM,TJDATE,SUNLON,DSUN,PI,DG2RAD
C
C     Statement function to calculate the floating point day of year.
C       IDFUN  - integer day of year (DDD).
C       IHFUN  - integer hour of day (HH).
C       IMFUN  - integer minute of hour (MM).
C       ISFUN  - integer second of minute (SS).
      DOYFUN(IDFUN,IHFUN,IMFUN,ISFUN) = FLOAT(IDFUN)+FLOAT(IHFUN)/24.
     $  + FLOAT(IMFUN)/1440. + FLOAT(ISFUN)/86400.
C
      PI = 3.141592654D0
      DG2RAD = PI/1.8D2
C
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED GETEPH2!'
D     WRITE(*,*)' IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1 = ',
D    $            IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1
D     WRITE(*,*)' IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2 = ',
D    $            IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2
D     WRITE(*,*)' EPHFIL = ',EPHFIL
D     WRITE(*,*)
D     PAUSE
C
      NUMPTS = 0
C
C     Convert inputs to floating point day of year (DOY) format.
C
      CALL DOYEAR2(IYR1,IMON1,IDAYM1,IHR1,IMINIT1,ISEC1,DOYIN1)
      CALL DOYEAR2(IYR2,IMON2,IDAYM2,IHR2,IMINIT2,ISEC2,DOYIN2)
D     WRITE(*,*)' DOYIN1,DOYIN2 = ',DOYIN1,DOYIN2
C
D     WRITE(*,*)' B4 OPEN: EPHFIL = ',EPHFIL
D     PAUSE
      OPEN(40,FILE='YR2000_30sec.eci',FORM='FORMATTED',
     $  ACCESS='SEQUENTIAL',STATUS='OLD')
D     WRITE(*,*)' AFTER OPEN: YR2000_30sec.eci'
D     PAUSE
C
C     Skip first 6 header records.
      DO I = 1,6
        READ(40,*)
      END DO
D     WRITE(*,*)' AFTER SKIP 6'
D     PAUSE
C
C     Read the start time of the data file.
      READ(40,100,ERR=1001) IDAYS,CMONS,IYRS,IHRS,IMINITS,SECNDSS,
     $  XS,YS,ZS
D     WRITE(*,*)' IDAYS,CMONS,IYRS,IHRS,IMINITS,SECNDSS = ',
D    $            IDAYS,CMONS,IYRS,IHRS,IMINITS,SECNDSS
D     PAUSE
C     Convert data file's start time to floating point DOY format.
      ISECNDS = INT(SECNDSS)
      IMONS = NMONTH(CMONS)
      CALL DOYEAR2(IYRS,IMONS,IDAYS,IHRS,IMINITS,ISECNDS,DOYSTRT)
D     WRITE(*,*)' DOYSTRT = ',DOYSTRT
D     PAUSE
C
C     Read the second time.
      READ(40,100,ERR=1001) IDAY,CMON,IYR,IHR,IMINIT,SECNDS,X2,Y2,Z2
D     WRITE(*,*)' IDAY,CMON,IYR,IHR,IMINIT,SECNDS = ',
D    $            IDAY,CMON,IYR,IHR,IMINIT,SECNDS
D     PAUSE
C     Convert data file's 2nd time to floating point DOY format.
      ISECNDS = INT(SECNDS)
      IMON = NMONTH(CMON)
      CALL DOYEAR2(IYR,IMON,IDAY,IHR,IMINIT,ISECNDS,DOY2ND)
D     WRITE(*,*)' DOY2ND = ',DOY2ND
D     PAUSE
C
C     Find the ephemeris' time step (seconds).
      EPHSTP = (DOY2ND - DOYSTRT) * 86400.
      ITEMP = INT(EPHSTP)
      EPHSTP = FLOAT(ITEMP)
D     WRITE(*,*)' EPHSTP = ',EPHSTP
D     PAUSE
C
C     Check if the user's start time lies within the ephemeris
C     data file times.
C
      IF((IYRS.GT.IYR1).OR.((IYRS.EQ.IYR1).AND.
     $  (DOYSTRT.GT.(DOYIN1+1)))) THEN
        WRITE(*,*)
        WRITE(*,*)' This data file starts after the user desired',
     $    ' start time - the data used will not cover the complete',
     $    ' period.'
      ELSE IF((IYRS.GT.IYR2).OR.((IYRS.EQ.IYR2).AND.
     $  (DOYSTRT.GT.(DOYIN2+1)))) THEN
        WRITE(*,*)
        WRITE(*,*)' This data file starts after the user desired',
     $    ' stop time - STOP execution.'
        PAUSE
        STOP 25
      END IF
C
      REWIND(40)
C
C     Skip first 6 header records.
      DO I = 1,6
        READ(40,1) SKIP
      END DO
C
C     Read the ephemeris locations.
C
      WRITE(*,*)
      WRITE(*,*)' Reading Ephemeris locations:'
      WRITE(*,*)
      ICNT = 0
      N1000 = 0
C
      DO WHILE (.TRUE.)
        ICNT = ICNT + 1
D       WRITE(*,*)' ICNT,NUMPTS = ',ICNT,NUMPTS
        IF(ICNT.EQ.1000) THEN
          ICNT = 0
          N1000 = N1000 + 1
          WRITE(*,*)' N1000,NUMPTS = ',N1000,NUMPTS
        END IF
        READ(40,100,ERR=1001,END=1002) IDAY,CMON,IYYYY,IHH,IMM,SECNDS,
     $                                 (XREAD(J),J=1,3)
        ISECS = INT(SECNDS)
        IMON = NMONTH(CMON)
        CALL DOYEAR2(IYYYY,IMON,IDAY,IHH,IMM,ISECS,DOYNOW)
        IDDD = INT(DOYNOW)
D       WRITE(*,*)' ICNT,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS = ',
D    $              ICNT,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS
D       WRITE(*,*)' (XREAD(J),J=1,3) = ',(XREAD(J),J=1,3)
D       PAUSE
C
        IF(((IYYYY.EQ.IYR1).AND.(DOYNOW.GE.DOYIN1)).OR.
     $    ((IYYYY.EQ.IYR2).AND.(DOYNOW.LE.DOYIN2)).OR.
     $    ((IYYYY.GT.IYR1).AND.(IYYYY.LT.IYR2))) THEN
C         This point's time lies between the user's start & stop dates.
C         Include this point in the work arrays.
          NUMPTS = NUMPTS + 1
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)' ICNT,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS = ',
D    $                  ICNT,NUMPTS,IYYYY,IDDD,IHH,IMM,SECS,ISECS
D           WRITE(*,*)' (XREAD(J),J=1,3) = ',(XREAD(J),J=1,3)
D           PAUSE
D         END IF
C
C         Load this date and time in the work array.
          DATEPTS(NUMPTS,1) = IYYYY
          DATEPTS(NUMPTS,2) = IDDD
          DATEPTS(NUMPTS,3) = IHH
          DATEPTS(NUMPTS,4) = IMM
          DATEPTS(NUMPTS,5) = ISECS
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'DATEPTS(92,1-5) = ',(DATEPTS(92,JJ),JJ=1,5)
D         END IF
C
C         Load this spacecraft position in the work array.
          DO K = 1,3
            EPHPTS(NUMPTS,K) = XREAD(K)
D           IF(NUMPTS.GT.88) THEN
D             WRITE(*,*)' ICNT,NUMPTS,K,EPHPTS(NUMPTS,K) = ',
D    $                    ICNT,NUMPTS,K,EPHPTS(NUMPTS,K)
D           END IF
          END DO
D         IF(NUMPTS.GT.88) THEN
D           RECICK = SQRT(EPHPTS(NUMPTS,1)**2+EPHPTS(NUMPTS,2)**2
D    $                   +EPHPTS(NUMPTS,3)**2)
D           RECICK = RECICK/6347.
D           WRITE(*,*)'ICNT,NUMPTS,RECICK,EPHPTS(NUMPTS,1-3) = ',
D    $                 ICNT,NUMPTS,RECICK,(EPHPTS(NUMPTS,JJ),JJ=1,3)
D           PAUSE
D         END IF
C
C         Calculate the Sun's ECI coordinates for test purposes, since
C         the official Solar epehemeris is not available.
C
C         Compute the Julian date.
C
          CALL DATE2(IYYYY,DOYNOW,IMM2,IDOM)
          FDOM = DOYFUN(IDOM,IHH,IMM,ISECS)
          CALL jdate(IYYYY,IMM2,FDOM,TJDATE)
C
C         Calculate the solar longitude.
C
          CALL sollon(TJDATE,SUNLON,DSUN)
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'TJDATE,SUNLON,DSUN = ',TJDATE,SUNLON,DSUN
D         END IF
C
          SLONR = SUNLON * DG2RAD
C
          SUNPTS(NUMPTS,1) = 100.*COS(SLONR)
          SUNPTS(NUMPTS,2) = 100.*SIN(SLONR)
          SUNPTS(NUMPTS,3) = 0.0
D         IF(NUMPTS.GT.88) THEN
D           WRITE(*,*)'SUNPTS(NUMPTS,1-3) = ',(SUNPTS(NUMPTS,JJ),JJ=1,3)
D           PAUSE
D         END IF
C
        END IF
      END DO
1001  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Error reading data!  I = ',I
      PAUSE
      STOP 1
1002  CONTINUE
C
      IF(NUMPTS.EQ.0) THEN
        WRITE(*,*)
        WRITE(*,*)' No data records used! STOP execution.'
        PAUSE
        STOP 27
      END IF
C
      CLOSE(40)
C
1     FORMAT(A1)
100   FORMAT(I2,1X,A3,1X,I4,1X,I2,1X,I2,1X,F5.2,2X,F15.2,2X,F16.2,
     $  2X,F15.2)
C
      RETURN
      END
C
C
      subroutine DOYEAR2(iyr,imn,idm,IHR,IMIN,ISEC,DOY)
c
c	  Modified routine based on APL IDL function by R. Sterner.
c
c     Input:
c		iyr        year (all digits for Y2K compliance)
c		imn        month
c		idm        day of month
C       IHR        hour of day.
C       IMIN       minute of hour
C       ISEC       second of minute
C
c     Output:
C       DOY        floating point day value (e.g., 221.36 days)
C
      integer iday(12)

c      iday are arrays for the day number at the 
c             start of each month (non-leap years)
      data iday /1,32,60,91,121,152,182,213,244,274,
     >              305,335 /

c    note...this algorithm won't catch centuries that are not leap centuries
c    leap century:   2000/400 = 5.0  leap year    1900/400 = 4.75 non leap year
      ileapyear = 0	    !leap year correction
      itest = jmod(iyr,4)   !general test to see if it is leap year
      if (itest.eq.0) then  !itest = 0 for leap years
	    if (imn.ge.3) then !correct only March-December for leapyr
	      ileapyear = 1
	    endif
      endif
D     WRITE(*,*)
D     WRITE(*,*)' ENTERED DOYEAR2!'
D     WRITE(*,*)' IMN,IDAY(IMN) = ', IMN,IDAY(IMN)
D     PAUSE
      idn = idm + iday(imn) - 1 + ileapyear
      DOY = FLOAT(IDN)+FLOAT(IHR)/24.+FLOAT(IMIN)/1440.
     $     +FLOAT(ISEC)/86400.
D     WRITE(*,*)
D     WRITE(*,*)' IN DOYEAR2!!  iyr,imn,idm,IHR,IMIN,ISEC,idn,DOY = ',
D    $                          iyr,imn,idm,IHR,IMIN,ISEC,idn,DOY
D     PAUSE
      return
      end
C
C
      INTEGER FUNCTION NMONTH(MONTH)
C
C     Calculate the month number.
C
      CHARACTER*3 MONTH
C
D     WRITE(*,*)
D     WRITE(*,*)' IN NMONTH!!  MONTH = ',MONTH
      IF(MONTH.EQ.'Jan') THEN
        NMONTH = 1
      ELSE IF(MONTH.EQ.'Feb') THEN
        NMONTH = 2
      ELSE IF(MONTH.EQ.'Mar') THEN
        NMONTH = 3
      ELSE IF(MONTH.EQ.'Apr') THEN
        NMONTH = 4
      ELSE IF(MONTH.EQ.'May') THEN
        NMONTH = 5
      ELSE IF(MONTH.EQ.'Jun') THEN
        NMONTH = 6
      ELSE IF(MONTH.EQ.'Jul') THEN
        NMONTH = 7
      ELSE IF(MONTH.EQ.'Aug') THEN
        NMONTH = 8
      ELSE IF(MONTH.EQ.'Sep') THEN
        NMONTH = 9
      ELSE IF(MONTH.EQ.'Oct') THEN
        NMONTH = 10
      ELSE IF(MONTH.EQ.'Nov') THEN
        NMONTH = 11
      ELSE IF(MONTH.EQ.'Dec') THEN
        NMONTH = 12
      ELSE
        WRITE(*,*)
        WRITE(*,*)' Month name not correct!  Should be like ''Feb''.'
      END IF
C
      RETURN
      END
C
C
      subroutine sollon(JD,sbeta,rsun)
C
C     This program calculates the J2000 solar longitude and
C     the heliocentric distance according to the VSOP87 theory...
C
C     Declare variables and dimension arrays.
C
      REAL*8 L0(64,3),L1(34,3),L2(20,3),L3(7,3),L4(2,3)
      REAL*8 R0(40,3),R1(10,3),R2(6,3),R3(2,3),R4(1,3)
      REAL*8 pi,jd,sbeta,t,sl0,sl1,sl2,sl3,sl4,rsun
      REAL*8 rs0,rs1,rs2,rs3
C
C     Establish constants.
C
      pi=3.141592654d0
C
C     Establish coefficients.
C
      L0(1,1)=175347046.0
      L0(1,2)=0.0d0
      L0(1,3)=0.0d0
      L0(2,1)=3341656.0
      L0(2,2)=4.6692568
      L0(2,3)=6283.0758500
      L0(3,1)=34894.0
      L0(3,2)=4.62610
      L0(3,3)=12566.15170
      L0(4,1)=3497.0
      L0(4,2)=2.7441
      L0(4,3)=5753.3849
      L0(5,1)=3418.0
      L0(5,2)=2.8289
      L0(5,3)=3.5231
      L0(6,1)=3136.0
      L0(6,2)=3.6277
      L0(6,3)=77713.7715
      L0(7,1)=2676.0
      L0(7,2)=4.4181
      L0(7,3)=7860.4194
      L0(8,1)=2343.0
      L0(8,2)=6.1352
      L0(8,3)=3930.2097
      L0(9,1)=1324.0
      L0(9,2)=0.7425
      L0(9,3)=11506.7698
      L0(10,1)=1273.0
      L0(10,2)=2.0371
      L0(10,3)=529.6910
      L0(11,1)=1199.0
      L0(11,2)=1.1096
      L0(11,3)=1577.3435
      L0(12,1)=990.0
      L0(12,2)=5.233
      L0(12,3)=5884.927
      L0(13,1)=902.0
      L0(13,2)=2.045
      L0(13,3)=26.298
      L0(14,1)=857.0
      L0(14,2)=3.508
      L0(14,3)=398.149
      L0(15,1)=780.0
      L0(15,2)=1.179
      L0(15,3)=5223.694
      L0(16,1)=753.0
      L0(16,2)=2.533
      L0(16,3)=5507.553
      L0(17,1)=505.0
      L0(17,2)=4.583
      L0(17,3)=18849.228
      L0(18,1)=492.0
      L0(18,2)=4.205
      L0(18,3)=775.523
      L0(19,1)=357.0
      L0(19,2)=2.920
      L0(19,3)=0.067
      L0(20,1)=317.0
      L0(20,2)=5.849
      L0(20,3)=11790.629
      L0(21,1)=284.0
      L0(21,2)=1.899
      L0(21,3)=796.298
      L0(22,1)=271.0
      L0(22,2)=0.315
      L0(22,3)=10977.079
      L0(23,1)=243.0
      L0(23,2)=0.345
      L0(23,3)=5486.778
      L0(24,1)=206.0
      L0(24,2)=4.806
      L0(24,3)=2544.314
      L0(25,1)=205.0
      L0(25,2)=1.869
      L0(25,3)=5573.143
      L0(26,1)=202.0
      L0(26,2)=2.458
      L0(26,3)=6069.777
      L0(27,1)=156.0
      L0(27,2)=0.833
      L0(27,3)=213.299
      L0(28,1)=132.0
      L0(28,2)=3.411
      L0(28,3)=2942.463
      L0(29,1)=126.0
      L0(29,2)=1.083
      L0(29,3)=20.775
      L0(30,1)=115.0
      L0(30,2)=0.645
      L0(30,3)=0.980
      L0(31,1)=103.0
      L0(31,2)=0.636
      L0(31,3)=4694.003
      L0(32,1)=102.0
      L0(32,2)=0.976
      L0(32,3)=15270.839
      L0(33,1)=102.0
      L0(33,2)=4.267
      L0(33,3)=7.114
      L0(34,1)=99.0
      L0(34,2)=6.21
      L0(34,3)=2146.17
      L0(35,1)=98.0
      L0(35,2)=0.68
      L0(35,3)=155.42
      L0(36,1)=86.0
      L0(36,2)=5.98
      L0(36,3)=161000.69
      L0(37,1)=85.0
      L0(37,2)=1.30
      L0(37,3)=6275.96
      L0(38,1)=85.0
      L0(38,2)=3.67
      L0(38,3)=71430.70
      L0(39,1)=80.0
      L0(39,2)=1.81
      L0(39,3)=17260.15
      L0(40,1)=79.0
      L0(40,2)=3.04
      L0(40,3)=12036.46
      L0(41,1)=75.0
      L0(41,2)=1.76
      L0(41,3)=5088.63
      L0(42,1)=74.0
      L0(42,2)=3.50
      L0(42,3)=3154.69
      L0(43,1)=74.0
      L0(43,2)=4.68
      L0(43,3)=801.82
      L0(44,1)=70.0
      L0(44,2)=0.83
      L0(44,3)=9437.76
      L0(45,1)=62.0
      L0(45,2)=3.98
      L0(45,3)=8827.39
      L0(46,1)=61.0
      L0(46,2)=1.82
      L0(46,3)=7084.90
      L0(47,1)=57.0
      L0(47,2)=2.78
      L0(47,3)=6286.60
      L0(48,1)=56.0
      L0(48,2)=4.39
      L0(48,3)=14143.50
      L0(49,1)=56.0
      L0(49,2)=3.47
      L0(49,3)=6279.55
      L0(50,1)=52.0
      L0(50,2)=0.19
      L0(50,3)=12139.55
      L0(51,1)=52.0
      L0(51,2)=1.33
      L0(51,3)=1748.02
      L0(52,1)=51.0
      L0(52,2)=0.28
      L0(52,3)=5856.48
      L0(53,1)=49.0
      L0(53,2)=0.49
      L0(53,3)=1194.45
      L0(54,1)=41.0
      L0(54,2)=5.37
      L0(54,3)=8429.24
      L0(55,1)=41.0
      L0(55,2)=2.40
      L0(55,3)=19651.05
      L0(56,1)=39.0
      L0(56,2)=6.17
      L0(56,3)=10447.39
      L0(57,1)=37.0
      L0(57,2)=6.04
      L0(57,3)=10213.29
      L0(58,1)=37.0
      L0(58,2)=2.57
      L0(58,3)=1059.38
      L0(59,1)=36.0
      L0(59,2)=1.71
      L0(59,3)=2352.87
      L0(60,1)=36.0
      L0(60,2)=1.78
      L0(60,3)=6812.77
      L0(61,1)=33.0
      L0(61,2)=0.59
      L0(61,3)=17789.85
      L0(62,1)=30.0
      L0(62,2)=0.44
      L0(62,3)=83996.85
      L0(63,1)=30.0
      L0(63,2)=2.74
      L0(63,3)=1349.87
      L0(64,1)=25.0
      L0(64,2)=3.16
      L0(64,3)=4690.48
C
      L1(1,1)=628307584999.0
      L1(1,2)=0.0
      L1(1,3)=0.0
      L1(2,1)=206059.0
      L1(2,2)=2.678235
      L1(2,3)=6283.075850
      L1(3,1)=4303.0
      L1(3,2)=2.6351
      L1(3,3)=12566.1517
      L1(4,1)=425.0
      L1(4,2)=1.590
      L1(4,3)=3.523
      L1(5,1)=119.0
      L1(5,2)=5.796
      L1(5,3)=26.298
      L1(6,1)=109.0
      L1(6,2)=2.966
      L1(6,3)=1577.344
      L1(7,1)=93.0
      L1(7,2)=2.59
      L1(7,3)=18849.23
      L1(8,1)=72.0
      L1(8,2)=1.14
      L1(8,3)=529.69
      L1(9,1)=68.0
      L1(9,2)=1.87
      L1(9,3)=398.15
      L1(10,1)=67.0
      L1(10,2)=4.41
      L1(10,3)=5507.55
      L1(11,1)=59.0
      L1(11,2)=2.89
      L1(11,3)=5223.69
      L1(12,1)=56.0
      L1(12,2)=2.17
      L1(12,3)=155.42
      L1(13,1)=45.0
      L1(13,2)=0.40
      L1(13,3)=796.30
      L1(14,1)=36.0
      L1(14,2)=0.47
      L1(14,3)=775.52
      L1(15,1)=29.0
      L1(15,2)=2.65
      L1(15,3)=7.11
      L1(16,1)=21.0
      L1(16,2)=5.34
      L1(16,3)=0.98
      L1(17,1)=19.0
      L1(17,2)=1.85
      L1(17,3)=5486.78
      L1(18,1)=19.0
      L1(18,2)=4.97
      L1(18,3)=213.30
      L1(19,1)=17.0
      L1(19,2)=2.99
      L1(19,3)=6275.96
      L1(20,1)=16.0
      L1(20,2)=0.03
      L1(20,3)=2544.31
      L1(21,1)=16.0
      L1(21,2)=1.43
      L1(21,3)=2146.17
      L1(22,1)=15.0
      L1(22,2)=1.21
      L1(22,3)=10977.08
      L1(23,1)=12.0
      L1(23,2)=2.83
      L1(23,3)=1748.02
      L1(24,1)=12.0
      L1(24,2)=3.26
      L1(24,3)=5088.63
      L1(25,1)=12.0
      L1(25,2)=5.27
      L1(25,3)=1194.45
      L1(26,1)=12.0
      L1(26,2)=2.08
      L1(26,3)=4694.00
      L1(27,1)=11.0
      L1(27,2)=0.77
      L1(27,3)=553.57
      L1(28,1)=10.0
      L1(28,2)=1.30
      L1(28,3)=6286.60
      L1(29,1)=10.0
      L1(29,2)=4.24
      L1(29,3)=1349.87
      L1(30,1)=9.0
      L1(30,2)=2.70
      L1(30,3)=242.73
      L1(31,1)=9.0
      L1(31,2)=5.64
      L1(31,3)=951.72
      L1(32,1)=8.0
      L1(32,2)=5.30
      L1(32,3)=2352.87
      L1(33,1)=6.0
      L1(33,2)=2.65
      L1(33,3)=9437.76
      L1(34,1)=6.0
      L1(34,2)=4.67
      L1(34,3)=4690.48
C
      L2(1,1)=8722.0
      L2(1,2)=1.0725
      L2(1,3)=6283.0758
      L2(2,1)=991.0
      L2(2,2)=3.1416
      L2(2,3)=0.0
      L2(3,1)=295.0
      L2(3,2)=0.437
      L2(3,3)=12566.152
      L2(4,1)=27.0
      L2(4,2)=0.05
      L2(4,3)=3.52
      L2(5,1)=16.0
      L2(5,2)=5.19
      L2(5,3)=26.30
      L2(6,1)=16.0
      L2(6,2)=3.69
      L2(6,3)=155.42
      L2(7,1)=9.0
      L2(7,2)=0.30
      L2(7,3)=18849.23
      L2(8,1)=9.0
      L2(8,2)=2.06
      L2(8,3)=77713.77
      L2(9,1)=7.0
      L2(9,2)=0.83
      L2(9,3)=775.52
      L2(10,1)=5.0
      L2(10,2)=4.66
      L2(10,3)=1577.34
      L2(11,1)=4.0
      L2(11,2)=1.03
      L2(11,3)=7.11
      L2(12,1)=4.0
      L2(12,2)=3.44
      L2(12,3)=5573.14
      L2(13,1)=3.0
      L2(13,2)=5.14
      L2(13,3)=796.30
      L2(14,1)=3.0
      L2(14,2)=6.05
      L2(14,3)=5507.55
      L2(15,1)=3.0
      L2(15,2)=1.19
      L2(15,3)=242.73
      L2(16,1)=3.0
      L2(16,2)=6.12
      L2(16,3)=529.69
      L2(17,1)=3.0
      L2(17,2)=0.30
      L2(17,3)=398.15
      L2(18,1)=3.0
      L2(18,2)=2.28
      L2(18,3)=553.57
      L2(19,1)=2.0
      L2(19,2)=4.38
      L2(19,3)=5223.69
      L2(20,1)=2.0
      L2(20,2)=3.75
      L2(20,3)=0.98
C
      L3(1,1)=289.0
      L3(1,2)=5.842
      L3(1,3)=6283.076
      L3(2,1)=21.0
      L3(2,2)=6.05
      L3(2,3)=12566.15
      L3(3,1)=3.0
      L3(3,2)=5.20
      L3(3,3)=155.42
      L3(4,1)=3.0
      L3(4,2)=3.14
      L3(4,3)=0.0
      L3(5,1)=1.0
      L3(5,2)=4.72
      L3(5,3)=3.52
      L3(6,1)=1.0
      L3(6,2)=5.97
      L3(6,3)=242.73
      L3(7,1)=1.0
      L3(7,2)=5.54
      L3(7,3)=18849.23
C
      L4(1,1)=8.0
      L4(1,2)=4.14
      L4(1,3)=6283.08
      L4(2,1)=1.0
      L4(2,2)=3.28
      L4(2,3)=12566.15
C
C     Coefficients for the heliocentric distance.
C
      R0(1,1)=100013989.0
      R0(1,2)=0.0
      R0(1,3)=0.0
      R0(2,1)=1670700.0
      R0(2,2)=3.0984635
      R0(2,3)=6283.0758500
      R0(3,1)=13956.0
      R0(3,2)=3.05525
      R0(3,3)=12566.15170
      R0(4,1)=3084.0
      R0(4,2)=5.1985
      R0(4,3)=77713.7715
      R0(5,1)=1628.0
      R0(5,2)=1.1739
      R0(5,3)=5753.3849
      R0(6,1)=1576.0
      R0(6,2)=2.8469
      R0(6,3)=7860.4194
      R0(7,1)=925.0
      R0(7,2)=5.453
      R0(7,3)=11506.770
      R0(8,1)=542.0
      R0(8,2)=4.564
      R0(8,3)=3930.210
      R0(9,1)=472.0
      R0(9,2)=3.661
      R0(9,3)=5884.927
      R0(10,1)=346.0
      R0(10,2)=0.964
      R0(10,3)=5507.553
      R0(11,1)=329.0
      R0(11,2)=5.9
      R0(11,3)=5223.694
      R0(12,1)=307.0
      R0(12,2)=0.299
      R0(12,3)=5573.143
      R0(13,1)=243.0
      R0(13,2)=4.273
      R0(13,3)=11790.629
      R0(14,1)=212.0
      R0(14,2)=5.847
      R0(14,3)=1577.344
      R0(15,1)=186.0
      R0(15,2)=5.022
      R0(15,3)=10977.079
      R0(16,1)=175.0
      R0(16,2)=3.012
      R0(16,3)=18849.228
      R0(17,1)=110.0
      R0(17,2)=5.055
      R0(17,3)=5486.778
      R0(18,1)=98.0
      R0(18,2)=0.89
      R0(18,3)=6069.78
      R0(19,1)=86.0
      R0(19,2)=5.69
      R0(19,3)=15720.84
      R0(20,1)=86.0
      R0(20,2)=1.27
      R0(20,3)=161000.69
      R0(21,1)=65.0
      R0(21,2)=0.27
      R0(21,3)=17260.15
      R0(22,1)=63.0
      R0(22,2)=0.92
      R0(22,3)=529.69
      R0(23,1)=57.0
      R0(23,2)=2.01
      R0(23,3)=83996.85
      R0(24,1)=56.0
      R0(24,2)=5.24
      R0(24,3)=71430.70
      R0(25,1)=49.0
      R0(25,2)=3.25
      R0(25,3)=2544.31
      R0(26,1)=47.0
      R0(26,2)=2.58
      R0(26,3)=775.52
      R0(27,1)=45.0
      R0(27,2)=5.54
      R0(27,3)=9437.76
      R0(28,1)=43.0
      R0(28,2)=6.01
      R0(28,3)=6275.96
      R0(29,1)=39.0
      R0(29,2)=5.36
      R0(29,3)=4694.00
      R0(30,1)=38.0
      R0(30,2)=2.39
      R0(30,3)=8827.39
      R0(31,1)=37.0
      R0(31,2)=0.83
      R0(31,3)=19651.05
      R0(32,1)=37.0
      R0(32,2)=4.90
      R0(32,3)=12139.55
      R0(33,1)=36.0
      R0(33,2)=1.67
      R0(33,3)=12036.46
      R0(34,1)=35.0
      R0(34,2)=1.84
      R0(34,3)=2942.46
      R0(35,1)=33.0
      R0(35,2)=0.24
      R0(35,3)=7084.90
      R0(36,1)=32.0
      R0(36,2)=0.18
      R0(36,3)=5088.63
      R0(37,1)=32.0
      R0(37,2)=1.78
      R0(37,3)=398.15
      R0(38,1)=28.0
      R0(38,2)=1.21
      R0(38,3)=6286.60
      R0(39,1)=28.0
      R0(39,2)=1.90
      R0(39,3)=6279.55
      R0(40,1)=26.0
      R0(40,2)=4.59
      R0(40,3)=10447.39
C
      R1(1,1)=103019.0
      R1(1,2)=1.107490
      R1(1,3)=6283.075850
      R1(2,1)=1721.0
      R1(2,2)=1.0644
      R1(2,3)=12566.1517
      R1(3,1)=702.0
      R1(3,2)=3.142
      R1(3,3)=0.0
      R1(4,1)=32.0
      R1(4,2)=1.02
      R1(4,3)=18849.23
      R1(5,1)=31.0
      R1(5,2)=2.84
      R1(5,3)=5507.55
      R1(6,1)=25.0
      R1(6,2)=1.32
      R1(6,3)=5223.69
      R1(7,1)=18.0
      R1(7,2)=1.42
      R1(7,3)=1577.34
      R1(8,1)=10.0
      R1(8,2)=5.91
      R1(8,3)=10977.08
      R1(9,1)=9.0
      R1(9,2)=1.42
      R1(9,3)=6275.96
      R1(10,1)=9.0
      R1(10,2)=0.27
      R1(10,3)=5486.78
C
      R2(1,1)=4359.0
      R2(1,2)=5.7846
      R2(1,3)=6283.0758
      R2(2,1)=124.0
      R2(2,2)=5.579
      R2(2,3)=12566.152
      R2(3,1)=12.0
      R2(3,2)=3.14
      R2(3,3)=0.0
      R2(4,1)=9.0
      R2(4,2)=3.63
      R2(4,3)=77713.77
      R2(5,1)=6.0
      R2(5,2)=1.87
      R2(5,3)=5573.14
      R2(6,1)=3.0
      R2(6,2)=5.47
      R2(6,3)=18849.23
C
      R3(1,1)=145.0
      R3(1,2)=4.273
      R3(1,3)=6283.076
      R3(2,1)=7.0
      R3(2,2)=3.92
      R3(2,3)=12566.15
C
      R4(1,1)=4.0
      R4(1,2)=2.56
      R4(1,3)=6283.08
C
C     Compute time in Julian millenia.
C
      t=(jd-2451545.0)/3.6525d5
C
C     Sum terms for L0, L1, L2, L3 and L4.
C
      sl0=0.0d0
      do 10 i=1,64
10    sl0=L0(i,1)*dcos(L0(i,2)+L0(i,3)*t)+sl0
      sl1=0.0d0
      do 12 i=1,34
12    sl1=L1(i,1)*dcos(L1(i,2)+L1(i,3)*t)+sl1
      sl2=0.0d0
      do 14 i=1,20
14    sl2=L2(i,1)*dcos(L2(i,2)+L2(i,3)*t)+sl2
      sl3=0.0d0
      do 16 i=1,7
16    sl3=L3(i,1)*dcos(L3(i,2)+L3(i,3)*t)+sl3
      sl4=0.0d0
      do 18 i=1,2
18    sl4=L4(i,1)*dcos(L4(i,2)+L4(i,3)*t)+sl4
C
C     Sum terms for R0, R1, R2, R3, R4.
C
      rs0=0.0d0
      do 20 i=1,40
20    rs0=R0(i,1)*dcos(R0(i,2)+R0(i,3)*t)+rs0
      rs1=0.0d0
      do 22 i=1,10
22    rs1=R1(i,1)*dcos(R1(i,2)+R1(i,3)*t)+rs1
      rs2=0.0d0
      do 24 i=1,6
24    rs2=R2(i,1)*dcos(R2(i,2)+R2(i,3)*t)+rs2
      rs3=0.0d0
      do 26 i=1,2
26    rs3=R3(i,1)*dcos(R3(i,2)+R3(i,3)*t)+rs3
      rs4=R4(1,1)*dcos(R4(1,2)+R4(1,3)*t)
C
C     Compute solar longitude in radians.
C
      sbeta=(sl0+sl1*t+sl2*t*t+sl3*t*t*t+sl4*t*t*t*t)/1.0d8+pi
      sbeta=dmod(sbeta,(2.0d0*pi))
      if (sbeta.lt.0.0d0) sbeta=sbeta+2.0d0*pi
C
C     Compute heliocentric distance.
C
      rsun=(rs0+rs1*t+rs2*t*t+rs3*t*t*t+rs4*t*t*t*t)/1.0d8
C
C     Convert to degrees.
C
C     sbeta=sbeta*1.8d2/pi-2.5092d-5
      sbeta=sbeta*1.8d2/pi
C
C     Finished.
C
      return
      end	
C
C
