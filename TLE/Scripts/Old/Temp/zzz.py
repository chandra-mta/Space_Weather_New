#!/usr/bin/env /data/mta/Script/Python3.6/envs/ska3/bin/python

#################################################################################################
#                                                                                               #
#       create_orbital_data_files.py: using the orbital elements data,                          #
#                                       create several orbital data files                       #
#                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                               #
#           last update: Feb 27, 2020                                                           #
#                                                                                               #
#################################################################################################

import sys
import os
import string
import re
import time
import math
import numpy
import Chandra.Time

import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')

from pylab import *
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines        as lines


ifile1 = './cxo_test1'
ifile2 = './cxo_test2'

ifile1 = './xmm_test1'
ifile2 = './xmm_test2'


with open(ifile1, 'r') as f:
    data1 = [line.strip() for line in f.readlines()]

with open(ifile2, 'r') as f:
    data2 = [line.strip() for line in f.readlines()]

t1 = []
x1 = []
y1 = []
z1 = []
for ent in data1:
    atemp = re.split('\s+', ent)
    t1.append((float(atemp[0]) - 1581286800) / 3600.0 )
    x1.append(float(atemp[6]))
    y1.append(float(atemp[7]))
    z1.append(float(atemp[8]))

x2 = []
y2 = []
z2 = []
for ent in data2:
    atemp = re.split('\s+', ent)
    x2.append(float(atemp[6]))
    y2.append(float(atemp[7]))
    z2.append(float(atemp[8]))


xsum = 0
ysum = 0
zsum = 0
dlen = len(x1)
for k in range(0, dlen):

    diff = abs((x1[k] - x2[k]) / x1[k])
    #print("I AM HERE: " + str(x1[k]) + '<-->' + str(x2[k]) + '<-->' + str(diff))
    xsum += diff

    diff = abs((y1[k] - y2[k]) / y1[k])
    ysum += diff

    diff = abs((z1[k] - z2[k]) / z1[k])
    zsum += diff


xavg = '%3.2f' % (100 * xsum / dlen)
yavg = '%3.2f' % (100 * ysum / dlen)
zavg = '%3.2f' % (100 * zsum / dlen)


print("DIFF: " + str(xavg) + '<-->' + str(yavg) + '<-->' + str(zavg))


plt.close('all')
mpl.rcParams['font.size'] = 10
props = font_manager.FontProperties(size=10)
plt.subplots_adjust(hspace=0.05)
ax = plt.subplot(111)

xmin = min(t1)
xmax = max(t1)

ymin = min(x1)
ymax = max(x1)
ydiff =  ymax - ymin
ymin -= 0.1 * ydiff
ymax += 0.1 * ydiff

ax0  = plt.subplot(311)
plt.plot(t1, x1, color='blue')
plt.plot(t1, x2, color='red')


ymin = min(y1)
ymax = max(y1)
ydiff =  ymax - ymin
ymin -= 0.1 * ydiff
ymax += 0.1 * ydiff

ax1  = plt.subplot(312)
plt.plot(t1, y1, color='blue')
plt.plot(t1, y2, color='red')


ymin = min(z1)
ymax = max(z1)
ydiff =  ymax - ymin
ymin -= 0.1 * ydiff
ymax += 0.1 * ydiff

ax2  = plt.subplot(313)
plt.plot(t1, z1, color='blue')
plt.plot(t1, z2, color='red')


line = ax0.get_xticklabels()
for label in line:
    label.set_visible(False)

line = ax1.get_xticklabels()
for label in line:
    label.set_visible(False)

xlabel('Time (hr)')

fig = matplotlib.pyplot.gcf()
fig.set_size_inches(5.0, 5.0)

outname = 'test.png'
#plt.tight_layout()
plt.savefig(outname, format='png', dpi=300)
plt.close('all')


