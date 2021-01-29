;+++++++++++++++++++++++++++++++++++++++++++++++++=
PRO MTA_XMM_DB
;+++++++++++++++++++++++++++++++++++++++++++++++++=

; 02. Apr 2008 BDS
; updated Aug 30, 2018      ti

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

web_dir = html_dir + 'XMM/'

xmm_7d_archive=xmm_dir+'Data/xmm_7day.archive2'

readcol,xmm_7d_archive, $ 
  time_stamp_arc,le0_arc,le1_arc,le2_arc, $
  hes0_arc,hes1_arc,hes2_arc,hec_arc, $
  format='F,F,F,F,F,F,F,F'

tlefile= tle_dir + "Data/xmm.spctrk"

readcol,tlefile,sec,yy,dd,hh,mm,ss,x_eci,y_eci,z_eci,vx,vy,vz, $
  format='L,I,I,I,I,I,F,F,F,F,F,F',skipline=5
sec=sec-8.83613e+08
time=(sec/60./60./24.)-2190.0-366.0-365.-365.-365.-366. ; 2009 days

r_eci=sqrt(x_eci^2+y_eci^2+z_eci^2)/1000.0

r_match=intarr(n_elements(time_stamp_arc))
; match xmm rates with altitude

openw,OUT,xmm_dir+"Data/mta_xmm_db.dat",/get_lun,/append

printf,OUT,"time le0 le1 le2 hes0 hes1 hes2 hec r_sec r_eci x_eci y_eci z_eci vx vy vz"

for i=0, n_elements(time_stamp_arc)-1 do begin
  diff      = abs(time_stamp_arc(i)-sec)
  b         = where(min(diff) eq diff)
  r_match(i)= n_elements(sec) ; no match found yet

  if (diff(b(0)) lt 1000.) then r_match(i)=b(0)
  print,b(0),diff(b(0)),r_eci(b(0)),r_match(i)

  if (r_match(i) lt n_elements(sec)) then begin
    print, "hello", i
    printf, OUT, $
      time_stamp_arc(i),le0_arc(i),le1_arc(i),le2_arc(i), $
      hes0_arc(i),hes1_arc(i),hes2_arc(i),hec_arc(i), $
      sec(r_match(i)),r_eci(r_match(i)), $
      x_eci(r_match(i)),y_eci(r_match(i)),z_eci(r_match(i)), $
      vx(r_match(i)),vy(r_match(i)),vz(r_match(i)), $
      format='(I12,7(" ",F15.7)," ",I12,7(" ",F15.7))'
  endif ; if r_match(i) lt n_elements(sec)) then begin
endfor ; for i=0, n_elements(sec)-1 do begin
free_lun, OUT
end
  
