#!/proj/sot/ska3/flight/bin/perl
#/usr/bin/env /proj/sot/ska/bin/perl

# --8<--8<--8<--8<--
#
# Copyright (C) 2006 Smithsonian Astrophysical Observatory
#
# This file is part of yaxx
#
# yaxx is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# yaxx is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the 
#       Free Software Foundation, Inc. 
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA
#
# -->8-->8-->8-->8--

#####################################################################################
#
# dsn_summary.pl
#
# Take information from arc (replan central) output concerning comm schedule and
# make a pretty output for use by SOT
#
#       Last Update: Aug 09, 2018       TI
#
#####################################################################################

#use strict;
use warnings;

use Chandra::Time;
use Ska::HashTable;
use IO::All;
use Carp;
use Data::Dumper;
use Getopt::Long;
use POSIX qw(strftime);
use Getopt::Long;
use Data::DumpXML qw(dump_xml);
use YAML ();

# Type Description        TStart (GMT)    TStop (GMT)     PASSPLAN.bot    PASSPLAN.eot    
# PASSPLAN.station        PASSPLAN.config PASSPLAN.site   PASSPLAN.sched_support_time
# PASSPLAN.activity       PASSPLAN.lga    PASSPLAN.soe

$Data::Dumper::Sortkeys = 1;

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

my %opt = (max_age => 1,
	   out_dir => "$comm_dir/Data/",
	   dsn_type => 'DSN_COMM',  # or PASSPLAN
	  );

my $ok = GetOptions(\%opt,
		    'test!',
		    'max_age=f',
		    'out_dir=s',
		    'dsn_type=s',
		    'help!',
		   );
croak "GetOptions failed" unless $ok;

help() if $opt{help};

my @dsn_records;		# Records of DSN data
my %dsn_records;

my @output = ( { field  => 'sched_support_time',
		 format => '%-15s',
		 label  => 'Support (GMT)'
	       },
	       { field  => 'bot',
		 format => '%04d',
		 format_label => '%-4s',
		 label  => 'BOT'
	       },
	       { field  => 'eot',
		 format => '%04d',
		 format_label => '%-4s',
		 label  => 'EOT'
	       },
	       { field  => 'activity',
		 format => '%-10s',
		 label  => 'Activity',
		 verbose   => 1,
	       },
	       { field  => 'soe',
		 format => '%-4s',
		 label  => 'SOE',
		 verbose   => 1,
	       },
	       { field  => 'station',
		 format => '%-9s',
		 label  => 'Station'
	       },
	       { field  => 'site',
		 format => '%-9s',
		 label  => 'Site'
	       },
	       { field  => 'lga',
		 format => '%4s',
		 label  => 'LGA',
		 verbose => 1,
	       },
	       { field  => 'track_local',
		 format => ' %-25s',
		 label  => 'Track time (local)'
	       },
	       { field  => 'bot_year_day',
		 format => ' %-13s',
		 label  => 'BOT year'
	       },
	       { field  => 'eot_year_day',
		 format => ' %-13s',
		 label  => 'EOT year'
	       },
	       { field  => 'bot_date',
		 format => ' %-13s',
		 label  => 'BOT date',
		 verbose=> 1,
	       },
	       { field  => 'eot_date',
		 format => ' %-13s',
		 label  => 'EOT date',
		 verbose=> 1,
	       },
	       { field  => 'bot_time',
		 format => ' %-13s',
		 label  => 'BOT time',
		 verbose=> 1,
	       },
	       { field  => 'eot_time',
		 format => ' %-13s',
		 label  => 'EOT time',
		 verbose=> 1,
	       },
	     );

my $max_file_age_seconds = $opt{max_age} * 24 * 3600; # Allow iFOT file to be max_age days old
my $time_conv = Chandra::Time->new();  # Generic time converter

my $date;
eval { GetOptions("date=s", \$date) } or croak "ERROR - GetOptions failed\n";
my $current_time = defined $date ? $time_conv->unix($date) : time;

my $comm;
my @comm_file = sort glob("$ENV{SKA}/data/arc/iFOT_events/comm/????:???:??:??:??*.rdb");
#print "@comm_file\n";
my $out_file = "dsn_summary.dat";

# @output = grep { not $_->{verbose} } @output;

croak "ERROR - no comm iFOT events files found\n" unless @comm_file;

# Take the most recent comm file and check that it is actually recent using
# the file name
my $comm_file = $comm_file[-1];
(my $comm_file_date = io($comm_file)->filename) =~ s/\.rdb//;

unless ($current_time - $time_conv->unix( $comm_file_date ) < $max_file_age_seconds) {
    my $msg = "ERROR - most recent comm iFOT file $comm_file is too old\n";
    $opt{test} ? print $msg : croak $msg;
}

# Read the most recent comm file
eval { $comm = Ska::HashTable->new($comm_file) };
croak "ERROR - could not read comm iFOT file $comm_file: $@\n" if ($@);

my %track_unix;
my %track_year;
while (my %comm = $comm->row()) {
    s/^\s+|\s+$//g for (values %comm); # Clean leading/trailing whitespace

    # Convert BOT and EOT to local time and date.  Since we only have hour and min for
    # each of these, need some gymnastics to get it right.  

    my $support_tstart_date = $comm{'TStart (GMT)'};
    my $support_tstart_unix = $time_conv->unix( $support_tstart_date );
    my ($support_tstart_year, $support_tstart_doy) =
      ($support_tstart_date =~ /\A (\d{4}) : (\d{3}) :/x);

    # Convert BOT and EOT to unix times, assuming the year and DOY for support start.
    # If this doesn't make sense, then the BOT/EOT times must be for the next DOY.
    for my $track (qw(bot eot)) {
	my ($hour, $min) = (sprintf("%04d", $comm{"$opt{dsn_type}.$track"}) =~ /(\d\d)(\d\d)/);
	my $unix = $time_conv->unix("$support_tstart_year:$support_tstart_doy:$hour:$min:00");
	$unix += 24*60*60+2 if ($unix < $support_tstart_unix); # Allow for possible leap second
	$track_unix{$track} = $unix;
	$comm{"${track}_year_day"} = time_to_year_day_frac($unix);
	$comm{"${track}_date"} = Chandra::Time->new($unix, {format => 'unix'})->date;
	$comm{"${track}_time"} = $unix;
    }
    
    # Output BOT/EOT as: 1130-1230 EDT, Fri 22 Sep
    my $bot_local      = strftime("%H%M",         localtime($track_unix{bot}));
    my $bot_info_local = strftime("%Z, %a %e %b", localtime($track_unix{bot}));
    my $eot_local      = strftime("%H%M",         localtime($track_unix{eot}));
    $comm{track_local} = sprintf("%s-%s %s", $bot_local, $eot_local, $bot_info_local);

    my %dsn_record;
    foreach my $output (@output) {
	my $field = $comm{ $output->{field} } || $comm{ "$opt{dsn_type}." . $output->{field} };
	my $value = sprintf($output->{format}, $field);
	$value =~ s/^ \s+ | \s+ $//xg; # Clean leading/trailing whitespace
	$dsn_record{ $output->{field} } = {  value => $value,
					     label => $output->{label},
					  };
    }
    push @dsn_records, \%dsn_record;
    $dsn_records{ $dsn_record{sched_support_time}{value} } = \%dsn_record;
}

# Generate the formatted DSN summary table
my $out;
foreach my $dsn_record ('label', 'dashes', @dsn_records) {
    foreach my $output (@output) {
	next if $output->{verbose};
	my $field = $output->{field};
	my $format = $output->{format_label} || $output->{format};
	my $value;
	if (ref($dsn_record) eq 'HASH') {
	    $value = $dsn_record->{$field}{value};
	} elsif ($dsn_record eq 'label') {
	    $value = $output->{label};
	} elsif ($dsn_record eq 'dashes') {
	    if ($output->{format} =~ /(\d+)/) {
		my $width = $1;
		$value = '-' x $width;
	    } else {
		($value = $output->{label}) =~ s/./-/g;
	    }
	}
	$out .= sprintf($format . ' ', $value);
    }
    $out .= "\n";
}

my %store = ( text => { value => $out,
			ext   => 'dat',
		      },
	      dump => { value => Dumper(\@dsn_records),
			ext   => 'dmp',
		      },
	      xml  => { value => dump_xml(@dsn_records),
			ext   => 'xml',
		      },
	      yaml  => { value => YAML::Dump(\@dsn_records),
			ext   => 'yaml',
		      }
	    );

# Remove non-ascii characters (typically <AO> in LGA field).  Only
# do this for YAML to ensure back-compatibility.
$store{yaml}->{value} =~ s/[^[:ascii:]]//g;

# Generate output files
foreach my $out_dir (split ':', $opt{out_dir}) {
    foreach my $store (values %store) {
	    my $file = "$out_dir/dsn_summary." . $store->{ext};
	    eval { $store->{value} > io($file)->assert };
	    croak "ERROR - could not write DSN schedule to $file: $@\n" if $@;
	    print $store->{value} if $opt{test};
    }
}

sub time_to_year_day_frac {
    my $time = $_[0];
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday) = gmtime($time);
    return sprintf("%4d %7.3f",
		   $year+1900,
		   $yday+1 + ($hour+$min/60+$sec/3600) / 24);
}

sub help
{
  my $verbose = @_ ? shift : 2;

  require Pod::Usage;
  Pod::Usage::pod2usage ( { -exitval => 0, -verbose => $verbose } );
}

=head1 NAME

dsn_summary.pl - Generate summary of near-term Chandra DSN schedule

=head1 SYNOPSIS

dsn_summary.pl [-test] [-max_age <value>] [-out_dir <dir_list>] [-help]

=head1 OPTIONS

=over 8

=item B<-test>

Run in test mode

=item B<-max_age> <value>

Maximum allowed age (days) for comm pass data file.  This is to prevent accidentally
using an out-of-date file.

=item B<-out_dir> <dir_list>

List of directories in a pathname format (i.e. separated by ':') to which the output
DSN summary files will be written.

=item B<-help>

Print this usage and exit.

=back

=head1 DESCRIPTION

B<dsn_summary.pl> uses DSN comm pass information derived from iFOT to generate a summary of 
the Chandra DSN schedule within +/- 3 days.  The summary data are written out in three formats
in the directories given by out_dir:
  
 Text : Human reading text table - dsn_summary.dat
 Dump : Perl Data::Dumper format - dsn_summary.dmp
 XML  : Data::DumpXML format     - dsn_summary.xml

=head1 EXAMPLE

 dsn_summary.pl -out_dir /proj/sot/ska/data/dsn_summary:/proj/rac/ops/ephem

=head1 USAGE

This tool is intended to be run as a regular cron job, e.g. using task_schedule:

 /proj/sot/ska/bin/task_schedule.pl -config /proj/sot/ska/data/dsn_summary/task_schedule.cfg

=head1 AUTHOR

Tom Aldcroft


