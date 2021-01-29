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

system("$soho_dir/Scripts/get_sw.pl"); 
system("$soho_dir/Scripts/plot_sw2.pl");
