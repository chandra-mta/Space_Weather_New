#! /usr/bin/perl -w

# Fetch the monthly ACE SWEPAM and SOHO MTOF files

# Robert Cameron
# May 2003
#
#   Last Update Sep 06, 2018        TI

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

$odir = "$soho_dir/Data";

$lynx = "/usr/bin/lynx";

$site1 = "ftp://"."$noaa_ftp"."ace2/";
$site2 = "http:/"."$umd_site"."crn/archive/";
$site3 = "http:/"."$umd_site"."pmsw_2week.used";

# get ACE SWEPAM files

print "Fetching monthly ACE SWEPAM files:\n";
$l = `$lynx -crawl -dump $site1`;
@l = split / /,$l;
@f = grep /_ace_swepam_1h.txt/, @l;
open (OF, ">$odir/swepam") or die "Cannot open output file $odir/swepam\n";
foreach ((sort(@f))[-4..-1]) {
    $f = `$lynx -source $site1/$_`;
    open (OFF, ">$odir/longterm/$_") or die "Cannot open output file $odir/longterm/$_\n";
    print OFF $f;
    print OF $f;
    print "   $_\n";
}

# get SOHO MTOF files

print "Fetching SOHO MTOF files:\n";
$l = `$lynx -crawl -dump $site2`;
@l = split "\n",$l;
@f = map { (/(CRN_\S+\.USED)/) ? $1 : () } @l; 

open (OF, ">$odir/mtof") or die "Cannot open output file $odir/mtof\n";

foreach ((sort(@f))[-6..-1]) {
    $f = `$lynx -source $site2/$_`;
    open (OFF, ">$odir/longterm/$_") or die "Cannot open output file $odir/longterm/$_\n";
    print OFF $f;
    print OF $f;
    print "   $_\n";
}

$f = `$lynx -source $site3`;
print OF $f;
print "   pmsw_2week.used\n";
