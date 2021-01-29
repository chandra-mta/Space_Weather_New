; convert a Chandra ephemeris file to ASCII
;
; Robert Cameron
; January 2000
;
;   Last Updata: Aug 29, 2018       TI


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

dir = ephem_dir + 'Data/'

f='PE.EPH'

jd1998 = julday(1,1,1998)
now98 = systime(1) - 883612800L
yrlen = [366,365,365,365]
fudgefactor = 0.3  ; (seconds) I need this to make CALDAT calculate times correctly

spawn,'wc -c '+dir+f,info
info=str_sep(strcompress(info(0)),' ')
;
;--- the following line is modified from info(1) to info(0)  feb. 10, 2015 (ti)
;
nbytes=long(info(0))
nrec = nbytes/2800
if nrec*2800L ne nbytes then print,'Warning!! Not an integral number of 2800-byte records in file ',f
if nrec lt 2 then print, 'Warning!! Too few 2800-byte records in file ',f

r1= read_ephemeris(dir+f,rec=0)
r2= read_ephemeris(dir+f,rec=1)
s = read_ephemeris(dir+f,rec=2)

print
print, 'File: ',dir,f
day = s.(0) mod 100
month = (s.(0)/100) mod 100
year = s.(0)/10000
if year lt 50 then year = year + 2000 else year = year + 1900
print
print,'Date of first ephemeris point (Year, Month, Day): ',year,month,day,format='(a,i4,i3.2,i3.2)'

if r1.ODB_EPHEM_START_DATE/1e4 lt 50 then $
       r1.ODB_EPHEM_START_DATE = r1.ODB_EPHEM_START_DATE + 20000000L $
  else r1.ODB_EPHEM_START_DATE = r1.ODB_EPHEM_START_DATE + 19000000L 
if r1.ODB_EPHEM_STOP_DATE/1e4 lt 50 then $
       r1.ODB_EPHEM_STOP_DATE = r1.ODB_EPHEM_STOP_DATE + 20000000L $
  else r1.ODB_EPHEM_STOP_DATE = r1.ODB_EPHEM_STOP_DATE + 19000000L 
if r1.ODB_EPHEM_EPOCH_YEAR lt 50 then $
       r1.ODB_EPHEM_EPOCH_YEAR = r1.ODB_EPHEM_EPOCH_YEAR + 2000 $
  else r1.ODB_EPHEM_EPOCH_YEAR = r1.ODB_EPHEM_EPOCH_YEAR + 1900 

print
print, 'Ephemeris Start Time (Year, DOY, SOD):',r1.ODB_EPHEM_START_DATE/1e4,$
r1.ODB_EPHEM_START_DAY_COUNT,r1.ODB_EPHEM_START_SEC_COUNT,form='(a,i5,i4.3,i6.5)'
print, 'Ephemeris Stop Time  (Year, DOY, SOD):',r1.ODB_EPHEM_STOP_DATE/1e4,$
r1.ODB_EPHEM_STOP_DAY_COUNT,r1.ODB_EPHEM_STOP_SEC_COUNT,form='(a,i5,i4.3,i6.5)'

print
print, 'Chandra Keplerian Elements: '
print
print,' Elements epoch:'
print,'   (YYYY MM DD hh mm ss.sss):',r1.ODB_EPHEM_EPOCH_YEAR,$
r1.ODB_EPHEM_EPOCH_MONTH,r1.ODB_EPHEM_EPOCH_DAY,r1.ODB_EPHEM_EPOCH_HOUR,$
r1.ODB_EPHEM_EPOCH_MIN,r1.ODB_EPHEM_EPOCH_MILLISEC/1e3,'.',r1.ODB_EPHEM_EPOCH_MILLISEC mod 1e3,$
format='(a,i5,i3.2,i3.2,i3.2,i3.2,i3.2,a,i3.3)'
print,'   (Seconds since start of 1985):',r1.ODB_EPHEM_EPOCH_TIME,form='(a,f16.3)'

;
; Bill Davis says that rate of change of RAAN is invalid in ephemeris records.
; It's approximately correct in low Earth orbit, but not the Chandra orbit.
; (due to code re-use by CSC in the OFLS).
;

r2d = 180/!dpi

print
print,' Semi-major axis (km):            ',r1.ODB_EPHEM_SMAJOR_AXIS
print,' Eccentricity:                    ',r1.ODB_EPHEM_ECCENT
print,' Inclination (deg):               ',r1.ODB_EPHEM_INCLIN*r2d
print,' Argument of Perigee (deg):       ',r1.ODB_EPHEM_PERIGEE*r2d
print,' RA of Ascending Node (deg):      ',r1.ODB_EPHEM_RAAN*r2d
print,' Mean Anomaly (deg):              ',r1.ODB_EPHEM_MEAN_ANOM*r2d
print,' True Anomaly (deg):              ',r1.ODB_EPHEM_TRUE_ANOM*r2d
print,' Arg of Perigee + True Anom (deg):',r1.ODB_EPHEM_SUM_APRGTA*r2d
print,' (approx.) Period (hours):        ',r1.ODB_EPHEM_PERIOD/100*24
print,' (approx.) Mean Motion (deg/hour):',r1.ODB_EPHEM_MEAN_MOTN*r2d*100/24
print,' (wrong) Rate of change of RA of AN (deg/day):',r1.ODB_EPHEM_RATE_ASCND*r2d*100

for i=3,nrec-1 do begin
  r=read_ephemeris(dir+f,rec=i)
  if n_tags(r) eq 10 then s=[s,r] $
    else if i lt nrec-1 then print,'Warning!! Non-Type-2 record found in wrong place in file ',f
endfor
;
; subtract 1 from ODB day-of-year (which starts at 1), to get seconds-of-year
;
valid_data = 1
openw,olun,dir+f+'.dat0',/get_lun
for i=0,n_elements(s)-1 do begin
  year = fix(s(i).ODB_EPHEM_DATE_FIRST_POINT / 10000) + 1900
  if year lt 1950 then year = year + 100
  jd = julday(1,1,year)
  doy=s(i).ODB_EPHEM_DAYS_IN_YEAR_FIRST_POINT
  sec=s(i).ODB_EPHEM_SEC_IN_DAY_FIRST_POINT
  dt=dindgen(50)*s(i).ODB_EPHEM_STEP_TIME
  px = [s(i).ODB_EPHEM_FIRST_POS_VECTOR(0),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(0,*))]*1d7
  py = [s(i).ODB_EPHEM_FIRST_POS_VECTOR(1),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(1,*))]*1d7
  pz = [s(i).ODB_EPHEM_FIRST_POS_VECTOR(2),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(2,*))]*1d7
  vx = [s(i).ODB_EPHEM_FIRST_VEL_VECTOR(0),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(3,*))]*1d7/864
  vy = [s(i).ODB_EPHEM_FIRST_VEL_VECTOR(1),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(4,*))]*1d7/864
  vz = [s(i).ODB_EPHEM_FIRST_VEL_VECTOR(2),reform(s(i).ODB_EPHEM_POS_VEL_DATA_2_50(5,*))]*1d7/864
  s1998 = (jd - jd1998 + doy - 1)*86400L + sec
  sarr = dt + s1998
  darr = doy - 1 + (dt+sec)/86400L
  fyarr = year + darr/yrlen(year mod 4)
  jdarr = darr - 0.5 + jd + fudgefactor/86400L    ; darr-0.5 puts darr on the JD time system
  caldat,jdarr,month,day,year,hour,minute,second
  minute = minute mod 60
  second = second mod 60
  if (s1998 gt now98-1e5 and s1998 lt now98+5e5) then $
    for j=0,49 do $
      if (px(j) lt 1d22 and valid_data gt 0) then $
        printf,olun, sarr(j),px(j),py(j),pz(j),vx(j),vy(j),vz(j),$
                     fyarr(j),month(j),day(j),hour(j),minute(j),second(j),$
        format='(4d16.3,3d11.3,f12.6,5(i3))' else valid_data = 0
endfor

end

