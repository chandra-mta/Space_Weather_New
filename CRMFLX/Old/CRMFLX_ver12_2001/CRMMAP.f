      PROGRAM MAPXY
C
C     Simple test driver for exercising CRMFLX.  Calculates flux in the
C     XY plane.
C
      INTEGER LUNIT(3),SMOOTH1,FPCHI,FPCLO      
      CHARACTER*1 ANS
      CHARACTER*32 FILOUT
C
      LUNIT(1) = 50
      LUNIT(2) = 51
      LUNIT(3) = 52
      IUSESW = 0
      FSWIMN = 1.E+3
      FSWI95 = 1.E+3
      FSWI50 = 1.E+3
      FSWISD = 1.E+3
C
      SMOOTH1 = 6
      NFLXGET = 5
      NDROPHI = 1
      NDROPLO = 1
      LOGFLG = 2
      RNGTOL = 5
      FPCHI = 80
      FPCLO = 20
C
      WRITE(*,*)'  Magnetosphere Ion XY Map '
      WRITE(*,*)
      WRITE(*,*)'  CRMFLX Version 1.0 (EXPERIMENTAL)'
      WRITE(*,*)
CC    WRITE(*,*)
CC    WRITE(*,*)' Input ion species type ',
CC   $ '(proton -> 1; helium -> 2; CNO -> 3;) :'
CC    READ(*,*) ISPECI
C     Tempararily Hardwired to protons only!
      ISPECI = 1
      WRITE(*,*)
      WRITE(*,*)' Input flux output type (1->Mean; 2->95%; 3->50%:'
      READ(*,*) INPFLX
CC    Tempararily Hardwired to output mean only!
CC    INPFLX = 1
C
1000  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Input Kp index (0 - 9):'
      READ(*,*) XKP
      WRITE(*,*)
      WRITE(*,*)' Input IUSESW:'
      READ(*,*) IUSESW
      IF((IUSESW.EQ.1).OR.(IUSESW.EQ.3)) THEN
        WRITE(*,*)
        WRITE(*,*)' Input FSWIMN:'
        READ(*,*) FSWIMN
        WRITE(*,*)
        WRITE(*,*)' Input FSWI95:'
        READ(*,*) FSWI95
        WRITE(*,*)
        WRITE(*,*)' Input FSWI50:'
        READ(*,*) FSWI50
        WRITE(*,*)
        WRITE(*,*)' Input FSWISD:'
        READ(*,*) FSWISD
      END IF
      WRITE(*,*)
      WRITE(*,*)' Input output file name (32 character limit):'
      READ(*,*) FILOUT
C
      OPEN(32,FILE=FILOUT,ACCESS='SEQUENTIAL',
     $  FORM='FORMATTED',STATUS='UNKNOWN')
C
      WRITE(32,*)' Xgsm  Ygsm  Flux_Mean  IDLOC'
C
C     Set the Z-value (Re) for this scene's flux slice.
      ZGSM = 0.
C
C     Set the start location coordinates (Re).
      X1 = -29.5
      Y1 = -29.5
C
C     Set the step size used (Re).
      DELX = +1.
      DELY = +1.
C
C     Set the number of points used in each direction.
      NUMX = 60
      NUMY = 60
C
C     Set the radius in the XY-plane of the central hole (Re).
      HOLE = 9.
C
C     Set the maximum radius in the XY-plane to show data (Re).
      RMAX = 30.
C
C     Generate the scene (mean flux).
      DO I = 1, NUMY
        YGSM = Y1 + (I-1)*DELY
        DO J = 1,NUMX
          XGSM = X1 + (J-1)*DELX
          RNOW = SQRT(XGSM**2 + YGSM**2)
          IF((RNOW.GE.HOLE).AND.(RNOW.LE.RMAX)) THEN
            CALL CRMFLX(LUNIT,XKP,XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $        FSWIMN,FSWI95,FSWI50,FSWISD,SMOOTH1,NFLXGET,NDROPHI,
     $        NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $        FLUX95,FLUX50,FLUXSD)
            IF(INPFLX.EQ.1) THEN
              FLUX = FLUXMN
            ELSE IF(INPFLX.EQ.2) THEN
              FLUX = FLUX95
            ELSE IF(INPFLX.EQ.3) THEN
              FLUX = FLUX50
            ELSE
              WRITE(*,*)
              WRITE(*,*)' Flux output type incorrect!  INPFLX = ',INPFLX
              PAUSE
              STOP 22
            END IF
            WRITE(32,100) XGSM,YGSM,FLUX,IDLOC
          END IF
        END DO
      END DO
      CLOSE(32)
C
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Run Again?  (Y/N):'
      READ(*,1) ANS
      IF((ANS.EQ.'Y').OR.(ANS.EQ.'y')) GO TO 1000
C
1     FORMAT(A)
C
100   FORMAT(1X,2F12.4,1X,E12.4,1X,I10)
C
      STOP
      END
C
C
