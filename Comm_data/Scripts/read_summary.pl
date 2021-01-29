#!/usr/bin/env perl
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


my $dsn_summ_file = "$ephem_dir/Data/dsn_summary.dmp";

my $dsn_summ = read_dsn_dump($dsn_summ_file);
foreach $pass (@{$dsn_summ}) {
    print "Pass info: \n";
    foreach (sort keys %{$pass}) {
	printf "  %-19s:  %-15s = %s\n", $_, $pass->{$_}->{label}, $pass->{$_}->{value};
    }
}

sub read_dsn_dump {
    my $file = shift;
    open(my $fh, $file) or die $!;
    local $/;
    my $dsn_dump = <$fh>;
    my $VAR1;
    eval $dsn_dump;
    die "ERROR - couldn't eval contents of $file: $@\n" if $@;
    return $VAR1;
}
