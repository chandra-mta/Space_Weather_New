; plot longterm archive of solar wind data and predictions

; Robert Cameron
; June 2003

loadcolors
!p.multi=[0,1,2]
rac_arread,'solwin.dat',y,d,hm,hrs,ad,ad0,ad1,as,as0,as1,md,md0,md1,ms,ms0,ms1,skip=15
h = hrs - hrs(0)

plot_io, h,as,/nodata, yra=[20,2000],ystyle=1,ytit='SW speed (km/s)'
ok = where(as gt 0)
oplot, h(ok),as(ok) ,color=1
ok = where(as0 gt 0)
oplot, h(ok),as0(ok),color=2
ok = where(as1 gt 0)
oplot, h(ok),as1(ok),color=3
ok = where(ms gt 0)
oplot, h(ok),ms(ok) ,color=4
ok = where(ms0 gt 0)
oplot, h(ok),ms0(ok),color=5
ok = where(ms1 gt 0)
oplot, h(ok),ms1(ok),color=6

plot_io, h,h,/nodata, yra=[0.1,10],ystyle=1,ytit='SW speed: pred/meas'
ok = where(as0 gt 0 and as gt 0)
oplot, h(ok),as0(ok)/as(ok) ,color=2
ok = where(as1 gt 0 and as gt 0)
oplot, h(ok),as1(ok)/as(ok) ,color=3
ok = where(ms0 gt 0 and ms gt 0)
oplot, h(ok),ms0(ok)/ms(ok) ,color=5
ok = where(ms1 gt 0 and ms gt 0)
oplot, h(ok),ms1(ok)/ms(ok) ,color=6

plot_io, h,ad,/nodata, yra=[0.1,100],ytit='SW density (p/s)'
ok = where(ad gt 0)
oplot, h(ok), ad(ok),color=1
ok = where(ad0 gt 0)
oplot, h(ok),ad0(ok),color=2
ok = where(ad1 gt 0)
oplot, h(ok),ad1(ok),color=3
ok = where(md gt 0)
oplot, h(ok), md(ok),color=4
ok = where(md0 gt 0)
oplot, h(ok),md0(ok),color=5
ok = where(md1 gt 0)
oplot, h(ok),md1(ok),color=6

plot_io, h,h,/nodata, yra=[0.1,10],ystyle=1,ytit='SW density: pred/meas'
ok = where(ad0 gt 0 and ad gt 0)
oplot, h(ok),ad0(ok)/ad(ok) ,color=2
ok = where(ad1 gt 0 and ad gt 0)
oplot, h(ok),ad1(ok)/ad(ok) ,color=3
ok = where(md0 gt 0 and md gt 0)
oplot, h(ok),md0(ok)/md(ok) ,color=5
ok = where(md1 gt 0 and md gt 0)
oplot, h(ok),md1(ok)/md(ok) ,color=6

end
