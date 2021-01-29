      program runcrm

c     calculate CRM proton flux for Chandra ephemeris
c     read from a file, for all 28 possible values of Kp.

c     compile and link as follows:
c     f77 -C -ftrap=%all,no%inexact runcrm.f ./CRMFLX_V33.f -o runcrm

c     Robert Cameron
c     September 2002

      implicit none

      integer lunit(3),ispeci,iusesw,smooth1,nflxget,ndrophi,ndroplo
      integer iusemsh,iusemsp,logflg,mon,d,h,m,s,i,j,iv,idloc,ios
      integer fpchi,fpclo
      real xkp,xgsm,ygsm,zgsm,xgse,ygse,zgse,xg(3000),yg(3000),zg(3000)
      real fswimn,fswi95,fswi50,fswisd,fluxmn,flux95,flux50,fluxsd
      real rngtol
      real*8 t,tg(3000),fyr
      character*2 fext(28)

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
      ispeci = 1
      iusesw = 1
      iusemsh = 2
      iusemsp = 0
      smooth1 = 4
      nflxget = 10
      ndrophi = 2
      ndroplo = 2
      logflg = 2
      rngtol = 4.0
      fpchi = 80
      fpclo = 20

      fswimn = 0.0
      fswi95 = 0.0
      fswi50 = 0.0
      fswisd = 0.0

c     read in the ephemeris data

      open(unit=1,name=
     & '/data/mta4/proj/rac/ops/ephem/PE.EPH.gsme_in_Re')
      iv = 0
      ios = 0
      do while (ios.eq.0)
         iv = iv + 1
         read(1,*,iostat=ios)
     $      t,xgsm,ygsm,zgsm,xgse,ygse,zgse,fyr,mon,d,h,m,s
         tg(iv) = t
         xg(iv) = xgsm
         yg(iv) = ygsm
         zg(iv) = zgsm
      end do
      iv = iv - 1 

      do i = 1,28
        xkp = (i-1)/3.0
        open(unit=2,name='/data/mta4/proj/rac/ops/CRM3/CRM3_p.dat'//fext&
     &(i))
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
