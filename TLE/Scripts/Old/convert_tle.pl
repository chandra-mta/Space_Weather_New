#!/usr/local/bin/perl -w

# convert TLE ephemeris files to J2000 ECI and GSM coordinates

# Robert Cameron
# July 2004

# updated Feb 10, 2015,     t. isobe (tisobe@cfa.harvard.edu)
# 
#   Last Upate: Aug 23, 2018    TI
#
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
$s_dir = $tle_dir."Scripts/";

chdir $s_dir;

# read the TLE ephemeris data from STDIN
# write the RA and Dec to STDOUT

$pi = 3.14159265359;
$r2d = 180/$pi;

@loy = qw(366 365 365 365);

@dtab = ([0,0,31,60,91,121,152,182,213,244,274,305,335],
         [0,0,31,59,90,120,151,181,212,243,273,304,334],
         [0,0,31,59,90,120,151,181,212,243,273,304,334],
         [0,0,31,59,90,120,151,181,212,243,273,304,334]);

while (<>) {
    @f = split;
    $epoch = $f[-5] + (($f[-4]-1 + $f[-3]/24 + $f[-2]/1440 + $f[-1]/86400)/$loy[$f[-5]%4]) if (/TLE EPOCH/);

    next if ($f[0] =~ /\D/ or $f[0] < 9);
    $r   = sqrt($f[6]*$f[6] + $f[7]*$f[7]);
    $r3  = sqrt($f[6]*$f[6] + $f[7]*$f[7] + $f[8]*$f[8]);
    $ra  = atan2($f[7],$f[6])*$r2d;
    $ra += 360 if ($ra < 0);
    $dec = 90 - atan2($r,$f[8])*$r2d;

    $coords    = sprintf "%11.6f%11.6f J%11.6f\n",$ra,$dec,$epoch;
    $precoords = `wcs/wcstools-3.9.5/bin/skycoor -n 6 -j -d $coords`;

    chomp $precoords;

    $precoords =~ s/J//;
    ($ra,$dec) = split ' ',$precoords;

    $x = $r3*cos($dec/$r2d)*cos($ra/$r2d);
    $y = $r3*cos($dec/$r2d)*sin($ra/$r2d);
    $z = $r3*sin($dec/$r2d);
    $fy = $f[1] + (($f[2]-1 + $f[3]/24 + $f[4]/1440 + $f[5]/86400)/$loy[$f[1]%4]);
    @dom = grep { $_ > 0 } map { $f[2] - $_ } @{$dtab[$f[1]%4]};
    printf "%12s %12.4f %12.4f %12.4f %s %12.6f%3d%3d%3d%3d%3d\n",$f[0],$x,$y,$z,$precoords,$fy,$#dom,$dom[-1],@f[3..5];
}

# /proj/ChaMP/soft/wcs/wcstools-3.3.3/bin/skycoor -j -d -n 6 @foo > foopre ; doesn't work from a coord file!
