#!/proj/sot/ska3/flight/bin/python

#####################################################################################################
#                                                                                                   #
#               plot_goes_data.py: get goes data and plot the data                                  #
#                                                                                                   #
#               author: t. isobe    (tisobe@cfa.harvard.edu)                                        #
#                                                                                                   #
#               Last update: Mar 16, 2021                                                           #
#                                                                                                   #
#####################################################################################################

import sys
import os
import json
import numpy as np
import urllib.request
from astropy.table import Table
from datetime import datetime, timedelta


import matplotlib as mpl

if __name__ == '__main__':
    mpl.use('Agg')
import matplotlib.pyplot       as plt
import matplotlib.font_manager as font_manager
from matplotlib.dates import DayLocator, ConciseDateFormatter

import argparse
import traceback
#
#--- Defining Directory Pathing
#
HTML_DIR = "/data/mta4/www/RADIATION_new"
PLOT_DIR = os.path.join(HTML_DIR,"GOES", "Plots")

#
#--- JSON data web links
#
DLINK = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json'
CLINK = 'https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json'

#
#--- Band limits by GOES channel in MeV
#
BAND_LIMITS = {'P1':[1.02, 1.86],
                'P2A':[1.9, 2.3],
                'P2B':[2.31, 3.34],
                'P3':[3.4, 6.48],
                'P4':[5.84, 11.0],
                'P5':[11.64, 23.27],
                'P6':[25.9, 38.1],
                'P7':[40.3, 73.4],
                'P8A':[83.7, 98.5],
                'P8B':[99.9, 118.0],
                'P8C':[115.0, 143.0],
                'P9':[160.0, 242.0],
                'P10':[276.0, 404.0]}

class Group_Info():
    """
    Stores info used in averaging differential flux data from GOES energy band channels 
    into an ACE energy band channel format.
    """
    def __init__(self,channel_tuple):
        """
        Initialize a Group_Info object
        input: channel_tuple --- a tuple of strings naming GOES energy band channels
        output: Group_Info object
        """
        self.channel_tuple = channel_tuple
        self.find_lims()
        self.find_weights()
        
    def find_lims(self):
        """
        Determine minimum and maximum energy values across channel selection
        input: none but reads from self.channel_tuple
        output: self.max --- greatest energy value across all channels in self.channel_tuple
                self.min --- smallest energy value across all channels in self.channel_tuple
        """
        lims = []
        for channel in self.channel_tuple:
            lims = lims + BAND_LIMITS[channel]
        self.min = min(lims)
        self.max = max(lims)
    
    def find_weights(self):
        """
        Determines weight used in averaging algorithm converting GOES energy bands into ACE energy bands
        input: none but reads from self.channel_tuple
        output: self.weights --- averaging weight for a GOES energy band
        """
        weights = []
        for channel in self.channel_tuple:
            weights.append(round(BAND_LIMITS[channel][1] - BAND_LIMITS[channel][0],2))
        self.weights = weights
#
#--- Differential Group Selection by channel: Determined by Band Limits to mimic ACE channels.
#
DIFF_GROUP_SELECTION = [Group_Info(('P1','P2A','P2B')),
                   Group_Info(('P3','P4')),
                   Group_Info(('P7','P8A'))]

#
#--- Integral Group Selection:
#
INTG_GROUP_SELECTION = ['>=10 MeV',
                        '>=50 MeV',
                        '>=100 MeV']

#
#--- String formatting used in date conversion and plotting axes
#
ASTROPY_FORMATTING = "%Y-%m-%dT%H:%M:%SZ"

TICK_FORMATTING = ['%y', #ticks are mostly years
           '%b %d',     # ticks are mostly months
           '%b %d',     # ticks are mostly days
           '%H:%M',  # hrs
           '%H:%M',  # min
           '%S.%f', ] #seconds

OFFSET_TICK_FORMATTING = ['', # offest ticks are mostly years
                          '', # offset ticks are mostly months
                          '', # offset ticks are mostly days
                          '', #hrs
                          '', # min
                          ''] #seconds


#---------------------------------------------------------------------------------------------------
#-- plot_goes_data: get goes data and plot the data                                               --
#---------------------------------------------------------------------------------------------------

def plot_goes_data(dlink = DLINK, clink = CLINK, choice=['diff','intg']):
    """
    get GOES data and plot the data
    input:  JSON file path or read from: 
        https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json
        https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json
    output: <plot_dir>/goes_particles.png
            <plot_dir>/goes_proton.png
    """
    if 'diff' in choice:
        diff_table = extract_goes_table(dlink)
        diff_data_dict = calc_ACE_p(diff_table)
#
#--- Define extra plotting variables
#
        diff_data_dict['units'] = "p/cm2-s-sr-MeV"
        diff_data_dict['title'] = "Proton Flux (Differential)"
        diff_data_dict['filename'] = f"{PLOT_DIR}/goes_protons.png"
        diff_data_dict['labels'] = [f"{x.min}-{x.max} Mev" for x in DIFF_GROUP_SELECTION]
        diff_data_dict['colors'] = ['fuchsia', 'green', 'blue']
        diff_data_dict['limits'] = {'y_min':1e-3, 'y_max':1e4}
        diff_data_dict['limit_lines'] = {'P4GM':90.91,
                                         'P41GM':0.71}
        plot_data(diff_data_dict)
        
    if 'intg' in choice:
        intg_table = extract_goes_table(clink)
        intg_data_dict = format_intg_data(intg_table)
#
#--- Define extra plotting variables
#
        intg_data_dict['units'] = "p/cm2-s-sr"
        intg_data_dict['title'] = "Proton Flux (Integral)"
        intg_data_dict['filename'] = f"{PLOT_DIR}/goes_particles.png"
        intg_data_dict['labels'] = INTG_GROUP_SELECTION
        intg_data_dict['colors'] = ['red', 'blue', '#51FF3B']
        intg_data_dict['limits'] = {'y_min':1e-2, 'y_max':1e4}
        plot_data(intg_data_dict)


#----------------------------------------------------------------------------
#-- extract_goes_table: extract GOES satellite flux data                   --
#----------------------------------------------------------------------------

def extract_goes_table(jlink):
    """
    extract GOES satellite flux data
    input: jlink--- JSON web address or file
    output: table--- astropy table of the GOES data.
    """
    if jlink.startswith('http'):
#
#--- read json file from the web
#
        try:
            with urllib.request.urlopen(jlink) as url:
                data = json.loads(url.read().decode())
        except:
            traceback.print_exc()
            data = []
    else:
        if os.path.isfile(jlink):
            try:
                with open(jlink) as f:
                    data = json.load(f)
            except:
                traceback.print_exc()
                data = []
    if len(data) < 1:
        exit(1)
    data = Table(data)
    return data

#----------------------------------------------------------------------------------
#-- calc_ACE_p: format the GOES differential flux into ACE flux channel values   --
#----------------------------------------------------------------------------------

def calc_ACE_p(table):
    """
    create combined flux data of astropy table based on weighted average
    input: table --- astropy table of the differential protons.
    output: diff_data_dict --- dictionary of combined flux data averaged into ACE energy bands.
    """
    diff_data_dict = {'plot_data':[]}

    for group_info in DIFF_GROUP_SELECTION:
#
#--- Initialize group data arrays
#
        channel = group_info.channel_tuple[0]
        sel = table['channel'] == channel
        subtable = table[sel]
        if 'times' not in diff_data_dict.keys():
            diff_data_dict['times'] = [datetime.strptime(x,ASTROPY_FORMATTING) for x in subtable['time_tag'].data]
#
#--- Flux averaged across energy bands from protons/cm2-s-ster-KeV to protons/cm2-s-ster-MeV
#
        avgs = subtable['flux'] * 1e3 * group_info.weights[0]

        for i in range(1,len(group_info.channel_tuple)):
#
#--- Iterate over the rest of the channels to calulate the averages
#
            channel = group_info.channel_tuple[i]
            sel = table['channel'] == channel
            subtable = table[sel]
            avgs = avgs + subtable['flux'] * 1e3 * group_info.weights[i]
        
        avgs = avgs/(group_info.max - group_info.min)
        diff_data_dict['plot_data'].append(avgs)
    return diff_data_dict

#--------------------------------------------------------------------------------
#-- calc_ACE_p: Format the GOES integral flux into plottable data dictionary   --
#--------------------------------------------------------------------------------

def format_intg_data(intg_table):
    """
    Formats the GOES integral flux astropy table into a data table
    input: intg_table --- astropy table of the integral protons
    output: intg_data_dict --- dictionary of integral data
    """
    intg_data_dict = {'plot_data':[]}
    sel = intg_table['energy'] == INTG_GROUP_SELECTION[0]
    subtable  = intg_table[sel]
    intg_data_dict['times'] = [datetime.strptime(x,ASTROPY_FORMATTING) for x in subtable['time_tag'].data]
    intg_data_dict['plot_data'].append(subtable['flux'])

    for i in range(1,len(INTG_GROUP_SELECTION)):
        sel = intg_table['energy'] == INTG_GROUP_SELECTION[i]
        subtable = intg_table[sel]
        intg_data_dict['plot_data'].append(subtable['flux'])
    return intg_data_dict

#-------------------------------------------------------------
#-- plot_data: Process a data dictionary to generate plots  --
#-------------------------------------------------------------

def plot_data(data_dict):
    """
    Generate a plot and save to a png file.
    input: data_dict - dictionary of plotting data, both x,y data numpy arrays and plot design parameters
    output: none but save a png file of the generated plot
    """
    plt.close('all')
#
#--- set a few parameters
#
    mpl.rcParams['font.size'] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)
    ax = plt.subplot(111)
    ax.set_ylim(ymin=data_dict['limits']['y_min'], 
                ymax=data_dict['limits']['y_max'],
                auto=False)
#    
#--- Plotting section
#
    for i in range(len(data_dict['plot_data'])):
        p, = plt.semilogy(
                          data_dict['times'],
                          data_dict['plot_data'][i],
                          color=data_dict['colors'][i],
                          label=data_dict['labels'][i],
                          marker='.',
                          markersize=0,
                          lw=0.8
                        )
#
#--- Format Tick marks automatically around days
#
    major_locator = DayLocator()
    ax.xaxis.set_major_locator(major_locator)
    formatter = ConciseDateFormatter(major_locator, 
                                     formats=TICK_FORMATTING, 
                                     offset_formats=OFFSET_TICK_FORMATTING)
    ax.xaxis.set_major_formatter(formatter)
    
    xticks = ax.get_xticks()
    for tick in xticks:
        ax.vlines(tick,
                  data_dict['limits']['y_min'],
                  data_dict['limits']['y_max'],
                  linestyle = 'dotted',
                  colors = 'black'
                 )
    
    if 'limit_lines' in data_dict.keys():
#
#--- Define positioning for limit line text
#
        xbound = ax.get_xbound()
        xpos = xbound[-1] + 0.01 * (xbound[-1] - xbound[0])
        for k,v in data_dict['limit_lines'].items():
            plt.axhline(v, color ='#F05D5D')
            plt.text(xpos, v, f"{k}\nLimit", color = 'black')
    
    ax.set_xlabel("Coordinated Universal Time")
    ax.set_ylabel(data_dict['units'])
    ax.legend(loc='upper left')
    plt.grid(axis='y')
    plt.title(data_dict['title'])
#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = plt.gcf()
    fig.set_size_inches(8.0, 5.0)
#
#--- save the plot in png format
#
    plt.savefig(data_dict['filename'], format='png', dpi=300)

    plt.close('all')

#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=['flight','test'], required=True, help="Determine running mode.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
#
#--- Path output to same location as unit tests
#
        OUT_DIR = os.path.join(os.getcwd(),"test","outTest")
        PLOT_DIR = os.path.join(OUT_DIR,"GOES", "Plots")
        os.makedirs(PLOT_DIR, exist_ok=True)
        plot_goes_data()
    elif args.mode == "flight":
#
#--- Create a lock file and exit strategy in case of race conditions
#
        import getpass
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog.")
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        plot_goes_data()

#
#--- Remove lock file once process is completed
#
        os.system(f"rm /tmp/{user}/{name}.lock")