#! /usr/bin/perl -w

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
#
#--- set directory paths
#
$rac   = $spw_dir;              #--- top Space Weather directory
$d_dir = "$ephem_dir/Data/";
$s_dir = "$ephem_dir/Scripts/";

$edir  = '/dsops/GOT/aux/DEPH.dir/';

run_main();

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------

sub run_main{
#
# find the latest (non-trivial) ephemeris file
#
    $MIN_FILE_SIZE = 100000;	                #----- Based on looking at existing ephem files


    @efiles = <$edir/DE?????.EPH>;
    @efiles = grep { m!$edir/DE[0-9]{5}.EPH! } @efiles;
    
    @date = map { substr $_,-9,5 } @efiles;
    $dm = 0;
    foreach (@date) {
        if ( $_ > $dm
	    and $_ < 90000
	    and (stat "$edir/DE$_.EPH")[7] > $MIN_FILE_SIZE) {
	    $dm = $_;
        }
    }
#
#--- process the latest ephemeris file
#
    $efile = "$edir/DE$dm.EPH";
    print "\nLatest ephemeris file: $efile\n";
    
    `cp $efile $d_dir/PE.EPH`;
    
    $output = `/usr/local/bin/idl $s_dir/ephem.idl`;
    
    print "IDL output: $output\n";
#
#--- if the file exists, rename is so that cocochan can read it
#
    `mv $d_dir/PE.EPH.dat0 $d_dir/PE.EPH.dat` if -s "$d_dir/PE.EPH.dat0";
#
#--- output of cocchan are PE.EPH.gsme and PE.EPH.gsme_in_R
#
    system("$s_dir/cocochan");
    
    remove_na();
#
#--- if the location is moved solun_eph.f must be recomplied
#
    system("$s_dir/solun_eph");
#
#---some idl funtion called by gsme_plots do not exist anymore.
#
#    system("/usr/local/bin/idl $wd/gsme_plots.idl");

}

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

sub remove_na{
    $pe_file = "$d_dir".'PE.EPH.gsme';
    open(FH, $pe_file);
    open(OUT, '> ./ztemp');
    while(<FH>){
        if($_ =~ /na/){
            next;
        }
        print OUT "$_";
    }
    close(OUT);
    close(FH);
    system("mv -f ./ztemp $pe_file");
    
    
    $per_file = "$d_dir".'PE.EPH.gsme_in_Re';
    open(FH, $per_file);
    open(OUT, '> ./ztemp');
    while(<FH>){
        if($_ =~ /na/){
            next;
        }
        print OUT "$_";
    }
    close(OUT);
    close(FH);
    system("mv -f ./ztemp $per_file");
}

