#!/usr/bin/env python
"""
**plot_goes_data.py**: Get and plot goes data.

:Author: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jan 29, 2026

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import signal
import os
import json
from time import sleep
import urllib.request
import urllib.error
from astropy.table import Table
from datetime import datetime
import matplotlib as mpl
import numpy as np
import psutil
if __name__ == "__main__":
    mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
import argparse
import traceback
from pathlib import Path
#
# --- Defining Directory Pathing
#
SPACE_WEATHER = Path(os.getenv("Space_Weather", "/data/mta4/Space_Weather"))
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))
GOES_DATA_DIR : Path = SPACE_WEATHER / "GOES" / "Data"
GOES_PLOT_DIR : Path = SPACE_WEATHER_WEB / "GOES" / "Plots"

#
# --- JSON data web links
#
DLINK = (
    "https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json"
)
CLINK = "https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json"

BAND_LIMITS = {
    "P1": {"min": 1.02, "max": 1.86},
    "P2A": {"min": 1.9, "max": 2.3},
    "P2B": {"min": 2.31, "max": 3.34},
    "P3": {"min": 3.4, "max": 6.48},
    "P4": {"min": 5.84, "max": 11.0},
    "P5": {"min": 11.64, "max": 23.27},
    "P6": {"min": 25.9, "max": 38.1},
    "P7": {"min": 40.3, "max": 73.4},
    "P8A": {"min": 83.7, "max": 98.5},
    "P8B": {"min": 99.9, "max": 118.0},
    "P8C": {"min": 115.0, "max": 143.0},
    "P9": {"min": 160.0, "max": 242.0},
    "P10": {"min": 276.0, "max": 404.0},
}  #: Band limits by GOES channel in MeV


class GroupInfo:
    """Stores info used in averaging differential flux data from GOES energy band channels into an ACE energy band channel format."""

    def __init__(self, channel_tuple):
        """Initialize a GroupInfo object

        :param channel_tuple: A tuple of strings naming GOES energy band channels
        :type channel_tuple: tuple(str)
        """
        self.channel_tuple = channel_tuple
        lims = []
        for channel in self.channel_tuple:
            lims = lims + list(BAND_LIMITS[channel].values()) #: Determine minimum and maximum energy values across channel selection
        self.min = min(lims)
        self.max = max(lims)
        self.weights = []
        for channel in self.channel_tuple:
            self.weights.append(
                round(BAND_LIMITS[channel]["max"] - BAND_LIMITS[channel]["min"], 2)
            ) #: Determines weight used in averaging algorithm converting GOES energy bands into ACE energy bands
    def __repr__(self):
        return f"GroupInfo(channels={self.channel_tuple!r}, min={self.min!r}, max={self.max!r})"

DIFF_GROUP_SELECTION = [
    GroupInfo(("P1", "P2A", "P2B")),
    GroupInfo(("P3", "P4")),
    GroupInfo(("P7", "P8A")),
]  #: Differential Group Selection by channel. Determined by Band Limits to mimic ACE channels.

ALL_DIFF_CHANNEL = set()
for x in DIFF_GROUP_SELECTION:
    ALL_DIFF_CHANNEL = ALL_DIFF_CHANNEL.union(set(x.channel_tuple))

INTG_GROUP_SELECTION = [
    ">=10 MeV",
    ">=50 MeV",
    ">=100 MeV",
]  #: Integral Group Selection

ISO_FORMATTING = (
    "%Y-%m-%dT%H:%M:%SZ"  #: String formatting used in date conversion and plotting axes
)

TICK_FORMATTING = [
    "%Y",  #: ticks are mostly years
    "%b-%d",  #: ticks are mostly months
    "%b-%d",  #: ticks are mostly days
    "%H:%M",  #: hrs
    "%H:%M",  #: min
    "%S.%f",  #: seconds
]

OFFSET_TICK_FORMATTING = [
    "",  #: offset ticks are mostly years
    "%Y",  #: offset ticks are mostly months
    "%Y-%b",  #: offset ticks are mostly days
    "%Y-%b",  #: hrs
    "%H:%M",  #: min
    "%H:%M",  #: seconds
]

def plot_goes_data(dlink=DLINK, clink=CLINK, choice=["diff", "intg"]):
    """Fetch and plot GOES data

    :param dlink: JSON file or web path for differential protons, defaults to DLINK
    :type dlink: str, optional
    :param clink: JSON file or web path for integral protons, defaults to CLINK
    :type clink: str, optional
    :param choice: List of strings to determine which kind of plot to generates, defaults to ["diff", "intg"]
    :type choice: list, optional
    """
    if "diff" in choice:
        diff_table = json2table(dlink)
        diff_table = reorient_particle_table(diff_table, gen_column="channel", column_list=ALL_DIFF_CHANNEL)
        lines = []
        for info in DIFF_GROUP_SELECTION:
            avg = group_avg(diff_table, info)
            lines.append(avg)

        times = [datetime.strptime(x, ISO_FORMATTING) for x in diff_table['time_tag']]
        diff_data_dict = {"times": times, "lines": lines}
        #
        # --- Define extra plotting variables
        #
        diff_data_dict["units"] = "p/cm2-s-sr-MeV"
        diff_data_dict["title"] = "Proton Flux (Differential)"
        diff_data_dict["filename"] = GOES_PLOT_DIR / "goes_protons.png"
        diff_data_dict["labels"] = [
            f"{x.min}-{x.max} Mev" for x in DIFF_GROUP_SELECTION
        ]
        diff_data_dict["colors"] = ["fuchsia", "green", "blue"]
        diff_data_dict["limits"] = {"y_min": 1e-4, "y_max": 1e4}
        diff_data_dict["limit_lines"] = {
            "P4GM": (90.91, diff_data_dict["colors"][1]),
            "P41GM": (0.71, diff_data_dict["colors"][2]),
        }
        plot_data(diff_data_dict)

    if "intg" in choice:
        intg_table = json2table(clink)
        intg_table = reorient_particle_table(intg_table, column_list=INTG_GROUP_SELECTION)
        lines = [intg_table[energy] for energy in INTG_GROUP_SELECTION]
        times = [datetime.strptime(x, ISO_FORMATTING) for x in intg_table['time_tag']]

        intg_data_dict = {"times": times, "lines": lines}
        #
        # --- Define extra plotting variables
        #
        intg_data_dict["units"] = "p/cm2-s-sr"
        intg_data_dict["title"] = "Proton Flux (Integral)"
        intg_data_dict["filename"] = GOES_PLOT_DIR / "goes_particles.png"
        intg_data_dict["labels"] = INTG_GROUP_SELECTION
        intg_data_dict["colors"] = ["red", "blue", "#51FF3B"]
        intg_data_dict["limits"] = {"y_min": 1e-2, "y_max": 1e4}
        plot_data(intg_data_dict)

def rerun(func):
    """
    Function decorator which sleeps and reruns the provided function upon encountering a set of errors.
    """
    _freq = 3
    _errors = (json.decoder.JSONDecodeError, urllib.error.URLError)
    def wrapper_func(*args,**kwargs):
        _last_exception = Exception()
        for i in range(_freq):
            try:
                return func(*args, **kwargs)
            except _errors as e:
                _last_exception = e
                sleep(5)
        _last_exception.add_note(f'Decorator ran function {_freq} times. Still encountered error.')
        raise _last_exception
    return wrapper_func

@rerun
def json2table(jlink):
    """Extract JSON file and format into Astropy Table

    :param jlink: JSON web address or file
    :type jlink: str
    :return: astropy table of the provided data.
    :rtype: astropy.Table

    """
    if os.path.isfile(jlink):
        with open(jlink) as f:
            data = json.load(f)
    else:
        with urllib.request.urlopen(jlink, timeout = 10) as url:
            data = json.loads(url.read().decode())
    data = Table(data)
    return data

def reorient_particle_table(table, gen_column = 'energy', column_list = None):
    """
    Take a particle table with multiple time tag entires (one for each energy).
    This is the default for SWPC data products. Then reorient to single time entries with flux for each column
    """
    for col in table.columns:
        if 'time' in col:
            time_column = col
    
    time_list = sorted(set(table[time_column].data))
    if column_list is None:
        column_list = sorted(set(table[gen_column]))
    
    new_rows = []
    for time in time_list:
        row = {time_column: time}
        for col in column_list:
            selection = np.logical_and(table[time_column] == time, table[gen_column] == col)
            if sum(selection) == 0:
                flux = np.ma.masked
            else:
                flux = table[selection]['flux'].data[0]
            row.update({col: flux})
        new_rows.append(row)
    
    return Table(rows = new_rows)

def group_avg(table, group_info, factor = 1e3):
    """
    Calculate the differential channel grouping average column
    :Note: Group Info is in MeV, therefore factor converts flux KeV -> MeV
    """
    #
    # --- Initialize a fully-false zeroed masked array for the averages
    # --- If any of the channels for that data point are unavailable
    #
    avg = np.ma.masked_array(np.zeros(len(table)), mask = np.zeros(len(table)))
    for channel, weight in zip(group_info.channel_tuple, group_info.weights):
        avg = np.ma.add(avg, table[channel] * weight)
    
    avg = avg * factor / (group_info.max - group_info.min)
    return avg

def plot_data(data_dict):
    """Generate a plot and save to a png file.

    :param data_dict: dictionary of plotting data, both x,y data numpy arrays and plot design parameters
    :type data_dict: dict
    :File Out: Saved png file of plot
    """
    plt.close("all")
    mpl.rcParams["font.size"] = 14
    props = font_manager.FontProperties(size=14)
    plt.subplots_adjust(hspace=0.10)
    ax = plt.subplot(111)
    ax.set_ylim(
        ymin=data_dict["limits"]["y_min"], ymax=data_dict["limits"]["y_max"], auto=False
    )
    #
    # --- Plotting section
    for i in range(len(data_dict["lines"])):
        (p,) = plt.semilogy(
            data_dict['times'],
            data_dict["lines"][i],
            color=data_dict["colors"][i],
            label=data_dict["labels"][i],
            marker=".",
            markersize=0,
            lw=0.8,
        )
    #
    # --- Format Tick marks automatically around days
    #
    major_locator = AutoDateLocator()
    ax.xaxis.set_major_locator(major_locator)
    formatter = ConciseDateFormatter(
        major_locator, formats=TICK_FORMATTING, offset_formats=OFFSET_TICK_FORMATTING
    )
    ax.xaxis.set_major_formatter(formatter)

    xticks = ax.get_xticks()
    for tick in xticks:
        ax.vlines(
            tick,
            data_dict["limits"]["y_min"],
            data_dict["limits"]["y_max"],
            linestyle="dotted",
            colors="black",
        )

    if "limit_lines" in data_dict.keys():
        #
        # --- Define positioning for limit line text
        #
        xbound = ax.get_xbound()
        xpos = xbound[-1] + 0.01 * (xbound[-1] - xbound[0])
        for k, v in data_dict["limit_lines"].items():
            plt.axhline(v[0], color="#F05D5D")
            plt.text(xpos, v[0], f"{k}\nLimit", color=v[1])

    ax.set_xlabel("Coordinated Universal Time")
    ax.set_ylabel(data_dict["units"])
    ax.legend(loc="upper left")
    plt.grid(axis="y")
    plt.title(data_dict["title"])
    #
    # --- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
    #
    fig = plt.gcf()
    fig.set_size_inches(8.0, 5.0)
    #
    # --- save the plot in png format
    #
    plt.savefig(data_dict["filename"], format="png", dpi=300)

    plt.close("all")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flight", "test"], required=True, help="Determine running mode.")
    parser.add_argument("-d", "--data", required = False, help = "Directory path to determine input location of data.")
    parser.add_argument("-p", "--path", required=False, help="Directory path to determine output location of plot.")
    args = parser.parse_args()
    #
    # --- Determine if running in test mode and change pathing if so
    #
    if args.mode == "test":
        #
        # --- Path output to same location as unit tests
        #
        if args.data:
            GOES_DATA_DIR = Path(args.data)
        else:
            GOES_DATA_DIR = Path(os.getcwd(), "test", '_outTest')

        if args.path:
            GOES_PLOT_DIR = Path(args.path)
        else:
            GOES_PLOT_DIR = Path(os.getcwd(), "test", "_outTest", "GOES", "Plots")
        
        os.makedirs(GOES_PLOT_DIR, exist_ok=True)
        try:
            plot_goes_data()
        except json.decoder.JSONDecodeError:
            traceback.print_exc()
            #: No cleanup of lock files
    elif args.mode == "flight":
        #: Create a lock file and exit strategy in case of stall.
        name = os.path.basename(__file__).split(".")[0]
        user = os.getenv("USER", "mta")
        lock = Path("/tmp", user, f"{name}.lock")

        #: If lock file exists, read the pid and kill the process, then remove the lock file
        if os.path.isfile(lock):
            with open(lock) as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGTERM)
            os.remove(lock)
        
        #: Lock file with current pid
        pid = os.getpid()
        os.makedirs(lock.parent, exist_ok = True)
        with open(lock, 'w') as f:
            f.write(str(pid))

        plot_goes_data()

        #: Remove lock file once process is completed
        os.remove(lock)