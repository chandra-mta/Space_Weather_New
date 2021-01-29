#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################################
#                                                                                                   #
#           update_goes_proton_page.py: update goes proton pages                                    #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Jan 28, 2020                                                           #
#                                                                                                   #
#####################################################################################################

import os
import sys
import re
import string
import random
import operator
import time
import numpy
#
#--- reading directory list
#
path = '/data/mta4/Space_Weather/house_keeping/dir_list'

f= open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#--- temp writing file name
#
rtail  = int(time.time())
zspace = '/tmp/zspace' + str(rtail)

dat_name = ['Gp_pchan_5m.txt',   'Gs_pchan_5m.txt']
####out_name = ['goes_pchan_p.html', 'goes_pchan_s.html']
out_name = ['goes14_pchan_p.html', 'goes_pchan_s.html']
#
#--- set direcotries
#
data_dir   = goes_dir + 'Data/'
templ_dir  = goes_dir + 'Scripts/Template/'
web_dir    = html_dir + 'GOES/'
plot_dir   = web_dir  + 'Plots/'

#---------------------------------------------------------------------------------------------------
#-- update_goes_proton_page: update goes proton pages
#---------------------------------------------------------------------------------------------------

def update_goes_proton_page():
    """
    update goes proton pages
    input: none but read from <data_dir>/Gp_pchan_5m.txt, Gs_pchan_5m.txt
    output: <web_dir>/GOES/goes_pchan_<p/s>.html
    """

    cmd = 'mkdir -p ' + plot_dir
    os.system(cmd)
#
#--- get goes satellite numbers
#
    ifile  = data_dir  + dat_name[0]
    g_num  = find_goes_num(ifile)           #--- primary

    ifile  = data_dir  + dat_name[1]
    g_num2 = find_goes_num(ifile)           #--- secondary
#
#--- read data and create new data pages
#
    for  k in range(0, len(dat_name)):

        gfile = dat_name[k]

        ifile = data_dir + gfile
        t_num = find_goes_num(ifile)        #--- goes number for this page
#
#--- create summary page content
#
        line  = create_summary_page(ifile, t_num)
#
#--- read header footer etc.
#
        hfile = templ_dir + 'G_header'
        head  = read_file(hfile)
        head  = head.replace('#GNUM#',   t_num)
        head  = head.replace('#SELECT#', "PROTONS")

        gfile = templ_dir + 'Gp_image'
        i_sec = read_file(gfile)
        i_sec = i_sec.replace('#GNUM#',  g_num)
        i_sec = i_sec.replace('#GNUM2#', g_num2)

        ffile = templ_dir + 'G_footer'
        foot  = read_file(ffile)

        line  = head + line + i_sec + foot
#
#--- update html page
#
        out   = web_dir + out_name[k]
        fo    = open(out, 'w')
        fo.write(line)
        fo.close()
    
#---------------------------------------------------------------------------------------------------
#-- create_summary_page: convert the data into the summary page format                            --
#---------------------------------------------------------------------------------------------------

def create_summary_page(ifile, g_num):
    """
    convert the data into the summary page format
    input:  ifile   --- original data file
            g_num   --- goes number of this data
    output: line    --- the html section of the data table
    """
#
#--- read headers of the tables
#
    hfile = templ_dir + 'Gp_table1'
    hdr1 = read_file(hfile)
    hdr1 = hdr1.replace('#GNUM#', g_num)

    hfile = templ_dir + 'Gp_table2'
    hdr2 = read_file(hfile)
#
#--- read data and converts each column to an array
#
    data = read_data_file(ifile)
    data = data[26:]
    aa   = convert_to_arrays(data)
#
#--- compute HRC proxy
#
    h1   = 6000 * aa[10] + 270000 * aa[11] + 100000 * aa[12]
#
#--- print the data
#
    line = hdr1

    for k in range(0, len(h1)):
        if aa[11][k] < 0.0:
            h1[k] = -10000

        aline = "%4d %2d %2d %4d %12.2f %12.5f %12.5f %12.5f %12.5f %12.5f %10.0f \n" \
                % (aa[0][k],  aa[1][k],  aa[2][k], aa[3][k],
                   aa[6][k],  aa[7][k],  aa[10][k],        
                   aa[13][k], aa[15][k], aa[16][k], h1[k]) 
        line  = line + aline

    if min(aa[6]) < 10000000.0:

        line  = line + hdr2
#
#--- compute average
#
        p1a   = numpy.mean(aa[6])
        p2a   = numpy.mean(aa[7])
        p5a   = numpy.mean(aa[10])
        p8a   = numpy.mean(aa[13])
        p10a  = numpy.mean(aa[15])
        p11a  = numpy.mean(aa[16])
        h1a   = numpy.mean(h1)
        aline = "AVERAGE %14.3f %14.6f %14.6f %14.6f %14.6f %14.6f %12.0f \n" \
                % (p1a, p2a, p5a, p8a, p10a, p11a, h1a)

        line  = line + aline
#
#--- compute fluence
#
        p1f   = numpy.sum(aa[6])  * 7200.0
        p2f   = numpy.sum(aa[7])  * 7200.0
        p5f   = numpy.sum(aa[10]) * 7200.0
        p8f   = numpy.sum(aa[13]) * 7200.0
        p10f  = numpy.sum(aa[15]) * 7200.0
        p11f  = numpy.sum(aa[16]) * 7200.0
        h1f   = numpy.sum(h1)     * 7200.0
        aline = "FLUENCE %14.4e %14.4e %14.4e %14.4e %14.4e %14.4e %14.4e \n" \
                % (p1f, p2f, p5f, p8f, p10f, p11f, h1f)

        line  = line + aline
        line  = line + "</pre>"
        line  = line + '<div style="padding-top:10px;"></div>'
        line  = line + "H1 = 6000*P4p + 270000*P5p + 100000*P6p \n"

    else:
        line  = line + "\n\n No Valid data for last 2 hours\n"


    line = line + '</div>\n'
    return line
    
#---------------------------------------------------------------------------------------------------
#-- convert_to_arrays: convert data into array data                                               --
#---------------------------------------------------------------------------------------------------

def convert_to_arrays(data):
    """
    convert data into array data
    input:  data    --- n line data set
            nave    --- a linst of arrays
    """

    c_len = len(re.split('\s+', data[0]))
    save  = []
    for k in range(0, c_len):
        save.append([])

    for ent in data:
        atemp = re.split('\s+', ent)
        for k in range(0, c_len):
            save[k].append(float(atemp[k]))

    nsave = []
    for k in range(0, c_len):
        nsave.append(numpy.array(save[k]))

    return nsave
    
#---------------------------------------------------------------------------------------------------
#-- find_goes_num: find goes satellite number                                                     --
#---------------------------------------------------------------------------------------------------

def find_goes_num(ifile):
    """
    find goes satellite number
    input:  ifile   --- data file name
    output: g_num   --- goes satellite number
    """
    
    g_num = 'nan'
    data = read_data_file(ifile)
    for ent in data:

        mc = re.search('GOES', ent)
        if mc is not None:
            atemp = re.split('GOES-', ent)
            btemp = re.split('\s+', atemp[1])
#
#--- for the case like: 5-minute  GOES-15 Energetic Proton Flux Channels
#
            if len(btemp) > 0:
                g_num = btemp[0].strip()
#
#--- for the case like: # Source: GOES-15
#
            else:
                g_num = atemp[1].strip()
            break

    return g_num
    
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_data_file(ifile, remove=0):

    f    = open(ifile, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    if remove > 0:
        if os.path.isfile(ifile):
            cmd = 'rm ' + ifile
            os.system(cmd)

    return data
    
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

def read_file(ifile):

    f    = open(ifile, 'r')
    data = f.read()
    f.close()

    return data

#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    update_goes_proton_page()
