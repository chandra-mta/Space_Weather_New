#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#       update_html_page.py: update radiation related html page                                 #
#                                                                                               #
#           author: t. isobe    (tiosbe@cfa.harvard.edu)                                        #
#                                                                                               #
#           last update: Mar 16, 2021                                                           #
#                                                                                               #
#################################################################################################

import os
import sys
import re
import subprocess
import time

#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

with open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))


mon_list1 = ['031', '060', '091', '121', '152', '182', '213', '244', '274', '305', '335', '366']
mon_list2 = ['031', '060', '090', '120', '151', '181', '212', '243', '273', '304', '334', '365']
lmon_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

fmon_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

web_dir   = html_dir + 'ACIS_Rad/'

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
#--- find out the last month
#
#        cyear = year
#        lmon      = mon -1
#        if lmon < 1:
#            lmon  = 12
#            cyear = year -1

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
#--- read monthly html page template
#
    with open('./Template/monthly_template', 'r') as f:
        data = f.read()

    data = data.replace('$#FYEAR#$', str(year))
    data = data.replace('$#UMON#$',umon )
    data = data.replace('$#MONYEAR#$', monyear)

    with open(mon_html, 'w') as fo:
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
#--  print_index:html: update index.html page                                                           ---
#----------------------------------------------------------------------------------------------------------

def print_index_html():
    """
    create and/or update radiation related html page
    """
#
#--- find today's date
#
    today = time.strftime("%Y:%m:%d:%j", time.gmtime())
    atemp = re.split(':', today)
    year  = int(atemp[0])
    mon   = int(atemp[1])
    day   = int(atemp[2])
    yday  = int(atemp[3])
#
#--- read header part and the first part of the index page
#
    with open('./Template/index_top', 'r') as f:
        line = f.read()
#
#--- start creating a link table
#
    line = line + '<table border=1 cellpadding=10 cellspacing=2>\n'
    #line = line + '<tr>\n'
    #line = line + '<td colspan=13>\n'
    #line = line + '<table border=1 width=100%>\n'
    #line = line + '<tr><th> <a href="./Html/all.html" style="font-size:120%">Mission since JAN2000</a></th></tr>\n'
    #line = line + '</table>\n'
    #line = line + '</td>\n'
    #line = line + '</tr>\n'

    line = line + '<tr>'
    line = line + '<th>Year</th><th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th><th>Jun</th>\n'
    line = line + '<th>Jul</th><th>Aug</th><th>Sep</th><th>Oct</th><th>Nov</th><th>Dec</th>\n'
    line = line + '</tr>\n'
    for eyear in range(year, 1999, -1):
        line = line + '<tr>\n' 
        line = line + '<th>' + str(eyear) + '</th>\n'

        lyear    = str(eyear)
        syear    = lyear[2] + lyear[3]

        for emon in range(1, 13):
            lmon     = lmon_list[emon -1]
            monyear  = lmon.lower() + syear
            cmonyear = monyear.upper()

            #if eyear == year and emon > mon:
            if eyear == year and emon > mon-1:
                line = line +  '<td>' + cmonyear + '</td>\n'
            else:
                line = line + '<td><a href="./Html/' + monyear + '.html">'+ cmonyear + '</a></td>\n'

        line = line + '</tr>\n\n'

    line  = line + '</table>\n'
#
#--- table finished. add a closing part
#
    line  = line + '<div style="padding-top: 15px"></div>\n'
    line  = line + '<hr />'
    line  = line + '<div style="padding-top: 15px"></div>\n'
    line  = line + '<p>If you have any questions about this page, please contact '
    line  = line + '<a href="mailto:swolk@cfa.harvard.edu">swolk@cfa.harvard.edu</a>\n'
    line  = line + "<script>\n\tsetTimeout('location.reload()',300000)</script>\n"

    line  = line + '</body</html>\n'
#
#--- now write out the page
#
    out = web_dir + 'index.html'
    with open(out, 'w') as fo:
        fo.write(line)

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
#
#--- if you provide year and month (in format of 2015 3), it will create the html pages for that month. 
#
    if len(sys.argv) == 2:
        year = argv[1]
        mon  = argv[2]
    else:
        year = ''
        mon  = ''
    print_html(year, mon)
#
#--- index page is always written up to this month of this year
#
    print_index_html()
