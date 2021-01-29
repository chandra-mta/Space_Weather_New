      PROGRAM MAPXY
C
C     Simple test driver for exercising CRMFLX.  Calculates the average
C     flux in the XY plane over the specified range of Zgsm values.
C
      INTEGER LUNIT(3),SMOOTH1,FPCHI,FPCLO      
      CHARACTER*1 ANS
      CHARACTER*32 FILOUT
      REAL FLUXOUT(60,60,60)
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
      SMOOTH1 = 0
      NFLXGET = 5
      NDROPHI = 1
      NDROPLO = 1
      LOGFLG = 2
      RNGTOL = 3
      FPCHI = 80
      FPCLO = 20
C
      WRITE(*,*)'  Magnetosphere Ion XY Map '
      WRITE(*,*)
      WRITE(*,*)'  CRMFLX Version 1.0 (Alpha)'
      WRITE(*,*)
CC    WRITE(*,*)
CC    WRITE(*,*)' Input ion species type ',
CC   $ '(proton -> 1; helium -> 2; CNO -> 3;) :'
CC    READ(*,*) ISPECI
C     Tempararily Hardwired to protons only!
      ISPECI = 1
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
C     Set the start location coordinates (Re).
      X1 = -29.5
      Y1 = -29.5
      Z1 = -6.0
C
C     Set the step size used (Re).
      DELX = +1.
      DELY = +1.
      DELZ = +1.
C
C     Set the number of points used in each direction.
      NUMX = 60
      NUMY = 60
      NUMZ = 19
C
C     Set the radius in the XY-plane of the cental hole (Re).
      HOLE = 9.
C
C     Set the maximum radius in the XY-plane to show data (Re).
      RMAX = 30.
C
C     Generate the scene (mean flux).
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' - Generating the scene (mean flux) -'
      WRITE(*,*)
      DO K = 1, NUMZ
        ZGSM = Z1 + (K-1)*DELZ
        WRITE(*,*)' K, ZGSM = ',K,ZGSM
        DO J = 1, NUMY
          YGSM = Y1 + (J-1)*DELY
          DO I = 1,NUMX
            XGSM = X1 + (I-1)*DELX
            RNOW = SQRT(XGSM**2 + YGSM**2)
            IF((RNOW.GE.HOLE).AND.(RNOW.LE.RMAX)) THEN
            CALL CRMFLX(LUNIT,XKP,XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $        FSWIMN,FSWI95,FSWI50,FSWISD,SMOOTH1,NFLXGET,NDROPHI,
     $        NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $        FLUX95,FLUX50,FLUXSD)
              FLUXOUT(I,J,K) = FLUXMN
            END IF
          END DO
        END DO
      END DO
C
C     Output the scene (mean flux).
      DO J = 1, NUMY
        YGSM = Y1 + (J-1)*DELY
        DO I = 1,NUMX
          XGSM = X1 + (I-1)*DELX
          RNOW = SQRT(XGSM**2 + YGSM**2)
          IF((RNOW.GE.HOLE).AND.(RNOW.LE.RMAX)) THEN
C           Calculate the average over Z for this XY point.
            FLUXMN = 0.
            DO K = 1,NUMZ
              FLUXMN = FLUXMN + FLUXOUT(I,J,K)
            END DO
            FLUXMN = FLUXMN/FLOAT(NUMZ)
            WRITE(32,100) XGSM,YGSM,FLUXMN,IDLOC
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
