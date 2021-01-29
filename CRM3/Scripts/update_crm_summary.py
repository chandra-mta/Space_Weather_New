#!/usr/bin/env /proj/sot/ska/bin/python
import os
import sys
import re
import string


f    = open('/data/mta4/www/RADIATION_new/CRM/CRMsummary.dat', 'r')
line = f.read()
f.close()

f    = open('/data/mta4/Space_Weather/house_keeping/crm_summary_html_template', 'r')
html = f.read()

html = html.replace("#TEXT#", line)

fo   = open('/data/mta4/www/RADIATION_new/CRM/CRMsummary.html', 'w')
fo.write(html)
fo.close()
