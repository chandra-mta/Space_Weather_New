      program runcrm

c     calculate CRM proton flux for Chandra ephemeris
c     read from a file, for all 28 possible values of Kp.

c     compile and link as follows:
c     f77 -C -ftrap=%all,no%inexact runcrm.f ./CRMFLX_V33.f -o runcrm

c     Robert Cameron
c     September 2002
c
c       Last update: feb 12, 2020     TI
c
c       gfortran -std=legacy -ffixed-form -fd-lines-as-comments
c                           -ffixed-line-length-none runcrm_test.f
c               /data/mta4/Space_Weather/CRMFLX/CRMFLX_V33/CRMFLX_V33.f -o runcrm_v33
c       (suggested by lina Jul 18, 2019)

      implicit none

      integer lunit(3),ispeci,iusesw,smooth1,nflxget,ndrophi,ndroplo
c      integer iusemsh,iusemsp,logflg,mon,d,h,m,s,i,j,iv,idloc,ios
      integer iusemsh,iusemsp,logflg,i,j,iv,idloc,ios
      integer fpchi,fpclo,lid
      real xkp,xgsm,ygsm,zgsm,xgse,ygse,zgse,xg(30000),yg(30000),zg(30000)
      real fswimn,fswi95,fswi50,fswisd,fluxmn,flux95,flux50,fluxsd
      real mon,d,h,m,s,kp
      real rngtol
      real*8 t,tg(30000),fyr
      character*2 fext(28), sp

      data fext /'00','03','07','10','13','17','20','23','27',
     $           '30','33','37','40','43','47','50','53','57',
     $           '60','63','67','70','73','77','80','83','87','90'/

c     set CRM input parameters:
c       - proton species.
c       - use CRM databases for magnetosphere and magnetosheath.
c       - do not add external solar wind flux to any of SW, MSH, MSP.
c       - spike rejection and near neighbour smoothing.
c       - linear flux averaging.

      data lunit /50,51,52/
      ispeci  = 1
      iusesw  = 1
      iusemsh = 2
      iusemsp = 0
      smooth1 = 4
      nflxget = 10
      ndrophi = 2
      ndroplo = 2
      logflg  = 2
      rngtol  = 4.0
      fpchi   = 80
      fpclo   = 20

      fswimn  = 0.0
      fswi95  = 0.0
      fswi50  = 0.0
      fswisd  = 0.0

c     read in the ephemeris data

      open(unit=1,file=
     $ '/data/mta4/Space_Weather/EPHEM/Data/PE.EPH.gsme_in_Re_short')
      iv = 0
      ios = 0
c      do while (ios.eq.0)
      do 
         iv = iv + 1
c         read(1,*,iostat=ios)
         read(1,*,end=10)
     $      t,xgsm,ygsm,zgsm,xgse,ygse,zgse,fyr,mon,d,h,m,kp,lid
         tg(iv) = t
         xg(iv) = xgsm
         yg(iv) = ygsm
         zg(iv) = zgsm
      end do
   10 close (1)
      iv = iv - 1 

      do i = 1,28
        xkp = (i-1)/3.0
        open(unit=2,file=
     $ '/data/mta4/Space_Weather/CRM3/ver12/CRM3_p.dat'//fext(i))
        do j = 1,iv
          call crmflx(lunit,xkp,xg(j),yg(j),zg(j),ispeci,iusesw,
     $                fswimn,fswi95,fswi50,fswisd,iusemsh,iusemsp,
     $                smooth1,nflxget,ndrophi,ndroplo,logflg,rngtol,
     $                fpchi,fpclo,idloc,fluxmn,flux95,flux50,fluxsd)
          write(2,1) tg(j),idloc,fluxmn,flux95,flux50,fluxsd
        end do
        close(unit=2)
      end do
 1    format(f13.1,i2,4e13.6)

      end
