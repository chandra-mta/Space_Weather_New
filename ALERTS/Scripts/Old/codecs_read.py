#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

import codecs

ifile = '/proj/sot/ska/data/arc/iFOT_events/sim/2020:078:13:36:01.000.rdb'


with codecs.open(ifile, 'r', encoding='utf-8', errors='ignore') as f:
    data = [line.strip() for line in f.readlines()]

print(data)
