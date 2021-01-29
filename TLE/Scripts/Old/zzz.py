#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

import sys
import os
import string
import re
import time
import math
import numpy
import Chandra.Time
from astLib import astCoords

r2d    = 180.0 / math.pi

x = -16436.8379
y = -34182.9453
z = -109273.1719
epoch = 2020.14445014

epoch = 2000



r   = math.sqrt(x * x + y * y )
r3  = math.sqrt(x * x + y * y + z * z)
ra  = math.atan2(y, x) * r2d
if ra < 0:
    ra += 360.0
dec = 90.0 - math.atan2(r, z) * r2d


print("I AM HERE BEFORE: " + str(ra) + '<-->' + str(dec))

out = astCoords.convertCoords('B1950', 'J2000', ra, dec, 0.0)
print("I AM HERE --> J2000: " + str(out))

out = astCoords.convertCoords('J2000', 'B1950', ra, dec, epoch)
print("I AM HERE --> B1950: " + str(out))

coord = '%11.6f%11.6f J%11.6f' % (ra, dec, epoch)
cmd   = './wcs/wcstools-3.9.5/bin/skycoor -n 6 -j -d ' + coord + '> zspace'
os.system(cmd)

with open('zspace', 'r') as f:
    out = f.read()

print("I AM HERE 2: " + str(out))
