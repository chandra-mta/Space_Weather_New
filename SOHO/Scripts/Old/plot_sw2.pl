#!/usr/bin/env /proj/sot/ska/bin/perl
#use warnings;

# Use monthly ACE SWEPAM and SOHO MTOF files
# to extrapolate solar wind into the future

# Robert Cameron
# May 2003
#
#   Last Update Feb 13, 2020        TI
#   

#from: http://quake.stanford.edu/~wso/words/Coordinates.html
#Lord Carrington determined the solar rotation rate 
#by watching low-latitude sunspots in the 1850s. 
#He defined a fixed solar coordinate system that rotates
#in a sidereal frame exactly once every 25.38 days 
#(Carrington, Observations of the Spots on the Sun, 1863, p 221, 244). 
#The synodic rotation rate varies a little during the year 
#because of the eccentricity of the Earth's orbit; 
#the mean synodic value is about 27.2753 days. 
#See the back of an Astronomical Almanac for details. 

# 27.2753 days x1 = 655 hours, x2 = 1309 hours, x3 = 1964 hours, x4 = 2618 hours

use PGPLOT;

#
#--- read pre defined directory paths
#
$dir_list = '/data/mta4/Space_Weather/house_keeping/dir_list';

open(FH, $dir_list);
while(<FH>){
    chomp $_;
    @atemp = split(':', $_);;
    $atemp[0] =~ s/^\s+|\s+$//g;
    $atemp[0] =~ s/'//g;
    $atemp[0] =~ s/"//g;

    $atemp[1] =~ s/^\s+|\s+$//g;

    ${$atemp[1]} = $atemp[0];
}
close(FH);

pgbegin (0,"$html_dir/Orbit/Plots/solwin.gif/vgif",1,5);
pgsch(2.4);

@month = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);

@dtab = ([0,0,31,60,91,121,152,182,213,244,274,305,335],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334]);

# create a 100-year hash of MJDs

@ylen = (366,365,365,365);
$d = 40586;
foreach (1970..2070) { $mjd{$_} = $d; $d += $ylen[$_ % 4] };

# get ACE SWEPAM data

open (IF, "$soho_dir/Data/swepam") or die "Cannot open input SWEPAM file\n";
@l = <IF>;
foreach (@l) {
  next unless /^20/;
  ($y,$m,$d,$hm,$mjd,$sod,$dum,$den,$spd,$dum) = split;
  $key = sprintf "%08d",$mjd*24 + $sod/3600;
  $doy = sprintf "%03d",$dtab[$y % 4][$m] + $d;
  $adate{$key} = "$y $doy $hm";
  $aden0{$key} = $den;
  $aden1{$key} = $den;
  $aspd0{$key} = $spd;
  $aspd1{$key} = $spd;
}
@ak = sort keys %adate;
$rak = $ak[-1]-$ak[0];
print "SWEPAM time range (hours) = $rak\n";

# get SOHO MTOF data

open (IF, "$soho_dir/Data/mtof") or die "Cannot open input MTOF file\n";
@l = <IF>;
foreach (@l) {
  next unless /^20/;
  ($y,$dhms,$dum,$dum,$den,$spd,$dum,$dum) = split;
  ($doy,$h,$m,$dum) = split ':',$dhms;
  $key = sprintf "%08d",($mjd{$y}+$doy)*24 + $h;
  $mdate{$key} = "$y $doy $h$m";
  $mden0{$key} = $den;
  $mden1{$key} = $den;
  $mspd0{$key} = $spd;
  $mspd1{$key} = $spd;
}
@mk = sort keys %mdate;
$rmk = $mk[-1]-$mk[0];
print "MTOF time range (hours) = $rmk\n";

# read Chandra ephemeris
#
#--- source link updated Aug 09, 2018 (TI)
#--- data input changed 02/13/20 (TI)
#
#open (IF, "$tle_dir/Data/cxo.gsme") or die "Cannot open input Chandra ephemeris file\n";
open (IF, "$ephem_dir/Data/PE.EPH.gsme_spherical") or die "Cannot open input Chandra ephemeris file\n";
@l = <IF>;
foreach (@l) {
  ($dum,$rkm,$tgsm,$pgsm,$dum,$dum,$fy,$mon,$d,$h,$min,$dum, $dum, $dum) = split;
  #next if ($min);      #--- commented out Aug 06, 2018 (TI)
  $y = int($fy);
  $h = sprintf "%02d",$h;
  $min = sprintf "%02d",$min;
  $doy = sprintf "%03d",$dtab[$y % 4][$mon] + $d;
  $key = sprintf "%08d",($mjd{$y}+$doy)*24 + $h;
  $edate{$key} = "$y $doy $h$min";
  $rkm{$key} = $rkm;
  $tgsm{$key} = $tgsm;
  $pgsm{$key} = $pgsm;
}
@ek = sort keys %edate;
$rek = $ek[-1]-$ek[0];
print "ephemeris time range (hours) = $rek\n";

# get current time, and extrapolate 30 days into the future

$ndays = 30;
$now = time;
($y,$doy) = (gmtime($now))[5,7];
$key0 = ($mjd{$y+1900}+$doy+1)*24;
for $fh (0..$ndays) { 
    ($mday,$mon,$yday) = (gmtime($now+$fh*86400))[3,4,7];
    push @doy,$yday+1;
    push @xlab,"$month[$mon] $mday";
}
for $fh (0..$ndays*24) {
    push @ddd,$fh/24;
    $key  = sprintf "%08d",$key0 + $fh;
    $key1 = sprintf "%08d",$key - 655;
    $key2 = sprintf "%08d",$key - 1309;
    $key3 = sprintf "%08d",$key - 1964;
    $key4 = sprintf "%08d",$key - 2618;
#    $adate{$key} = $ydh;
#    $mdate{$key} = $ydh;
    @aden=();
    @aspd=();
    @mden=();
    @mspd=();
    foreach (($key1,$key2,$key3,$key4)) {
	push @aden,$aden0{$_} if ($aden0{$_} and abs($aden0{$_}) < 9900);
	push @aspd,$aspd0{$_} if ($aspd0{$_} and abs($aspd0{$_}) < 9900);
	push @mden,$mden0{$_} if ($mden0{$_} and abs($mden0{$_}) < 9900);
	push @mspd,$mspd0{$_} if ($mspd0{$_} and abs($mspd0{$_}) < 9900);
    }
    push @aden0,(@aden < 1)? -9999 : $aden[0];
    push @aspd0,(@aspd < 1)? -9999 : $aspd[0];
    push @mden0,(@mden < 1)? -9999 : $mden[0];
    push @mspd0,(@mspd < 1)? -9999 : $mspd[0];

    push @aden1,(@aden < 2)? -9999 : $aden[0]*2 - $aden[1];
    push @aspd1,(@aspd < 2)? -9999 : $aspd[0]*2 - $aspd[1];
    push @mden1,(@mden < 2)? -9999 : $mden[0]*2 - $mden[1];
    push @mspd1,(@mspd < 2)? -9999 : $mspd[0]*2 - $mspd[1];
    #push @rkm,$rkm{$key}/1000; #--- replaced below Aug 06, 2018 (TI)
    push @rkm,$rkm{$key};
    push @mlat,90-$tgsm{$key};
    push @mlon,$pgsm{$key};
    push @adenu0,(@aden < 2)? -9999 : $aden[1] - $aden[0];
    push @aspdu0,(@aspd < 2)? -9999 : $aspd[1] - $aspd[0];
    push @mdenu0,(@mden < 2)? -9999 : $mden[1] - $mden[0];
    push @mspdu0,(@mspd < 2)? -9999 : $mspd[1] - $mspd[0];

    push @adenu1,(@aden < 3)? -9999 : $aden[1]*2 - $aden[2] - $aden[0];
    push @aspdu1,(@aspd < 3)? -9999 : $aspd[1]*2 - $aspd[2] - $aspd[0];
    push @mdenu1,(@mden < 3)? -9999 : $mden[1]*2 - $mden[2] - $mden[0];
    push @mspdu1,(@mspd < 3)? -9999 : $mspd[1]*2 - $mspd[2] - $mspd[0];

    if (@aden > 1) { $adens0 += ($aden[1] - $aden[0])**2; $nadens0++ };
    if (@aspd > 1) { $aspds0 += ($aspd[1] - $aspd[0])**2; $naspds0++ };
    if (@mden > 1) { $mdens0 += ($mden[1] - $mden[0])**2; $nmdens0++ };
    if (@mspd > 1) { $mspds0 += ($mspd[1] - $mspd[0])**2; $nmspds0++ };
    if (@aden > 2) { $adens1 += ($aden[1]*2 - $aden[2] - $aden[0])**2; $nadens1++ };
    if (@aspd > 2) { $aspds1 += ($aspd[1]*2 - $aspd[2] - $aspd[0])**2; $naspds1++ };
    if (@mden > 2) { $mdens1 += ($mden[1]*2 - $mden[2] - $mden[0])**2; $nmdens1++ };
    if (@mspd > 2) { $mspds1 += ($mspd[1]*2 - $mspd[2] - $mspd[0])**2; $nmspds1++ };
}
$nadens0--;
$naspds0--;
$nmdens0--;
$nmspds0--;
$nadens1--;
$naspds1--;
$nmdens1--;
$nmspds1--;
$adens = sprintf "%.1f,%.1f",sqrt($adens0/$nadens0),sqrt($adens1/$nadens1);
$aspds = sprintf "%d,%d",sqrt($aspds0/$naspds0),sqrt($aspds1/$naspds1);
$mdens = sprintf "%.1f,%.1f",sqrt($mdens0/$nmdens0),sqrt($mdens1/$nmdens1);
$mspds = sprintf "%d,%d",sqrt($mspds0/$nmspds0),sqrt($mspds1/$nmspds1);

$npt = @ddd;

$tstamp = `date`;
chomp $tstamp;

pgsci(1);
pgpage;
pgsvp(0.05,0.95,0.15,0.9);
pgswin($ddd[0], $ddd[-1], -200, 200);
pgbox('BCTS',0,0,'BCTN',0,0);
for (0..$#doy/5) { pgptxt ($_*5, -230, 0, 0.5, $doy[$_*5]) }; 
pglab ("", "degrees,Mm", "");
pgtext ($ddd[0]+13, 210, "GSM Coordinates");
pgtext ($ddd[-1]-8, 210, $tstamp);
pgsci(3);
pgline ($npt, \@ddd, \@rkm);
pgsci(2);
pgline ($npt, \@ddd, \@mlat);
pgsci(1);
pgpoint ($npt, \@ddd, \@mlon, 1);

pgsci(1);
pgpage;
pgsvp(0.05,0.95,0.1,0.95);
pgswin($ddd[0], $ddd[-1], 0, 1000);
pgbox('BCTS',0,0,'BCTN',0,0);
for (0..$#doy/5) { pgptxt ($_*5, -70, 0, 0.5, $xlab[$_*5]) };
pglab ("", "km/s", "");
pgtext ($ddd[0]+13, 1020, "Solar Wind Speed");
pgtext ($ddd[-1]-6, 1020, ". 0th order, + 1st order");
pgsci(3);
pgpoint ($npt, \@ddd, \@aspd0, 1);
pgpoint ($npt, \@ddd, \@aspd1, 2);
pgtext ($ddd[0], 1020, "ACE SWEPAM");
pgsci(2);
pgpoint ($npt, \@ddd, \@mspd0, 1);
pgpoint ($npt, \@ddd, \@mspd1, 2);
pgtext ($ddd[0]+3.5, 1020, "SOHO MTOF");

pgsci(1);
pgpage;
pgsvp(0.05,0.95,0.1,0.95);
pgswin($ddd[0], $ddd[-1], -1000, 1000);
pgbox('BCTS',0,0,'BCTN',0,0);
for (0..$#doy/5) { pgptxt ($_*5, -1130, 0, 0.5, $doy[$_*5]) }; 
pglab ("", "km/s", "");
pgtext ($ddd[0]+9, 1040, "Solar Wind Speed Uncertainty (Predicted - Measured)");
pgsci(3);
pgpoint ($npt, \@ddd, \@aspdu0, 1);
pgpoint ($npt, \@ddd, \@aspdu1, 2);
pgtext ($ddd[0], 1040, $aspds);
pgsci(2);
pgpoint ($npt, \@ddd, \@mspdu0, 1);
pgpoint ($npt, \@ddd, \@mspdu1, 2);
pgtext ($ddd[0]+2.5, 1040, $mspds);

pgsci(1);
pgpage;
pgsvp(0.05,0.95,0.1,0.95);
pgswin($ddd[0], $ddd[-1], 0, 40);
pgbox('BCTS',0.0,0,'BCTN',0.0,0);
for (0..$#doy/5) { pgptxt ($_*5, -3, 0, 0.5, $xlab[$_*5]) };
pglab ("", "p/cc", "");
pgtext ($ddd[0]+12, 41, "Solar Wind Proton Density");
pgsci(3);
pgpoint ($npt, \@ddd, \@aden0, 1);
pgpoint ($npt, \@ddd, \@aden1, 2);
pgsci(2);
pgpoint ($npt, \@ddd, \@mden0, 1);
pgpoint ($npt, \@ddd, \@mden1, 2);

pgsci(1);
pgpage;
pgsvp(0.05,0.95,0.2,0.95);
pgswin($ddd[0], $ddd[-1], -40, 40);
pgbox('BCTS',0.0,0,'BCTN',0.0,0);
for (0..$#doy/5) { pgptxt ($_*5, -46, 0, 0.5, $doy[$_*5]) }; 
pglab ("Day of Year", "p/cc", "");
pgtext ($ddd[0]+7, 42, "Solar Wind Proton Density Uncertainty  (Predicted - Measured)");
pgsci(3);
pgpoint ($npt, \@ddd, \@adenu0, 1);
pgpoint ($npt, \@ddd, \@adenu1, 2);
pgtext ($ddd[0], 42, $adens);
pgsci(2);
pgpoint ($npt, \@ddd, \@mdenu0, 1);
pgpoint ($npt, \@ddd, \@mdenu1, 2);
pgtext ($ddd[0]+2.5, 42, $mdens);

pgend;
