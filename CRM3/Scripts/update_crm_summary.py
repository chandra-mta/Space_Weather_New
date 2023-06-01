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

#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    os.system('mkdir -p TestOut')
    test_out = os.getcwd() + '/TestOut'

f    = open('/data/mta4/www/RADIATION_new/CRM/CRMsummary.dat', 'r')
line = f.read()
f.close()

f    = open('/data/mta4/Space_Weather/house_keeping/crm_summary_html_template', 'r')
html = f.read()

html = html.replace("#TEXT#", line)

outfile = '/data/mta4/www/RADIATION_new/CRM/CRMsummary.html'
#for writing out files in test directory
if (os.getenv('TEST') == 'TEST'):
    outfile = test_out + "/" + os.path.basename(outfile)
fo   = open(outfile, 'w')
fo.write(html)
fo.close()
#
#-- quite often the plotting routine stack and becomes a staled process
#-- check the previous one and kill it
#
cmd = 'ps aux|grep plot_crm_flux_data.py > ' + zspace
os.system(cmd)

with open(zspace, 'r') as f:
    data = [line.strip() for line in f.readlines()]

cmd = 'rm -rf ' + zspace
os.system(cmd)

for ent in data:
    ms = re.search('grep', ent)
    if ms is not None:
        continue 

    atemp = re.split('\s+', ent)
    cmd   = 'kill -9 ' + atemp[1]
    os.system(cmd)


