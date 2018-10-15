#!/usr/bin/perl -s

$| = 1;

$::n //= 2;
while (<>) {
  chomp;
  my @w = split /\s+/;

  for (1 .. $::n) {
    my $i = int rand(@w - 1);
    my $j = $i + 1;
    @w[$i, $j] = @w[$j, $i];
  }

  print join(' ', @w) . "\n";
}


