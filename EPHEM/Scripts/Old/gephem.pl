#! /usr/bin/perl -w

# interpolate from the ephemeris file

# Robert Cameron
# November 1999
#
#   Last Update: Aug 08, 2018   TI
#

$t1998 = time - 883612800;

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

$inf  = "$ephem_dir/Data/PE.EPH.dat";
$outf = "$ephem_dir/Data/gephem.dat";

open EF, $inf or exit 0;

$d2 = <EF>;
while (<EF>) {
    @d1 = split;
    last if ($d1[0] > $t1998);
    $d2 = $_;
}

@d2 = split ' ',$d2;
$r1 = sqrt($d1[1]**2 + $d1[2]**2 + $d1[3]**2)/1e3;
$r2 = sqrt($d2[1]**2 + $d2[2]**2 + $d2[3]**2)/1e3;
$leg = ($r1 > $r2)? "A" : "D";
print "$d1[0] $d2[0]\n";
$ft = ($t1998 - $d1[0])/($d2[0]-$d1[0]);
$x  = $d1[1] + ($d2[1]-$d1[1])*$ft;
$y  = $d1[2] + ($d2[2]-$d1[2])*$ft;
$z  = $d1[3] + ($d2[3]-$d1[3])*$ft;
$vx = $d1[4] + ($d2[4]-$d1[4])*$ft;
$vy = $d1[5] + ($d2[5]-$d1[5])*$ft;
$vz = $d1[6] + ($d2[6]-$d1[6])*$ft;
$r = $r1 + ($r2-$r1)*$ft;

$l = sprintf "%7d %s %16.3f%16.3f%16.3f%16.3f%16.3f%16.3f%16.3f\n",
        $r,$leg,$t1998,$x,$y,$z,$vx,$vy,$vz;

sleep 30;  # to prevent datafile timing conflicts with other scripts

open(OF,">$outf") or die "Cannot create $outf\n";
print OF $l;
