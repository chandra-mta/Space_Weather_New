; plot Chandra ephemeris in GSM or GSE coordinates
; overlay the Chandra DSN contact schedule

; Robert Cameron
; June 2000
; David Morris
; Dec 2000: updated to handle new CRM_p_mn.dat format and year rollover
; RAC, March 2001: use CRM_p.dat30 file

; create a 100-year vector of day offsets from 1998
;
;   last update Feb 18, 2020        TI
;
;
;--- read directory list
;
ifile  = '/data/mta4/Space_Weather/house_keeping/dir_list'
openr, lun, ifile, /get_lun
cmd    = 'wc -l ' + ifile
spawn, cmd, xnum
xxnum  = strsplit(xnum(0),' ',/extract)
tnum   = long(xxnum(0))
lines  = strarr(tnum)
readf,lun, lines
close, lun

tnum1 = tnum - 1
for i = 0, tnum1 do begin
    xline = strsplit(lines[i], ':' ,/extract)
    cmd   = xline[1] + '=' + xline[0]
    x     = execute(cmd)
endfor

web_dir   = html_dir + 'Orbit/'


ylen = [366,365,365,365]
d98 = lonarr(100)
for i = 1,99 do d98(i) = d98(i-1) + ylen((1998 + i-1) mod 4)

; read the GSM, GSE ephemerides

;rac_arread,tle_dir+'Data/cxo.gsme',tg,r,mlat,mlon,elat,elon,fy,mon,day,hour,min,sec
rac_arread,ephem_dir+'Data/PE.EPH.gsme_sperical_short',tg,r,mlat,mlon,elat,elon,fy,mon,day,hour,min,sec
;
; --- Aug 02, 2018 (TI)
;
timeconv,tg,y,dy,h,m,s,y0=1998
y = y - 1998
d = dy + d98(y)
r = r/1e3
d0 = d98(y(0))
doy = d - d0

; read the DSN contact schedule

;filename = '/proj/rac/ops/ephem/DSN.sch'
;spawn,'wc -l '+filename,info
;info=str_sep(strcompress(info(0)),' ')
;nlines=long(info(1))
;rec = {byr:0,bot:0.0,eyr:0,eot:0.0,txt:''}
;rec=replicate(rec,nlines)
;openr,nlun,filename,/get_lun
;readf,nlun,rec
filename = comm_dir + '/Data/dsn_summary.dat'
readcol,filename,byr,botd,eyr,eotd,format='x,x,x,x,x,x,x,x,x,x,i,f,i,f', skipline=2
bot = d98(byr-1998)+botd
eot = d98(eyr-1998)+eotd
;bot = d98(rec.byr-1998) + rec.bot
;eot = d98(rec.eyr-1998) + rec.eot

; read the CRM region info, for the Kp = 3 case only

;rac_arread,'/proj/rac/ops/CRM/CRM_p_mn.dat',t,r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,k0,k1,k2,k3,k4,k5,k6,k7,k8,k9
rac_arread,crm3_dir+'/Data/CRM3_p.dat30',t,r3,fmn,f95,f50,fsd
reg1= where(r3 eq 1,nreg1)
reg2= where(r3 eq 2,nreg2)
reg3= where(r3 eq 3,nreg3)

; set up colour vectors

red = bytarr(256)+255
green = red
blue = red
red[0:6]=[0,255,0,0,0,255,255]
green[0:6]=[0,0,255,0,255,255,0]
blue[0:6]=[0,0,0,255,255,0,255]
TVLCT, red,green,blue

!x.style=1
!p.multi=[0,1,3]
!p.charsize=2
!y.omargin=[2,0]

start_JD = julday(1,0,1998)
dummy = LABEL_DATE(DATE_FORMAT='%M-%D',offset=start_JD)

plot, doy, r, ytit='Geocentric Alt. (Mm)',ymargin=[0,2],xmar=[10,10],$
  tit='Geocentric Solar Magnetospheric Coords  +  DSN Contact Schedule'
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)]-d0,[80,80],thick=4
if nreg1 gt 0 then oplot, doy(reg1),r(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, doy(reg2),r(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, doy(reg3),r(reg3),psym=3,color=5

plot, doy, mlon, yticks=5,ytickv=[-180,-90,0,90,180],xmar=[10,10],$
  yra=[-200,200],yminor=3, ytit='Longitude (deg)',ymargin=[0,0]
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)]-d0,[0,0],thick=4
if nreg1 gt 0 then oplot, doy(reg1),mlon(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, doy(reg2),mlon(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, doy(reg3),mlon(reg3),psym=3,color=5
axis,yaxis=1,yticks=5,ytickv=[-180,-90,0,90,180],$
  ytickname=['GEOTAIL','DAWN','  SUNWARD','DUSK','GEOTAIL']

plot, d, 90-mlat, ytit='Latitude (deg)',xstyle=1,ymar=[2,0],yra=[-100,100],$
  XTICKFORMAT='LABEL_DATE',xtit='UTC Date, Day of Year',xmar=[10,10],$
  yticks=3,yminor=9,ytickv=[-90,0,90]
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)],[0,0],thick=4
if nreg1 gt 0 then oplot, d(reg1),90-mlat(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, d(reg2),90-mlat(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, d(reg3),90-mlat(reg3),psym=3,color=5

out=tvrd()
WRITE_GIF, web_dir + 'Plots/GSM.gif', out,red,green,blue

plot, doy, r, ytit='Geocentric Alt. (Mm)',ymargin=[0,2],xmar=[10,10],$
  tit='Geocentric Solar Ecliptic Coords  +  DSN Contact Schedule'
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)]-d0,[80,80],thick=4
if nreg1 gt 0 then oplot, doy(reg1),r(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, doy(reg2),r(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, doy(reg3),r(reg3),psym=3,color=5

plot, doy, elon, yticks=5,ytickv=[-180,-90,0,90,180],xmar=[10,10],$
  yra=[-200,200],yminor=3, ytit='Longitude (deg)',ymargin=[0,0]
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)]-d0,[0,0],thick=4
if nreg1 gt 0 then oplot, doy(reg1),elon(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, doy(reg2),elon(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, doy(reg3),elon(reg3),psym=3,color=5
axis,yaxis=1,yticks=5,ytickv=[-180,-90,0,90,180],$
  ytickname=['GEOTAIL','DAWN','  SUNWARD','DUSK','GEOTAIL']

plot, d, 90-elat, ytit='Latitude (deg)',xstyle=1,ymar=[2,0],yra=[-100,100],$
  XTICKFORMAT='LABEL_DATE',xtit='UTC Date, Day of Year',xmar=[10,10],$
  yticks=3,yminor=9,ytickv=[-90,0,90]
for i=0,n_elements(bot)-1 do oplot, [bot(i),eot(i)],[0,0],thick=4
if nreg1 gt 0 then oplot, d(reg1),90-elat(reg1),psym=3,color=4
if nreg2 gt 0 then oplot, d(reg2),90-elat(reg2),psym=3,color=6
if nreg3 gt 0 then oplot, d(reg3),90-elat(reg3),psym=3,color=5

out=tvrd()
WRITE_GIF, web_dir + 'Plots/GSE.gif', out,red,green,blue

end
