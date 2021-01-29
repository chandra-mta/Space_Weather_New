#!/usr/bin/perl 

#---------------------------------------------------------------------
#
#   convrt_to_fphist.perl:  convert FPHIST-2001.dat to the format
#                           used by crmpl2.pro
#
#       author: t. isobe    (tisobe@cfa.harvard.edu)
#       last update:    Aug 13, 2018
#
#---------------------------------------------------------------------

$input = `cat /proj/sot/acis/FLU-MON/FPHIST-2001.dat`;
@flist = split(/\n+/, $input);
open(OUT, ">../Data/fphist.dat");

foreach $ent (@flist){
    @atemp = split(/\s+/, $ent);
    $cnt   = @atemp;
    if($cnt < 3){
        next;
    }
    @btemp = split(/:/, $atemp[0]);
    foreach $out (@btemp){
        print OUT "$out ";
    }

    if($atemp[1] =~ /HRC-I/){
        print OUT  "\t12\t";

    }elsif($atemp[1] =~ /HRC-S/){
        print OUT "\t11\t";

    }elsif($atemp[1] =~ /ACIS-I/){
        print OUT "\t2\t";

    }else{
        print OUT "\t1\t";
    }

    print OUT "$atemp[2]\n";
}
close(OUT);


