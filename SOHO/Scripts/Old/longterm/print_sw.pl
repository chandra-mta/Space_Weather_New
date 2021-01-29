#! /usr/bin/perl -w

# compare measured and predicted solar wind data

# Robert Cameron
# June 2003

@dtab = ([0,0,31,60,91,121,152,182,213,244,274,305,335],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334],
	 [0,0,31,59,90,120,151,181,212,243,273,304,334]);

# create a 100-year hash of MJDs

@ylen = (366,365,365,365);
$d = 40586;
foreach (1970..2070) { $mjd{$_} = $d; $d += $ylen[$_ % 4] };

# get ACE SWEPAM data

@acefiles = glob("*ace_swepam_1h.txt");
foreach (@acefiles) {
    open (IF, $_) or die "Cannot open input SWEPAM file: $_\n";
    while (<IF>) {
	next unless /^20/;
	($y,$m,$d,$hm,$mjd,$sod,$dum,$den,$spd,$dum) = split;
	$key = sprintf "%08d",$mjd*24 + $sod/3600;
	$doy = sprintf "%03d",$dtab[$y % 4][$m] + $d;
	$date{$key} = "$y $doy $hm";
	$aden{$key} = $den;
	$aspd{$key} = $spd;
    }
}

# get SOHO MTOF data

@mtofiles = glob("CRN_*.USED");
foreach (@mtofiles) {
    open (IF, $_) or die "Cannot open input SWEPAM file: $_\n";
    while (<IF>) {
	next unless /^20/;
	($y,$dhms,$dum,$dum,$den,$spd,$dum,$dum) = split;
	($doy,$h,$m,$dum) = split ':',$dhms;
	$key = sprintf "%08d",($mjd{$y}+$doy)*24 + $h;
	$date{$key} = "$y $doy $h$m";
	$mden{$key} = $den;
	$mspd{$key} = $spd;
    }
}

print "year doy hhmm hours aden aden0 aden1 aspd asp0 asp1 mden mden0 mden1 mspd msp0 msp1\n";
foreach $key (sort(keys(%date))) {
    $aden = ($aden{$key})? $aden{$key} : -9999;
    $aspd = ($aspd{$key})? $aspd{$key} : -9999;
    $mden = ($mden{$key})? $mden{$key} : -9999;
    $mspd = ($mspd{$key})? $mspd{$key} : -9999;
    $key1 = sprintf "%08d",$key - 655;
    $key2 = sprintf "%08d",$key - 1309;
    $key3 = sprintf "%08d",$key - 1964;
    @aden = ();
    @aspd = ();
    @mden = ();
    @mspd = ();
    foreach (($key1,$key2,$key3)) {
	push @aden,$aden{$_} if ($aden{$_} and abs($aden{$_}) < 9900);
	push @aspd,$aspd{$_} if ($aspd{$_} and abs($aspd{$_}) < 9900);
	push @mden,$mden{$_} if ($mden{$_} and abs($mden{$_}) < 9900);
	push @mspd,$mspd{$_} if ($mspd{$_} and abs($mspd{$_}) < 9900);
    }
    $aden0 = (@aden < 1)? -9999 : $aden[0];
    $aspd0 = (@aspd < 1)? -9999 : $aspd[0];
    $mden0 = (@mden < 1)? -9999 : $mden[0];
    $mspd0 = (@mspd < 1)? -9999 : $mspd[0];
    $aden1 = (@aden < 2)? -9999 : sprintf "%.1f",$aden[0]*2 - $aden[1];
    $aspd1 = (@aspd < 2)? -9999 : sprintf "%.1f",$aspd[0]*2 - $aspd[1];
    $mden1 = (@mden < 2)? -9999 : sprintf "%.2f",$mden[0]*2 - $mden[1];
    $mspd1 = (@mspd < 2)? -9999 : sprintf "%.2f",$mspd[0]*2 - $mspd[1];
    printf "$date{$key} $key %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f\n",
                       $aden,$aden0,$aden1,$aspd,$aspd0,$aspd1,$mden,$mden0,$mden1,$mspd,$mspd0,$mspd1;
}
