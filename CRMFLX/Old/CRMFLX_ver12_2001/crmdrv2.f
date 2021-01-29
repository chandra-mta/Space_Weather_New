      PROGRAM CRMDRV2
C
C     Simple test driver for exercising CRMFLX.  Calculates flux at a
C     single point.
C
      INTEGER LUNIT(3),SMOOTH1,FPCHI,FPCLO
      character*1 ans
C
      LUNIT(1) = 50
      LUNIT(2) = 51
      LUNIT(3) = 52
      IUSESW = 1
      IM = 2
      FSWIMN = 1.E+3
      FSWI95 = 1.E+3
      FSWI50 = 1.E+3
      FSWISD = 1.E+3
C
      SMOOTH1 = 5
      NFLXGET = 10
      NDROPHI = 2
      NDROPLO = 2
      LOGFLG = 2
      RNGTOL = 8.0
      FPCHI = 80.0
      FPCLO = 20.0
C
      WRITE(*,*)'  CRMFLX Version 1.2 (Experimental)'
      WRITE(*,*)
      WRITE(*,*)
CC    WRITE(*,*)' Input ion species type ',
CC   $ '(proton -> 1; helium -> 2; CNO -> 3;) :'
CC    READ(*,*) ISPECI
      ISPECI = 1
C
1000  CONTINUE
      WRITE(*,*)
      WRITE(*,*)' Input Kp index (0 - 9):'
      READ(*,*) XKP
      WRITE(*,*)
      WRITE(*,*)' Input spacecraft coordinate - Xgsm, Ygsm, Zgsm (Re):'
      READ(*,*) XGSM,YGSM,ZGSM
      WRITE(*,*)
      WRITE(*,*)' Input IUSESW, IUSEMSH:'
      READ(*,*) IUSESW,IM
      IF((IUSESW.EQ.1).OR.(IUSESW.EQ.3).OR.(IM.EQ.1).OR.(IM.EQ.3)) THEN
        WRITE(*,*)
        WRITE(*,*)' Input FSWIMN, FSWI95, FSWI50, FSWISD:'
        READ(*,*) FSWIMN,FSWI95,FSWI50,FSWISD
      END IF
C
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Input Summary'
      WRITE(*,*)
      WRITE(*,100) XKP
      WRITE(*,101) XGSM
      WRITE(*,102) YGSM
      WRITE(*,103) ZGSM
      WRITE(*,104) ISPECI
      WRITE(*,105) IUSESW
      WRITE(*,110) IM
      IF((IUSESW.EQ.1).OR.(IUSESW.EQ.3).OR.(IM.EQ.1).OR.(IM.EQ.3)) THEN
        WRITE(*,106) FSWIMN
        WRITE(*,107) FSWI95
        WRITE(*,108) FSWI50
        WRITE(*,109) FSWISD
      END IF
C
      CALL CRMFLX(LUNIT,XKP,XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $        FSWIMN,FSWI95,FSWI50,FSWISD,IM,SMOOTH1,NFLXGET,NDROPHI,
     $        NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $        FLUX95,FLUX50,FLUXSD)
C
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Output Summary'
      WRITE(*,*)
      WRITE(*,200) IDLOC
      WRITE(*,201) FLUXMN
      WRITE(*,202) FLUX95
      WRITE(*,203) FLUX50
      WRITE(*,204) FLUXSD
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Run Again?  (Y/N):'
      READ(*,1) ANS
      IF((ANS.EQ.'Y').OR.(ANS.EQ.'y')) GO TO 1000
C
1     FORMAT(A)
C
100   FORMAT(1X,' XKP     = ',F12.2)
101   FORMAT(1X,' Xgsm    = ',F12.2)
102   FORMAT(1X,' Ygsm    = ',F12.2)
103   FORMAT(1X,' Zgsm    = ',F12.2)
104   FORMAT(1X,' ISPECI  = ',I12)
105   FORMAT(1X,' IUSESW  = ',I12)
110   FORMAT(1X,' IUSEMSH = ',I12)
106   FORMAT(1X,' FSWIMN  = ',I12)
107   FORMAT(1X,' FSWI95  = ',I12)
108   FORMAT(1X,' FSWI50  = ',I12)
109   FORMAT(1X,' FSWISD  = ',I12)
C
200   FORMAT(1X,' IDLOC   = ',I12)
201   FORMAT(1X,' FLUXMN  = ',1PE12.2)
202   FORMAT(1X,' FLUX95  = ',1PE12.2)
203   FORMAT(1X,' FLUX50  = ',1PE12.2)
204   FORMAT(1X,' FLUXSD  = ',1PE12.2)
C
      STOP
      END
C
C
