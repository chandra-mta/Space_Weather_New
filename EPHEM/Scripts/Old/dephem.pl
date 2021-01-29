#! /usr/bin/perl -w

#-------------------------------------------------------------------
#
# maintain a longterm archive of ephemeris data
#
# Robert Cameron
# March 2002
#
# This program should only extract records from the start
# of each DE files (i.e. real definitive ephemeris data).
# Consequently, the latest DE file is not processed.
#
#---- Last update: Aug 27, 2018         TI
#
#-------------------------------------------------------------------
#
#--- create a 100-year hash of seconds offsets from 1970
#
@ylen = (31622400,31536000,31536000,31536000);
$s    = 0;

foreach (1970..2070) { $soy{$_} = $s; $s += $ylen[$_ % 4] };
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

$edir = '/dsops/GOT/aux/DEPH.dir';
$wdir = "$ephem_dir/Data/longterm/";
#
#--- make hash of already processed files
#
@mefiles = <$wdir/DE/deph.???????>;
foreach (@mefiles) { $done{$_} = 1 };
#
#--- make list of available ephemeris files
#
@efiles  = <$edir/DE?????.EPH>;
@efiles1 = grep { m!$edir/DE9[0-9]{4}.EPH! } @efiles;
@efiles2 = grep { m!$edir/DE[0-8][0-9]{4}.EPH! } @efiles;
@efiles  = (@efiles1,@efiles2);
foreach (@efiles) { push @ef,$_ unless ((-s $_) < 5000) };
#
#--- process each ephemeris file, extracting only 
#--- times not covered by a future ephemeris file.
#
foreach $i (0..$#ef) {
    $date    = substr $ef[$i],-9,5;
    $y       = ($date < 90000)? 2000000 : 1900000;
    $bigdate = $y + $date;
    $of      = "$wdir/DE/deph.$bigdate";

    next if $done{$of};                     #--- don't re-process files

    last unless $ef[$i+1];                  #--- cannot extract data from the latest file

    $date    = substr $ef[$i+1],-9,5;
    $y       = ($date < 90000)? 2000000 : 1900000;
    $bigdate = $y + $date;
    $nof     = "$wdir/DE/deph.$bigdate";

    next if $done{$nof};                    #--- don't process files that have been bypassed
#    
#--- get the start time of the next ephemeris file
#
    open (EF, $ef[$i+1]) or die "Cannot open next input ephemeris file $ef[$i+1]\n";

    system("cp -f $ef[$i+1] $wdir/pedat");
    system("idl ephem_longterm.idl");

    `cat $wdir/pedat_out >> $wdir/dephem.dat`;    # this is dangerous! Could result in out-of-order data!
    system("mv $wdir/pedat_out $of");
    system("rm $wdir/pedat");
}
