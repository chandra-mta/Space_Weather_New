      PROGRAM MSPH_Verify_V33
C
C     Simple test driver for verifying the magnetosphere database has been correctly converted from
C     ASCII to binary format.  Calculates flux at a single point.
C
      INTEGER LUNIT(3),SMOOTH1,FPCHI,FPCLO
C
      OPEN(40,FILE='MSPH_Verify.OUT',ACCESS='SEQUENTIAL',
     $  FORM='FORMATTED',STATUS='UNKNOWN')
C
C     *** INPUTS ***
C
      LUNIT(1) = 50
      LUNIT(2) = 51
      LUNIT(3) = 52
      FSWIMN = 1.E+3
      FSWI95 = 1.E+3
      FSWI50 = 1.E+3
      FSWISD = 1.E+3
CC    SMOOTH1 = 2
      SMOOTH1 = 0
      NFLXGET = 5
      NDROPHI = 1
      NDROPLO = 1
      LOGFLG = 2
      RNGTOL = 3
      FPCHI = 80
      FPCLO = 20
      ISPECI = 1
      XKP  = 3.0
      XGSM = 6.94
      YGSM = 0.72
      ZGSM = 4.54
      IUSESW  = 0
      IUSEMSH = 0
      IUSEMSP = 0
C
C     *** OUTPUTS (for comparison) ***
C
      IDLOC1  = 3
      FLUXMN1 = 2.97E+05
      FLUX951 = 8.51E+05
      FLUX501 = 1.43E+05
      FLUXSD1 = 4.47E+05
C
C
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Input Summary'
      WRITE(*,*)
      WRITE(*,*)' Magnetosphere Database Verification'
      WRITE(*,*)
      WRITE(*,100) XKP
      WRITE(*,101) XGSM
      WRITE(*,102) YGSM
      WRITE(*,103) ZGSM
      WRITE(*,104) ISPECI
      WRITE(*,105) IUSESW
      IF((IUSESW.EQ.1).OR.(IUSESW.EQ.3)) THEN
        WRITE(*,106) FSWIMN
        WRITE(*,107) FSWI95
        WRITE(*,108) FSWI50
        WRITE(*,109) FSWISD
      END IF
      WRITE(*,110) IUSEMSH
      WRITE(*,111) IUSEMSP
C
      WRITE(40,*)
      WRITE(40,*)
      WRITE(40,*)' Input Summary'
      WRITE(40,*)
      WRITE(40,*)' Magnetosphere Database Verification'
      WRITE(40,*)
      WRITE(40,100) XKP
      WRITE(40,101) XGSM
      WRITE(40,102) YGSM
      WRITE(40,103) ZGSM
      WRITE(40,104) ISPECI
      WRITE(40,105) IUSESW
      IF((IUSESW.EQ.1).OR.(IUSESW.EQ.3)) THEN
        WRITE(40,106) FSWIMN
        WRITE(40,107) FSWI95
        WRITE(40,108) FSWI50
        WRITE(40,109) FSWISD
      END IF
      WRITE(40,110) IUSEMSH
      WRITE(40,111) IUSEMSP
C
      CALL CRMFLX(LUNIT,XKP,XGSM,YGSM,ZGSM,ISPECI,IUSESW,
     $    FSWIMN,FSWI95,FSWI50,FSWISD,IUSEMSH,IUSEMSP,SMOOTH1,NFLXGET,
     $    NDROPHI,NDROPLO,LOGFLG,RNGTOL,FPCHI,FPCLO,IDLOC,FLUXMN,
     $    FLUX95,FLUX50,FLUXSD)
C
      WRITE(*,*)
      WRITE(*,*)
      WRITE(*,*)' Output Summary'
      WRITE(*,*)
      WRITE(*,*)'             True_Value     Current_Value'
      WRITE(*,200) IDLOC1,IDLOC
      WRITE(*,201) FLUXMN1,FLUXMN
      WRITE(*,202) FLUX951,FLUX95
      WRITE(*,203) FLUX501,FLUX50
      WRITE(*,204) FLUXSD1,FLUXSD
C
      WRITE(40,*)
      WRITE(40,*)
      WRITE(40,*)' Output Summary'
      WRITE(40,*)
      WRITE(40,*)'             True_Value     Current_Value'
      WRITE(40,200) IDLOC1,IDLOC
      WRITE(40,201) FLUXMN1,FLUXMN
      WRITE(40,202) FLUX951,FLUX95
      WRITE(40,203) FLUX501,FLUX50
      WRITE(40,204) FLUXSD1,FLUXSD
C
      WRITE(*,*)
      WRITE(*,*)' Output summary in file ''MSPH_Verify.OUT'''
      PAUSE  'PAUSED'
C
1     FORMAT(A)
C
100   FORMAT(1X,' XKP    = ',F12.2)
101   FORMAT(1X,' Xgsm   = ',F12.2)
102   FORMAT(1X,' Ygsm   = ',F12.2)
103   FORMAT(1X,' Zgsm   = ',F12.2)
104   FORMAT(1X,' ISPECI = ',I12)
105   FORMAT(1X,' IUSESW = ',I12)
106   FORMAT(1X,' FSWIMN = ',I12)
107   FORMAT(1X,' FSWI95 = ',I12)
108   FORMAT(1X,' FSWI50 = ',I12)
109   FORMAT(1X,' FSWISD = ',I12)
110   FORMAT(1X,' IUSEMSH= ',I12)
111   FORMAT(1X,' IUSEMSP= ',I12)
C
200   FORMAT(1X,' IDLOC  = ',I12,4X,I12)
201   FORMAT(1X,' FLUXMN = ',1PE12.2,4X,E12.2)
202   FORMAT(1X,' FLUX95 = ',1PE12.2,4X,E12.2)
203   FORMAT(1X,' FLUX50 = ',1PE12.2,4X,E12.2)
204   FORMAT(1X,' FLUXSD = ',1PE12.2,4X,E12.2)
C
      STOP
      END
C
C
