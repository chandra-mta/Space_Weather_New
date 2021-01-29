; IDL Version 7.0.6, Solaris (sunos sparc m64)
; Journal File for mta@rhodes
; Working directory: /data/mta4/www/alerts
; Date: Thu Mar 10 15:09:25 2011
 
readcol,'/proj/sot/ska/data/arc/iFOT_events/comm/2011:069:20:06:00.000.rdb',in,format='a',skipline=2
print,in(0)
;DSN
readfmt,'/proj/sot/ska/data/arc/iFOT_events/comm/2011:069:20:06:00.000.rdb',in,format='a',skipline=2
; % Keyword FORMAT not allowed in call to: READFMT
readcol,'/proj/sot/ska/data/arc/iFOT_events/comm/2011:069:20:06:00.000.rdb',in,format='a',skipline=2,delimiter="XXX"
print,in(0)
;DSN Comm Time 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 DSS-65 N064 MADRID 066/2045-2300 TKG PASS   O
print,strjoin(strsplit(in(0),"\t",/extract,/regexp),"+")
; % Keyword REGEXP not allowed in call to: STRTOK
print,strjoin(strsplit(in(0),"\t",/extract,/regex),"+")
;DSN Comm Time 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 DSS-65 N064 MADRID 066/2045-2300 TKG PASS   O
print,strjoin(strsplit(in(0),"	",/extract),"+")
;DSN Comm Time 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 DSS-65 N064 MADRID 066/2045-2300 TKG PASS   O
print,strjoin(strsplit(in(0)," ",/extract),"+")
;DSN+Comm+Time+2011:066:20:45:00.000+2011:066:23:00:00.000+2145+2245+DSS-65+N064+MADRID+066/2045-2300+TKG+PASS+ +O
print,strjoin(strsplit(in(0),"[\t]",/extract,/regex),"+")
;DSN Comm Time 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 DSS-65 N064 MADRID 066/2045-2300 TKG PASS   O
x=rdrdb("/pool14/brad/grat")
; % CREATE_STRUCT: Illegal tag name: TStart(GMT).
; % REPLICATE: Variable is undefined: STRUCT.
x=rdrdb("/pool14/brad/grat",/noheader)
; % CREATE_STRUCT: Incorrect number of arguments.
; % REPLICATE: Variable is undefined: STRUCT.
findpro,'rdb_read'
; Procedure rdb_read found in directory  /data/swolk/idl_libs/mit/ddidl/useful/
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type Description TStart (GMT) TStop (GMT) GRATING.GRATING
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;Type Description TStart (GMT) TStop (GMT) OBS.TARGET OBS.MODE OBS.OBSID OBS.SI TARGET_CAL.OBSID
;TARGET_CAL.TARGET
;S S S S S S S S S
; % Syntax error.
; % Attempt to call undefined procedure/function: 'RDB_STRUCTTEMP'.
print,strjoin(strsplit(in(0),STRING(9B),/extract),"+")
; % Variable is undefined: IN.
readcol,'/proj/sot/ska/data/arc/iFOT_events/comm/2011:069:20:06:00.000.rdb',in,format='a',skipline=2,delimiter="XXX"
print,strjoin(strsplit(in(0),STRING(9B),/extract),"+")
;DSN Comm Time 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 DSS-65 N064 MADRID 066/2045-2300 TKG PASS   O
.run rdb_read
; % Syntax error.
; % Type of end does not match statement (END expected).
; % 2 Compilation error(s) in module RDB_READ.
; % Return statement in procedures can't have values.
; % Return statement in procedures can't have values.
; % Return statement in procedures can't have values.
; % Return statement in procedures can't have values.
; % Return statement in procedures can't have values.
; % 5 Compilation error(s) in module $MAIN$.
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
; % Variable is undefined: STR_SPLIT.
findpro,'rdrdb'
; % FINDPRO: Procedure rdrdb not found in a !PATH directory.
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
; % Variable is undefined: STR_SPLIT.
retall
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
; % Variable is undefined: STR_SPLIT.
findpro,strsplit
; % FINDPRO: ERROR - First parameter (.pro name) must be a scalar string
findpro,'strsplit'
; Procedure strsplit found in directory  /usr/local/rsi/idl/lib/
retall
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
; % Attempt to subscript COL_READ with COL is out of range.
retall
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;           0            0            0            0            0            0            0            0
;           0
;S S S S S S S S S
; % Syntax error.
; % Attempt to call undefined procedure/function: 'RDB_STRUCTTEMP'.
findpro,'rdb_structtemp'
; Procedure rdb_structtemp found in directory  /data/mta4/www/alerts/
; Procedure rdb_structtemp found in directory  /data/swolk/idl_libs/mit/ddidl/marx/
; Procedure rdb_structtemp found in directory  /data/swolk/idl_libs/mit/ddidl/meta/
; Procedure rdb_structtemp found in directory  /data/swolk/idl_libs/mit/ddidl/caldb/
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;           0            0            0            0
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;           0            0            0            0
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
retall
.run rdb_read
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type Description TStart (GMT) TStop (GMT) GRATING.GRATING
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
print,strjoin(strsplit(in(0),"STRING(9B)",/extract),"+")
;D+ Comm +ime 2011:066:20:45:00.000 2011:066:23:00:00.000 2145 2245 D+-65 +064 MAD+D 066/2045-2300 +K+ PA+   O
reatll
; % Attempt to call undefined procedure/function: 'REATLL'.
retall
.run rdb_read
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type Description+TStart (GMT)+TStop (GMT)+GRATING.GRATING
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
rdb_struct_defn = {Type Description:'', TStart (GMT):'', TStop (GMT):'', GRATING.GRATING:''}
; % Syntax error.
rdb_struct_defn = {Type:'', TStart:'', TStop:'', GRATING.GRATING:''}
; % Syntax error.
rdb_struct_defn = {Type:'', TStart:'', TStop:'', GRATING:''}
name="Type Description"
split=strsplit(name)
print, split(0)
;           0
retall
.run rdb_read
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type+TStart+TStop+GRATING.GRATING
;S S S S
; % Syntax error.
;rdb_read: EXECUTE failed for structure definition.
retall
.run rdb_read
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type+TStart+TStop+GRATING
;S S S S
print,x.Type
;Grating Moves Grating Moves Grating Moves Grating Moves
print,x(1).Type
;Grating Moves
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;Type+TStart+TStop+OBS+OBS+OBS+OBS+TARGET_CAL+TARGET_CAL
;S S S S S S S S S
; % Conflicting or duplicate structure tag definition: OBS.
;rdb_read: EXECUTE failed for structure definition.
retall
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;Type+TStart+TStop+OBS_TARGET+OBS_MODE+OBS_OBSID+OBS_SI+TARGET_CAL_OBSID+TARGET_CAL_TARGET
;S S S S S S S S S
retall
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;Type_Description+TStart_(GMT)+TStop_(GMT)+OBS_TARGET+OBS_MODE+OBS_OBSID+OBS_SI+TARGET_CAL_OBSID+TARGET_CAL_TARGET
;S S S S S S S S S
; % Syntax error.
retall
.run rdb_read
x=rdb_read("/pool14/brad/2011:069:20:06:00.000.rdb")
;File /pool14/brad/2011:069:20:06:00.000.rdb has           31 lines
;Type_Description+TStart_GMT+TStop_GMT+OBS_TARGET+OBS_MODE+OBS_OBSID+OBS_SI+TARGET_CAL_OBSID+TARGET_CAL_TARGET
;S S S S S S S S S
x=rdb_read("/pool14/brad/grat")
;File /pool14/brad/grat has            6 lines
;Type_Description+TStart_GMT+TStop_GMT+GRATING_GRATING
;S S S S
findpro,'rdb_read'
; Procedure rdb_read found in directory  /data/mta4/www/alerts/
; Procedure rdb_read found in directory  /data/swolk/idl_libs/mit/ddidl/useful/
