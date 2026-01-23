#!/proj/sot/ska3/flight/bin/python
"""
**update_html_page.py**: update radiation related html page

:Author: t. isobe  (tisobe@cfa.harvard.edu)
:Maintainer: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 16, 2021

"""
import os
import sys
import json
import re
import time
import argparse
import calendar
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
#
# --- Define Directory Pathing
#
WEB_DIR = "/data/mta4/www/RADIATION/ACIS_Rad"

UTC_NOW = datetime.now(timezone.utc)
UTC_LAST_MONTH = UTC_NOW + relativedelta(months=-1)
YEARS = [str(i) for i in range(UTC_LAST_MONTH.year, 1999, -1)]
MONTHS = [i for i in calendar.month_abbr[1:]]

mon_list1 = ['031', '060', '091', '121', '152', '182', '213', '244', '274', '305', '335', '366']
mon_list2 = ['031', '060', '090', '120', '151', '181', '212', '243', '273', '304', '334', '365']
lmon_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
fmon_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True))

def get_options(args=None):
    parser = argparse.ArgumentParser(description="Update ACIS Radiation Correlation Pages")
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    opt = parser.parse_args(args)
    return opt

def render_index():
    subhtmls = {}
    for year in YEARS:
        subhtmls[year] = {}
        for i, month in enumerate(MONTHS):
            #: Fill with a link to the subpage if we are path the target month.
            #: Subtracted by one for different month enumeration.
            if (int(year) < UTC_LAST_MONTH.year) or (i <= UTC_LAST_MONTH.month - 1):
                subhtmls[year][month] = f'<a href="./Html/{month.lower()}{year[2:]}.html">{month.upper()}{year[2:]}</a>'    
    index_template = _JINJA_ENV.get_template('index.jinja')
    index_render = index_template.render(subhtmls=subhtmls,
                                         years=YEARS,
                                         months=MONTHS)
    with open(f"{WEB_DIR}/index.html", 'w') as f:
        f.write(index_render)

def render_year(year):
    pass

def render_month(year : str, month : str):
    """Generate the Monthly ACIS Radiation Correlation Pages

    :param year: Year of the ACIS Radiation Correlation
    :type year: str
    :param month: Month of the ACIS Radiation Correlation
    :type month: str

    """
    month_template = _JINJA_ENV.get_template('month.jinja')
    month_render = month_template.render(year = year,
                                         month = month)
    with open(f"{WEB_DIR}/Html/{month.lower()}{year[2:]}.html", 'w') as f:
        f.write(month_render)

#----------------------------------------------------------------------------------------------------------
#--  print_html: create and/or update radiation related html page                                       ---
#----------------------------------------------------------------------------------------------------------

def print_html(year, mon):
    """
    create and/or update radiation related html page
    """
#
#--- find today's date
#
    if year == '':
        today = time.strftime("%Y:%m:%d:%j", time.gmtime())
        atemp = re.split(':', today)
        year  = int(atemp[0])
        mon   = int(atemp[1])
        day   = int(atemp[2])
        yday  = int(atemp[3])
#
#--- for the case year and mon are given
#
    cyear = year
    lmon  = mon
#
#--- choose a correct month list depending on whether this is the leap year
#
    if isLeapYear(cyear) == 1:
        mon_list = mon_list1
    else:
        mon_list = mon_list2

    last_day  = mon_list[lmon-1]
#
#--- convert the month from a numeric to letter
#
    umon      = lmon_list[lmon-1]
    smon      = umon.lower()

    lmon_year =  str(cyear)
    syear     =  lmon_year[2] + lmon_year[3]
    last_year =  str(year -1)
    syear2    =  last_year[2] + last_year[3]
    monyear   =  smon + syear
#
#--- set output html page names
#
    year_html = 'all' + syear + '.html'
    mon_html  = monyear + '.html'
    rad_html  = 'rad_time_' + monyear + '.html'
#
#--- read yearly html page template
#
    with open('./Template/yearly_template', 'r') as f:
        data = f.read()

    data = data.replace('$#FYEAR#$', str(year))
    data = data.replace('$#SYEAR#$', syear)

    with open(year_html, 'w') as fo:
        fo.write(data)
#
#--- read rad_time html page template
#
    with open('./Template/rad_time_template', 'r') as f:
        data = f.read()

    data = data.replace('$#LMONTH#$', fmon_list[mon-2])
    data = data.replace('$#FYEAR#$', str(year))
    data = data.replace('$#MONYEAR#$', monyear)

    with  open(rad_html, 'w') as fo:
        fo.write(data)


#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

def isLeapYear(year):
    """
    chek the year is a leap year
    Input:  year   in full lenth (e.g. 2014, 813)
    Output: 0   --- not leap year
            1   --- yes it is leap year
    """
    year = int(float(year))
    chk  = year % 4 #---- evry 4 yrs leap year
    chk2 = year % 100   #---- except every 100 years (e.g. 2100, 2200)
    chk3 = year % 400   #---- excpet every 400 years (e.g. 2000, 2400)
    
    val  = 0
    if chk == 0:
        val = 1
    if chk2 == 0:
        val = 0
    if chk3 == 0:
        val = 1
    
    return val


#----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    opt = get_options()

    if opt.mode == 'test':
        WEB_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(WEB_DIR, exist_ok = True)
        os.makedirs(f"{WEB_DIR}/Html", exist_ok = True)
        os.makedirs(f"{WEB_DIR}/Plot", exist_ok = True)
    
    render_index()
    render_month(
        year = str(UTC_LAST_MONTH.year),
        month = MONTHS[UTC_LAST_MONTH.month - 1]
    )
# #
# #--- if you provide year and month (in format of 2015 3), it will create the html pages for that month. 
# #
#     if len(sys.argv) == 2:
#         year = argv[1]
#         mon  = argv[2]
#     else:
#         year = ''
#         mon  = ''
#     print_html(year, mon)
# #
# #--- index page is always written up to this month of this year
# #
#     print_index_html()
