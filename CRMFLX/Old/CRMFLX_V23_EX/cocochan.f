      program cocochan

c Convert Chandra ECI linear coords to GSE, GSE coords

c Robert Cameron
c April 2001
c BDS Mar 2002

c compile and link this program as follows:
c f77 cocochan.f ./GEOPACK.f -o cocochan
c f77 cocochan.f ./GEOPACK.f ./CRMFLX_V33.f
c         -o cocochan

      integer idct(12),ios,yr,mon,d,h,min,s,doy
c      real x,y,z,vx,vy,vz,pi,re,Xgm,Ygm,Zgm,Xge,Yge,Zge
      real x,y,z,vx,vy,vz,pi,re,Xkp
      real*8 t,fy

      data pi /3.1415926535/
      data re /6371.0/
      data idct /0,31,59,90,120,151,181,212,243,273,304,334/

      open(unit=1,name='/data/mta4/proj/rac/ops/ephem/PE.EPH.dat')
      open(unit=2,name='/data/mta4/proj/rac/ops/ephem/PE.EPH.gsme')
      open(unit=3,name='/data/mta4/proj/rac/ops/ephem/PE.EPH.gsme_in_Re'
     &  )

      do 100 while (ios.eq.0)
         read(1,*,iostat=ios) t,x,y,z,vx,vy,vz,fy,mon,d,h,min,s,Xkp

c convert position to km

         x = x/1e3
         y = y/1e3
         z = z/1e3

c calculate day of year (incorrect on centuries)

         yr = int(fy)
         doy = d + idct(mon)
CCC         if (jmod(yr,4) .eq. 0 .and. mon .ge. 3) doy = doy + 1
         if (mod(yr,4) .eq. 0 .and. mon .ge. 3) doy = doy + 1

c calculate cartesian coordinates using GEOPACK 

         call recalc_08(yr,doy,h,min,s,Xgeo,Ygeo,Zgeo)
         call geigeo_08(x,y,z,Xgeo,Ygeo,Zgeo,1)
         call magsm_08(Xgeo,Ygeo,Zgeo,Xgsm,Ygsm,Zgsm,1)
c         call gsmgse_08(Xgsm,Ygsm,Zgsm,Xgse,Ygse,Zgse,1)

c convert to spherical coordinates

c         call sphcar(R,Tgsm,Pgsm,Xgsm,Ygsm,Zgsm,-1)
c         Tgsm = Tgsm * 180 / pi
c         Pgsm = Pgsm * 180 / pi
c         if (Pgsm .gt. 180) Pgsm = Pgsm - 360
c         call sphcar(Rgse,Tgse,Pgse,Xgse,Ygse,Zgse,-1)
c         Tgse = Tgse * 180 / pi
c         Pgse = Pgse * 180 / pi
c         if (Pgse .gt. 180) Pgse = Pgse - 360
         R = sqrt(x*x+y*y+z*z)
c         Rgsm = sqrt(Xgsm*Xgsm+Ygsm*Ygsm+Zgsm*Zgsm)

c convert cartesian coordinates to units of Earth radii

         Xgm = Xgsm/re
         Ygm = Ygsm/re
         Zgm = Zgsm/re
c         Xge = Xgse/re
c         Yge = Ygse/re
c         Zge = Zgse/re

      call locreg(Xkp,Xgm,Ygm,Zgm,Xtail,Ytail,Ztail,idloc)
c      if (ios.eq.0) write(2,3) t,R,Tgsm,Pgsm,Tgse,Pgse,fy,mon,d,h,min,s
      if (ios.eq.0) write(2,3) t,R,x,y,z,Xgsm,Ygsm,Zgsm,idloc
      if (ios.eq.0) write(3,4)t,Xgm,Ygm,Zgm,Xge,Yge,Zge,fy,mon,d,h,min,s
 100  continue
 3    format(f12.1,7("\t",f10.2),"\t",i1)
 4    format(f12.1,6f11.6,f12.6,5i3)

      end

      real function kpLookup(yr,mon,day,hr,min,sec)
c      look up archived Kp value for given time
c      this doesn't work
      real y,m,d,h0,h3,h6,h9,h12,h15,h18,h21
      character p0,p3,p6,p9,p12,p15,p18,p21
      integer iost
      open(unit=4,name='/data/mta/Script/Ephem/Old/KP/kp_arc.tab')
      do 200 while (iost.eq.0)
         read(4,5,iostat=iost) y,m,d,h0,p0,h3,p3,h6,p6,h9,p9,h12,p12,
     *                        h15,p15,h18,p18,h21,p21
 6       format(3I2,2X,2(4(I1,A1,1X),1X))
 5       format(3I2,2X,4(I1,A1,1X),1X,4(I1,A1,1X))
         print *, y,m,d,h0,p0
 200  continue
      kpLookup = 0
      iost = 0
      return
      end
