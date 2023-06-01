#!/proj/sot/ska3/flight/bin/python
import os
import sys
import re
import string
#
#--- temp writing file name
#
import time
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#-- quite often the plotting routine stack and becomes a staled process
#-- check the previous one and kill it
#
cmd = 'ps aux|grep plot_p3_data.py > ' + zspace
os.system(cmd)

with open(zspace, 'r') as f:
    data = [line.strip() for line in f.readlines()]

cmd = 'rm -rf ' + zspace
os.system(cmd)

for ent in data:
    atemp = re.split('\s+', ent)
    cmd   = 'kill -9 ' + atemp[1]
    os.system(cmd)


