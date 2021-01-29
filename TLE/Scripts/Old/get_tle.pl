#!/usr/bin/perl -w

# process TLE ephemeris files for XMM and CXO

# Robert Cameron
# June 2004

#  updated Feb 26, 2020       T. Isobe (tisobe@cfa.harvard.edu)
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
$s_dir    = $tle_dir."Scripts/";
$data_dir = $tle_dir."Data/";
#
#--- input html
#
$tle_url = "http://www.celestrak.com/NORAD/elements/science.txt";

chdir $tle_dir.'Scripts/';
#
#--- fetch the TLE data
#

@tle = `/usr/bin/lynx -source $tle_url`;
die scalar(gmtime)." No TLE data found in $tle_url\n" unless (@tle);

foreach $i (0..$#tle) { 
    $cxo = $i if ($tle[$i] =~ /^CXO\s*$/);
    $xmm = $i if ($tle[$i] =~ /^XMM/);
}
#
#--- cxo data
#
if ($cxo) {
    open (CF, ">$data_dir/cxo.tle") or die scalar(gmtime)." $0: $!\n";
    for ($cxo..$cxo+2) { print CF $tle[$_] };

    open (CF2, ">$data_dir/cxo.tle2") or die scalar(gmtime)." $0: $!\n";
    #print CF2 "2 -7200 14400 5\n";
    #print CF2 "2 -7200 28800 5\n";
    print CF2 "2 -7200 43200 5\n";

    for ($cxo+1..$cxo+2) { print CF2 $tle[$_] };
    print CF2 "0 0 0 0\n";
#
#--- xmm data
##
} else { print STDERR "$0: CXO TLE not found at $tle_url\n" };

if ($xmm) {
    open (XF, ">$data_dir/xmm.tle") or die scalar(gmtime)." $0: $!\n";
    for ($xmm..$xmm+2) { print XF $tle[$_] };

    open (XF2, ">$data_dir/xmm.tle2") or die scalar(gmtime)." $0: $!\n";
    print XF2 "2 -7200 14400 5\n";

    for ($xmm+1..$xmm+2) { print XF2 $tle[$_] };
    print XF2 "0 0 0 0\n";

} else { print STDERR "$0: XMM TLE not found at $tle_url\n" };
#
#-- run scripts
#
`rm $data_dir/cxo.spctrk; $s_dir/spacetrack  < $data_dir/cxo.tle2 >  $data_dir/cxo.spctrk`;
`rm $data_dir/xmm.spctrk; $s_dir/spacetrack  < $data_dir/xmm.tle2 >  $data_dir/xmm.spctrk`;
`rm $data_dir/cxo.j2000;  $s_dir/convert_tle.pl < $data_dir/cxo.spctrk > $data_dir/cxo.j2000`;
`rm $data_dir/xmm.j2000;  $s_dir/convert_tle.pl < $data_dir/xmm.spctrk > $data_dir/xmm.j2000`;
`$s_dir/cocoxmm`;
