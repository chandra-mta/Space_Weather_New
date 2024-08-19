#!/proj/sot/ska3/flight/bin/python

#########################################################################################
#                                                                                       #
#               plot_p3_data.py: create scaled p3 data plot                             #
#                                                                                       #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                            #
#                                                                                       #
#               Last update: Mar 16, 2021                                               #
#                                                                                       #
#########################################################################################

import os
import re
import time
import numpy
import Chandra.Time
import matplotlib as mpl
from calendar import isleap
import argparse
import signal

if __name__ == '__main__':
    mpl.use('Agg')

import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
#
#--- Define Directory Pathing
#
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
ACE_PLOT_DIR = "/data/mta4/www/RADIATION_new/ACE/Plots"

#
#--- other setting
#
p5_p3_scale = 7         #--- p5 to p3 scale factor
p6_p3_scale = 36        #--- p5 to p3 scale factor
p7_p3_scale = 110       #--- p7 to p3 scale factor
t_arch      = 7         #--- how many days to
#
#--- current time
#
current_time_date    = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
current_chandra_time = Chandra.Time.DateTime(current_time_date).secs
this_year            = int(float(time.strftime('%Y', time.gmtime())))
this_doy             = int(float(time.strftime('%j', time.gmtime())))
year_start           = Chandra.Time.DateTime(str(this_year) + ':001:00:00:00').secs

#---------------------------------------------------------------------------------------
#-- plot_p3_data: get ace data and plot the data                                    --
#---------------------------------------------------------------------------------------

def plot_p3_data():
    """
    create scaled p3 data plot
    input: none but read from <data_dir>/ace_7day_archive
    output: <ace_plot_dir>/mta_ace_plot_P3.png
    """
#
#--- read data and save in column array data format
#
    ifile = f"{ACE_DATA_DIR}/ace_7day_archive"
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    adata = convert_to_arrays(data)
#
#--- plot data
#
    plot_data(adata)

#---------------------------------------------------------------------------------------
#-- convert_to_arrays: convert data into array data                                   --
#---------------------------------------------------------------------------------------

def convert_to_arrays(data):
   
    sdata = []
    for k in range(0, 8):
       sdata.append([])

    chk = 0
    for ent in data:
        atemp = re.split('\s+', ent)
        chk1  = float(atemp[6])
        chk2  = float(atemp[9])
        if (chk1 != 0) or (chk2 != 0):
            continue
#
#--- convert to ydate (input date format example: 2021 03 16  0845)
#
        ltime = atemp[0] + ':' +  atemp[1] + ':' + atemp[2] 
        ltime = time.strftime('%Y:%j', time.strptime(ltime, '%Y:%m:%d'))
        btemp = re.split(':', ltime)
        year  = int(float(btemp[0]))
        yday  = float(btemp[1])
        hh    = float(atemp[3][0] + atemp[3][1])
        mm    = float(atemp[3][2] + atemp[3][3])
        yday += hh /24.0 + mm / 1440.0 
#
#--- if the year changes, use ydate from the year started
#
        if chk == 0:                #--- keeping the year of the first data point
            byear = year
            base = 365 + isleap(byear)
            chk = 1

        if year > byear:
            yday += base
        sdata[0].append(yday)
#
#--- electron part
#
        sdata[1].append(float(atemp[7]))
        sdata[2].append(float(atemp[8]))
#
#--- proton part
#
        sdata[3].append(float(atemp[10]))
        sdata[4].append(float(atemp[11]))
        sdata[5].append(float(atemp[12]))
        sdata[6].append(float(atemp[13]))
        sdata[7].append(float(atemp[14]))

    return sdata

#---------------------------------------------------------------------------------------
#-- plot_data: plot data
#---------------------------------------------------------------------------------------

def plot_data(ndata):
    """
    plot data
    input:  atime   --- time array
            darray  --- a list of data arrays
    ouput:  <plot_dir>/mta_ace_plot_P3.png
    """
#
#--- set color list
#
    c_list = ['blue', 'purple', 'lime', 'orange', 'fuchsia', 'olive', 'green']
#
#--- open data for easy reading
#
    atime  = ndata[0]
    e1     = ndata[1]
    e2     = ndata[2]
    p2     = ndata[3]
    p3     = ndata[4]
    p5     = ndata[5]
    p6     = ndata[6]
    p7     = ndata[7]
    p3s    = numpy.array(p5) * p5_p3_scale
    p3a    = numpy.array(p6) * p6_p3_scale
    p3b    = numpy.array(p7) * p7_p3_scale
#
#--- set x and y min and max
#
    xmax   = int(max(atime)) + 1
    xmin   = xmax - 7.0
    xdiff  = 7.0

    ymin   = min(p7)
    if ymin < 0.01:
        ymin = 0.01

    ymax   = -10000
    for ar in [p3, p3s, p3a, p3b, p5, p6, p7]:
        val = max(ar)
        if val > ymax:
            ymax = val
#
#--- set position parameters
#
    x0     = xmin + 0.05 * xdiff
    x1     = xmin + 0.25 * xdiff
    x2     = xmin + 0.45 * xdiff
    x3     = xmin + 0.65 * xdiff
    x4     = xmin + 0.05 * xdiff
    x5     = xmin + 0.25 * xdiff
    x6     = xmin + 0.45 * xdiff
    x7     = xmax - 0.35 * xdiff
    yp1    = 0.6  * ymax
    yp2    = 0.3  * ymax
    yp3    = 0.2  * ymin 
    yp4    = 1.15 * ymax

    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 10
    props = font_manager.FontProperties(size=10)
    plt.subplots_adjust(hspace=0.10)
#
#--- set panel parameters
#
    ax = plt.subplot(111)
    ax.set_autoscale_on(False)
    ax.set_xbound(xmin, xmax)
    ax.set_xlim(xmin=xmin, xmax=xmax, auto=False)
    ax.set_ylim(ymin=ymin, ymax=ymax, auto=False)
    ax.yaxis.grid(linestyle='--',lw=1.0)
#
#--- plot lines
#
    p, = plt.semilogy(atime, p3a, color=c_list[6], marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p3b, color=c_list[1], marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p3s, color=c_list[2], marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p3,  color='#3573d6', marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p5,  color=c_list[0], marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p6,  color='black',   marker='.', markersize=0.5,lw=0.0)
    p, = plt.semilogy(atime, p7,  color=c_list[4], marker='.', markersize=0.5,lw=0.0)
#
#-- add limit lines
#
    p, = plt.semilogy([xmin, xmax], [50000,50000],  color=c_list[3], marker='.', markersize=0,lw=0.8)
    p, = plt.semilogy([xmin, xmax], [16667,16667],  color=c_list[0], marker='.', markersize=0,lw=0.8)
#
#--- add labels
#
    ax.set_ylabel('Protons/cm2-s-sr-MeV')
    ax.set_xlabel('UTC (days)')

    title = 'ACE RTSW (Estimated) EPAM w/ scaled P3'
    plt.title(title, fontsize=10, fontweight='bold', fontstyle='italic', loc='left')
#
#--- lengend for lines
#
    plt.text(x0, yp1, '112-187*',      color=c_list[6], fontsize=10)
    plt.text(x1, yp1, '112-187**',     color=c_list[1], fontsize=10)
    plt.text(x2, yp1, '112-187***',    color=c_list[2], fontsize=10)
    plt.text(x3, yp1, '115-195',       color='#3573d6', fontsize=10)
    plt.text(x4, yp2, '310-580',       color=c_list[0], fontsize=10)
    plt.text(x5, yp2, '761-1220',      color='black',   fontsize=10)
    plt.text(x6, yp2, '1060-1910 keV', color=c_list[4], fontsize=10)
#
#--- starting time of the data  6 days ago
#
    dval  = int(xmin)
    if dval <= 0:
        dval = 1
    dval = f"{dval:>03}"
    ltime = str(this_year) + ':' + dval
    ltime = time.strftime('%Y-%m-%dT00:00:00UTC', time.strptime(ltime, '%Y:%j'))
    line = 'Begin: ' + ltime 
    plt.text(x7, yp4, line, fontsize=8)
#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = plt.gcf()
    fig.set_size_inches(7.0, 5.5)
#
#--- save the plot in png format
#
    outname = f"{ACE_PLOT_DIR}/mta_ace_plot_P3.png"
    plt.tight_layout()
    plt.savefig(outname, format='png', dpi=300)

    plt.close('all')

#---------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-d", "--data", required = False, help = "Directory path to determine input location of data.")
    parser.add_argument("-p", "--path", required = False, help = "Directory path to determine output location of plot.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
#
#--- Path output to same location as unit tests
#
        if args.data:
            ACE_DATA_DIR = args.data
        else:
            ACE_DATA_DIR = f"{os.getcwd()}/test/outTest"

        if args.path:
            ACE_PLOT_DIR = args.path
        else:
            ACE_PLOT_DIR = f"{os.getcwd()}/test/outTest"
        os.makedirs(ACE_PLOT_DIR, exist_ok = True)
        plot_p3_data()
    elif args.mode == 'flight':
#
#--- Create a lock file and exit strategy in case of race conditions
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            with open(f"/tmp/{user}/{name}.lock") as f:
                pid = int(f.readlines()[-1].strip())
            os.remove(f"/tmp/{user}/{name}.lock")
            os.kill(pid,signal.SIGTERM)
            os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")
        else:
            os.system(f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock")
        plot_p3_data()
#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")