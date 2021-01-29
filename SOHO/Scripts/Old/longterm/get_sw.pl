#!/usr/bin/env /proj/axaf/bin/perl -w

# Fetch monthly ACE SWEPAM and SOHO MTOF files

# Robert Cameron
# June 2003

use Net::FTP;

$odir = "/proj/rac/ops/SOHO/longterm";
$lynx = "/opt/local/bin/lynx";

# get ACE SWEPAM files

print "Fetching monthly ACE SWEPAM files:\n";
$ftp = Net::FTP->new("sec.noaa.gov") or die scalar(gmtime)." Cannot connect: $@\n";
$ftp->login() or die scalar(gmtime)." Cannot login anonymously: $!\n";
$ftp->cwd("/pub/lists/ace2") or die scalar(gmtime)." Cannot cd to /pub/lists/ace2: $!\n";
@f = $ftp->ls() or die scalar(gmtime)." Cannot get listing: $!\n";
@files = grep { /ace_swepam_1h.txt/ } @f; 
foreach ((reverse(sort(@files)))[0..2]) { $ftp->get($_,"$odir/$_") or die scalar(gmtime)." Cannot get file $_: $!\n"; print "$_\n" };

# get SOHO MTOF files

print "Fetching SOHO MTOF files:\n";
$site = "http://umtof.umd.edu/pm/crn/archive/";
$l = `$lynx -crawl -dump $site`;
@l = split "\n",$l;
@files = map { (/(CRN_\S+\.USED)/) ? $1 : () } @l; 
foreach ((reverse(sort(@files)))[0..3]) {
    $f = `$lynx -source $site/$_`;
    open (OF, ">$odir/$_") or die scalar(gmtime)." Cannot open output file $odir/$_\n";
    print OF $f;
    print "$_\n";
}
